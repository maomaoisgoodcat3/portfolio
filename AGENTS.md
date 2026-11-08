# AGENTS.md

Instructions for AI coding agents working in this repository
(Antigravity, OpenCode, GitHub Copilot, Cline). Keep this file short;
details live in `docs/`.

## Project
Personal portfolio website for a CV. Monorepo:
- `be/` - FastAPI backend (Python 3.12). Entry point `be/app/main.py`, settings in `be/app/config.py`.
- `fe/` - Next.js + TypeScript frontend (not created yet).
- `docker-compose.yml` - Postgres 17 (`db`) and the API (`api`).
- `docs/` - PLAN, TASKS, DECISIONS, CONVENTIONS.

## Read before you plan
1. `docs/TASKS.md` - work only on the task ID the user gives you.
2. `docs/DECISIONS.md` - settled decisions. Do not reopen them; ask if one blocks you.
3. `docs/CONVENTIONS.md` - code style, naming, commit format.

## Environment
- Windows 11 Home, PowerShell. Repo root: `C:\dev\portfolio`.
- Python and Node come from the conda env `portfolio` (`environment.yml`).
- Docker Desktop runs `db` and `api`. Host ports bind to 127.0.0.1 only.
  Postgres is on host port 5433; inside Compose the API reaches `db:5432`.

## Hard rules
1. Never open, print, copy or edit any `.env` file, and never print environment
   variables. Learn variable names from `be/.env.example`.
2. Never run commands that delete files, install or remove packages, rewrite git
   history, push, or delete Docker volumes. Write the command in your reply and
   let the user run it.
3. Do not edit `AGENTS.md`, `.agents/`, `opencode.json`, `environment.yml` or
   `docker-compose.yml` unless the task explicitly says so.
4. Every exposed port binds to `127.0.0.1`. Never `0.0.0.0` on the host side.
5. No secrets, tokens or real personal data in code, tests, fixtures, logs or
   commit messages.
6. For changes to more than one file, present a plan and wait for approval
   before editing.
7. Stay inside the task's scope. List anything else you notice under
   "Follow-ups" instead of doing it.

## Definition of done
- Tests added or updated for the change. Give the exact `pytest` command; the
  user runs it and pastes the result.
- `ruff check be` reports no errors.
- `docs/TASKS.md` updated (status and a one-line note); new decisions appended
  to `docs/DECISIONS.md`.
- The final message lists every file changed and every command the user must run.