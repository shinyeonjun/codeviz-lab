"""execution_steps에 trace 컨텍스트 컬럼 추가

Revision ID: 20260330_000002
Revises: 20260330_000001
Create Date: 2026-03-30 00:00:02
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260330_000002"
down_revision = "20260330_000001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "execution_steps",
        sa.Column("globals_snapshot", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
    )
    op.add_column(
        "execution_steps",
        sa.Column("call_stack", sa.JSON(), nullable=False, server_default=sa.text("'[]'::json")),
    )
    op.add_column(
        "execution_steps",
        sa.Column("metadata", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
    )

    op.alter_column("execution_steps", "globals_snapshot", server_default=None)
    op.alter_column("execution_steps", "call_stack", server_default=None)
    op.alter_column("execution_steps", "metadata", server_default=None)


def downgrade() -> None:
    op.drop_column("execution_steps", "metadata")
    op.drop_column("execution_steps", "call_stack")
    op.drop_column("execution_steps", "globals_snapshot")
