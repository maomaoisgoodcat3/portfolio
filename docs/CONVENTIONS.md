# Conventions

## Language
- Code, comments, commit messages and all text on the site: English.
- Planning notes in `docs/` may be in Vietnamese.

## Repository layout
- `be/` backend (FastAPI): app code in `be/app/`, tests in `be/tests/`.
- `fe/` frontend (Next.js, not created yet).
- `docs/` PLAN, TASKS, DECISIONS, CONVENTIONS.
- `AGENTS.md` and `.agents/` (rules and skills) for AI agents.
- `docker-compose.yml`, `environment.yml`, `.gitattributes`, `.gitignore` at the repo root.

## Secrets and config
- Settings come from environment variables through pydantic-settings.
- Every variable is listed with a fake value in `be/.env.example`; the real
  `be/.env` is created by hand and never committed.

## Ports
- Every published port binds to `127.0.0.1`, never `0.0.0.0` on the host side.
- Host ports: API 8000, Postgres 5433.

## Line endings
- LF for everything (`.gitattributes`), except `.ps1` and `.cmd` (CRLF).

## Python (be/)
- Lint and format with ruff: `ruff check be`, `ruff format be`.
- snake_case for functions and variables, PascalCase for classes,
  UPPER_CASE for constants.
- Tests use pytest, run from `be/`. Files are named `test_<module>.py`;
  one behaviour per test.

## TypeScript (fe/)
- Filled in when the frontend starts. Strict mode on.

## Git
- One branch per task: `task/T-02-short-name`.
- Conventional Commits: `feat`, `fix`, `chore`, `docs`, `test`, `refactor`,
  with scope `be`, `fe`, `infra` or `docs`. Example: `feat(be): add health check`.
- Check `git status` before every commit; no `.env` file may be staged.
- I push myself; agents never push.

## Tasks
- `docs/TASKS.md` uses IDs `T-01`, `T-02`, ... Each task has a status:
  `todo`, `doing` or `done`.

## Agent files
- `AGENTS.md` stays short (under two pages); details go in `docs/`.
- Files in `.agents/rules/` start with YAML frontmatter that has a `trigger`.
- Skills live in `.agents/skills/<name>/SKILL.md`; `<name>` is lowercase with
  hyphens and matches the `name` field. No Antigravity workflows.