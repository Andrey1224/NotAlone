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
    msg_count_a: Mapped[int] = mapped_column(Integer, nullable=False, default=0)  # Message count from user_a
    msg_count_b: Mapped[int] = mapped_column(Integer, nullable=False, default=0)  # Message count from user_b
    rating_a: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 1-5 rating from user_a
    rating_b: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 1-5 rating from user_b

    def __repr__(self) -> str:
        return f"<ChatSession(id={self.id}, match_id={self.match_id})>"
