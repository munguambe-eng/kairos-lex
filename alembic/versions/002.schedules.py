"""Add schedules table

Revision ID: 002
Revises: 001
"""
from alembic import op
import sqlalchemy as sa

revision = '002'
down_revision = '001'


def upgrade():
    op.create_table('schedules',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('report_type', sa.String(10), nullable=False),
        sa.Column('period_type', sa.String(20), nullable=False),
        sa.Column('run_time', sa.String(10), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('db_path', sa.String(500), nullable=True),
        sa.Column('rentity_id', sa.String(50), nullable=True),
        sa.Column('rentity_branch', sa.String(255), nullable=True),
        sa.Column('submission_code', sa.String(10), nullable=True),
        sa.Column('currency_code_local', sa.String(10), nullable=True),
        sa.Column('reporting_user_code', sa.String(100), nullable=True),
        sa.Column('entity_name', sa.String(100), nullable=True),
        sa.Column('institution_name', sa.String(255), nullable=True),
        sa.Column('institution_code', sa.String(20), nullable=True),
        sa.Column('last_run_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('next_run_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade():
    op.drop_table('schedules')