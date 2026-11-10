# Project-brain MCP server

This server exposes read-only MCP tools for the project task and decision docs.
It uses the MCP Python SDK v2 over stdio.
Run it from the repository with `python tools/brain/server.py`.
The server reads only `docs/TASKS.md` and `docs/DECISIONS.md`.
No tool accepts a filesystem path.

Run the tests from `tools/brain` with `pytest -q`.
