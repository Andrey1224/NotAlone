"""Safety & Moderation models - reports and moderation actions."""

from datetime import datetime

from sqlalchemy import BigInteger, CheckConstraint, DateTime, ForeignKey, Index, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from core.db import Base


class Report(Base):
    """User-generated report (complaint) about another user."""

    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    chat_session_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("chat_sessions.id", ondelete="SET NULL"), nullable=True
    )
    from_user: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    to_user: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    reason: Mapped[str] = mapped_column(String(24), nullable=False)  # spam|abuse|danger|other
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="new")  # new|in_review|resolved
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        # Validate reason
        CheckConstraint("reason IN ('spam','abuse','danger','other')", name="chk_report_reason"),
        # Validate status
        CheckConstraint("status IN ('new','in_review','resolved')", name="chk_report_status"),
        # Index for finding open reports
        Index("idx_reports_open", "status", postgresql_where=text("status IN ('new','in_review')")),
        # Index for finding reports by target user
        Index(
            "idx_reports_target_open",
            "to_user",
            "status",
            postgresql_where=text("status IN ('new','in_review')"),
        ),
        # Prevent duplicate reports in same session
        Index(
            "uq_reports_once_per_session",
            "chat_session_id",
            "from_user",
            "to_user",
            "reason",
            unique=True,
            postgresql_where=text("status='new' AND chat_session_id IS NOT NULL"),
        ),
    )

    def __repr__(self) -> str:
        return f"<Report(id={self.id}, from={self.from_user}, to={self.to_user}, reason={self.reason})>"


class ModerationAction(Base):
    """Admin/automated moderation action history."""

    __tablename__ = "moderation_actions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    target_user: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    action: Mapped[str] = mapped_column(String(24), nullable=False)  # warn|suspend|ban|unban
    actor: Mapped[str] = mapped_column(String(64), nullable=False)  # admin_user or "system"
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    __table_args__ = (Index("idx_moderation_target", "target_user"),)

    def __repr__(self) -> str:
        return f"<ModerationAction(id={self.id}, target={self.target_user}, action={self.action})>"
