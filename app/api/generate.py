"""
generate.py — API routes for database-mode generation and scheduling.
"""
import os
import datetime
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session
from redis import Redis
from rq import Queue

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.config import get_settings
from app.models.user import User, Job, XMLFile, ExceptionRecord, AuditLog, Schedule

router = APIRouter()
settings = get_settings()

# Default DB path — can be overridden per request
DEFAULT_DB_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "kairos_banking.db"
)

REPORT_CODES = {"EFT": "DEFT", "IFT": "DIFT", "CTR": "DCTR"}


def get_redis():
    return Redis.from_url(settings.REDIS_URL)


# ── Pydantic models ────────────────────────────────────────────────────────

class GenerateRequest(BaseModel):
    report_type: str                    # EFT / IFT / CTR
    date_from: str                      # YYYY-MM-DD
    date_to: str                        # YYYY-MM-DD
    period_type: str = "single"         # single / weekly / monthly
    db_path: str | None = None
    rentity_id: str = "33"
    rentity_branch: str = "Kairos Bank Mozambique Sede"
    submission_code: str = "E"
    currency_code_local: str = "MZN"
    reporting_user_code: str = "ComplianceUser01"
    entity_name: str = "KAIROS"
    institution_name: str = "Kairos Bank Mozambique S.A."
    institution_code: str = "00830"
    schema_version: str = "5.0.2"


class ScheduleCreate(BaseModel):
    name: str
    report_type: str
    period_type: str
    run_time: str = "06:00"             # HH:MM
    db_path: str | None = None
    rentity_id: str = "33"
    rentity_branch: str = "Kairos Bank Mozambique Sede"
    submission_code: str = "E"
    currency_code_local: str = "MZN"
    reporting_user_code: str = "ComplianceUser01"
    entity_name: str = "KAIROS"
    institution_name: str = "Kairos Bank Mozambique S.A."
    institution_code: str = "00830"


# ── Run now ────────────────────────────────────────────────────────────────

@router.post("/run")
def generate_from_database(
    req: GenerateRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    report_type = req.report_type.upper()
    if report_type not in REPORT_CODES:
        raise HTTPException(400, f"Invalid report type. Choose: {list(REPORT_CODES)}")

    if req.period_type in ("weekly", "monthly") and report_type not in ("EFT", "IFT", "CTR"):
        raise HTTPException(400, "Weekly/monthly periods are for structuring detection only")

    db_path = req.db_path or os.path.abspath(DEFAULT_DB_PATH)
    if not os.path.exists(db_path):
        raise HTTPException(400, f"Database not found: {db_path}")

    # Create job record
    job = Job(
        user_id=current_user.id,
        report_type=report_type,
        report_code=REPORT_CODES[report_type],
        original_filename=f"DB:{report_type}:{req.date_from}:{req.date_to}",
        upload_path=db_path,
        rentity_id=req.rentity_id,
        rentity_branch=req.rentity_branch,
        submission_code=req.submission_code,
        currency_code_local=req.currency_code_local,
        reporting_user_code=req.reporting_user_code,
        schema_version=req.schema_version,
        status="pending",
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    output_dir = os.path.join(settings.XML_OUTPUT_DIR, str(job.id))
    xsd_path   = os.path.join(
        os.path.dirname(__file__), "..", "..", "scripts", "goAML_XML_Schema_5.xsd"
    )

    config = {
        "mode":               "database",
        "report_type":        report_type,
        "report_code":        REPORT_CODES[report_type],
        "db_path":            db_path,
        "date_from":          req.date_from,
        "date_to":            req.date_to,
        "period_type":        req.period_type,
        "output_dir":         output_dir,
        "xsd_path":           xsd_path if os.path.exists(xsd_path) else None,
        "entity_name":        req.entity_name,
        "institution_name":   req.institution_name,
        "institution_code":   req.institution_code,
        "rentity_id":         req.rentity_id,
        "rentity_branch":     req.rentity_branch,
        "submission_code":    req.submission_code,
        "currency_code_local":req.currency_code_local,
        "reporting_user_code":req.reporting_user_code,
        "schema_version":     req.schema_version,
    }

    redis_conn = get_redis()
    q = Queue("kairos_jobs", connection=redis_conn)
    rq_job = q.enqueue(
        "app.worker.run_job",
        kwargs={"db_job_id": job.id, "config": config},
        job_timeout=3600,
    )

    job.rq_job_id = rq_job.id
    db.commit()

    db.add(AuditLog(
        user_id=current_user.id,
        action="GENERATE_DB",
        resource_type="job",
        resource_id=str(job.id),
        details={"report_type": report_type, "date_from": req.date_from,
                 "date_to": req.date_to, "period_type": req.period_type},
        ip_address=request.client.host if request.client else None,
    ))
    db.commit()

    return {"job_id": job.id, "status": "pending",
            "message": f"Database generation started for {report_type} {req.date_from}→{req.date_to}"}


# ── Schedules CRUD ─────────────────────────────────────────────────────────

@router.get("/schedules")
def list_schedules(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows = db.query(Schedule).filter(Schedule.user_id == current_user.id).all()
    return [_sched_dict(s) for s in rows]


@router.post("/schedules", status_code=201)
def create_schedule(
    data: ScheduleCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    report_type = data.report_type.upper()
    if report_type not in REPORT_CODES:
        raise HTTPException(400, f"Invalid report type")

    s = Schedule(
        user_id=current_user.id,
        name=data.name,
        report_type=report_type,
        period_type=data.period_type,
        run_time=data.run_time,
        db_path=data.db_path or os.path.abspath(DEFAULT_DB_PATH),
        rentity_id=data.rentity_id,
        rentity_branch=data.rentity_branch,
        submission_code=data.submission_code,
        currency_code_local=data.currency_code_local,
        reporting_user_code=data.reporting_user_code,
        entity_name=data.entity_name,
        institution_name=data.institution_name,
        institution_code=data.institution_code,
        is_active=True,
    )
    db.add(s)
    db.commit()
    db.refresh(s)
    return _sched_dict(s)


@router.patch("/schedules/{schedule_id}/toggle")
def toggle_schedule(
    schedule_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    s = db.query(Schedule).filter(
        Schedule.id == schedule_id,
        Schedule.user_id == current_user.id
    ).first()
    if not s:
        raise HTTPException(404, "Schedule not found")
    s.is_active = not s.is_active
    db.commit()
    return _sched_dict(s)


@router.delete("/schedules/{schedule_id}", status_code=204)
def delete_schedule(
    schedule_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    s = db.query(Schedule).filter(
        Schedule.id == schedule_id,
        Schedule.user_id == current_user.id
    ).first()
    if not s:
        raise HTTPException(404, "Schedule not found")
    db.delete(s)
    db.commit()


def _sched_dict(s: Schedule) -> dict:
    return {
        "id": s.id,
        "name": s.name,
        "report_type": s.report_type,
        "period_type": s.period_type,
        "run_time": s.run_time,
        "is_active": s.is_active,
        "last_run_at": s.last_run_at.isoformat() if s.last_run_at else None,
        "next_run_at": s.next_run_at.isoformat() if s.next_run_at else None,
        "created_at": s.created_at.isoformat() if s.created_at else None,
        "institution_name": s.institution_name,
        "reporting_user_code": s.reporting_user_code,
    }
