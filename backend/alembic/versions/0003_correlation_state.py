"""add persistent correlation state

Revision ID: 0003_correlation_state
Revises: 0002_auth_permissions
Create Date: 2026-05-01
"""
from alembic import op
import sqlalchemy as sa

revision = "0003_correlation_state"
down_revision = "0002_auth_permissions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "correlation_state",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("source_key", sa.String(255), nullable=False, unique=True),
        sa.Column("rule", sa.String(128), nullable=False),
        sa.Column("last_alert_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("correlation_state")
