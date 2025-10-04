"""Reports and blocking endpoints for safety & moderation."""

import logging
import time

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.deps import get_db
from core.auth import bot_auth
from core.metrics import blocks_latency_seconds, blocks_total, reports_latency_seconds, reports_total
from core.redis import get_redis

router = APIRouter(prefix="/reports", tags=["reports"])
logger = logging.getLogger(__name__)

VALID_REASONS = {"spam", "abuse", "danger", "other"}


class ReportIn(BaseModel):
    """Input model for creating a report."""

    chat_session_id: int
    to_user_tg: int
    reason: str  # spam|abuse|danger|other
    comment: str | None = None


class BlockIn(BaseModel):
    """Input model for blocking a peer."""

    peer_tg: int


@router.post("", status_code=200)
async def create_report(
    body: ReportIn,
    db: AsyncSession = Depends(get_db),
    caller_tg: int = Depends(bot_auth),
) -> dict[str, bool]:
    """
    Create a new report (complaint) from one user about another.

    Validates:
    - Reason is in allowed list
    - Rate limit: 1 report per 60 seconds per user
    - Users are actually participants in the specified chat_session
    - Prevents duplicates via unique constraint

    Args:
        body: Report details
        db: Database session
        caller_tg: Telegram user ID of reporter (from bot_auth)

    Returns:
        {"ok": True} on success

    Raises:
        HTTPException: On validation failure or rate limit
    """
    t0 = time.perf_counter()
    try:
        # Validate reason
        if body.reason not in VALID_REASONS:
            raise HTTPException(400, f"Invalid reason. Must be one of: {VALID_REASONS}")

        # Rate limit: 1 report per 60 seconds
        redis = await get_redis()
        rl_key = f"rl:report:{caller_tg}"
        if not await redis.setnx(rl_key, "1"):
            raise HTTPException(429, "Too many reports. Please wait before reporting again.")
        await redis.expire(rl_key, 60)

        # Validate that caller and to_user are participants in the chat_session
        # and resolve their internal user IDs
        validation_query = text(
            """
            SELECT ua.id AS from_id, ub.id AS to_id
            FROM chat_sessions cs
            JOIN matches m ON m.id = cs.match_id
            JOIN users ua ON (ua.id = m.user_a OR ua.id = m.user_b)
            JOIN users ub ON (ub.id = m.user_a OR ub.id = m.user_b)
            WHERE cs.id = :sid
              AND ua.tg_id = :caller
              AND ub.tg_id = :peer
              AND ua.id != ub.id
        """
        )

        row = (
            (
                await db.execute(
                    validation_query, {"sid": body.chat_session_id, "caller": caller_tg, "peer": body.to_user_tg}
                )
            )
            .mappings()
            .first()
        )

        if not row:
            raise HTTPException(
                400, "Invalid session or user mismatch. Ensure you are a participant in the specified session."
            )

        # Insert report (ON CONFLICT DO NOTHING prevents duplicates)
        insert_query = text(
            """
            INSERT INTO reports(chat_session_id, from_user, to_user, reason, comment)
            VALUES (:sid, :from_id, :to_id, :reason, :comment)
            ON CONFLICT ON CONSTRAINT uq_reports_once_per_session DO NOTHING
        """
        )

        await db.execute(
            insert_query,
            {
                "sid": body.chat_session_id,
                "from_id": row["from_id"],
                "to_id": row["to_id"],
                "reason": body.reason,
                "comment": body.comment or "",
            },
        )
        await db.commit()

        # Metrics
        reports_total.labels(reason=body.reason).inc()

        logger.info(f"Report created: from={caller_tg}, to={body.to_user_tg}, reason={body.reason}")

        return {"ok": True}

    finally:
        reports_latency_seconds.observe(time.perf_counter() - t0)


@router.post("/block", status_code=200)
async def block_peer(
    body: BlockIn,
    db: AsyncSession = Depends(get_db),
    caller_tg: int = Depends(bot_auth),
) -> dict[str, bool]:
    """
    Immediately end active chat session and impose 30-day cooldown for both users.

    This is a user-initiated block (not moderation action).
    Effects:
    - Ends active chat_session
    - Marks match as completed
    - Adds 30-day cooldown in both directions (prevents rematching)

    Args:
        body: Peer to block
        db: Database session
        caller_tg: Telegram user ID of caller (from bot_auth)

    Returns:
        {"ok": True} on success

    Raises:
        HTTPException: If no active session found
    """
    t0 = time.perf_counter()
    try:
        # Find active session involving both users
        find_session_query = text(
            """
            SELECT cs.id AS chat_id, cs.match_id, m.user_a, m.user_b,
                   ua.tg_id AS tg_a, ub.tg_id AS tg_b
            FROM chat_sessions cs
            JOIN matches m ON m.id = cs.match_id
            JOIN users ua ON ua.id = m.user_a
            JOIN users ub ON ub.id = m.user_b
            WHERE cs.ended_at IS NULL
              AND (ua.tg_id = :caller OR ub.tg_id = :caller)
              AND (ua.tg_id = :peer OR ub.tg_id = :peer)
            LIMIT 1
        """
        )

        row = (await db.execute(find_session_query, {"caller": caller_tg, "peer": body.peer_tg})).mappings().first()

        if not row:
            raise HTTPException(404, "No active session found with this user")

        # End chat session
        await db.execute(
            text("UPDATE chat_sessions SET ended_at = now() WHERE id = :id AND ended_at IS NULL"),
            {"id": row["chat_id"]},
        )

        # Mark match as completed
        await db.execute(
            text("UPDATE matches SET status = 'completed' WHERE id = :id AND status IN ('active', 'proposed')"),
            {"id": row["match_id"]},
        )

        # Add 30-day cooldown in both directions
        cooldown_query = text(
            """
            WITH pairs AS (
                SELECT ua.id AS u1, ub.id AS u2
                FROM users ua, users ub
                WHERE ua.tg_id = :caller AND ub.tg_id = :peer
            )
            INSERT INTO recent_contacts(user_id, other_id, until)
            SELECT u1, u2, now() + interval '30 days' FROM pairs
            UNION ALL
            SELECT u2, u1, now() + interval '30 days' FROM pairs
            ON CONFLICT (user_id, other_id) DO UPDATE SET until = excluded.until
        """
        )

        await db.execute(cooldown_query, {"caller": caller_tg, "peer": body.peer_tg})
        await db.commit()

        # Metrics
        blocks_total.inc()

        logger.info(f"Block executed: caller={caller_tg}, peer={body.peer_tg}, session={row['chat_id']}")

        return {"ok": True}

    finally:
        blocks_latency_seconds.observe(time.perf_counter() - t0)
