from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User, Job, XMLFile, ExceptionRecord, AuditLog

# ── REPORTS ──────────────────────────────────────────────────────────────
router = APIRouter()


@router.get("/")
def list_reports(
    report_type: str | None = None,
    status: str | None = None,
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(XMLFile).join(Job).filter(Job.user_id == current_user.id)
    if report_type:
        q = q.filter(Job.report_type == report_type.upper())
    if status == "valid":
        q = q.filter(XMLFile.is_valid == True)
    elif status == "invalid":
        q = q.filter(XMLFile.is_valid == False)

    files = q.order_by(XMLFile.created_at.desc()).offset(skip).limit(limit).all()
    return [
        {
            "id": f.id,
            "job_id": f.job_id,
            "filename": f.filename,
            "report_type": f.job.report_type,
            "transaction_count": f.transaction_count,
            "is_valid": f.is_valid,
            "file_size_bytes": f.file_size_bytes,
            "created_at": f.created_at.isoformat() if f.created_at else None,
            "job_status": f.job.status,
        }
        for f in files
    ]
