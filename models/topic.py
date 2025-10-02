from sqlalchemy import String, Integer, BigInteger, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.db import Base


class Topic(Base):
    """Topic model."""

    __tablename__ = "topics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    slug: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(128), nullable=False)

    # Relationships
    users: Mapped[list["UserTopic"]] = relationship("UserTopic", back_populates="topic", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Topic(id={self.id}, slug={self.slug})>"


class UserTopic(Base):
    """User-Topic relationship with weight."""

    __tablename__ = "user_topics"

    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    topic_id: Mapped[int] = mapped_column(Integer, ForeignKey("topics.id", ondelete="CASCADE"), primary_key=True)
    weight: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="topics")  # type: ignore
    topic: Mapped["Topic"] = relationship("Topic", back_populates="users")

    __table_args__ = (Index("idx_user_topics_topic_id", "topic_id"),)

    def __repr__(self) -> str:
        return f"<UserTopic(user_id={self.user_id}, topic_id={self.topic_id}, weight={self.weight})>"
