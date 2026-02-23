"""Add user_activity table

Revision ID: 002
Revises: 001
Create Date: 2026-02-23 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "user_activity",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("username", sa.String(length=100), nullable=True),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("message_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_chars", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("short_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("medium_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("long_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("media_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("question_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("reactions_received", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("active_hours", sa.String(length=200), nullable=False, server_default=""),
        sa.Column("bot_mentions", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("bot_replies", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("swear_count", sa.Integer(), nullable=False, server_default="0"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "date", name="uq_user_activity_user_date"),
    )


def downgrade() -> None:
    op.drop_table("user_activity")
