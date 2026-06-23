"""사용자별 학습 진행 테이블 추가

Revision ID: 20260611_000003
Revises: 20260330_000002
Create Date: 2026-06-11 05:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260611_000003"
down_revision = "20260330_000002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "user_lesson_progress",
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("lesson_id", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="studied"),
        sa.Column("first_studied_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_studied_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("study_count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("total_study_seconds", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id", "lesson_id"),
    )


def downgrade() -> None:
    op.drop_table("user_lesson_progress")
