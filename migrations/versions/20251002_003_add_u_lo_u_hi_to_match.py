"""Add u_lo u_hi fields to Match for deduplication

Revision ID: 20251002_003
Revises: 0bf07bfbb0e1
Create Date: 2025-10-02 18:00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20251002_003"
down_revision: str | None = "0bf07bfbb0e1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Add u_lo and u_hi columns
    op.add_column("matches", sa.Column("u_lo", sa.BigInteger(), nullable=True))
    op.add_column("matches", sa.Column("u_hi", sa.BigInteger(), nullable=True))

    # Populate existing rows with ordered pairs
    op.execute("""
        UPDATE matches
        SET u_lo = LEAST(user_a, user_b),
            u_hi = GREATEST(user_a, user_b)
    """)

    # Make columns NOT NULL
    op.alter_column("matches", "u_lo", nullable=False)
    op.alter_column("matches", "u_hi", nullable=False)

    # Create indexes
    op.create_index(op.f("ix_matches_u_lo"), "matches", ["u_lo"], unique=False)
    op.create_index(op.f("ix_matches_u_hi"), "matches", ["u_hi"], unique=False)

    # Create unique partial index for proposed matches
    op.execute("""
        CREATE UNIQUE INDEX idx_match_pair_proposed
        ON matches (u_lo, u_hi)
        WHERE status = 'proposed'
    """)


def downgrade() -> None:
    # Drop indexes
    op.execute("DROP INDEX IF EXISTS idx_match_pair_proposed")
    op.drop_index(op.f("ix_matches_u_hi"), table_name="matches")
    op.drop_index(op.f("ix_matches_u_lo"), table_name="matches")

    # Drop columns
    op.drop_column("matches", "u_hi")
    op.drop_column("matches", "u_lo")
