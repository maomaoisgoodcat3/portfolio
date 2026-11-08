---
trigger: glob
globs: be/**
---

# Backend rules (files under be/)

- Python 3.12 with type hints on every function signature.
- FastAPI: one router module per resource under `be/app/api/`; register routers
  in `be/app/main.py`.
- Settings only through the `Settings` class in `be/app/config.py`
  (pydantic-settings). Do not read `os.environ` anywhere else.
- Database access uses SQLAlchemy 2.0 style (`select()`, `Session`). Never build
  SQL strings with f-strings or string concatenation.
- Every schema change needs an Alembic migration. Never edit a migration that
  has already been applied.
- Every new endpoint gets at least two tests in `be/tests/`: the normal case and
  the main error case.
- Errors go out as `HTTPException` with a clear `detail`. Never return stack
  traces, SQL or internal paths to clients.