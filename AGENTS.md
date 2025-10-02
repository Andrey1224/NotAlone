# Repository Guidelines

## Project Structure & Module Organization
- `apps/api` exposes HTTP endpoints and shared routers; `apps/bot` drives Telegram flows; `apps/ai_coach` and `apps/workers` host async services.
- `core` centralizes settings, logging, and utilities; extend it before scattering helpers elsewhere.
- Persisted models live in `models`, while `migrations` tracks Alembic revisions; run new schema changes through both.
- Container and deployment manifests live in `deploy`; shared Make targets in `Makefile`.
- Tests sit in `tests` and mirror module names (e.g., `tests/apps/api/test_match.py`).

## Build, Test, and Development Commands
- `make up` boots the Docker stack (API, bot, db, redis); `make down` tears it down.
- `make dev-api` and `make dev-bot` run API and Telegram bot locally once Postgres/Redis are up.
- `make migrate` applies Alembic migrations; pair with `make migrate-create` when introducing schema changes.
- `make fmt`, `make lint`, and `make test` format, lint, and execute pytest + coverage respectively.
- For focused runs use `pytest tests/apps/api -k match_flow`; add `--cov=apps --cov=models` to track coverage.

## Coding Style & Naming Conventions
- Python 3.12 code is formatted with Black (120 char limit) and import-sorted via isort; Ruff enforces lint rules (E,F,I,N,W,B,C4,UP).
- Prefer snake_case for modules/files, PascalCase for SQLAlchemy models, snake_case attributes/fields, and SCREAMING_SNAKE for settings.
- Type hints are mandatory; keep code mypy-clean with `mypy --config-file pyproject.toml`.

## Testing Guidelines
- Use pytest with asyncio fixtures; new async tests should leverage `pytest.mark.asyncio`.
- Name files `test_<area>.py`, classes `Test<Feature>`, functions `test_<scenario>`.
- Target integration coverage around matching flows; include factories or fakes for external services.
- Ensure migrations include regression tests when touching schema-critical logic.

## Commit & Pull Request Guidelines
- Follow Conventional Commit prefixes (`feat:`, `fix:`, `chore:`, `docs:`); keep subjects under 60 chars and wrap bodies at 72.
- Reference issues in the body (`Refs #123`) and describe rollout considerations or migrations run.
- PRs should summarize scope, list manual/automated test evidence, and attach bot screenshots or API traces when behavior changes.

## Security & Configuration Tips
- Keep secrets in `.env`; never commit tokens. Rotate Telegram and OpenAI keys immediately on leaks.
- Validate `.env` updates against `core/settings` defaults and document new variables in `README.md`.
- Restrict logging of PII; rely on anonymized identifiers when adding metrics or alerts.
