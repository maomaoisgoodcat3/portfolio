# Conventions

## Language
- Code, comments, commit messages and all text on the site: English.
- Planning notes in `docs/` may be in Vietnamese.

## Repository layout
- `be/` backend (FastAPI): app code in `be/app/`, tests in `be/tests/`.
- `fe/` frontend (Next.js App Router, TypeScript, Tailwind v4) in `fe/src/`.
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
  - Run `ruff check be` before `pytest`; ruff catches missing imports and undefined names first.
- Tests use only the portfolio_test database (see conftest.py); never point tests at portfolio_dev.
- Helpers in sessions.py and rate_limit.py flush but never commit; routers commit once per request. Tests pass `now` explicitly.

## TypeScript (fe/)
- Next.js App Router in fe/src/app, TypeScript strict, Tailwind. Run npm commands from fe/.
- All backend calls go through fe/src/lib/api.ts, always to relative /api/... URLs, with credentials "same-origin".
- The CSRF token lives in React state only (never localStorage, sessionStorage or a cookie set by the frontend) and is sent as X-CSRF-Token on POST, PUT, PATCH and DELETE.
- Never use dangerouslySetInnerHTML. Links are rendered only for http:// and https:// URLs (safeHref).
- The dev server binds to 127.0.0.1 (next dev -H 127.0.0.1).
- Before every commit, in fe/: npm run lint, npx tsc --noEmit, npm run build.
- State (useState) lives only in components marked "use client"; page.tsx holds no state.
- User text always wraps (overflow-wrap: anywhere); no fixed widths and no horizontal scroll at 360px.
- next.config.ts is edited by adding keys only, never replaced; the Tailwind loader lives in turbopack.rules.
## Block content keys

One block = one entry. Only `profile` is limited to one block. Items stay in the database but are not used in the UI.

| type | title | props |
|---|---|---|
| profile | not shown | name, headline, location, avatar_url (https only) |
| links | link text | url (required) |
| contact | label, e.g. "Email" | content (shown after Reveal) |
| about | heading | content |
| experience | role | subtitle (company), period, content, url |
| projects | project name | period, content, url, tags |
| research | paper title | subtitle (venue or status), period, content, url |
| skills | group name | tags |
| stats | label | provider ("github"), account |

Public page: profile fills the top half of the fixed left sidebar; links, then contact, fill the bottom half, which scrolls on its own. Other types are grouped in this order: about, experience, projects, research, skills, stats. Every url goes through `safeHref`. Missing keys render nothing.

## Git
- One branch per task: `task/T-02-short-name`.
- Conventional Commits: `feat`, `fix`, `chore`, `docs`, `test`, `refactor`,
  with scope `be`, `fe`, `infra` or `docs`. Example: `feat(be): add health check`.
- Check `git status` before every commit; no `.env` file may be staged.
- I push myself; agents never push.
- Work on a task branch (`git switch -c task/T-03-short-name`). WIP commits use the type `wip` (`wip(be): T-03 handoff`) and never go to `main` unsquashed.
- Commit a wip checkpoint as soon as an agent finishes, before testing. Never use Discard in the Source Control view on uncommitted agent work.
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
- Table names are plural snake_case; primary keys are uuid generated in Python, except rate_limits (text key).
- Content tables have created_at and updated_at (timestamptz, default now()); state and log tables (sessions, recovery_codes, login_events, rate_limits) keep only the timestamps they need.
- Every schema change is an Alembic migration that also downgrades. After the first deploy, never edit an applied migration; before it, editing is allowed only with downgrade and upgrade on every database that ran it.
- Run migrations inside the api container: docker compose exec api alembic upgrade head.

## API
- Public routes under /api/public/*, admin routes under /api/admin/* and always behind require_admin.
- Errors use HTTPException with a short detail; never return stack traces or SQL.

## Auth
- Every /api/admin route depends on require_admin. No exceptions; a test walks app.routes to enforce it.
- POST, PUT, PATCH and DELETE on admin routes need the X-CSRF-Token header.
- Login errors are always the same generic message.
- The session cookie is always set with the same attributes: __Host-session, HttpOnly, Secure, SameSite=Strict, Path=/, no Domain.
- Never log passwords, TOTP codes, recovery codes, tokens or secrets.
- Auth tests use TestClient(app, base_url="https://testserver").
- New secrets go in be/.env with a placeholder in be/.env.example; agents never read be/.env.

## Tooling
- MCP servers live in tools/<name>, use their own conda env, are read-only unless a task says otherwise, and never write to stdout.