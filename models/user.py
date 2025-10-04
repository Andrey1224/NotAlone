from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.db import Base

if TYPE_CHECKING:
    from models.topic import UserTopic


class User(Base):
    """User model."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tg_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False, index=True)
    nickname: Mapped[str] = mapped_column(String(64), nullable=False)
    tz: Mapped[str] = mapped_column(String(32), nullable=False)
    bio_short: Mapped[str | None] = mapped_column(String(160), nullable=True)
    safety_ack: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    topics: Mapped[list["UserTopic"]] = relationship("UserTopic", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<User(id={self.id}, nickname={self.nickname})>"
