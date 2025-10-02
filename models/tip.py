from datetime import datetime

from sqlalchemy import BigInteger, String, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column

from core.db import Base


class Tip(Base):
    """Tip/payment model."""

    __tablename__ = "tips"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    match_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    from_user: Mapped[int] = mapped_column(BigInteger, nullable=False)
    to_user: Mapped[int] = mapped_column(BigInteger, nullable=False)
    amount_minor: Mapped[int] = mapped_column(BigInteger, nullable=False)  # Amount in smallest currency unit
    currency: Mapped[str] = mapped_column(String(8), nullable=False, default="XTR")  # Telegram Stars
    provider: Mapped[str] = mapped_column(String(32), nullable=False, default="telegram-stars")
    provider_fee_minor: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    our_commission_minor: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="pending")  # pending, paid, failed
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (Index("idx_tips_match_id", "match_id"),)

    def __repr__(self) -> str:
        return f"<Tip(id={self.id}, from_user={self.from_user}, to_user={self.to_user}, amount={self.amount_minor})>"
