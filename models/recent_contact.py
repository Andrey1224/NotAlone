"""Recent contact model for preventing repeat matches."""

from datetime import datetime

from sqlalchemy import BigInteger, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from core.db import Base


class RecentContact(Base):
    """Recent contact model to prevent repeat matches within cooldown period."""

    __tablename__ = "recent_contacts"

    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, nullable=False)
    other_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, nullable=False)
    until: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    def __repr__(self) -> str:
        return f"<RecentContact(user_id={self.user_id}, other_id={self.other_id}, until={self.until})>"
