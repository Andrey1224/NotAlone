"""Add msg_count_a and msg_count_b to chat_sessions

Revision ID: 20251003_004
Revises: 20251002_003
Create Date: 2025-10-03 18:00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20251003_004"
down_revision: str | None = "20251002_003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Add msg_count_a and msg_count_b columns with default 0
    op.add_column("chat_sessions", sa.Column("msg_count_a", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("chat_sessions", sa.Column("msg_count_b", sa.Integer(), nullable=False, server_default="0"))


def downgrade() -> None:
    # Drop columns
    op.drop_column("chat_sessions", "msg_count_b")
    op.drop_column("chat_sessions", "msg_count_a")
