"""Payment endpoints."""

import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.deps import get_db
from core.metrics import tips_errors_total
from core.security import verify_tips_payload

router = APIRouter()
logger = logging.getLogger(__name__)


class CreateTipRequest(BaseModel):
    """Request to create a tip."""

    from_user_id: int
    to_user_id: int
    match_id: int
    amount: int  # in XTR (Telegram Stars)


class TipWebhookPayload(BaseModel):
    """Webhook payload for tip status updates."""

    tip_id: int
    status: str  # paid, failed
    provider_transaction_id: str | None = None


@router.post("/tips/create")
async def create_tip(request: CreateTipRequest, db: AsyncSession = Depends(get_db)) -> dict[str, str | int]:
    """Create a tip invoice."""
    # TODO: Implement tip creation logic
    # 1. Create tip record in database
    # 2. Generate Telegram Stars invoice
    # 3. Return invoice URL
    return {
        "status": "created",
        "tip_id": 1,
        "invoice_url": "https://t.me/invoice/placeholder",
        "amount": request.amount,
    }


@router.post("/webhook/telegram-stars")
async def telegram_stars_webhook(payload: TipWebhookPayload, db: AsyncSession = Depends(get_db)) -> dict[str, str]:
    """Handle Telegram Stars payment webhook."""
    # TODO: Implement webhook handler
    # 1. Verify webhook signature
    # 2. Update tip status in database
    # 3. Notify users
    return {"status": "processed"}


class SuccessfulPayment(BaseModel):
    """Telegram successful_payment object."""

    currency: str
    total_amount: int
    invoice_payload: str
    telegram_payment_charge_id: str
    provider_payment_charge_id: str | None = None


class RecordPaymentRequest(BaseModel):
    """Request to record a successful payment from bot."""

    successful_payment: SuccessfulPayment


@router.post("/record")
async def record_payment(request: RecordPaymentRequest, db: AsyncSession = Depends(get_db)) -> dict[str, str | int]:
    """
    Record successful payment from Telegram Stars.

    Internal endpoint called by bot after receiving successful_payment update.

    Args:
        request: Payment data from successful_payment
        db: Database session

    Returns:
        {"status": "ok", "from_tg": ..., "to_tg": ...}

    Raises:
        HTTPException 400 if payment is invalid
    """
    sp = request.successful_payment

    # Validate currency
    if sp.currency != "XTR":
        logger.warning(f"Invalid currency: {sp.currency}")
        tips_errors_total.labels(error_type="invalid_currency").inc()
        raise HTTPException(status_code=400, detail="invalid_currency")

    # Verify HMAC signature
    valid, payload = verify_tips_payload(sp.invoice_payload)
    if not valid:
        logger.warning(f"Invalid HMAC signature in payload: {sp.invoice_payload[:50]}...")
        tips_errors_total.labels(error_type="invalid_hmac").inc()
        raise HTTPException(status_code=400, detail="invalid_signature")

    # Parse payload: match_id:from_tg:to_tg:amount
    try:
        parts = payload.split(":")
        if len(parts) != 4:
            raise ValueError("Invalid payload format")
        match_id, from_tg, to_tg, amount = parts
        match_id_int = int(match_id)
        from_tg_int = int(from_tg)
        to_tg_int = int(to_tg)
        amount_int = int(amount)
    except (ValueError, AttributeError) as e:
        logger.error(f"Malformed payload: {payload}, error: {e}")
        tips_errors_total.labels(error_type="malformed_payload").inc()
        raise HTTPException(status_code=400, detail="malformed_payload") from e

    # Calculate 10% commission
    commission = int(round(amount_int * 0.10))

    # Upsert payment record (idempotent by telegram_payment_charge_id)
    query = text(
        """
        INSERT INTO tips(
            match_id, from_user, to_user, amount_minor, currency, provider,
            provider_fee_minor, our_commission_minor, status, created_at,
            telegram_payment_id, invoice_payload
        )
        SELECT m.id, ua.id, ub.id,
               :amt, :cur, 'telegram-stars',
               0, :commission, 'paid', now(), :tpid, :signed_payload
        FROM matches m
        JOIN users ua ON ua.tg_id = :from_tg
        JOIN users ub ON ub.tg_id = :to_tg
        WHERE m.id = :match_id
        ON CONFLICT (telegram_payment_id) DO NOTHING
        RETURNING id
    """
    )

    result = await db.execute(
        query,
        {
            "amt": amount_int,
            "cur": sp.currency,
            "tpid": sp.telegram_payment_charge_id,
            "signed_payload": sp.invoice_payload,
            "from_tg": from_tg_int,
            "to_tg": to_tg_int,
            "match_id": match_id_int,
            "commission": commission,
        },
    )
    await db.commit()

    # Check if record was inserted (or was duplicate)
    inserted = result.first()
    if inserted:
        logger.info(
            f"Payment recorded: tip_id={inserted[0]}, amount={amount_int} XTR, from={from_tg_int}, to={to_tg_int}"
        )
    else:
        logger.info(f"Duplicate payment ignored: tpid={sp.telegram_payment_charge_id}")

    return {"status": "ok", "from_tg": from_tg_int, "to_tg": to_tg_int}
