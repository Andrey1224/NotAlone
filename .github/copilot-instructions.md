# GitHub Copilot Instructions for NotAlone

## Project Overview
This is a Telegram bot for anonymous peer-to-peer support matching. Users find conversation partners based on shared life experiences (burnout, loss, relocation). Built with Python 3.12, FastAPI, aiogram 3.x, PostgreSQL, Redis, and optional AI coaching.

## MCP Tool Usage

**Always use Context7 when I need code generation, setup or configuration steps, or library/API documentation.** This means you should automatically use the Context7 MCP tools to resolve library id and get library docs without me having to explicitly ask.

**Use Serena MCP for all code navigation and edits.** Serena provides semantic code understanding and precise editing capabilities for this codebase.

- If you need browser/UI actions → Use Playwright MCP
- If you need context from documents/code/databases → Use Context7 MCP
- If you can solve with pure code/locally → Don't use MCP
- For code navigation, symbol finding, and edits → Use Serena MCP

## Architecture & Service Boundaries

**4 main services** (each with its own entry point):
- `apps/api/` - FastAPI REST API + Telegram webhook receiver
- `apps/bot/` - aiogram 3.x bot with webhooks (NOT polling)
- `apps/ai_coach/` - Optional AI conversation hints with PII anonymization
- `apps/workers/` - Background Redis Stream consumers for matching

**Core modules** in `core/`: config (Pydantic Settings), db (async SQLAlchemy), redis, security.
**Data models** in `models/`: SQLAlchemy 2.x with `Mapped[type]` and `mapped_column()` syntax.

## Development Workflow

### Quick Start Commands
```bash
make up              # Full Docker stack (preferred for development)
make dev-api         # Local API only (requires: docker compose up db redis -d)
make dev-bot         # Local bot only
make migrate         # Apply database migrations
make migrate-create  # Create new migration (interactive)
make fmt             # Auto-format (ruff --fix, black, isort)
make lint            # Type check (mypy) + lint (ruff)
make test            # pytest with coverage
```

### Database Operations
- **Always** use `AsyncSession` with `async with AsyncSessionLocal() as session`
- Migrations managed by Alembic - never modify models without creating migrations
- Import all models in `migrations/env.py` for autogenerate to work
- Use `from core.db import Base` for model inheritance

## Project-Specific Patterns

### Async Throughout
Every operation is async: database, Redis, HTTP clients, bot handlers. Use `async def` and `await` consistently.

### Environment Configuration
```python
from core.config import settings  # Pydantic Settings singleton
# All config via environment variables, loaded from .env
```

### Dependency Injection (FastAPI)
```python
from apps.api.deps import get_db, get_redis_client

async def endpoint(
    db: AsyncSession = Depends(get_db),
    redis: redis.Redis = Depends(get_redis_client)
):
```

### SQLAlchemy 2.x Modern Syntax
```python
# Use this (new):
class User(Base):
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False)

# NOT this (old):
# id = Column(BigInteger, primary_key=True)
```

### Bot Webhooks (Critical)
- Bot runs via webhooks at `{PUBLIC_BASE_URL}/telegram/webhook`
- **Never** use polling mode - webhooks only
- Requires HTTPS with valid certificate in production
- Webhook setup in `apps/bot/bot.py` on_startup

### Redis Streams for Match Queue
- User requests written to Redis Stream on `/find` endpoint
- Worker consumes via `XREADGROUP` with consumer groups
- Anti-repeat logic prevents duplicate recent matches
- TTL for queue entries (24h default)

## Critical Implementation Details

### Privacy & Anonymity
- **Zero PII collection** - no phone/email/real names
- Only pseudonyms in `User.nickname`
- AI coach strips PII before LLM calls (`apps/ai_coach/anonymize.py`)
- Log anonymized identifiers only

### Telegram Stars Payments
- Use Bot API 9.x XTR currency methods
- Record both `provider_fee_minor` and `our_commission_minor`
- Webhook handler at `/payments/webhook/telegram-stars`
- Show itemized receipts for transparency

### AI Boundaries
- **NOT therapy** - only coaching hints
- Feature-flagged via `AI_ENABLED=false` by default
- Suggestions shown privately to sender only
- Include crisis hotline disclaimers
- Anonymize text in `anonymize.py` before LLM

## Code Quality Standards

### Formatting & Linting
- **Line length**: 120 chars (configured in ruff/black)
- **Import order**: isort with automatic sorting
- **Type hints**: Mandatory - keep mypy clean
- **Ignore patterns**: B008 (FastAPI Depends), F821 (forward refs)

### Testing Strategy
- Unit tests for business logic (scoring algorithms, anonymization)
- Integration tests for API endpoints with test database
- Target ≥70% coverage on critical paths (matching, payments)
- Use pytest fixtures for database/Redis setup

### File Naming
- `test_<area>.py` for test files
- Snake_case for modules, PascalCase for models
- SCREAMING_SNAKE for environment variables

## Common Gotchas

1. **Alembic autogenerate**: Import new models in `migrations/env.py` or autogenerate misses them
2. **Redis Streams**: Consumer groups need `XGROUP CREATE` before first `XREADGROUP`
3. **Async sessions**: Always use `async with` pattern, never store sessions as instance variables
4. **Bot rate limits**: Implement exponential backoff for Telegram API calls
5. **Webhook vs polling**: This project uses webhooks exclusively - no polling mode

## Security Checklist

- Store secrets in environment variables only (`.env` file)
- Rate limiting via `RateLimitMiddleware` in bot
- HTTPS required for production webhooks
- PII minimization and anonymization throughout
- User safety acknowledgment flow (`safety_ack` field)

When implementing new features, follow the existing service boundaries and async patterns. Prefer extending existing modules over creating new ones unless there's a clear architectural reason.
