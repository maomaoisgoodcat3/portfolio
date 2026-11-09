# Plan

Personal portfolio website with a private admin area. It replaces the Favorita
project on my CV. Deadline for the MVP: 2026-11-13.

## Goals (in priority order)
1. Replace Favorita on my CV. Show developer skills first (frontend and
   backend), plus some AI.
2. Run live on the internet so recruiters and others can visit it, not only on
   localhost.
3. Very strict security, because the site links to many of my profiles.

## Audience
| Group | Needs to see | Time on page |
|---|---|---|
| HR, recruiters | Target role, main skills, experience, profile links | Tens of seconds |
| Interviewing engineers | Repo, README, architecture, tests, CI, security and chatbot design | A few minutes |
| Lecturers, research groups | Thesis, ORCID, paper under review | A few minutes |

## Language and domain
- All site content is in English.
- Hosted on a Vercel subdomain; no custom domain.

## Roles
- **Visitor**: no login; sees public blocks and can use the chatbot.
- **Admin**: one person (me); full control of content, layout and visibility.

## Features
### Public side
- Basic profile: avatar, name, university, high school, major, ... Each item is a configurable block.
- Profile links: Facebook, LinkedIn, LeetCode, GitHub, ORCID, ... (any site can be added).
- GitHub stats: public repos, stars, commits, typical working hours (shown coarsely, can be hidden). Synced on a schedule.
- LeetCode stats: solved by Easy/Medium/Hard, frequent topics. Synced on a schedule.
- Special items, e.g. a paper "under review", with a toggle to show or hide the venue.
- Chatbot: summarises information and answers specific questions, using public data only.

### Admin side
- Login page with a warning banner ("admin only"); login attempts are still allowed.
- Create, edit and delete all content.
- Visibility per block or item: public or admin-only.
- Layout editable by drag-and-drop or by editing the config. Layout is stored as JSON per block (type, order, visibility, properties).
- Private notes, admin-only. Never store passwords, financial data or Gmail data.
- Integrations: enable/disable each adapter, see status and last sync time.
- Chatbot monitoring: anonymised logs and statistics.

## Security
### Login
- No sign-up page. Passwords hashed with Argon2id. TOTP two-factor auth.
- One-time TOTP recovery codes, stored hashed.
- Password reset by emailed link: single use, short expiry, token stored hashed; reset also requires a TOTP or recovery code.
- Generic error messages that do not reveal whether an account exists.
- Temporary lockout and rate limiting after failed attempts.
- Session cookie HttpOnly, Secure, SameSite; CSRF protection.
- Email alert on every successful login; login audit log.

### Application
- Review against OWASP Top 10. Validate all input on the backend.
- Security headers (CSP, ...), strict CORS, API rate limits.
- Secrets only in environment variables, never in the repo.
- Dependency vulnerability scanning. Encrypted database backups, never stored publicly.
- Contact block shows no raw home address, phone number or plain-text email (use a form or an obfuscated email).

### Authorisation
- Checked on the backend for every endpoint, not by hiding buttons in the frontend.
- Automated tests: every admin endpoint returns 401 or 403 when not logged in.

## Chatbot (RAG agent)
- Rule #1: the agent indexes and reads public data only. Private data lives in tables the agent cannot reach. Protection is at the data layer, not in the prompt.
- The agent uses its own database role with SELECT only on the public schema or views.
- Tool results and synced content from other sites are data, not instructions.
- Abuse protection: per-IP rate limit, captcha, length limits, daily budget cap, kill switch.
- Common questions are answered from a cache or FAQ; only complex ones call the LLM.
- Logs: anonymised questions (IP hashed with a salt), latency, cost, errors; fixed retention period.
- Eval in CI: a standard question set (accuracy, cites sources) and a prompt-injection set (target: zero leaks).
- Model: a free API (e.g. Gemini) behind an interface so it is easy to swap; Ollama only for local dev. Function calling first; MCP later.

## External sites (adapters)
- One adapter per site, all behind the same interface. Adapters sync on a schedule and store results in the database; pages never call external APIs on each visit.
- Official API (GitHub, ORCID): real stats. Unofficial API (LeetCode): may break, so cache and show old numbers. Link only (Facebook, LinkedIn): no API calls.
- On error, show the last numbers with their update time.

## Architecture
- Monorepo: `be/` (Python, FastAPI, REST, Docker) and `fe/` (React + TypeScript on Next.js), fully separate.
- PostgreSQL (pgvector later). Local dev with Docker Compose.
- Deploy via GitHub and Vercel.
- CI/CD with GitHub Actions: lint, test, security scan, build, deploy (proposed).
- Tests: unit; integration with Postgres in Docker; end-to-end with Playwright; authorisation tests; chatbot eval (proposed).

## Phases
1. **MVP (goes on the CV):** public page, admin CRUD, full secure login, per-block visibility, GitHub integration, tests, CI/CD, live deploy.
2. **Adapter framework:** LeetCode, ORCID and other sites; scheduled sync.
3. **Chatbot:** RAG on public data, guardrails, abuse protection, eval and attack set.
4. **Polish:** drag-and-drop layout, monitoring, special items.

## Schedule (MVP)
| Date | Work |
|---|---|
| 2026-11-06 | Accounts and real quotas checked |
| 2026-11-07 | Tools installed on Windows, repo created, destructive commands blocked |
| 2026-11-08 | Docker Desktop, FastAPI + Postgres skeleton, agent rules and skills |
| 2026-11-09 | Database schema for blocks and visibility, migration, CRUD API, unit tests |
| 2026-11-10 | Admin login (Argon2id, TOTP, CSRF, lockout, 401/403 tests); MCP project brain |
| 2026-11-11 | Next.js public page and admin; UI tests; OWASP review |
| 2026-11-12 | GitHub adapter, CI, deploy to Vercel |
| 2026-11-13 | Buffer: password reset email, login alert email, fixes, README |

If late, move these past 2026-11-13 in this order: GitHub adapter, end-to-end tests, login alert email.
Never postpone login security, authorisation tests or the deploy.

## Quota budget (2026-11-09 to 2026-11-12)
- Antigravity: two 5-hour windows per day, one large task per window; keep the weekly limit for T-05 and T-07.
- OpenCode: Flash-Lite by default; at most two hard questions per day on Gemini 3.8 Flash (daily limit resets at 15:00 Vietnam time).
- Copilot: tab completion all day; the 200 monthly AI credits are the last fallback.
- Ollama: small single tasks only.

## Open questions (to settle on 2026-11-09)
- Free hosting for Postgres (and Redis): storage, pgvector, backups, does it sleep when idle?
- MVP without Redis (rate limits and cache in Postgres)?
- Can Vercel run the Dockerised backend on the free plan? If not, pick another container platform.
- Email service (password reset, login alerts) and captcha service.
- LLM for the chatbot (proposal: Gemini via Google AI Studio, behind an interface).
- Content of each block (proposal: Profile, About, Skills, Experience, Projects, Research, Profiles, GitHub stats, LeetCode stats, Contact).
- Admin UI language (proposal: English).
- Chatbot log retention period.