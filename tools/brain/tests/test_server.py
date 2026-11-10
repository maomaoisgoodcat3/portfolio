from pathlib import Path

from tools.brain.server import find_task, parse_decisions, parse_tasks, truncate_result


def write_docs(tmp_path: Path, tasks: str, decisions: str = "") -> Path:
    (tmp_path / "TASKS.md").write_text(tasks, encoding="utf-8")
    (tmp_path / "DECISIONS.md").write_text(decisions, encoding="utf-8")
    return tmp_path


def test_parse_tasks_reads_sample_table(tmp_path):
    docs = write_docs(
        tmp_path,
        "| ID | Task | Planned | Status | Notes |\n"
        "|---|---|---|---|---|\n"
        "| T-06 | Build brain server | 2026-11-10 | todo | pending |\n",
    )
    assert parse_tasks(docs) == [
        {
            "id": "T-06",
            "description": "Build brain server",
            "date": "2026-11-10",
            "status": "todo",
            "notes": "pending",
        }
    ]


def test_parse_tasks_preserves_pipe_in_description(tmp_path):
    docs = write_docs(
        tmp_path,
        "| T-06 | Read tasks | decisions | 2026-11-10 | doing | active |\n",
    )
    assert parse_tasks(docs)[0]["description"] == "Read tasks | decisions"


def test_list_tasks_filters_by_status(tmp_path):
    docs = write_docs(
        tmp_path,
        "| T-01 | First | 2026-11-01 | done | |\n"
        "| T-02 | Second | 2026-11-02 | todo | |\n",
    )
    assert [task["id"] for task in parse_tasks(docs) if task["status"] == "todo"] == [
        "T-02"
    ]


def test_find_task_rejects_bad_task_id(tmp_path):
    docs = write_docs(tmp_path, "")
    assert find_task(docs, "T-1") == {"error": "Invalid task ID"}


def test_find_task_reports_unknown_task_id(tmp_path):
    docs = write_docs(tmp_path, "| T-01 | First | 2026-11-01 | done | |\n")
    assert find_task(docs, "T-02") == {"error": "Task not found"}


def test_get_decisions_filters_case_insensitively_and_applies_limit(tmp_path):
    docs = write_docs(
        tmp_path,
        "",
        "- 2026-11-01 - Alpha decision\n"
        "- 2026-11-02 - Beta choice\n"
        "- 2026-11-03 - Alpha replacement\n",
    )
    assert parse_decisions(docs, "ALPHA", 1) == [
        "- 2026-11-03 - Alpha replacement"
    ]


def test_results_are_truncated_at_8000_characters():
    result = truncate_result("x" * 8100)
    assert len(result) == 8000
    assert result.endswith("...(truncated)")
