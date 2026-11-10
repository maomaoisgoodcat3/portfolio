import json
import logging
import re
import sys
from pathlib import Path
from typing import Any

from mcp.server.mcpserver import MCPServer

logging.basicConfig(stream=sys.stderr, level=logging.INFO)
logger = logging.getLogger(__name__)

mcp = MCPServer("project-brain")
DOCS_DIR = Path(__file__).resolve().parents[2] / "docs"
TASK_ROW = re.compile(r"^\| T-\d{2} \|")
TASK_ID = re.compile(r"^T-\d{2}$")


def _read_doc(docs_dir: Path, name: str) -> str:
    return (docs_dir / name).read_text(encoding="utf-8")


def _task_from_cells(cells: list[str]) -> dict[str, str]:
    if len(cells) < 5:
        return {}
    if len(cells) > 5:
        cells = [cells[0], "|".join(cells[1:-3]), *cells[-3:]]
    task_id, description, date, status, notes = cells[:5]
    return {
        "id": task_id.strip(),
        "description": description.strip(),
        "date": date.strip(),
        "status": status.strip(),
        "notes": notes.strip(),
    }


def parse_tasks(docs_dir: Path) -> list[dict[str, str]]:
    tasks: list[dict[str, str]] = []
    for line in _read_doc(docs_dir, "TASKS.md").splitlines():
        if not TASK_ROW.match(line):
            continue
        task = _task_from_cells(line.split("|")[1:-1])
        if task:
            tasks.append(task)
    return tasks


def find_task(docs_dir: Path, task_id: str) -> dict[str, str]:
    if not TASK_ID.fullmatch(task_id):
        return {"error": "Invalid task ID"}
    for task in parse_tasks(docs_dir):
        if task["id"] == task_id:
            return task
    return {"error": "Task not found"}


def parse_decisions(
    docs_dir: Path,
    contains: str | None = None,
    limit: int = 20,
) -> list[str]:
    needle = contains.casefold() if contains is not None else None
    bounded_limit = max(1, min(50, limit))
    decisions = [
        line
        for line in _read_doc(docs_dir, "DECISIONS.md").splitlines()
        if line.startswith("- 20")
        and (needle is None or needle in line.casefold())
    ]
    return decisions[-bounded_limit:]


def truncate_result(value: str, max_chars: int = 8000) -> str:
    if len(value) <= max_chars:
        return value
    suffix = "...(truncated)"
    return value[: max_chars - len(suffix)] + suffix


def _serialize(value: Any) -> str:
    return truncate_result(json.dumps(value, ensure_ascii=False, indent=1))


@mcp.tool()
def list_tasks(status: str | None = None) -> str:
    tasks = parse_tasks(DOCS_DIR)
    if status is not None:
        tasks = [task for task in tasks if task["status"] == status]
    result = [
        {"id": task["id"], "title": task["description"][:80], "status": task["status"]}
        for task in tasks
    ]
    return _serialize(result)


@mcp.tool()
def get_task(task_id: str) -> str:
    return _serialize(find_task(DOCS_DIR, task_id))


@mcp.tool()
def get_decisions(contains: str | None = None, limit: int = 20) -> str:
    return _serialize(parse_decisions(DOCS_DIR, contains, limit))


if __name__ == "__main__":
    mcp.run()
