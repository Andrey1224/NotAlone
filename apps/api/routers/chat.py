"""Chat endpoints for message relay and ending dialogs."""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.deps import get_db

router = APIRouter()


class RelayMessageRequest(BaseModel):  # type: ignore[misc]
    """Request to relay a message to peer."""

    from_user: int  # Telegram user ID of sender
    text: str  # Message text


class EndChatRequest(BaseModel):  # type: ignore[misc]
    """Request to end active chat session."""

    user_id: int  # Telegram user ID ending the chat
    reason: str | None = None  # Optional reason for ending


@router.post("/relay")  # type: ignore[misc]
async def relay_message(request: RelayMessageRequest, db: AsyncSession = Depends(get_db)) -> dict[str, int | str]:
    """
    Relay a message from one user to their active chat peer.

    Returns peer's telegram ID and nickname for bot to send message.
    """
    from models.chat import ChatSession
    from models.match import Match
    from models.user import User

    # First, find the user by telegram ID to get internal user_id
    user_result = await db.execute(select(User).where(User.tg_id == request.from_user))
    sender = user_result.scalar_one_or_none()

    if not sender:
        raise HTTPException(status_code=404, detail="User not found")

    # Find active chat session for this user (using internal user_id)
    # ORDER BY to get the most recent active session first
    result = await db.execute(
        select(ChatSession, Match)
        .join(Match, ChatSession.match_id == Match.id)
        .where(
            and_(
                ChatSession.ended_at.is_(None),  # Session not ended
                Match.status == "active",  # Match is active
                (Match.user_a == sender.id) | (Match.user_b == sender.id),  # User is part of match
            )
        )
        .order_by(ChatSession.started_at.desc())  # Most recent first
    )
    row = result.first()

    if not row:
        raise HTTPException(status_code=403, detail="No active chat session found")

    chat_session, match = row

    # Determine peer user ID (using internal user_id, not tg_id)
    if match.user_a == sender.id:
        peer_user_id = match.user_b
        # Increment msg_count_a
        chat_session.msg_count_a += 1
    elif match.user_b == sender.id:
        peer_user_id = match.user_a
        # Increment msg_count_b
        chat_session.msg_count_b += 1
    else:
        raise HTTPException(status_code=403, detail="User not part of this match")

    # Get peer's telegram ID and nickname
    peer_result = await db.execute(select(User).where(User.id == peer_user_id))
    peer = peer_result.scalar_one_or_none()

    if not peer:
        raise HTTPException(status_code=404, detail="Peer user not found")

    # Commit message count increment
    await db.commit()

    return {
        "peer_tg_id": peer.tg_id,
        "peer_nickname": sender.nickname,  # Send sender's nickname to display to peer
        "status": "relayed",
    }


@router.post("/end")  # type: ignore[misc]
async def end_chat(request: EndChatRequest, db: AsyncSession = Depends(get_db)) -> dict[str, int | str]:
    """
    End an active chat session.

    Updates chat_session.ended_at and match.status to 'completed'.
    Returns peer's telegram ID for notification.
    """
    from models.chat import ChatSession
    from models.match import Match
    from models.user import User

    # First, find the user by telegram ID to get internal user_id
    user_result = await db.execute(select(User).where(User.tg_id == request.user_id))
    ender = user_result.scalar_one_or_none()

    if not ender:
        raise HTTPException(status_code=404, detail="User not found")

    # Find active chat session for this user (using internal user_id)
    result = await db.execute(
        select(ChatSession, Match)
        .join(Match, ChatSession.match_id == Match.id)
        .where(
            and_(
                ChatSession.ended_at.is_(None),  # Session not ended
                Match.status == "active",  # Match is active
                (Match.user_a == ender.id) | (Match.user_b == ender.id),  # User is part of match
            )
        )
    )
    row = result.first()

    if not row:
        raise HTTPException(status_code=404, detail="No active chat session found")

    chat_session, match = row

    # Determine peer user ID (using internal user_id, not tg_id)
    if match.user_a == ender.id:
        peer_user_id = match.user_b
    elif match.user_b == ender.id:
        peer_user_id = match.user_a
    else:
        raise HTTPException(status_code=403, detail="User not part of this match")

    # Get peer's telegram ID
    peer_result = await db.execute(select(User).where(User.id == peer_user_id))
    peer = peer_result.scalar_one_or_none()

    if not peer:
        raise HTTPException(status_code=404, detail="Peer user not found")

    # Mark session as ended and match as completed
    chat_session.ended_at = datetime.utcnow()
    match.status = "completed"

    await db.commit()

    return {"peer_tg_id": peer.tg_id, "status": "ended", "chat_session_id": chat_session.id}
