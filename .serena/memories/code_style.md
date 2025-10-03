# Code Style and Conventions

## Python Version
- Python 3.12+

## Code Formatting
- **Black:** line length 120 characters
- **isort:** import sorting
- **Ruff:** linting with rules E, F, I, N, W, B, C4, UP
- **mypy:** type checking

## Naming Conventions
- **Files/modules:** snake_case
- **Classes:** PascalCase (SQLAlchemy models)
- **Functions/variables:** snake_case
- **Constants:** SCREAMING_SNAKE_CASE
- **Settings:** SCREAMING_SNAKE_CASE

## Type Hints
- Mandatory for all functions and methods
- Keep code mypy-clean

## Code Structure
- Keep code organized by modules in `apps/`
- Use dependency injection via FastAPI/aiogram
- Use async/await patterns consistently
- Follow SQLAlchemy 2.x patterns

## Dependencies
Defined in `pyproject.toml`:
- Production: FastAPI, aiogram, SQLAlchemy, etc.
- Development: ruff, black, isort, mypy, pytest

## Configuration
- Use Pydantic settings in `core/config.py`
- Environment variables in `.env`
- Never commit secrets
