# Task Completion Checklist

## When Task is Completed

### Code Quality
1. **Format code:** `make fmt`
2. **Lint code:** `make lint`
3. **Run tests:** `make test`

### Database Changes
If you modified models or database schema:
1. **Create migration:** `make migrate-create`
2. **Apply migration:** `make migrate`
3. **Test migration rollback** (if needed)

### Testing
- Run relevant unit tests
- Test integration flows
- Include factories/mocks for external services
- Target coverage around matching flows

### Git Workflow
- Follow Conventional Commits: `feat:`, `fix:`, `chore:`, `docs:`
- Keep subject under 60 chars
- Reference issues in body (`Refs #123`)
- Describe rollout considerations

### Security
- Check `.env` updates against `core/settings`
- Never commit tokens or secrets
- Validate no PII in logs

### Documentation
- Update README.md if needed
- Document new environment variables
- Add inline documentation for complex logic

## Pre-commit Checks
The project uses pre-commit hooks that automatically run:
- ruff check and fix
- black formatting
- isort import sorting
- mypy type checking
