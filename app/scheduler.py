"""
scheduler.py — APScheduler process for automatic XML generation.
Run in a separate terminal: python -m app.scheduler

Reads the schedules table every minute and fires jobs whose run_time
matches the current time. Uses RQ to execute in the worker process.
"""
import os
import time
import logging
import datetime
from redis import Redis
from rq import Queue
from apscheduler.schedulers.blocking import BlockingScheduler

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("kairos.scheduler")

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")


def _get_date_range(period_type: str):
    today = datetime.date.today()
    if period_type == "single":
        return str(today), str(today)
    elif period_type == "weekly":
        date_to   = today
        date_from = today - datetime.timedelta(days=6)
        return str(date_from), str(date_to)
    elif period_type == "monthly":
        date_to   = today
        date_from = today - datetime.timedelta(days=29)
        return str(date_from), str(date_to)
    return str(today), str(today)


def check_and_fire_schedules():
    """Called every minute — fire any schedules whose run_time matches now."""
    from app.core.database import SessionLocal
    from app.models.user import Schedule, Job
    from app.core.config import get_settings

    settings   = get_settings()
    db         = SessionLocal()
    redis_conn = Redis.from_url(REDIS_URL)
    q          = Queue("kairos_jobs", connection=redis_conn)

    now_str = datetime.datetime.now().strftime("%H:%M")

    try:
        active = db.query(Schedule).filter(Schedule.is_active == True).all()
        for sched in active:
            if sched.run_time != now_str:
                continue

            logger.info("Firing schedule %d — %s %s %s",
                        sched.id, sched.name, sched.report_type, sched.period_type)

            REPORT_CODES = {"EFT": "DEFT", "IFT": "DIFT", "CTR": "DCTR"}
            report_code  = REPORT_CODES.get(sched.report_type, "DEFT")
            date_from, date_to = _get_date_range(sched.period_type)

            db_path = sched.db_path or os.path.join(
                os.path.dirname(__file__), "..", "kairos_banking.db"
            )
            xsd_path = os.path.join(
                os.path.dirname(__file__), "..", "scripts", "goAML_XML_Schema_5.xsd"
            )

            # Create job record
            job = Job(
                user_id=sched.user_id,
                report_type=sched.report_type,
                report_code=report_code,
                original_filename=f"SCHEDULED:{sched.name}:{date_from}",
                upload_path=db_path,
                rentity_id=sched.rentity_id,
                rentity_branch=sched.rentity_branch,
                submission_code=sched.submission_code,
                currency_code_local=sched.currency_code_local,
                reporting_user_code=sched.reporting_user_code,
                status="pending",
            )
            db.add(job)
            db.commit()
            db.refresh(job)

            output_dir = os.path.join(settings.XML_OUTPUT_DIR, str(job.id))

            config = {
                "mode":                "database",
                "report_type":         sched.report_type,
                "report_code":         report_code,
                "db_path":             db_path,
                "date_from":           date_from,
                "date_to":             date_to,
                "period_type":         sched.period_type,
                "output_dir":          output_dir,
                "xsd_path":            xsd_path if os.path.exists(xsd_path) else None,
                "entity_name":         sched.entity_name or "KAIROS",
                "institution_name":    sched.institution_name or "Kairos Bank Mozambique S.A.",
                "institution_code":    sched.institution_code or "00830",
                "rentity_id":          sched.rentity_id or "33",
                "rentity_branch":      sched.rentity_branch or "Sede",
                "submission_code":     sched.submission_code or "E",
                "currency_code_local": sched.currency_code_local or "MZN",
                "reporting_user_code": sched.reporting_user_code or "ComplianceUser01",
            }

            rq_job = q.enqueue(
                "app.worker.run_job",
                kwargs={"db_job_id": job.id, "config": config},
                job_timeout=3600,
            )
            job.rq_job_id = rq_job.id

            # Update schedule last/next run
            sched.last_run_at = datetime.datetime.utcnow()
            sched.next_run_at = datetime.datetime.utcnow() + datetime.timedelta(days=1)
            db.commit()

            logger.info("Schedule %d fired → job %d", sched.id, job.id)

    except Exception:
        logger.exception("Scheduler error")
    finally:
        db.close()


if __name__ == "__main__":
    logger.info("Kairos scheduler starting...")

    scheduler = BlockingScheduler()
    scheduler.add_job(
        check_and_fire_schedules,
        trigger="cron",
        minute="*",          # check every minute
        id="schedule_check",
    )

    logger.info("Scheduler running — checks every minute for due schedules")
    logger.info("Press Ctrl+C to stop")

    try:
        scheduler.start()
    except KeyboardInterrupt:
        logger.info("Scheduler stopped")
