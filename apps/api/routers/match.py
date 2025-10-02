"""Match endpoints."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.deps import get_db

router = APIRouter()


class MatchFindRequest(BaseModel):
    """Request to find a match."""

    user_id: int
    topics: list[str]
    timezone: str


class MatchConfirmRequest(BaseModel):
    """Request to confirm a match."""

    match_id: int
    user_id: int
    accepted: bool


async def find_match(request: MatchFindRequest, db: AsyncSession = Depends(get_db)) -> dict[str, str]:
    """Find a match for user."""
    from datetime import datetime

    from sqlalchemy import select

    from apps.api.deps import get_redis_client
    from models.user import User

    # Validate user exists and has profile with ≥2 topics
    result = await db.execute(select(User).where(User.tg_id == request.user_id))
    user = result.scalar_one_or_none()

    if not user:
        return {"status": "error", "message": "User not found"}

    if not user.safety_ack:
        return {"status": "error", "message": "Safety acknowledgement required"}

    # Check user has ≥2 topics
    from sqlalchemy import func

    from models.topic import UserTopic

    topic_count_result = await db.execute(select(func.count(UserTopic.topic_id)).where(UserTopic.user_id == user.id))
    topic_count = topic_count_result.scalar()

    if topic_count < 2:
        return {"status": "error", "message": "At least 2 topics required"}

    # Add to Redis Stream
    redis_client = await get_redis_client()

    payload = {
        "user_id": str(user.id),
        "tg_id": str(request.user_id),
        "topics": ",".join(request.topics),
        "timezone": request.timezone,
        "requested_at": datetime.utcnow().isoformat(),
    }

    # XADD to match.find stream
    stream_id = await redis_client.xadd("match.find", payload)

    return {
        "status": "queued",
        "user_id": str(request.user_id),
        "stream_id": stream_id,
        "message": "Searching for match...",
    }


async def confirm_match(request: MatchConfirmRequest, db: AsyncSession = Depends(get_db)) -> dict[str, str]:
    """Confirm or decline a match."""
    from datetime import datetime, timedelta

    from sqlalchemy import select

    from models.chat import ChatSession
    from models.match import Match
    from models.recent_contact import RecentContact
    from models.user import User

    # Get match
    result = await db.execute(select(Match).where(Match.id == request.match_id))
    match = result.scalar_one_or_none()

    if not match:
        return {"status": "error", "message": "Match not found"}

    # Get user to determine which side they are
    user_result = await db.execute(select(User).where(User.tg_id == request.user_id))
    user = user_result.scalar_one_or_none()

    if not user:
        return {"status": "error", "message": "User not found"}

    # Update acceptance status
    if user.id == match.user_a:
        match.user_a_accepted = request.accepted
    elif user.id == match.user_b:
        match.user_b_accepted = request.accepted
    else:
        return {"status": "error", "message": "User not part of this match"}

    # If declined, set status and add to recent_contacts
    if not request.accepted:
        match.status = "declined"
        # Add to recent_contacts with 72h TTL
        until = datetime.utcnow() + timedelta(hours=72)
        db.add(
            RecentContact(
                user_id=user.id, other_id=match.user_a if user.id == match.user_b else match.user_b, until=until
            )
        )
        await db.commit()
        return {"status": "declined", "match_id": str(request.match_id)}

    # Check if both accepted
    if match.user_a_accepted and match.user_b_accepted:
        match.status = "active"

        # Create chat session
        chat_session = ChatSession(match_id=match.id)
        db.add(chat_session)

        await db.commit()

        return {
            "status": "active",
            "match_id": str(request.match_id),
            "chat_session_id": str(chat_session.id),
            "message": "Match confirmed! Chat session started.",
        }

    # One user accepted, waiting for other
    await db.commit()
    return {
        "status": "waiting",
        "match_id": str(request.match_id),
        "message": "Waiting for other user to accept",
    }
