"""Fix unique constraint to allow rematching

Revision ID: 20251003_006
Revises: d156e58a8030
Create Date: 2025-10-03 16:59:27

Problem:
    Global UNIQUE(user_a, user_b) constraint prevents ANY rematch between users,
    even after previous match is completed. This blocks legitimate rematching.

Solution:
    1. Remove global uq_match_users constraint
    2. Expand partial unique index to cover 'proposed' AND 'active' statuses
       (prevents concurrent matches, but allows sequential rematches)
    3. Add CHECK constraint to prevent self-matching

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20251003_006"
down_revision: str | None = "d156e58a8030"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Allow rematching by removing global unique constraint."""
    # 1. Drop the global UNIQUE(user_a, user_b) constraint
    op.drop_constraint("uq_match_users", "matches", type_="unique")

    # 2. Drop old partial index (only on 'proposed')
    op.drop_index("idx_match_pair_proposed", table_name="matches")

    # 3. Create new partial unique index for OPEN matches ('proposed' OR 'active')
    #    This prevents concurrent matches but allows rematches after completion
    op.execute(
        """
        CREATE UNIQUE INDEX idx_match_pair_open
        ON matches(u_lo, u_hi)
        WHERE status IN ('proposed', 'active');
    """
    )

    # 4. Add CHECK constraint to prevent self-matching (user_a cannot equal user_b)
    op.create_check_constraint("chk_match_no_self", "matches", "user_a <> user_b")


def downgrade() -> None:
    """Restore global unique constraint (blocks rematching)."""
    # Remove CHECK constraint
    op.drop_constraint("chk_match_no_self", "matches", type_="check")

    # Drop new partial index
    op.drop_index("idx_match_pair_open", table_name="matches")

    # Restore old partial index (only 'proposed')
    op.execute(
        """
        CREATE UNIQUE INDEX idx_match_pair_proposed
        ON matches(u_lo, u_hi)
        WHERE status = 'proposed';
    """
    )

    # Restore global UNIQUE constraint
    op.create_unique_constraint("uq_match_users", "matches", ["user_a", "user_b"])
