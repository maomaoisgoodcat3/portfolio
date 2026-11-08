# Conventions

## Language
- All text on the site, code, comments and commit messages: English.

## Repository layout
- `be/` backend (FastAPI): app code in `be/app/`, tests in `be/tests/`.
- `fe/` frontend (Next.js, not created yet).
- `docs/` PLAN, TASKS, DECISIONS, CONVENTIONS.
- `docker-compose.yml`, `environment.yml`, `.gitattributes`, `.gitignore` at the repo root.

## Secrets and config
- Settings come from environment variables through pydantic-settings.
- Every variable is listed with a fake value in `be/.env.example`; the real `be/.env` is created by hand and never committed.

## Ports
- Every published port binds to `127.0.0.1`, never `0.0.0.0` on the host side.
- Host ports: API 8000, Postgres 5433.

## Line endings
- LF for everything (`.gitattributes`), except `.ps1` and `.cmd` (CRLF).

## Tests
- pytest; run from `be/`: `Set-Location C:\dev\portfolio\be` then `pytest`.

## Git
- Conventional Commits with a scope, e.g. `feat(be): backend skeleton with health check`.
- Check `git status` before every commit; no `.env` file may be staged.
- I push myself; agents never push.