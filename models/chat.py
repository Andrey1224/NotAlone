from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column

from core.db import Base


class ChatSession(Base):
    """Chat session model."""

    __tablename__ = "chat_sessions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    match_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False, index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    rating_a: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 1-5 rating from user_a
    rating_b: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 1-5 rating from user_b

    def __repr__(self) -> str:
        return f"<ChatSession(id={self.id}, match_id={self.match_id})>"
