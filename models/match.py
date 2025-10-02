from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from core.db import Base


class Match(Base):
    """Match model for connecting two users."""

    __tablename__ = "matches"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_a: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    user_b: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    # Ordered pair for deduplication: u_lo = min(user_a, user_b), u_hi = max(user_a, user_b)
    u_lo: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    u_hi: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default="proposed"
    )  # proposed, active, declined, expired, completed
    user_a_accepted: Mapped[bool | None] = mapped_column(Boolean, nullable=True, default=None)
    user_b_accepted: Mapped[bool | None] = mapped_column(Boolean, nullable=True, default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    __table_args__ = (
        UniqueConstraint("user_a", "user_b", name="uq_match_users"),
        # Prevent duplicate matches for same pair (regardless of order) in proposed state
        Index("idx_match_pair_proposed", "u_lo", "u_hi", unique=True, postgresql_where=(status == "proposed")),
    )

    def __repr__(self) -> str:
        return f"<Match(id={self.id}, user_a={self.user_a}, user_b={self.user_b}, status={self.status})>"
