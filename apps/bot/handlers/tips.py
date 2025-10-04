"""Tips/payment handlers for Telegram Stars (XTR)."""

import logging
import time

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice, Message

from apps.bot.api_client import api_client
from core.metrics import tips_errors_total, tips_paid_total, tips_processing_duration
from core.redis import get_redis
from core.security import sign_tips_payload

router = Router()
logger = logging.getLogger(__name__)

# Preset tip amounts in XTR (Telegram Stars)
PRESETS = [30, 100, 200, 500]


@router.message(Command("tips"))
async def cmd_tips(message: Message) -> None:
    """
    Handle /tips command - show tip presets for conversation partner.

    Usage: /tips <match_id>
    If match_id is not provided, show help message.
    """
    # Parse match_id from command args
    if message.text and len(message.text.split()) > 1:
        try:
            match_id = int(message.text.split()[1])
        except ValueError:
            await message.answer("❌ Неверный формат. Используйте: /tips <match_id>")
            return
    else:
        await message.answer(
            "💙 Чаевые собеседнику\n\n"
            "Чтобы отправить чаевые, используйте кнопку после завершения диалога "
            "или команду /tips с ID матча."
        )
        return

    # Get match info from API to determine peer
    try:
        # Note: We'll need to add this endpoint to get match info
        # For now, show generic presets
        await show_tip_presets(message, match_id, peer_tg_id=0)
    except Exception as e:
        logger.error(f"Error showing tips for match {match_id}: {e}")
        await message.answer("❌ Не удалось загрузить информацию о диалоге.")


async def show_tip_presets(message: Message, match_id: int, peer_tg_id: int) -> None:
    """
    Show tip preset buttons.

    Args:
        message: Message to reply to
        match_id: Match ID
        peer_tg_id: Peer's Telegram ID
    """
    # Create inline keyboard with preset amounts
    buttons = []
    for amount in PRESETS:
        callback_data = f"tip:{match_id}:{peer_tg_id}:{amount}"
        buttons.append([InlineKeyboardButton(text=f"⭐ {amount} Stars", callback_data=callback_data)])

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    await message.answer(
        "💙 Выберите сумму чаевых\n\nСпасибо, что используете наш сервис!\nКомиссия платформы: 10%",
        reply_markup=keyboard,
    )


@router.callback_query(F.data.startswith("tip:"))
async def on_tip_callback(callback: CallbackQuery) -> None:
    """
    Handle tip preset selection.

    Callback data format: tip:<match_id>:<peer_tg_id>:<amount>

    Steps:
    1. Parse callback data
    2. Redis lock to prevent double-clicks (idempotency)
    3. Check eligibility via API
    4. Create signed invoice payload
    5. Send Telegram Stars invoice
    """
    if not callback.data or not callback.from_user:
        await callback.answer("❌ Ошибка обработки", show_alert=True)
        return

    # Parse callback data
    try:
        _, match_id_str, peer_tg_id_str, amount_str = callback.data.split(":")
        match_id = int(match_id_str)
        peer_tg_id = int(peer_tg_id_str)
        amount = int(amount_str)
    except ValueError:
        await callback.answer("❌ Некорректные данные", show_alert=True)
        return

    # Check if sending to self
    if callback.from_user.id == peer_tg_id:
        await callback.answer("❌ Нельзя отправить чаевые самому себе", show_alert=True)
        tips_errors_total.labels(error_type="self_tip").inc()
        return

    # Redis lock for idempotency (prevent double-click)
    redis = await get_redis()
    lock_key = f"tips:cb:{callback.id}"
    lock_acquired = await redis.set(lock_key, "1", ex=60, nx=True)

    if not lock_acquired:
        await callback.answer("⏳ Запрос уже обрабатывается...", show_alert=True)
        tips_errors_total.labels(error_type="duplicate_click").inc()
        return

    # Start timing for metrics
    start_time = time.time()

    try:
        # Check eligibility via API
        response = await api_client.get(
            f"/tips/eligibility?match_id={match_id}&from_={callback.from_user.id}&to={peer_tg_id}"
        )

        if response.get("ok") is not True:
            await callback.answer("❌ Сессия неактивна или истёк срок (24ч)", show_alert=True)
            tips_errors_total.labels(error_type="not_eligible").inc()
            return

    except Exception as e:
        logger.error(f"Eligibility check failed: {e}")
        await callback.answer("❌ Ошибка проверки прав доступа", show_alert=True)
        tips_errors_total.labels(error_type="eligibility_check_failed").inc()
        return

    # Create signed payload
    payload_str = f"{match_id}:{callback.from_user.id}:{peer_tg_id}:{amount}"
    signed_payload = sign_tips_payload(payload_str)

    # Send Telegram Stars invoice
    try:
        await callback.message.bot.send_invoice(
            chat_id=callback.from_user.id,
            title="Чаевые собеседнику",
            description="Спасибо за разговор! Комиссия платформы: 10%",
            payload=signed_payload,
            provider_token="",  # Empty for Telegram Stars (XTR)
            currency="XTR",  # Telegram Stars
            prices=[LabeledPrice(label=f"{amount} Stars", amount=amount)],
        )

        # Record processing time
        duration = time.time() - start_time
        tips_processing_duration.observe(duration)

        await callback.answer("✅ Счёт отправлен!")

        # Edit original message to confirm
        if callback.message:
            await callback.message.edit_text(
                f"✅ Счёт на {amount} ⭐ Stars отправлен!\n\nОплатите его для завершения транзакции."
            )

    except Exception as e:
        logger.error(f"Failed to send invoice: {e}")
        await callback.answer("❌ Не удалось создать счёт", show_alert=True)
        tips_errors_total.labels(error_type="invoice_send_failed").inc()


@router.pre_checkout_query()
async def handle_pre_checkout_query(pre_checkout_query) -> None:
    """
    Handle pre-checkout query from Telegram.

    This handler is called BEFORE the actual payment is processed.
    We must answer within 10 seconds or payment will fail.

    For Telegram Stars, we can do basic validation here:
    - Verify payload format
    - Check currency is XTR
    - Optionally verify eligibility (though already checked at invoice creation)

    For now, we approve all pre-checkout queries since validation
    was done during invoice creation.
    """
    from aiogram.types import PreCheckoutQuery

    query: PreCheckoutQuery = pre_checkout_query

    try:
        # Basic validation: ensure currency is XTR
        if query.currency != "XTR":
            logger.warning(f"Pre-checkout: invalid currency {query.currency}")
            await query.answer(ok=False, error_message="Поддерживаются только Telegram Stars (XTR)")
            tips_errors_total.labels(error_type="pre_checkout_invalid_currency").inc()
            return

        # Optionally verify HMAC signature (paranoid check)
        from core.security import verify_tips_payload

        valid, _ = verify_tips_payload(query.invoice_payload)
        if not valid:
            logger.warning("Pre-checkout: invalid HMAC in payload")
            await query.answer(ok=False, error_message="Недействительная подпись платежа")
            tips_errors_total.labels(error_type="pre_checkout_invalid_hmac").inc()
            return

        # All checks passed - approve payment
        logger.info(f"Pre-checkout approved: {query.id}, amount={query.total_amount} XTR")
        await query.answer(ok=True)

    except Exception as e:
        logger.error(f"Pre-checkout error: {e}")
        # On error, reject payment to be safe
        await query.answer(ok=False, error_message="Произошла ошибка. Попробуйте позже.")
        tips_errors_total.labels(error_type="pre_checkout_exception").inc()


@router.message(F.successful_payment)
async def on_successful_payment(message: Message) -> None:
    """
    Handle successful payment from Telegram Stars.

    This handler is triggered when user successfully pays the invoice.

    Steps:
    1. Extract successful_payment data
    2. Send to API /payments/record for idempotent storage
    3. If new record created, send notifications to both users
    4. Use Redis deduplication to prevent repeated notifications
    """
    if not message.successful_payment or not message.from_user:
        logger.warning("successful_payment handler called without payment data")
        return

    sp = message.successful_payment
    logger.info(
        f"Successful payment received: {sp.total_amount} {sp.currency}, charge_id={sp.telegram_payment_charge_id}"
    )

    # Redis deduplication key for notifications
    redis = await get_redis()
    notif_key = f"notif:tip:{sp.telegram_payment_charge_id}"
    already_notified = await redis.get(notif_key)

    if already_notified:
        logger.info(f"Payment {sp.telegram_payment_charge_id} already processed, skipping notification")
        await message.answer("✅ Платёж уже обработан!")
        return

    # Send payment data to API for recording
    try:
        response = await api_client.post(
            "/payments/record",
            json_data={
                "successful_payment": {
                    "currency": sp.currency,
                    "total_amount": sp.total_amount,
                    "invoice_payload": sp.invoice_payload,
                    "telegram_payment_charge_id": sp.telegram_payment_charge_id,
                    "provider_payment_charge_id": sp.provider_payment_charge_id,
                }
            },
        )

        if response.get("status") == "ok":
            from_tg = response.get("from_tg")
            to_tg = response.get("to_tg")

            # Set Redis flag to prevent duplicate notifications (24h TTL)
            await redis.set(notif_key, "1", ex=86400)

            # Increment success counter
            tips_paid_total.inc()

            # Calculate amounts
            amount_xtr = sp.total_amount
            commission = int(round(amount_xtr * 0.10))
            recipient_amount = amount_xtr - commission

            # Send confirmation to sender
            await message.answer(
                f"✅ Платёж успешно обработан!\n\n"
                f"Сумма: {amount_xtr} ⭐ Stars\n"
                f"Комиссия платформы: {commission} ⭐ Stars (10%)\n"
                f"Получатель получит: {recipient_amount} ⭐ Stars\n\n"
                f"Спасибо за поддержку! 💙"
            )

            # Send notification to recipient
            if to_tg and to_tg != from_tg:
                try:
                    await message.bot.send_message(
                        chat_id=to_tg,
                        text=f"💙 Вы получили чаевые!\n\n"
                        f"Собеседник отправил вам {recipient_amount} ⭐ Stars\n\n"
                        f"Спасибо за участие в проекте!",
                    )
                except Exception as e:
                    logger.error(f"Failed to notify recipient {to_tg}: {e}")
                    tips_errors_total.labels(error_type="notification_failed").inc()

        else:
            await message.answer("❌ Ошибка обработки платежа. Свяжитесь с поддержкой.")
            tips_errors_total.labels(error_type="payment_record_failed").inc()

    except Exception as e:
        logger.error(f"Failed to record payment: {e}")
        await message.answer("❌ Ошибка сохранения платежа. Попробуйте позже или свяжитесь с поддержкой.")
        tips_errors_total.labels(error_type="payment_exception").inc()
