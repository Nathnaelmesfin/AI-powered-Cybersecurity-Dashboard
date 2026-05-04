"""add auth permission tables

Revision ID: 0002_auth_permissions
Revises: 0001_initial
Create Date: 2026-04-30
"""
from alembic import op
import sqlalchemy as sa

revision = "0002_auth_permissions"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "role_permissions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("role_id", sa.Integer(), sa.ForeignKey("roles.id"), nullable=False),
        sa.Column("action", sa.String(128), nullable=False),
    )
    op.add_column("users", sa.Column("password_hash", sa.String(255), nullable=False, server_default=""))


def downgrade() -> None:
    op.drop_column("users", "password_hash")
    op.drop_table("role_permissions")
