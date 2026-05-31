from sqlalchemy import Column, Integer, String, DateTime, Float, Text, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    full_name = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(50), default="compliance_officer")
    institution_name = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    jobs = relationship("Job", back_populates="user")
    audit_logs = relationship("AuditLog", back_populates="user")


class Job(Base):
    """An upload + generation job submitted by a compliance officer."""
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Report configuration (user-provided per upload)
    report_type = Column(String(10), nullable=False)   # DEFT, DCTR, DIFT, DSTR
    report_code = Column(String(10), nullable=False)
    entity_reference = Column(String(255), nullable=True)
    rentity_id = Column(String(50), nullable=True)
    rentity_branch = Column(String(255), nullable=True)
    submission_code = Column(String(10), nullable=True)
    currency_code_local = Column(String(10), default="MZN")
    reporting_user_code = Column(String(100), nullable=True)
    schema_version = Column(String(20), default="5.0.2")

    # Upload
    original_filename = Column(String(500), nullable=False)
    upload_path = Column(String(500), nullable=False)
    upload_size_bytes = Column(Integer, nullable=True)

    # Processing state
    status = Column(String(50), default="pending")
    # pending | processing | validating | completed | failed

    # Results
    total_transactions = Column(Integer, default=0)
    reported_count = Column(Integer, default=0)
    exception_count = Column(Integer, default=0)
    xml_files_generated = Column(Integer, default=0)

    # Logs
    processing_log = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)

    # Redis job id for tracking
    rq_job_id = Column(String(100), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="jobs")
    xml_files = relationship("XMLFile", back_populates="job")
    exceptions = relationship("ExceptionRecord", back_populates="job")


class XMLFile(Base):
    """A generated XML file linked to a job."""
    __tablename__ = "xml_files"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    filename = Column(String(500), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size_bytes = Column(Integer, nullable=True)
    transaction_count = Column(Integer, default=0)
    chunk_index = Column(Integer, default=1)
    is_valid = Column(Boolean, nullable=True)   # XSD validation result
    validation_errors = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    job = relationship("Job", back_populates="xml_files")


class ExceptionRecord(Base):
    """A transaction that failed processing or XSD validation."""
    __tablename__ = "exceptions"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    transaction_id = Column(String(255), nullable=True)
    error_reason = Column(Text, nullable=False)
    error_type = Column(String(100), nullable=True)
    # missing_field | validation_error | xml_error | processing_error
    raw_data = Column(JSON, nullable=True)
    status = Column(String(50), default="pending")
    # pending | resolved | ignored
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    job = relationship("Job", back_populates="exceptions")


class AuditLog(Base):
    """Every significant action is logged here."""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String(100), nullable=False)
    resource_type = Column(String(100), nullable=True)
    resource_id = Column(String(100), nullable=True)
    details = Column(JSON, nullable=True)
    ip_address = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="audit_logs")



class Schedule(Base):
    """Recurring XML generation schedule."""
    __tablename__ = "schedules"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(255), nullable=False)
    report_type = Column(String(10), nullable=False)   # EFT / IFT / CTR
    period_type = Column(String(20), nullable=False)   # single / weekly / monthly
    run_time = Column(String(10), nullable=True)        # HH:MM e.g. "06:00"
    is_active = Column(Boolean, default=True)
    db_path = Column(String(500), nullable=True)

    # Report config
    rentity_id = Column(String(50), nullable=True)
    rentity_branch = Column(String(255), nullable=True)
    submission_code = Column(String(10), default="E")
    currency_code_local = Column(String(10), default="MZN")
    reporting_user_code = Column(String(100), nullable=True)
    entity_name = Column(String(100), default="KAIROS")
    institution_name = Column(String(255), nullable=True)
    institution_code = Column(String(20), nullable=True)

    last_run_at = Column(DateTime(timezone=True), nullable=True)
    next_run_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", backref="schedules")
