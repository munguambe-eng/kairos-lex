from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User, ExceptionRecord, Job

router = APIRouter()


@router.get("/")
def list_exceptions(
    job_id: Optional[int] = Query(None),
    skip: int = 0,
    limit: int = 200,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = (
        db.query(ExceptionRecord)
        .join(Job)
        .filter(Job.user_id == current_user.id)
    )
    if job_id:
        q = q.filter(ExceptionRecord.job_id == job_id)

    rows = q.order_by(ExceptionRecord.created_at.desc()).offset(skip).limit(limit).all()
    return [
        {
            "id": r.id,
            "job_id": r.job_id,
            "transaction_id": r.transaction_id,
            "error_reason": r.error_reason,
            "error_type": r.error_type,
            "raw_data": r.raw_data,
            "status": r.status,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows
    ]
