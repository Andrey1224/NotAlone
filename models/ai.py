from datetime import datetime

from sqlalchemy import BigInteger, String, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from core.db import Base


class AiHint(Base):
    """AI coaching hints model."""

    __tablename__ = "ai_hints"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    chat_session_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    hint_type: Mapped[str] = mapped_column(String(16), nullable=False)  # empathy, question, boundary
    text: Mapped[str] = mapped_column(String(512), nullable=False)
    accepted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return f"<AiHint(id={self.id}, chat_session_id={self.chat_session_id}, hint_type={self.hint_type})>"


class SafetyFlag(Base):
    """Safety flags for moderation."""

    __tablename__ = "safety_flags"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    chat_session_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    label: Mapped[str] = mapped_column(String(32), nullable=False)  # toxicity, self-harm, etc.
    severity: Mapped[str] = mapped_column(String(16), nullable=False)  # low, medium, high, critical
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return f"<SafetyFlag(id={self.id}, label={self.label}, severity={self.severity})>"
