"""Sprint 5: Safety & Moderation - reports, moderation_actions

Revision ID: 20251005_001
Revises: 20251003_006
Create Date: 2025-10-05

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "20251005_001"
down_revision = "20251003_006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Create reports table with FK constraints and validation
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS reports (
            id BIGSERIAL PRIMARY KEY,
            chat_session_id BIGINT REFERENCES chat_sessions(id) ON DELETE SET NULL,
            from_user BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            to_user BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            reason VARCHAR(24) NOT NULL,
            comment TEXT,
            status VARCHAR(16) NOT NULL DEFAULT 'new',
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            closed_at TIMESTAMPTZ,
            CONSTRAINT chk_report_reason CHECK (reason IN ('spam','abuse','danger','other')),
            CONSTRAINT chk_report_status CHECK (status IN ('new','in_review','resolved'))
        )
    """
    )

    # Index for finding open reports
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_reports_open
        ON reports(status) WHERE status IN ('new','in_review')
    """
    )

    # Index for finding reports by target user
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_reports_target_open
        ON reports(to_user, status) WHERE status IN ('new','in_review')
    """
    )

    # Unique constraint: prevent duplicate reports in same session
    op.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS uq_reports_once_per_session
        ON reports(chat_session_id, from_user, to_user, reason)
        WHERE status='new' AND chat_session_id IS NOT NULL
    """
    )

    # 2. Create moderation_actions table
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS moderation_actions (
            id BIGSERIAL PRIMARY KEY,
            target_user BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            action VARCHAR(24) NOT NULL,
            actor VARCHAR(64) NOT NULL,
            reason TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """
    )

    # Index for finding moderation history by user
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_moderation_target
        ON moderation_actions(target_user)
    """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS moderation_actions CASCADE")
    op.execute("DROP TABLE IF EXISTS reports CASCADE")
