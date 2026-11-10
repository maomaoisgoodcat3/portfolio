# Decisions

One line per decision: `- YYYY-MM-DD - <decision> - because <reason>` (reason when there is one).
Settled decisions are not reopened without a new entry that replaces them.

## Product
- 2026-11-05 - Site content is in English.
- 2026-11-05 - Use a Vercel subdomain, no custom domain.
- 2026-11-05 - The project replaces Favorita on the CV; the TradeLab idea is dropped.
- 2026-11-05 - Never store passwords, financial data or Gmail data on the site.
- 2026-11-05 - The chatbot reads public data only, enforced at the data layer - because a prompt alone cannot stop data leaks.
- 2026-11-05 - The paper under review is shown publicly, with a toggle to hide the venue.
- 2026-11-05 - Backend is Python with a REST API, packaged with Docker, separate from the frontend; deploy via GitHub and Vercel.
- 2026-11-06 - Frontend is React + TypeScript on Next.js.
- 2026-11-06 - One repo with `fe/` and `be/`.
- 2026-11-06 - The public page shows every public block; no filters or per-role views.
- 2026-11-06 - When there is a choice, pick the more secure option.
- 2026-11-06 - Accepted security additions: password reset also needs TOTP or a recovery code; recovery codes are one-time and hashed; the chatbot uses a SELECT-only database role on public data; chatbot logs hash IPs with a salt and have a retention period; GitHub working hours are shown coarsely with a hide toggle; database backups are encrypted and never public; the Contact block has no raw address, phone or plain email - because each one closes a concrete attack or privacy leak.

## Tools and agents
- 2026-11-06 - Agent tool chain: Antigravity -> OpenCode + Gemini API key -> GitHub Copilot (Student) -> Ollama -> manual - because Gemini CLI stopped serving free accounts on 2026-06-18, so tier 2 needs an open-source agent with a free Gemini API key.
- 2026-11-07 - Antigravity uses the Request Review preset; Turbo is never used; AI Credit Overages set to Never; telemetry off - because every command and plan must be approved by me.
- 2026-11-08 - Antigravity deny rules use workspace-relative paths: `read_file(.env)`, `read_file(be/.env)` - because a rule target is a path, so `read_file(.env)` alone did not block `be/.env`.
- 2026-11-08 - OpenCode runs with `"tools": {"bash": false}` and `"bash": "deny"`, and must pass a start-of-session check (asking it to run `git status` must be refused) - because in one test it deleted a folder despite the config; in a later test it blocked correctly.
- 2026-11-08 - Cline is the backup for tier 2, with every auto-approve option off and YOLO mode never on - because its safety comes from approving each action by hand.
- 2026-11-08 - `AGENTS.md` at the repo root is the single source of agent rules for all four tools - because separate copies per tool drift apart.
- 2026-11-08 - Repeatable procedures are skills in `.agents/skills/<name>/SKILL.md` (start-task, review-diff, close-task), invoked as `/<name>`; no Antigravity workflows - because workflows stopped working on 2026-11-01 and skills follow an open format read by Antigravity, OpenCode and Copilot.
- 2026-11-08 - Skills that change files say "Use only when the user types /<name>" in their description - because agents may trigger skills on their own.
- 2026-11-08 - Backend details live in `.agents/rules/backend.md` with `trigger: glob` on `be/**` - because they only matter when backend files are touched.
- 2026-11-08 - Cline gets skills by path ("Follow .agents/skills/<name>/SKILL.md") - because Cline does not read `.agents/skills/`.
- 2026-11-08 - MCP tokens go only in the global `~/.gemini/config/mcp_config.json`, never in `.agents/mcp_config.json`; MCP tools sit in Ask - because the repo is public and MCP servers run with my permissions.
- 2026-11-09 - In OpenCode 1.x, skills are invoked by name ("Use the start-task skill for task T-03") or through thin wrappers in .opencode/commands/ - because OpenCode 1.x does not list skills in the / menu.
- 2026-11-09 - In Copilot, skills are invoked by path ("Follow .agents/skills/<name>/SKILL.md") until they appear in the / menu - because the / menu did not list them in the test.
- 2026-11-09 - Cline is paused; if OpenCode fails its start-of-session check, go straight to Copilot - because Cline responded too slowly to be usable.
- 2026-11-09 - One task per conversation; when a conversation gets long, write a handoff note and start a new one instead of using /compact - because a summary made by the agent can drop rules, while a handoff note lives in the repo.
- 2026-11-09 - Switching tools mid-task: commit WIP on the task branch, write a handoff note (Done, In progress, Next step, Last test run, Do not touch, Open questions), then open the new tool with the standard handoff prompt - because tools do not share memory; only the repo carries context.
- 2026-11-09 - Never run /init in OpenCode or Copilot - because it would rewrite AGENTS.md or add a second instruction file.
- 2026-11-09 - Local models (Ollama, qwen2.5-coder 3B, 4k context) are used only through `ollama run` for small single tasks: regex, docstrings, commit messages, explaining under 80 lines - because the machine has little free RAM and OpenCode's prompt does not fit in 4k tokens.
- 2026-11-09 - OpenCode + Ollama: <not set up / tried, result: ...>.
- 2026-11-09 - OpenCode uses a Flash-Lite model (<exact model id>) by default (set in the global ~/.config/opencode/opencode.json, not in the repo) and switches to gemini-3.8-flash only for hard steps - because the free Gemini API tier allows 20 requests per day for 3.8 Flash and 3.6 Flash (checked in AI Studio on 2026-11-09) and <RPD> for Flash-Lite, and each agent loop is one request.
- 2026-11-09 - Work is routed by size: tab completion (Copilot) for line-level code, Ollama for small single tasks, OpenCode for small fixes, Antigravity for multi-file tasks with a plan - because the Antigravity weekly limit must last until the deploy on 2026-11-12.
- 2026-11-09 - Prompts state which files the agent may read ("Read only ... Ask before opening any other file.") - because unscoped prompts made the agent read about ten files for a two-file task.

## Environment
- 2026-11-07 - Pure Windows 11 Home: the repo lives at `C:\dev\portfolio`; WSL 2 is only the Docker backend and a place to run Linux commands when needed.
- 2026-11-07 - Use conda via Miniforge (conda-forge) with one `environment.yml`, instead of venv - because it can manage many kinds of libraries, not only Python.
- 2026-11-07 - Python 3.12 and Node 24 come from the conda env. (If Node had to be installed from nodejs.org instead, write that here.)
- 2026-11-07 - Line endings are LF via `.gitattributes` (`.ps1` and `.cmd` stay CRLF) - because the code runs in Linux containers.
- 2026-11-07 - Real secrets never enter the repo: `.env` files are git-ignored, only `.env.example` with fake values is committed - because the repo is public.

## Backend and Docker
- 2026-11-08 - Docker Desktop with the WSL 2 backend - because it is the only option on Windows Home.
- 2026-11-08 - Images: `postgres:17` for `db`, `python:3.12-slim` for `api`.
- 2026-11-08 - Every published port binds to 127.0.0.1 - because nothing should be reachable from the local network.
- 2026-11-08 - Postgres is published on host port 5433 (`127.0.0.1:5433:5432`); the API still uses `db:5432` inside Compose - because a native Windows Postgres already uses port 5432.
- 2026-11-08 - Library versions in use: Python 3.12.16, pytest 9.2.0, anyio 4.16.0, fastapi <x>, uvicorn <x>, pydantic-settings <x>, sqlalchemy <x>, psycopg <x>, alembic <x>, httpx <x>, ruff <x>, nodejs <x>.


## Architecture (2026-11-09)
- 2026-11-09 - Deploy frontend and backend as one Vercel project with Vercel Services; FastAPI on the native Python runtime, not the container runtime - because one domain allows a SameSite=Strict session cookie without CORS, and the container runtime is still in beta.
- 2026-11-09 - Neon Postgres Free plan for production - because it is free, includes pgvector for phase 3, and scales to zero when idle.
- 2026-11-09 - Resend Free plan, sending from onboarding@resend.dev to the admin's own address - because all emails go to the admin only, so no custom domain is needed.
- 2026-11-09 - No Redis in the MVP; sessions, login counters and rate limits are stored in Postgres - because serverless functions keep no memory between requests and one fewer service is easier to secure.
- 2026-11-09 - Nine block types: profile, about, skills, experience, projects, research, links, stats, contact; external profile links are "links" (not "profiles") - because "profile" and "profiles" were too easy to confuse.
- 2026-11-09 - One "stats" block type for every external site: each item names a provider; synced data goes to one external_stats table keyed by (provider, account); each site is a subclass of BaseStatsAdapter in a registry, and Pydantic validates items with a discriminated union on provider - because adding a site must not need a schema migration.
- 2026-11-09 - New blocks and items default to visibility 'admin' - because new content must never become public by accident.
- 2026-11-09 - Visibility and block type use text columns with CHECK constraints instead of Postgres enums - because changing a CHECK constraint is a simpler migration.
- 2026-11-09 - Admin routes depend on require_admin from T-04 onward, returning 401 until real auth exists in T-05 - because no admin endpoint may ever be open, even between tasks.
- 2026-11-09 - Task branches are squash-merged into main - because main should show one commit per task.
- 2026-11-09 - In SQLAlchemy models, use short constraint names (`type`, `visibility`, `title_length`) with MetaData naming convention (`ix`, `uq`, `ck`, `fk`, `pk`) - because explicit full names would duplicate convention prefixes.
- 2026-11-09 - In Alembic env.py, create engine directly with `create_engine(settings.get_database_url())` without `config.set_main_option` - because URL object is used directly and password exposure in config logs is avoided.
- 2026-11-09 - In Settings, database credentials and host/port are required without default values - because credentials and target environment should always be explicitly supplied by configuration.
- 2026-11-10 - Tests run only on the database portfolio_test; conftest refuses any database name not ending in _test - because tests must never delete dev data.
- 2026-11-10 - be/.env points host tools to 127.0.0.1:5433 (Docker Postgres); docker-compose.yml overrides POSTGRES_HOST=db and POSTGRES_PORT=5432 for the api container - because pytest was silently using the native Windows Postgres on 5432.
- 2026-11-10 - A block's type cannot change after creation, and stats items are stored as validated, normalized data - because stored items must always match their block type.
- 2026-11-10 - __pycache__ and *.pyc are ignored by git - because build/cache artifacts should not be tracked.
