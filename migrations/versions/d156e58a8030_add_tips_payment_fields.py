"""add_tips_payment_fields

Revision ID: d156e58a8030
Revises: 20251003_004
Create Date: 2025-10-03 16:19:09.668360

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d156e58a8030"
down_revision: str | None = "20251003_004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add telegram_payment_id and invoice_payload to tips table."""
    # Add new columns
    op.add_column("tips", sa.Column("telegram_payment_id", sa.String(128), nullable=True))
    op.add_column("tips", sa.Column("invoice_payload", sa.Text(), nullable=True))

    # Add unique constraint on telegram_payment_id
    op.create_unique_constraint("uq_tips_telegram_payment_id", "tips", ["telegram_payment_id"])

    # Add index for faster lookups
    op.create_index("idx_tips_telegram_payment_id", "tips", ["telegram_payment_id"])


def downgrade() -> None:
    """Remove telegram_payment_id and invoice_payload from tips table."""
    op.drop_index("idx_tips_telegram_payment_id", table_name="tips")
    op.drop_constraint("uq_tips_telegram_payment_id", "tips", type_="unique")
    op.drop_column("tips", "invoice_payload")
    op.drop_column("tips", "telegram_payment_id")
