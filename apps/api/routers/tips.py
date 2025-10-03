"""Tips eligibility endpoints."""

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.deps import get_db

router = APIRouter(prefix="/tips", tags=["tips"])
logger = logging.getLogger(__name__)


@router.get("/eligibility")
async def check_eligibility(
    match_id: int,
    from_: int,  # from is a reserved keyword
    to: int,
    db: AsyncSession = Depends(get_db),
) -> dict[str, bool]:
    """
    Check if user is eligible to send tips.

    Eligibility criteria:
    - Match exists and involves both users
    - Match is active OR completed ≤24 hours ago

    Args:
        match_id: Match ID
        from_: Telegram ID of sender
        to: Telegram ID of recipient
        db: Database session

    Returns:
        {"ok": True} if eligible

    Raises:
        HTTPException 403 if not eligible
    """
    query = text(
        """
        SELECT 1
        FROM matches m
        JOIN chat_sessions cs ON cs.match_id = m.id
        JOIN users ua ON ua.id = m.user_a
        JOIN users ub ON ub.id = m.user_b
        WHERE m.id = :match_id
          AND ((ua.tg_id = :from_tg AND ub.tg_id = :to_tg)
               OR (ua.tg_id = :to_tg AND ub.tg_id = :from_tg))
          AND (m.status = 'active'
               OR (m.status = 'completed' AND cs.ended_at >= now() - interval '24 hours'))
        LIMIT 1
    """
    )

    result = await db.execute(query, {"match_id": match_id, "from_tg": from_, "to_tg": to})
    eligible = result.first()

    if not eligible:
        logger.warning(f"Tips eligibility check failed: match_id={match_id}, from={from_}, to={to}")
        raise HTTPException(status_code=403, detail="not_eligible")

    return {"ok": True}
