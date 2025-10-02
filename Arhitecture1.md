# SPEC-1 — Поиск собеседников по интересам (бот в Telegram)

## Background

Людям часто не хватает «своих» собеседников по нишевым интересам (хобби, профессиональные темы, жизненные ситуации). Существующие соцсети предлагают широкие сообщества, но слабую персонализацию, а тематические чаты перегружены шумом.

Идея: создать лёгкий вход в приватный диалог «один на один» или в малую группу (2–4 человека) на основе точного совпадения интересов и ожиданий: формат общения (чат/аудио), цель (поддержка, обмен опытом, дружба), язык, часовой пояс. MVP сфокусирован на Telegram-боте, т.к. у платформы низкий порог входа, хорошая доступность и встроенные платежи для чаевых.



## Requirements

**Vision:** «Ты не один» — сервис 1‑на‑1 поддержки на основе общих пережитых ситуаций и интересов. Стартовая платформа — Telegram‑бот.

### MoSCoW
**Must**
- RU/CIS рынок, язык интерфейса — русский.
- Telegram‑бот как единственный клиент в MVP.
- Матчинг только 1‑на‑1.
- Анонимность по умолчанию: псевдоним + набор тем + часовой пояс + краткое описание (без ФИО/телефона/почты/геолокации).
- Регистрация через Telegram.
- Профиль с тегами/темами пережитого опыта и интересов (напр. «переезд», «выгорание», «развод» и т.п.).
- Явные границы сервиса: peer‑to‑peer поддержка, не психотерапия; предупреждение и ссылки на горячие линии.
- Безопасность: жалоба/блокировка, авторазрыв матча.
- Конфиденциальность: минимизация данных, право на удаление профиля/диалогов.
- Базовый алгоритм матчей: взаимное совпадение по 2–3 ключевым тегам + часовой пояс/временные окна.
- Чаевые после диалога; модель комиссии платформы.

**Should**
- Анкета ожиданий: цель (поддержка/совет/дружба), формат (чат), уровень чувствительности тем.
- Онбординг с примерами безопасной коммуникации и правил.
- Рейтинг «полезности» диалога (эмодзи/1–5), влияет на выдачу.
- Тест A/B: строгий матч по тегам vs мягкий (суперсет тем).

**Could**
- Темп‑чат (таймер 24–72 ч) с возможностью «продлить» по взаимному согласию.
- Анонимные аватарки/стикеры от бота.
- «Ко‑лист» — список тем на будущее.
- Еженедельные дайджесты: «вам подходят 5 новых людей».

**Won’t (MVP)**
- Группы/аудио/видео.
- Публичные чаты и ленты.
- Проф‑консультации и мед‑советы.



## Method

### Архитектура (MVP)
- Клиент: Telegram‑бот (Bot API).
- Бэкенд: HTTP API (Node.js/TypeScript или Python) + очередь задач.
- Хранилище: PostgreSQL (профили, теги, матчи, метрики), Redis (кэши и очередь матчей), S3‑совместимое хранилище для экспортов.
- Интеграции: Telegram Bot API (чаты, inline‑кнопки), платежи (PSP/Stars), анти‑спам/рейт‑лимиты.
- **AI‑модуль (coach‑в‑диалоге, не терапевт):** сервис подсказок по эмпатичному общению на основе контекста чата; оффлайн режим по умолчанию (не вмешивается, только предлагает подсказки).

```plantuml
@startuml
actor UserA as A
actor UserB as B
participant "Telegram Bot" as Bot
participant API
collections Redis
database Postgres as DB
rectangle Payments {
  [PSP]
}
rectangle AI {
  [Prompt Orchestrator]
  [LLM Provider]
  [Safety Filters]
}

A -> Bot: сообщения
B -> Bot: сообщения
Bot -> API: webhook updates
API -> Redis: store context window
API -> AI: request coaching hints (anonymized)
AI -> API: hints (empathetic phrasing, questions)
API -> Bot: send inline hints (видит только отправитель)
API -> DB: store feedback & metrics
...
A -> Bot: «Оставить чаевые»
Bot -> Payments: invoice
@enduml
```

### Модель данных (черновик)
- `users(id, tg_id, nickname, tz, bio_short, safety_ack, created_at)`
- `topics(id, slug, title)`
- `user_topics(user_id, topic_id, weight)`
- `preferences(user_id, sensitivity_level, purpose, avail_windows)`
- `match_queue(user_id, score_ready_at)`
- `matches(id, user_a, user_b, created_at, status)`
- `chat_sessions(id, match_id, started_at, ended_at, rating_a, rating_b)`
- `tips(id, match_id, from_user, to_user, amount_minor, currency, provider, provider_fee_minor, our_commission_minor, status, created_at)`
- **AI‑сущности:**
  - `ai_hints(id, chat_session_id, user_id, hint_type, text, created_at, accepted boolean)`
  - `safety_flags(id, chat_session_id, user_id, label, severity, created_at)`
- Индексы по `user_topics(topic_id)`, GIN по массивам тем/окон, `matches(user_a,user_b)` уникальность.

### Алгоритм матчинга (MVP)
1. Пользователь нажимает «Найти собеседника». Записываем в очередь с TTL (например, 24 ч).
2. Выбираем кандидатов:
   - Совпадение по ≥2 общим темам (весам ≥ порога).
   - Совместимые окна по часовому поясу/времени.
   - Исключаем недавние неудачные матчи.
3. Считаем скоринг: `score = 0.6*tags_overlap + 0.2*time_overlap + 0.2*recent_helpfulness`.
4. Отправляем лучшего кандидата обоим с превью: псевдоним, 3 топ‑тега, короткое описание. Требуем **взаимного согласия**.
5. При согласии создаём приватный чат (бот шлёт интро‑сообщение и правила).

### Платежи и комиссия (стратегия для RU/CIS)
- Чаевые как цифровой контент: Telegram Stars или локальный PSP (YooKassa/CloudPayments/ECOMMPAY).
- Stripe — для будущего EN‑запуска.
- Учёт комиссии: на уровне записи `tips` фиксируем fee провайдера и нашу комиссию; прозрачный чек в чате.

### AI‑coach: функции и ограничения
- **Что делает:**
  - Предлагает эмпатичные формулировки и вопросы (напр. «говорить про потерю питомца»), напоминает про активное слушание, валидирует чувства.
  - Подсказывает границы: не давать мед/юрид. советов, не обещать «всё исправить».
  - Выявляет риски (самоповреждение/кризис) — *только флаги модерации* и ссылки на горячие линии; не диагностирует.
- **Как работает:**
  - Контекст чата анонимизируется (удаляем ники/идентификаторы, гео, явные PII) перед отправкой в LLM.
  - Подсказки приходят **только отправителю** как скрытые inline‑подсказки, пользователь сам решает вставлять их или нет.
  - Локальные правила (prompt‑guardrails) для чувствительных тем.
- **Что не делает:**
  - Не выступает «терапевтом», не даёт медицинских/психологических диагнозов и не заменяет специалистов.

### Безопасность и приватность
- Минимум PII: не собираем телефон/почту; опциональные поля — только по явному согласию.
- Жалобы/блокировки, авто‑мьют при токсичности ключевых слов.
- Хранение чатов на стороне Telegram; у нас — только метаданные и агрегаты.
- LLM‑запросы проходят через слой анонимизации + фильтры безопасности (токсичность, самоповреждение, сексуальный контент, незаконная деятельность).
- Минимум PII: не собираем телефон/почту; опциональные поля — только по явному согласию.
- Жалобы/блокировки, авто‑мьют при токсичности ключевых слов.
- Хранение чатов на стороне Telegram; у нас — только метаданные и агрегаты.



## Implementation

### Технологический стек (проверено на текущие версии)
- **Язык/Фреймворк**: **Python 3.12**.
- **Бот**: **aiogram 3.x** (полностью async, поддержка Bot API 9.x), вебхуки. 
- **Веб‑фреймворк**: **FastAPI** (ASGI), в проде — **Gunicorn + Uvicorn workers**.
- **ORM**: **SQLAlchemy 2.x** + Alembic (или Prisma Python нет → остаёмся на SQLAlchemy).
- **БД**: **PostgreSQL 18** (JSONB, GIN индексы).
- **Кэш/очередь**: **Redis 7.4** (Streams для очереди матчей, rate limiting, распределённые локи).
- **Платежи**: **Telegram Stars (XTR) для цифровых чаевых** через Bot API; для EN‑запуска позже — Stripe (когда выйдем на поддерживаемые страны); локальные PSP — опционально вне Telegram.
- **AI‑coach**: сервис‑обёртка (FastAPI) → LLM провайдер, с анонимизацией и safety‑фильтрами.
- **DevOps**: Docker; прод — Kubernetes/Helm; мониторинг (Prometheus + Grafana), централизованные логи (Loki/ELK), Sentry.

### Сервисная раскладка
- `api-gateway` (NestJS, REST + Telegram webhook).
- `match-worker` (NestJS microservice/cron): обработка очереди матчей, скоринг, TTL.
- `payments-service`: выставление инвойсов Stars, учёт комиссий, вебхуки статусов.
- `ai-coach-service`: анонимизация текста, запрос к LLM, пост‑фильтры, метрики.

### Ключевые эндпойнты (черновик)
- `POST /telegram/webhook` — апдейты.
- `POST /match/find` — поставить в очередь.
- `POST /match/confirm` — взаимное согласие.
- `POST /tips/create` — выставить счёт (Stars XTR).
- `POST /ai/hint` — получить подсказку (скрыто, только отправителю).

### Миграции и схемы (SQLAlchemy + Alembic, фрагменты)
```python
from sqlalchemy import BigInteger, String, Boolean, DateTime, ForeignKey, Integer
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from datetime import datetime

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tg_id: Mapped[int] = mapped_column(BigInteger, unique=True)
    nickname: Mapped[str] = mapped_column(String(64))
    tz: Mapped[str] = mapped_column(String(32))
    bio_short: Mapped[str | None] = mapped_column(String(160))
    safety_ack: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
```prisma
model User {
  id           BigInt   @id @default(autoincrement())
  tgId         BigInt   @unique
  nickname     String   @db.VarChar(64)
  tz           String   @db.VarChar(32)
  bioShort     String?  @db.VarChar(160)
  safetyAck    Boolean  @default(false)
  createdAt    DateTime @default(now())
  topics       UserTopic[]
}

model Topic {
  id     Int     @id @default(autoincrement())
  slug   String  @unique
  title  String
  users  UserTopic[]
}

model UserTopic {
  userId  BigInt
  topicId Int
  weight  Int     @default(1)
  @@id([userId, topicId])
  @@index([topicId])
}

model Match {
  id        BigInt   @id @default(autoincrement())
  userA     BigInt
  userB     BigInt
  status    String   @db.VarChar(16) // proposed, active, declined, expired
  createdAt DateTime @default(now())
  @@unique([userA, userB])
}

model ChatSession {
  id        BigInt   @id @default(autoincrement())
  matchId   BigInt   @unique
  startedAt DateTime @default(now())
  endedAt   DateTime?
  ratingA   Int?
  ratingB   Int?
}

model Tip {
  id          BigInt   @id @default(autoincrement())
  matchId     BigInt
  fromUser    BigInt
  toUser      BigInt
  amountMinor BigInt
  currency    String   @db.VarChar(8) // XTR
  provider    String   @db.VarChar(32) // telegram-stars
  providerFee BigInt   @default(0)
  ourFee      BigInt   @default(0)
  status      String   @db.VarChar(16) // pending, paid, failed
  createdAt   DateTime @default(now())
  @@index([matchId])
}

model AiHint {
  id        BigInt   @id @default(autoincrement())
  chatId    BigInt
  userId    BigInt
  hintType  String   @db.VarChar(16) // empathy, question, boundary
  text      String
  accepted  Boolean  @default(false)
  createdAt DateTime @default(now())
}
```

### Алгоритмы (детализация)
- **Очередь матчей (Redis Streams):**
  - Producer: `match/find` пишет событие `user_id, topics[], tz`.
  - Consumer group `match-workers` читает, ищет кандидатов через SQL:
    - `JOIN user_topics` по совпадению ≥2 тем; ранжирование по сумме весов.
    - Фильтр по часовому поясу/окнам доступности.
  - Анти‑повторы: таблица `recent_contacts(user_id, other_id, until)`.
- **Скоринг:** `0.6 * tag_overlap + 0.2 * time_overlap + 0.2 * helpfulness_score`.
- **AI‑подсказки:**
  - Препроцессор: удаление PII, замена никнеймов токенами, усечение контекста.
  - Prompt‑шаблоны для чувствительных тем (утрата питомца, развод, выгорание) + стиль «эмпатия, валидирующие фразы, без диагнозов».
  - Рендер в inline‑кнопке «Вставить подсказку».

### Платежный поток (Stars, XTR)
1) Пользователь нажимает «Оставить чаевые».  
2) Бот создаёт инвойс XTR, показывает сумму с нашей комиссией (например, 10%).  
3) Telegram обрабатывает оплату; бот получает статус и пишет запись `Tip`.  
4) Вывод средств и отчётность — по правилам Telegram Stars.

### Безопасная коммуникация
- Onboarding‑карточки с правилами (не давать диагнозы, не обещать «починить», уважать границы, SOS‑ресурсы).
- Кнопка «SOS» с ссылками на горячие линии по стране пользователя.
- Фильтр токсичности — soft‑block + уведомление модератору.

### QA и аналитика
- Метрики: `match_rate`, `accept_rate`, `chat_duration`, `tip_rate`, `avg_tip`, `report_rate`.
- A/B‑флаги через конфиг, сохранение в `experiment_assignments`.
- Нагрузочные тесты матч‑поиска (pgbench + k6).

## Milestones
1. **M0 — Скелет бота (1–2 недели):** /start, анкета, темы, сохранение профиля (aiogram + FastAPI, webhook, DB миграции).
2. **M1 — Матчинг 1‑на‑1 (1–2 недели):** очередь (Redis Streams), скоринг, взаимное согласие, старт приватного чата.
3. **M2 — Чаевые (1 неделя):** инвойсы Stars (XTR) через Bot API, запись комиссий, чек в чате.
4. **M3 — AI‑coach (2 недели):** анонимизация, базовые подсказки RU, ручная модерация.
5. **M4 — Безопасность и отчётность (1 неделя):** жалобы/блок, SOS, ключевые метрики, алерты.
6. **M5 — Полировка и запуск (1 неделя):** онбординг, тексты, лимиты, мониторинг.

## Gathering Results
- **Цели MVP (через 4 недели после запуска):**
  - ≥60% получают матч ≤24ч; `accept_rate` ≥40%; средняя длительность ≥10 мин.
  - `tip_rate` ≥8%, `avg_tip` ≥ заданного порога; жалобы ≤3%.
- **Качественная обратная связь:** 10–15 интервью; правки скоринга/онбординга/подсказок AI.

## ToR (Техзадание для подрядчиков)
**Цель:** реализовать MVP Telegram‑бота «Ты не один» с матчингом 1‑на‑1, анонимностью, чаевыми (Stars) и AI‑подсказками RU.

**Пилотные допущения:**
- Аудитория: **100–300 пользователей** в первый месяц.
- Размещение: **EU‑регион** для наилучшей доступности RU/CIS.
- Бюджет: **free/минимальные тиры**; допускаем автоспячку.

**Объём работ (спринты):**
- **Спринт 1 (M0):** инфраструктура (репо, CI, контейнеры), FastAPI + aiogram, /start, анкета, профиль, БД, вебхук, команды.
- **Спринт 2 (M1):** Redis Streams, алгоритм подбора (SQL + индексы), взаимное согласие, старт приватного чата, логи/метрики.
- **Спринт 3 (M2):** интеграция Stars: инвойс XTR, статусы, запись комиссий, квитанция в чате, админ‑отчёты.
- **Спринт 4 (M3):** AI‑coach сервис, анонимизация, промпт‑шаблоны RU, safety‑фильтры, inline‑подсказки, флаги включения.
- **Спринт 5 (M4–M5):** жалобы/блок, SOS, анти‑спам/рейт‑лимиты, алерты, A/B флаги, тексты.

**Артефакты:**
- ТЗ на БД (ER‑диаграмма, миграции), API‑контракты (OpenAPI), чек‑листы тестов, Helm‑чарты, runbook.

**Критерии приёмки:**
- 95% апдейтов обрабатываются <500 мс при 100 RPS (стенд).
- Успешная оплата XTR end‑to‑end; запись комиссий; корректная отмена/ошибки.
- Анонимность: в логах нет PII; телеметрия без tg_id в открытом виде.
- AI‑подсказки: RU‑тексты, не публикуются автоматически; включаются флагом.

**Нефункциональные:**
- Обязательные линтеры/тайпы: ruff, mypy, black; покрытие тестами ≥70% критического пути.
- Секреты в Vault/Secrets Manager; TLS 1.3; HSTS на webhook.

**Риски/ограничения:** платформенные правила Telegram для цифровых товаров/Stars, юридические требования по донатам.

## Technical Review — Best Practices
- **Bot API & платежи:** для цифровых услуг Telegram требует **Stars (XTR)**; используем методы Bot API 9.x (`XTR` валюта). citeturn0search2turn0search8
- **Telegram‑фреймворк:** **aiogram 3.x** — актуальный async‑стек для Python. citeturn0search1turn0search17
- **Вебхуки:** продуктивный способ доставки апдейтов; HTTPS, валидный сертификат; см. рекомендации Telegram. citeturn1search0
- **ASGI‑деплой:** Gunicorn с uvicorn‑worker — индустриальный стандарт для FastAPI. citeturn1search13
- **Хранилища:** PostgreSQL 18 (свежий релиз) и Redis 7.4 (поддержка новых фич, TLS). citeturn0search6turn0search15
- **Stripe:** не поддерживает РФ; планируем только для EN‑рынков. citeturn0search11
- **Безопасность Telegram‑ботов:** бот‑чаты не E2E‑шифруются (HTTPS/TLS), поэтому минимизируем данные, предупреждаем пользователей. citeturn1news20

## Бюджет: запуск на бесплатных/минимальных тирах (Test Phase)
**Цель:** развернуть MVP с минимумом затрат, допускается авто‑засыпание сервисов.

### Предлагаемая схема (EU)
- **Хостинг API/бота**: Render/Fly.io/Railway — выбрать **EU‑локацию** (например, Frankfurt/AMS); включить авто‑спячку.
- **PostgreSQL**: Neon/Supabase — кластер в **EU‑West**; подключить pgBouncer/Pooling.
- **Redis/Очередь**: Upstash/Redis Cloud — EU‑регион, бесплатный план.
- **Мониторинг/логи**: Grafana Cloud (EU) free + Sentry EU; базовые алерты по вебхуку.
- **Объектное хранилище**: Cloudflare R2 — EU; бэкапы БД/снапшоты схем.
- **CI/CD**: GitHub Actions — free‑minutes, ограничить параллелизм.
- **Платежи**: Telegram Stars — без собственной платёжной инфры.

### Ограничители затрат
- Фича‑флаги: AI‑coach выключен по умолчанию, включается на 5–10% чатов.
- Aggressive idle‑timeouts: gunicorn `--timeout 30`, базы с auto‑suspend.
- Rate limiting: cap RPS до 2–5 RPS на IP/user.
- Крон‑задачи раз в сутки; логи — 7 дней retention.

### SLA пилота и апгрейд
- Цель пинга: p95 < 1.5s на бесплатных тирах.
- Порог апгрейда: >300 MAU или очереди > 50 событий/мин → перенос API/бота на один VPS в EU (Hetzner/DigitalOcean) с фиксированной ценой.

## Need Professional Help in Developing Your Architecture?
Пишите: [sammuti.com](https://sammuti.com) 🙂
Пишите: [sammuti.com](https://sammuti.com) 🙂 in Developing Your Architecture?
Пишите: [sammuti.com](https://sammuti.com) 🙂



---

# Приложение: Чек‑лист запуска, скелет репозитория и план Спринта 1

## Чек‑лист запуска Telegram‑бота
1. **BotFather**
   - [ ] `/newbot`: имя и `@username`.
   - [ ] `/setdescription`, `/setabouttext`, `/setuserpic`.
   - [ ] `/setprivacy` → Disable (чтобы бот видел все сообщения в личных чатах с ним).
   - [ ] `/setcommands` (RU):
     ```
     start - начать
     profile - профиль
     find - найти собеседника
     tips - оставить чаевые
     help - правила и помощь
     ```
   - [ ] Подключить **Stars (XTR)**: в настройках платежей (BotFather → Payments/Stars), указать получателя.
2. **Инфраструктура**
   - [ ] Домен `api.<project>.ru`, TLS‑сертификат (Let's Encrypt/ACM).
   - [ ] Webhook URL: `https://api.<project>.ru/telegram/webhook`.
   - [ ] Секреты в Vault/Secrets Manager: `TELEGRAM_BOT_TOKEN`, `DATABASE_URL`, `REDIS_URL`, `STARS_*`.
3. **Безопасность**
   - [ ] Ограничение IP/Geo на webhook (CDN/Firewall), HSTS.
   - [ ] Rate limit на user_id/chat_id (Redis Leaky Bucket).
   - [ ] Логи без PII; trace‑ids; алерты p95 latency, error rate.
4. **Платежи**
   - [ ] Тест инвойса XTR в сэндбоксе/низких суммах.
   - [ ] Учет комиссии и чек‑сообщение.
5. **Контент**
   - [ ] Onboarding‑карточки (правила/дисклеймеры, SOS‑ссылки по стране RU/CIS).
   - [ ] Шаблоны подсказок AI (RU) — фича‑флаг `ai_hints=true`.

## Скелет репозитория (Python, FastAPI + aiogram)
```
repo
├─ apps
│  ├─ api
│  │  ├─ main.py
│  │  ├─ deps.py
│  │  ├─ routers
│  │  │  ├─ health.py
│  │  │  ├─ payments.py
│  │  │  └─ match.py
│  │  └─ telemetry.py
│  ├─ bot
│  │  ├─ __init__.py
│  │  ├─ bot.py
│  │  ├─ handlers
│  │  │  ├─ start.py
│  │  │  ├─ profile.py
│  │  │  ├─ find.py
│  │  │  └─ tips.py
│  │  ├─ middlewares
│  │  │  └─ rate_limit.py
│  │  └─ keyboards
│  │     ├─ inline.py
│  │     └─ reply.py
│  ├─ ai_coach
│  │  ├─ main.py
│  │  ├─ anonymize.py
│  │  └─ provider.py
│  └─ workers
│     └─ match_worker.py
├─ core
│  ├─ config.py
│  ├─ db.py
│  ├─ redis.py
│  └─ security.py
├─ migrations (alembic)
├─ models (SQLAlchemy)
│  ├─ __init__.py
│  ├─ user.py
│  ├─ topic.py
│  ├─ match.py
│  ├─ chat.py
│  ├─ tip.py
│  └─ ai.py
├─ tests
│  ├─ unit
│  └─ integration
├─ deploy
│  ├─ docker
│  │  ├─ api.Dockerfile
│  │  ├─ bot.Dockerfile
│  │  └─ worker.Dockerfile
│  ├─ compose.yml
│  └─ k8s
│     ├─ api.yaml
│     ├─ bot.yaml
│     ├─ worker.yaml
│     └─ redis-postgres.yaml
├─ Makefile
├─ pyproject.toml
├─ README.md
└─ .env.example
```

### Минимальные файлы (фрагменты)
**apps/api/main.py**
```python
from fastapi import FastAPI
from apps.api.routers import health

app = FastAPI(title="ty-ne-odin API")
app.include_router(health.router)

@app.get("/")
def root():
    return {"status": "ok"}
```

**apps/bot/bot.py**
```python
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
import os

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
WEBHOOK_PATH = "/telegram/webhook"

bot = Bot(BOT_TOKEN)
dp = Dispatcher()

async def on_startup(app: web.Application):
    await bot.set_webhook(app["base_url"] + WEBHOOK_PATH)

def create_app(base_url: str):
    app = web.Application()
    app["base_url"] = base_url
    SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path=WEBHOOK_PATH)
    app.on_startup.append(on_startup)
    setup_application(app, dp, bot=bot)
    return app

if __name__ == "__main__":
    web.run_app(create_app(os.getenv("PUBLIC_BASE_URL")))
```

**deploy/compose.yml**
```yaml
services:
  api:
    build: { context: .., dockerfile: deploy/docker/api.Dockerfile }
    env_file: ../.env
    ports: ["8000:8000"]
    depends_on: [db, redis]
  bot:
    build: { context: .., dockerfile: deploy/docker/bot.Dockerfile }
    env_file: ../.env
    environment:
      PUBLIC_BASE_URL: ${PUBLIC_BASE_URL}
    ports: ["8080:8080"]
    depends_on: [api]
  worker:
    build: { context: .., dockerfile: deploy/docker/worker.Dockerfile }
    env_file: ../.env
    depends_on: [db, redis]
  db:
    image: postgres:18
    environment:
      POSTGRES_PASSWORD: postgres
    ports: ["5432:5432"]
  redis:
    image: redis:7.4
    ports: ["6379:6379"]
```

**Makefile**
```makefile
.PHONY: up down fmt lint test migrate
up: ; docker compose -f deploy/compose.yml up -d --build
down: ; docker compose -f deploy/compose.yml down -v
fmt: ; ruff check --fix . && black . && isort .
lint: ; mypy . && ruff check .
test: ; pytest -q
migrate: ; alembic upgrade head
```

**.env.example**
```
TELEGRAM_BOT_TOKEN=xxx
DATABASE_URL=postgresql+psycopg://postgres:postgres@db:5432/postgres
REDIS_URL=redis://redis:6379/0
PUBLIC_BASE_URL=https://api.example.ru
```

## План Спринта 1 (2 недели)
**Цель:** поднять скелет сервиса и базовые сценарии: /start, профиль, анкета, записи в БД, webhook, health.

**Задачи (issues):**
- FEAT‑1: Инициализировать репозиторий, pyproject, базовые зависимости (FastAPI, aiogram, SQLAlchemy, Alembic, Redis, pydantic, loguru, ruff, mypy, pytest).
- FEAT‑2: Настроить Docker и compose (api, bot, worker, db, redis).
- FEAT‑3: Реализовать webhook обработчик и регистрацию /setwebhook.
- FEAT‑4: Модель БД: users, topics, user_topics + миграции.
- FEAT‑5: Хэндлеры бота: /start, /profile, сбор тем (inline‑кнопки), сохранение в БД.
- FEAT‑6: Health/metrics эндпойнты, Prometheus экспортер.
- CHORE‑1: Линтеры/форматтеры (ruff/black/isort, mypy), pre‑commit.
- OPS‑1: CI (GitHub Actions): линт/тест/билд контейнеров.

**Критерии готовности:**
- Webhook работает по HTTPS, бот отвечает на /start и записывает профиль.
- Миграции применяются, данные сохраняются, метрики доступные.
- Код проходит линтеры и тесты; контейнеры собираются.

**Риски и план B:**
- Проблемы с TLS/доменом → временный ngrok/Cloudflare Tunnel (только для стейджа).
- Telegram ограничения на webhook частоту → бэкофф и алерты.

