

## Sprint 3 — Пересылка сообщений (Message Relay) и завершение чата
**Цель:** обеспечить полноценный диалог 1‑на‑1 внутри активной `chat_session` без хранения содержимого сообщений, с командой `/end`.

### Правила и допущения
- Сообщения не сохраняем (только счётчики/метрики).
- Поддержка **текста** в MVP; медиа добавим позже.
- Пересылка идёт через бота: отправителю отображается «отправлено», собеседник получает текст с ником отправителя.
- Работает **только в `status='active'`**; вне активной сессии бот предлагает `/find`.

### Изменения БД (миграция)
```sql
ALTER TABLE chat_sessions
  ADD COLUMN msg_count_a INT NOT NULL DEFAULT 0,
  ADD COLUMN msg_count_b INT NOT NULL DEFAULT 0;
```

### API контракты
- `POST /chat/relay` — { from_user, text } → 200/403. Валидация активной сессии, возврат peer `tg_id`.
- `POST /chat/end` — { user_id, reason? } → 200; помечает `ended_at=now()` и статус матча `completed`.

### Логика маршрутизации (псевдокод)
```python
# apps/api/routers/chat.py
@router.post("/chat/relay")
async def relay(payload: RelayIn, db):
    # 1) найти активную сессию пользователя
    sess = await db.q("""
        SELECT cs.id, m.user_a, m.user_b
        FROM chat_sessions cs
        JOIN matches m ON m.id = cs.match_id
        WHERE cs.ended_at IS NULL AND m.status='active'
          AND (m.user_a=:u OR m.user_b=:u)
        LIMIT 1
    """, {"u": payload.from_user})
    if not sess: raise HTTPException(403)
    peer = sess.user_b if sess.user_a==payload.from_user else sess.user_a
    # 2) инкремент счётчика
    await db.exec("UPDATE chat_sessions SET msg_count_a=msg_count_a+1 WHERE id=:id" if sess.user_a==payload.from_user else "UPDATE chat_sessions SET msg_count_b=msg_count_b+1 WHERE id=:id", {"id": sess.id})
    return {"peer_user_id": peer}
```

```python
# apps/bot/handlers/chat.py (aiogram)
@dp.message()  # текст по умолчанию
async def on_text(msg: Message):
    # игнорировать команды и служебные
    if msg.text and msg.text.startswith('/'):
        return
    # запрос к API
    r = await api_client.post('/chat/relay', json={"from_user": msg.from_user.id, "text": msg.text})
    if r.status == 200:
        peer_tg_id = r.json()["peer_tg_id"] if "peer_tg_id" in r.json() else r.json().get("peer_user_id")
        # переслать собеседнику
        await bot.send_message(peer_tg_id, f"✉️ {msg.from_user.username or 'собеседник'}: {msg.text}")
    else:
        await msg.answer("Нет активного диалога. Нажмите /find.")
```

### Команда завершения `/end`
```python
# apps/bot/handlers/end.py
@dp.message(Command("end"))
async def end_dialog(msg: Message):
    # подтверждение
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Завершить диалог", callback_data=f"end:{msg.from_user.id}")]])
    await msg.answer("Завершить диалог? Это остановит пересылку сообщений.", reply_markup=kb)

@dp.callback_query(F.data.startswith("end:"))
async def end_confirm(cb: CallbackQuery):
    r = await api_client.post('/chat/end', json={"user_id": cb.from_user.id})
    if r.status == 200:
        # уведомить обеих сторон и показать CTA чаевых
        peer_id = r.json()["peer_tg_id"]
        await cb.message.answer("Диалог завершён. Спасибо за общение! /find чтобы начать новый.")
        await bot.send_message(peer_id, "Собеседник завершил диалог. Хотите оставить чаевые? /tips")
        await cb.answer()
    else:
        await cb.answer("Нет активного диалога", show_alert=True)
```

### Граничные случаи
- Сообщение во время `expired/declined` → ответ «Нет активного диалога. /find».
- Блокировка Telegram (peer закрыл бота) → ловим `Forbidden`, уведомляем отправителя о недоставке.
- Rate limit: максимум 15 сообщений/мин на пользователя (Redis token bucket).

### Ручные тесты Sprint 3 (ключевые)
- **R1**: текст A→B и B→A в активной сессии отображается на обеих сторонах.
- **R2**: сообщение вне активной сессии → подсказка `/find`.
- **R3**: /end у одной стороны → обе получают уведомления, пересылка прекращается.
- **R4**: отправка после /end → подсказка `/find`.
- **R5**: rate limit 15/мин → мягкое предупреждение.

### Критерии приёмки Sprint 3
- p95 пересылки ≤ 800 мс, потерь сообщений нет (на тесте).
- Ноль жалоб на «сообщения приходят вне диалога».
- /end всегда завершает пересылку в ≤ 2 сек.
