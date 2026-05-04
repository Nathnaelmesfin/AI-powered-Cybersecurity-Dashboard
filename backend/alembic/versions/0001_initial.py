"""initial tables

Revision ID: 0001_initial
Revises: 
Create Date: 2026-04-30
"""
from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table("roles", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("name", sa.String(64), nullable=False, unique=True))
    op.create_table("users", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("username", sa.String(128), nullable=False, unique=True), sa.Column("role_id", sa.Integer(), sa.ForeignKey("roles.id"), nullable=False))
    op.create_table("assets", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("name", sa.String(255), nullable=False, unique=True), sa.Column("asset_type", sa.String(32), nullable=False), sa.Column("status", sa.String(32), nullable=False), sa.Column("risk_score", sa.Integer(), nullable=False), sa.Column("owner", sa.String(255)), sa.Column("location", sa.String(255)))
    op.create_table("incidents", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("title", sa.String(255), nullable=False), sa.Column("severity", sa.String(32), nullable=False), sa.Column("status", sa.String(32), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.Column("asset_id", sa.Integer()), sa.Column("summary", sa.Text()))
    op.create_table("playbook_runs", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("run_id", sa.String(64), nullable=False, unique=True), sa.Column("playbook_id", sa.Integer(), nullable=False), sa.Column("mode", sa.String(32), nullable=False), sa.Column("status", sa.String(32), nullable=False), sa.Column("requested_by", sa.String(128), nullable=False), sa.Column("requires_approval", sa.Boolean(), nullable=False), sa.Column("approved_by", sa.String(128)))
    op.create_table("audit_logs", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("actor", sa.String(128), nullable=False), sa.Column("action", sa.String(255), nullable=False), sa.Column("target", sa.String(255), nullable=False), sa.Column("details", sa.Text()), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    op.create_table("telemetry_events", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("source", sa.String(128), nullable=False), sa.Column("event_type", sa.String(128), nullable=False), sa.Column("severity", sa.String(32), nullable=False), sa.Column("payload", sa.Text(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))


def downgrade() -> None:
    for table in ["telemetry_events", "audit_logs", "playbook_runs", "incidents", "assets", "users", "roles"]:
        op.drop_table(table)
