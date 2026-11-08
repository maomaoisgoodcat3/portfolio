# Tasks

Status is one of `todo`, `doing`, `done`. Before switching to another agent or
tool, write in Notes where the work stopped.

| ID | Task | Planned | Status | Notes |
|---|---|---|---|---|
| T-00 | Dev environment on Windows: conda env, Git repo, agent permissions | 2026-11-07 | done | 2026-11-08: env `portfolio` from `environment.yml`; repo at `C:\dev\portfolio`; delete commands blocked or asked in Antigravity; OpenCode passed the second permission test; Cline asks before reading `.env`. Still to test: Antigravity blocks reading `be/.env` with the new rule; Cline delete test. |
| T-01 | Backend skeleton: FastAPI `GET /health`, settings with pydantic-settings, `be/.env.example`, Docker Compose (`db` + `api`), first pytest | 2026-11-08 | done | 2026-11-08: `/health` returns `{"status":"ok"}`; `pytest` 1 passed; `select 1` works in `db`; host port for Postgres changed to 5433. |
| T-02 | Agent rules and skills (`AGENTS.md`, `.agents/`) | 2026-11-08 | done | 2026-11-08: `AGENTS.md`, backend glob rule, skills `start-task`, `review-diff`, `close-task`. Rules loaded by: Antigravity <yes/no>, OpenCode <yes/no>, Copilot <yes/no>, Cline <yes/no>. Skills listed by: Antigravity <yes/no>, OpenCode <yes/no>, Copilot <yes/no>. Pointer files added: <none / .github/copilot-instructions.md / .clinerules/00-agents.md>. |
| T-03 | Database schema for blocks and visibility, Alembic migration | 2026-11-09 | todo |Handoff T-03 (from Antigravity, 2026-11-09 02:28)
Done: plan drafted, not approved
Next step: review the plan against tab 8 |
| T-04 | Content CRUD API with unit tests | 2026-11-09 | todo | |
| T-05 | Admin login: Argon2id, session cookie, CSRF, lockout, TOTP, recovery codes, 401/403 tests | 2026-11-10 | todo | |
| T-06 | MCP project brain shared by the agents | 2026-11-10 | todo | |
| T-07 | Next.js frontend: public page and admin | 2026-11-11 | todo | |
| T-08 | UI tests (browser subagent, Playwright) and OWASP review | 2026-11-11 | todo | |
| T-09 | GitHub adapter | 2026-11-12 | todo | |
| T-10 | CI with GitHub Actions and deploy to Vercel | 2026-11-12 | todo | |
| T-11 | Buffer: password reset email, login alert email, fixes, README | 2026-11-13 | todo | |