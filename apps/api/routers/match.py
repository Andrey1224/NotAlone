"""Match endpoints."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.deps import get_db

router = APIRouter()


class MatchFindRequest(BaseModel):  # type: ignore[misc]
    """Request to find a match."""

    user_id: int
    topics: list[str]
    timezone: str


class MatchConfirmRequest(BaseModel):  # type: ignore[misc]
    """Request to confirm a match."""

    match_id: int
    action: str  # "accept" or "decline"
    user_id: int  # User making the action


@router.post("/find")  # type: ignore[misc]
async def find_match(request: MatchFindRequest, db: AsyncSession = Depends(get_db)) -> dict[str, str]:
    """Find a match for user."""
    print(
        f"DEBUG: Received match request: user_id={request.user_id}, topics={request.topics}, timezone={request.timezone}"
    )

    from datetime import datetime

    from sqlalchemy import select

    from apps.api.deps import get_redis_client
    from models.user import User

    # Validate user exists and has profile with ≥2 topics
    result = await db.execute(select(User).where(User.tg_id == request.user_id))
    user = result.scalar_one_or_none()
    print(f"DEBUG: Found user: {user.nickname if user else 'None'}")

    if not user:
        print("DEBUG: User not found")
        return {"status": "error", "message": "User not found"}

    if not user.safety_ack:
        print("DEBUG: Safety acknowledgement required")
        return {"status": "error", "message": "Safety acknowledgement required"}

    # Check user has ≥2 topics
    from sqlalchemy import func

    from models.topic import UserTopic

    topic_count_result = await db.execute(select(func.count(UserTopic.topic_id)).where(UserTopic.user_id == user.id))
    topic_count = topic_count_result.scalar()
    print(f"DEBUG: User has {topic_count} topics")

    if topic_count < 2:
        print("DEBUG: Not enough topics")
        return {"status": "error", "message": "At least 2 topics required"}

    # Add to Redis Stream
    redis_client = await get_redis_client()
    print("DEBUG: Got Redis client")

    payload = {
        "user_id": str(user.id),
        "tg_id": str(request.user_id),
        "topics": ",".join(request.topics),
        "timezone": request.timezone,
        "requested_at": datetime.utcnow().isoformat(),
    }
    print(f"DEBUG: Payload for Redis: {payload}")

    # XADD to match.find stream
    stream_id = await redis_client.xadd("match.find", payload)
    print(f"DEBUG: Added to Redis stream with ID: {stream_id}")

    return {
        "status": "queued",
        "user_id": str(request.user_id),
        "stream_id": stream_id,
        "message": "Searching for match...",
    }


@router.post("/confirm")  # type: ignore[misc]
async def confirm_match(request: MatchConfirmRequest, db: AsyncSession = Depends(get_db)) -> dict[str, str]:
    """Confirm or decline a match."""
    from datetime import datetime, timedelta

    from sqlalchemy import and_, or_, select

    from apps.workers.notifier import notifier
    from models.chat import ChatSession
    from models.match import Match
    from models.recent_contact import RecentContact
    from models.user import User

    # Get match
    result = await db.execute(select(Match).where(Match.id == request.match_id))
    match = result.scalar_one_or_none()

    if not match:
        return {"status": "error", "message": "Match not found"}

    # SECURITY: Check match is in proposed state (prevent re-processing)
    if match.status != "proposed":
        return {"status": "error", "message": f"Match not in proposed state (current: {match.status})"}

    # Check if expired
    if match.expires_at and match.expires_at < datetime.utcnow():
        match.status = "expired"
        await db.commit()
        return {"status": "expired", "message": "Match offer expired"}

    # Parse action
    accepted = request.action == "accept"

    # Get user
    user_result = await db.execute(select(User).where(User.id == request.user_id))
    user = user_result.scalar_one_or_none()

    if not user:
        return {"status": "error", "message": "User not found"}

    # SECURITY: Validate user is part of this match
    if user.id not in (match.user_a, match.user_b):
        return {"status": "error", "message": "User not part of this match"}

    # Update acceptance status
    if user.id == match.user_a:
        match.user_a_accepted = accepted
        other_user_id = match.user_b
    elif user.id == match.user_b:
        match.user_b_accepted = accepted
        other_user_id = match.user_a
    else:
        # This should never happen due to check above, but keep for safety
        return {"status": "error", "message": "User not part of this match"}

    # If declined, set status and add to recent_contacts
    if not accepted:
        match.status = "declined"
        # Add to recent_contacts with 72h TTL (bidirectional to prevent reverse matches)
        until = datetime.utcnow() + timedelta(hours=72)
        db.add(RecentContact(user_id=user.id, other_id=other_user_id, until=until))
        db.add(RecentContact(user_id=other_user_id, other_id=user.id, until=until))
        await db.commit()

        # Notify other user
        await notifier.send_match_declined(db, other_user_id)

        return {"status": "declined", "match_id": str(request.match_id)}

    # Check if both accepted
    if match.user_a_accepted and match.user_b_accepted:
        # CLOSE ALL OTHER ACTIVE CHATS FOR BOTH USERS
        # This prevents multiple active chats issue

        # Close all other active sessions for both users
        close_sessions_result = await db.execute(
            select(ChatSession)
            .join(Match, ChatSession.match_id == Match.id)
            .where(
                and_(
                    ChatSession.ended_at.is_(None),
                    Match.status == "active",
                    or_(Match.user_a.in_([match.user_a, match.user_b]), Match.user_b.in_([match.user_a, match.user_b])),
                    Match.id != match.id,
                )
            )
        )

        old_sessions = close_sessions_result.scalars().all()
        for old_session in old_sessions:
            old_session.ended_at = datetime.utcnow()

        # Also close the matches themselves
        close_matches_result = await db.execute(
            select(Match).where(
                and_(
                    Match.status == "active",
                    or_(Match.user_a.in_([match.user_a, match.user_b]), Match.user_b.in_([match.user_a, match.user_b])),
                    Match.id != match.id,
                )
            )
        )

        old_matches = close_matches_result.scalars().all()
        for old_match in old_matches:
            old_match.status = "completed"

        match.status = "active"

        # Create chat session
        chat_session = ChatSession(match_id=match.id)
        db.add(chat_session)

        await db.commit()

        # Send intro message to both users
        await notifier.send_match_active(db, match.user_a, match.user_b)
        await notifier.send_match_active(db, match.user_b, match.user_a)

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
