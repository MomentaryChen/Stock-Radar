"""Add active clients table for realtime usage count

Revision ID: 009
Revises: 008
Create Date: 2026-03-31
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "009"
down_revision: Union[str, None] = "008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "active_clients",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("client_id", sa.String(length=64), nullable=False, unique=True),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("idx_active_clients_last_seen_at", "active_clients", ["last_seen_at"])


def downgrade() -> None:
    op.drop_index("idx_active_clients_last_seen_at", table_name="active_clients")
    op.drop_table("active_clients")
