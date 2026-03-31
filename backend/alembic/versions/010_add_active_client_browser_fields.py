"""Add browser metadata fields to active clients

Revision ID: 010
Revises: 009
Create Date: 2026-03-31
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "010"
down_revision: Union[str, None] = "009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("active_clients", sa.Column("first_seen_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
    op.add_column("active_clients", sa.Column("user_agent", sa.String(length=512), nullable=True))
    op.add_column("active_clients", sa.Column("browser_language", sa.String(length=32), nullable=True))
    op.add_column("active_clients", sa.Column("platform", sa.String(length=64), nullable=True))
    op.add_column("active_clients", sa.Column("timezone", sa.String(length=64), nullable=True))
    op.add_column("active_clients", sa.Column("screen_width", sa.Integer(), nullable=True))
    op.add_column("active_clients", sa.Column("screen_height", sa.Integer(), nullable=True))
    op.add_column("active_clients", sa.Column("viewport_width", sa.Integer(), nullable=True))
    op.add_column("active_clients", sa.Column("viewport_height", sa.Integer(), nullable=True))
    op.add_column("active_clients", sa.Column("current_path", sa.String(length=255), nullable=True))
    op.add_column("active_clients", sa.Column("referrer", sa.String(length=512), nullable=True))
    op.add_column("active_clients", sa.Column("ip_address", sa.String(length=64), nullable=True))
    op.execute(sa.text("UPDATE active_clients SET first_seen_at = last_seen_at WHERE first_seen_at IS NULL"))


def downgrade() -> None:
    op.drop_column("active_clients", "ip_address")
    op.drop_column("active_clients", "referrer")
    op.drop_column("active_clients", "current_path")
    op.drop_column("active_clients", "viewport_height")
    op.drop_column("active_clients", "viewport_width")
    op.drop_column("active_clients", "screen_height")
    op.drop_column("active_clients", "screen_width")
    op.drop_column("active_clients", "timezone")
    op.drop_column("active_clients", "platform")
    op.drop_column("active_clients", "browser_language")
    op.drop_column("active_clients", "user_agent")
    op.drop_column("active_clients", "first_seen_at")
