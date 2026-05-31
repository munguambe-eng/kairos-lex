from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, case

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User, Job, XMLFile, ExceptionRecord, AuditLog

router = APIRouter()


@router.get("/stats")
def dashboard_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    uid = current_user.id

    total_jobs = db.query(func.count(Job.id)).filter(Job.user_id == uid).scalar() or 0
    pending = db.query(func.count(Job.id)).filter(Job.user_id == uid, Job.status == "pending").scalar() or 0
    processing = db.query(func.count(Job.id)).filter(Job.user_id == uid, Job.status == "processing").scalar() or 0
    completed = db.query(func.count(Job.id)).filter(Job.user_id == uid, Job.status == "completed").scalar() or 0
    failed = db.query(func.count(Job.id)).filter(Job.user_id == uid, Job.status == "failed").scalar() or 0

    total_tx = db.query(func.coalesce(func.sum(Job.total_transactions), 0)).filter(Job.user_id == uid).scalar() or 0
    reported = db.query(func.coalesce(func.sum(Job.reported_count), 0)).filter(Job.user_id == uid).scalar() or 0
    exceptions = db.query(func.coalesce(func.sum(Job.exception_count), 0)).filter(Job.user_id == uid).scalar() or 0
    xml_count = db.query(func.count(XMLFile.id)).join(Job).filter(Job.user_id == uid).scalar() or 0

    # Recent jobs
    recent_jobs = (
        db.query(Job)
        .filter(Job.user_id == uid)
        .order_by(Job.created_at.desc())
        .limit(5)
        .all()
    )

    # Recent XML files
    recent_xml = (
        db.query(XMLFile)
        .join(Job)
        .filter(Job.user_id == uid)
        .order_by(XMLFile.created_at.desc())
        .limit(5)
        .all()
    )

    # Report type breakdown
    type_counts = (
        db.query(Job.report_type, func.count(Job.id))
        .filter(Job.user_id == uid)
        .group_by(Job.report_type)
        .all()
    )

    return {
        "jobs": {
            "total": total_jobs,
            "pending": pending + processing,
            "completed": completed,
            "failed": failed,
        },
        "transactions": {
            "total": int(total_tx),
            "reported": int(reported),
            "exceptions": int(exceptions),
        },
        "xml_files_generated": int(xml_count),
        "by_report_type": {rt: cnt for rt, cnt in type_counts},
        "recent_jobs": [
            {
                "id": j.id,
                "report_type": j.report_type,
                "original_filename": j.original_filename,
                "status": j.status,
                "total_transactions": j.total_transactions,
                "created_at": j.created_at.isoformat() if j.created_at else None,
            }
            for j in recent_jobs
        ],
        "recent_xml": [
            {
                "id": f.id,
                "filename": f.filename,
                "job_id": f.job_id,
                "transaction_count": f.transaction_count,
                "is_valid": f.is_valid,
                "created_at": f.created_at.isoformat() if f.created_at else None,
            }
            for f in recent_xml
        ],
    }
