# Security

How this portfolio protects its single admin account and its public data. Checked against OWASP Top 10:2025 on 2026-11-11.

| OWASP 2025 | Measures in this repo |
|---|---|
| A01 Broken Access Control | Every /api/admin route depends on require_admin; a test walks app.routes to enforce it. The public API returns only public blocks. New content defaults to visibility admin. The stats sync connects as stats_writer, limited to external_stats. |
| A02 Security Misconfiguration | Security headers on pages (fe/next.config.ts) and on the API (be/app/security_headers.py). FastAPI docs and openapi.json are off unless APP_ENV=development. Dev ports bind to 127.0.0.1. No X-Powered-By header. |
| A03 Software Supply Chain Failures | Lockfile committed; Python pins checked with pip index versions before install. npm audit: <result>. pip-audit: <result>. Scheduled sync uses only official GitHub actions and no third-party action.|
| A04 Cryptographic Failures | Argon2id password hashes; TOTP secrets encrypted with Fernet (key only in the environment); session tokens stored as SHA-256 hashes; HTTPS and HSTS from Vercel. Production uses its own TOTP_ENC_KEY and Neon connections require TLS (sslmode=require).|
| A05 Injection | SQLAlchemy with bound parameters, no raw SQL built from input; Pydantic models reject unknown fields; React escapes output, no dangerouslySetInnerHTML; links only for http and https URLs. |
| A06 Insecure Design | One admin, no sign-up; the admin account is created only by a CLI that checks a TOTP code; the planned chatbot reads public data through a SELECT-only role. |
| A07 Authentication Failures | Mandatory TOTP with replay protection; ten one-time recovery codes stored hashed; generic login errors and a dummy hash check for unknown emails; 429 after 5 failures in 15 minutes per email and per IP; new session token after the TOTP step; idle 30 min, absolute 8 h; cookie __Host-session, HttpOnly, Secure, SameSite=Strict. |
| A08 Software or Data Integrity Failures | CSRF token in X-CSRF-Token on every admin write; only JSON input, validated by Pydantic; main gets one reviewed, squashed commit per task. |
| A09 Security Logging and Alerting Failures | Login attempts are stored in login_events; passwords, codes, tokens and secrets are never logged. Login alert email is planned (T-11). |
| A10 Mishandling of Exceptional Conditions | HTTPException with short messages; validation errors never echo input; no stack traces or SQL reach the client. |

## Known limitations
- Page CSP allows 'unsafe-inline' (no nonces while cacheComponents is on) and images from any https origin until avatar upload exists.
- A burst of parallel first login attempts can exceed the 5-try limit; fix with an atomic upsert after deploy.
- Contact text is hidden behind Reveal but is still in the public API response.
