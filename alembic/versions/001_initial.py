"""Initial schema

Revision ID: 001
Revises: 
Create Date: 2025-01-01
"""
from alembic import op
import sqlalchemy as sa

revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('full_name', sa.String(255), nullable=False),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('role', sa.String(50), nullable=True),
        sa.Column('institution_name', sa.String(255), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)

    op.create_table('jobs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('report_type', sa.String(10), nullable=False),
        sa.Column('report_code', sa.String(10), nullable=False),
        sa.Column('entity_reference', sa.String(255), nullable=True),
        sa.Column('rentity_id', sa.String(50), nullable=True),
        sa.Column('rentity_branch', sa.String(255), nullable=True),
        sa.Column('submission_code', sa.String(10), nullable=True),
        sa.Column('currency_code_local', sa.String(10), nullable=True),
        sa.Column('reporting_user_code', sa.String(100), nullable=True),
        sa.Column('schema_version', sa.String(20), nullable=True),
        sa.Column('original_filename', sa.String(500), nullable=False),
        sa.Column('upload_path', sa.String(500), nullable=False),
        sa.Column('upload_size_bytes', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(50), nullable=True),
        sa.Column('total_transactions', sa.Integer(), nullable=True),
        sa.Column('reported_count', sa.Integer(), nullable=True),
        sa.Column('exception_count', sa.Integer(), nullable=True),
        sa.Column('xml_files_generated', sa.Integer(), nullable=True),
        sa.Column('processing_log', sa.Text(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('rq_job_id', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table('xml_files',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('job_id', sa.Integer(), nullable=False),
        sa.Column('filename', sa.String(500), nullable=False),
        sa.Column('file_path', sa.String(500), nullable=False),
        sa.Column('file_size_bytes', sa.Integer(), nullable=True),
        sa.Column('transaction_count', sa.Integer(), nullable=True),
        sa.Column('chunk_index', sa.Integer(), nullable=True),
        sa.Column('is_valid', sa.Boolean(), nullable=True),
        sa.Column('validation_errors', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['job_id'], ['jobs.id']),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table('exceptions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('job_id', sa.Integer(), nullable=False),
        sa.Column('transaction_id', sa.String(255), nullable=True),
        sa.Column('error_reason', sa.Text(), nullable=False),
        sa.Column('error_type', sa.String(100), nullable=True),
        sa.Column('raw_data', sa.JSON(), nullable=True),
        sa.Column('status', sa.String(50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['job_id'], ['jobs.id']),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table('audit_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('action', sa.String(100), nullable=False),
        sa.Column('resource_type', sa.String(100), nullable=True),
        sa.Column('resource_id', sa.String(100), nullable=True),
        sa.Column('details', sa.JSON(), nullable=True),
        sa.Column('ip_address', sa.String(50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade():
    op.drop_table('audit_logs')
    op.drop_table('exceptions')
    op.drop_table('xml_files')
    op.drop_table('jobs')
    op.drop_table('users')
