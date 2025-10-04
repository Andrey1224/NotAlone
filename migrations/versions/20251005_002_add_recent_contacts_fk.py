"""Add foreign keys and index to recent_contacts

Revision ID: 20251005_002
Revises: 20251005_001
Create Date: 2025-10-05

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "20251005_002"
down_revision = "20251005_001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add foreign key constraints to existing recent_contacts table
    # These were missing from Sprint 2 migration but needed for referential integrity
    op.execute(
        """
        ALTER TABLE recent_contacts
        ADD CONSTRAINT fk_recent_contacts_user_id
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    """
    )

    op.execute(
        """
        ALTER TABLE recent_contacts
        ADD CONSTRAINT fk_recent_contacts_other_id
        FOREIGN KEY (other_id) REFERENCES users(id) ON DELETE CASCADE
    """
    )

    # Add index for checking cooldown expiry (if not exists)
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_recent_contacts_until
        ON recent_contacts(until)
    """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_recent_contacts_until")
    op.execute("ALTER TABLE recent_contacts DROP CONSTRAINT IF EXISTS fk_recent_contacts_other_id")
    op.execute("ALTER TABLE recent_contacts DROP CONSTRAINT IF EXISTS fk_recent_contacts_user_id")
