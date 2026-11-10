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
- Next.js App Router in fe/src/app, TypeScript strict, Tailwind. Run npm commands from fe/.
- All backend calls go through fe/src/lib/api.ts, always to relative /api/... URLs, with credentials "same-origin".
- The CSRF token lives in React state only (never localStorage, sessionStorage or a cookie set by the frontend) and is sent as X-CSRF-Token on POST, PUT, PATCH and DELETE.
- Never use dangerouslySetInnerHTML. Links are rendered only for http:// and https:// URLs (safeHref).
- The dev server binds to 127.0.0.1 (next dev -H 127.0.0.1).
- Before every commit, in fe/: npm run lint, npx tsc --noEmit, npm run build.

## Block content keys
- profile props: name, headline, location. about props: text. contact props: text.
- skills items: name, level. experience, projects, research items: title, subtitle, period, description, url, tags (string array).
- links and contact items: label, url. stats items: provider, account, show.
- Missing keys render nothing; unknown keys are ignored.

## Git
- One branch per task: `task/T-02-short-name`.
- Conventional Commits: `feat`, `fix`, `chore`, `docs`, `test`, `refactor`,
  with scope `be`, `fe`, `infra` or `docs`. Example: `feat(be): add health check`.
- Check `git status` before every commit; no `.env` file may be staged.
- I push myself; agents never push.
- Work on a task branch (`git switch -c task/T-03-short-name`). WIP commits use the type `wip` (`wip(be): T-03 handoff`) and never go to `main` unsquashed.

## Tasks
- `docs/TASKS.md` uses IDs `T-01`, `T-02`, ... Each task has a status:
  `todo`, `doing` or `done`.

## Agent files
- `AGENTS.md` stays short (under two pages); details go in `docs/`.
- Files in `.agents/rules/` start with YAML frontmatter that has a `trigger`.
- Skills live in `.agents/skills/<name>/SKILL.md`; `<name>` is lowercase with
  hyphens and matches the `name` field. No Antigravity workflows.

## Prompts
- Standard prompt sections: Context, Goal, Acceptance criteria, Scope, Constraints, Output.
- Paste full error output; never trim logs.
- At most three files per agent turn.

## Database
- Table names are plural snake_case; primary keys are uuid generated in Python.
- Every table has created_at and updated_at (timestamptz, default now()).
- Every schema change is an Alembic migration that also downgrades; never edit a migration that has been applied.
- Run migrations inside the api container: docker compose exec api alembic upgrade head.

## API
- Public routes under /api/public/*, admin routes under /api/admin/* and always behind require_admin.
- Errors use HTTPException with a short detail; never return stack traces or SQL.