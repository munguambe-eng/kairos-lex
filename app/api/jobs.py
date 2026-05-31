import os
import uuid
import shutil
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, Request
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from redis import Redis
from rq import Queue

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.config import get_settings
from app.models.user import User, Job, XMLFile, AuditLog

router = APIRouter()
settings = get_settings()

ALLOWED_EXTENSIONS = {".xlsx", ".xls", ".csv"}
REPORT_CODES = {
    "EFT": "DEFT",
    "IFT": "DIFT",
    "CTR": "DCTR",
    "STR": "DSTR",
}


def get_redis():
    return Redis.from_url(settings.REDIS_URL)


@router.post("/upload")
async def upload_and_generate(
    request: Request,
    file: UploadFile = File(...),
    report_type: str = Form(...),
    rentity_id: str = Form("33"),
    rentity_branch: str = Form("UBA Mozambique Sede"),
    submission_code: str = Form("E"),
    currency_code_local: str = Form("MZN"),
    reporting_user_code: str = Form("ComplianceUser01"),
    schema_version: str = Form("5.0.2"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Validate report type
    report_type = report_type.upper()
    if report_type not in REPORT_CODES:
        raise HTTPException(status_code=400, detail=f"Invalid report type. Choose from: {list(REPORT_CODES.keys())}")

    # Validate file extension
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"File type not allowed. Use: {ALLOWED_EXTENSIONS}")

    # Save upload
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    safe_name = f"{uuid.uuid4()}_{file.filename}"
    upload_path = os.path.join(settings.UPLOAD_DIR, safe_name)

    with open(upload_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    file_size = os.path.getsize(upload_path)

    # Create job record
    report_code = REPORT_CODES[report_type]
    job = Job(
        user_id=current_user.id,
        report_type=report_type,
        report_code=report_code,
        original_filename=file.filename,
        upload_path=upload_path,
        upload_size_bytes=file_size,
        rentity_id=rentity_id,
        rentity_branch=rentity_branch,
        submission_code=submission_code,
        currency_code_local=currency_code_local,
        reporting_user_code=reporting_user_code,
        schema_version=schema_version,
        status="pending",
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    # Enqueue background job
    config = {
        "report_type": report_type,
        "report_code": report_code,
        "rentity_id": rentity_id,
        "rentity_branch": rentity_branch,
        "submission_code": submission_code,
        "currency_code_local": currency_code_local,
        "reporting_user_code": reporting_user_code,
        "schema_version": schema_version,
    }

    output_dir = os.path.join(settings.XML_OUTPUT_DIR, str(job.id))
    xsd_path = os.path.join(os.path.dirname(__file__), "..", "..", "scripts", "goAML_XML_Schema_5.xsd")

    redis_conn = get_redis()
    q = Queue("kairos_jobs", connection=redis_conn)
  # NEW — replace with this
    rq_job = q.enqueue(
    "app.worker.run_job",
    kwargs={
        "db_job_id": job.id,
        "filepath": upload_path,
        "output_dir": output_dir,
        "config": config,
        "xsd_path": xsd_path if os.path.exists(xsd_path) else None,
    },
    job_timeout=3600,
    )
    job.rq_job_id = rq_job.id
    db.commit()

    # Audit
    db.add(AuditLog(
        user_id=current_user.id,
        action="UPLOAD",
        resource_type="job",
        resource_id=str(job.id),
        details={"filename": file.filename, "report_type": report_type},
        ip_address=request.client.host if request.client else None,
    ))
    db.commit()

    return {
        "job_id": job.id,
        "status": "pending",
        "message": f"File uploaded. Processing {report_type} report in background.",
        "rq_job_id": rq_job.id,
    }


@router.get("/")
def list_jobs(
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    jobs = (
        db.query(Job)
        .filter(Job.user_id == current_user.id)
        .order_by(Job.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return [_job_to_dict(j) for j in jobs]


@router.get("/{job_id}")
def get_job(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    job = db.query(Job).filter(Job.id == job_id, Job.user_id == current_user.id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return _job_to_dict(job, include_log=True)


@router.get("/{job_id}/xml-files")
def list_xml_files(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    job = db.query(Job).filter(Job.id == job_id, Job.user_id == current_user.id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    files = db.query(XMLFile).filter(XMLFile.job_id == job_id).all()
    return [
        {
            "id": f.id,
            "filename": f.filename,
            "size_bytes": f.file_size_bytes,
            "transaction_count": f.transaction_count,
            "chunk_index": f.chunk_index,
            "is_valid": f.is_valid,
            "validation_errors": f.validation_errors,
            "created_at": f.created_at.isoformat() if f.created_at else None,
        }
        for f in files
    ]


@router.get("/{job_id}/download/{file_id}")
def download_xml(
    job_id: int,
    file_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    job = db.query(Job).filter(Job.id == job_id, Job.user_id == current_user.id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    xml_file = db.query(XMLFile).filter(XMLFile.id == file_id, XMLFile.job_id == job_id).first()
    if not xml_file:
        raise HTTPException(status_code=404, detail="File not found")

    if not os.path.exists(xml_file.file_path):
        raise HTTPException(status_code=404, detail="File no longer exists on disk")

    db.add(AuditLog(
        user_id=current_user.id,
        action="DOWNLOAD_XML",
        resource_type="xml_file",
        resource_id=str(file_id),
        details={"filename": xml_file.filename},
    ))
    db.commit()

    return FileResponse(
        path=xml_file.file_path,
        filename=xml_file.filename,
        media_type="application/xml",
    )


def _job_to_dict(job: Job, include_log: bool = False) -> dict:
    d = {
        "id": job.id,
        "report_type": job.report_type,
        "report_code": job.report_code,
        "original_filename": job.original_filename,
        "status": job.status,
        "total_transactions": job.total_transactions,
        "reported_count": job.reported_count,
        "exception_count": job.exception_count,
        "xml_files_generated": job.xml_files_generated,
        "error_message": job.error_message,
        "created_at": job.created_at.isoformat() if job.created_at else None,
        "completed_at": job.completed_at.isoformat() if job.completed_at else None,
        "rentity_branch": job.rentity_branch,
        "reporting_user_code": job.reporting_user_code,
    }
    if include_log:
        d["processing_log"] = job.processing_log
    return d
