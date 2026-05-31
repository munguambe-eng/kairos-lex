"""
worker.py — RQ background worker.
Handles both excel and database generation modes.
Run: python -m app.worker
"""
import os, sys, logging, datetime
from redis import Redis
from rq import Queue
from rq.worker import SimpleWorker

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("kairos.worker")

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
QUEUES    = ["kairos_jobs"]


def run_job(db_job_id: int, config: dict = None,
            # legacy params kept for backward compat
            filepath: str = None, output_dir: str = None,
            xsd_path: str = None):
    """
    Unified job runner. config dict drives everything.
    Legacy callers that pass filepath/output_dir are auto-converted.
    """
    from sqlalchemy.orm import Session
    from app.core.database import SessionLocal
    from app.models.user import Job, XMLFile, ExceptionRecord
    from app.services.xml_generator import run_generation

    # Backward compat — wrap legacy params into config
    if config is None:
        config = {}
    if filepath and "filepath" not in config:
        config["mode"]       = config.get("mode", "excel")
        config["filepath"]   = filepath
        config["output_dir"] = output_dir or "./xml_output"
        config["xsd_path"]   = xsd_path
    if "output_dir" not in config:
        config["output_dir"] = os.path.join(
            os.getenv("XML_OUTPUT_DIR", "./xml_output"), str(db_job_id)
        )

    db: Session = SessionLocal()
    job = None
    try:
        job = db.query(Job).filter(Job.id == db_job_id).first()
        if not job:
            logger.error("Job %d not found", db_job_id)
            return

        job.status = "processing"
        db.commit()
        logger.info("Worker starting job %d | mode=%s", db_job_id, config.get("mode"))

        # Enrich config from job record if not already set
        config.setdefault("report_type",         job.report_type)
        config.setdefault("report_code",         job.report_code)
        config.setdefault("rentity_id",          job.rentity_id or "33")
        config.setdefault("rentity_branch",      job.rentity_branch or "Sede")
        config.setdefault("submission_code",     job.submission_code or "E")
        config.setdefault("currency_code_local", job.currency_code_local or "MZN")
        config.setdefault("reporting_user_code", job.reporting_user_code or "ComplianceUser01")
        config.setdefault("schema_version",      job.schema_version or "5.0.2")

        result = run_generation(config)

        # ── Persist XML file records ───────────────────────────────────
        for i, meta in enumerate(result.get("xml_files", [])):
            xml_rec = XMLFile(
                job_id=db_job_id,
                filename=meta["filename"],
                file_path=meta["path"],
                file_size_bytes=meta.get("size"),
                transaction_count=meta.get("transactions", 0),
                chunk_index=i + 1,
                is_valid=meta.get("is_valid"),
                validation_errors=str(meta.get("validation_errors", "")),
            )
            db.add(xml_rec)

        # ── Persist exceptions ─────────────────────────────────────────
        for exc in result.get("exceptions", []):
            exc_rec = ExceptionRecord(
                job_id=db_job_id,
                transaction_id=exc.get("transaction_id"),
                error_reason=exc.get("error_reason", "Unknown error"),
                error_type=exc.get("error_type", "processing_error"),
                raw_data=exc.get("raw_data", {}),
                status="pending",
            )
            db.add(exc_rec)

        # ── Update job ─────────────────────────────────────────────────
        job.status              = result["status"]
        job.total_transactions  = result.get("total_transactions", 0)
        job.reported_count      = result.get("reported_count", 0)
        job.exception_count     = result.get("exception_count", 0)
        job.xml_files_generated = len(result.get("xml_files", []))
        job.processing_log      = "\n".join(result.get("log", []))
        job.completed_at        = datetime.datetime.utcnow()

        if result["status"] == "failed":
            job.error_message = result["log"][-1] if result["log"] else "Unknown error"

        db.commit()
        logger.info("Job %d done — status=%s reported=%d exceptions=%d",
                    db_job_id, result["status"],
                    result.get("reported_count", 0), result.get("exception_count", 0))

    except Exception as exc:
        logger.exception("Worker error on job %d", db_job_id)
        if job:
            job.status        = "failed"
            job.error_message = str(exc)
            job.completed_at  = datetime.datetime.utcnow()
            db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    redis_conn = Redis.from_url(REDIS_URL)
    queues     = [Queue(name, connection=redis_conn) for name in QUEUES]
    worker     = SimpleWorker(queues, connection=redis_conn)
    logger.info("Kairos worker started — queues: %s", QUEUES)
    worker.work()
