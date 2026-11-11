from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import httpx

from app.adapters.github import GithubAdapter


def test_github_fetch_skips_forks_and_follows_repository_pagination() -> None:
    first_page = [
        {
            "full_name": f"owner/repo-{index}",
            "fork": index == 0,
            "stargazers_count": 1,
        }
        for index in range(100)
    ]
    second_page = [
        {"full_name": "owner/final", "fork": False, "stargazers_count": 7}
    ]

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/users/owner":
            return httpx.Response(200, json={"public_repos": 101})
        if request.url.path == "/users/owner/repos":
            page = request.url.params["page"]
            return httpx.Response(200, json=first_page if page == "1" else second_page)
        if request.url.path.startswith("/repos/"):
            return httpx.Response(200, json={"Python": 1})
        if request.url.path == "/users/owner/events/public":
            return httpx.Response(200, json=[])
        return httpx.Response(404)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    data = GithubAdapter(client=client).fetch("owner")

    assert data["public_repos"] == 101
    assert data["stars"] == 106


def test_github_fetch_returns_top_three_languages() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/users/owner":
            return httpx.Response(200, json={"public_repos": 3})
        if request.url.path == "/users/owner/repos":
            return httpx.Response(
                200,
                json=[
                    {"full_name": "owner/one", "fork": False, "stargazers_count": 0},
                    {"full_name": "owner/two", "fork": False, "stargazers_count": 0},
                    {"full_name": "owner/three", "fork": False, "stargazers_count": 0},
                ],
            )
        if request.url.path == "/repos/owner/one/languages":
            return httpx.Response(200, json={"Python": 10, "Go": 2})
        if request.url.path == "/repos/owner/two/languages":
            return httpx.Response(200, json={"Python": 10, "TypeScript": 2})
        if request.url.path == "/repos/owner/three/languages":
            return httpx.Response(200, json={"Python": 10, "Rust": 2})
        if request.url.path == "/users/owner/events/public":
            return httpx.Response(200, json=[])
        return httpx.Response(404)

    data = GithubAdapter(
        client=httpx.Client(transport=httpx.MockTransport(handler))
    ).fetch("owner")

    assert data["top_languages"] == ["Python", "Go", "TypeScript"]


def test_github_active_parts_use_vietnam_timezone() -> None:
    local_base = datetime.now(ZoneInfo("Asia/Ho_Chi_Minh")) - timedelta(days=1)
    local_events = [
        local_base.replace(hour=1, minute=0, second=0, microsecond=0),
        local_base.replace(hour=7, minute=0, second=0, microsecond=0),
        local_base.replace(hour=13, minute=0, second=0, microsecond=0),
        local_base.replace(hour=19, minute=0, second=0, microsecond=0),
    ]
    events = [
        {
            "type": "PushEvent",
            "created_at": event.astimezone(timezone.utc)
            .isoformat()
            .replace("+00:00", "Z"),
        }
        for event in local_events
    ]

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/users/owner":
            return httpx.Response(200, json={"public_repos": 0})
        if request.url.path == "/users/owner/repos":
            return httpx.Response(200, json=[])
        if request.url.path == "/users/owner/events/public":
            return httpx.Response(200, json=events)
        return httpx.Response(404)

    data = GithubAdapter(
        client=httpx.Client(transport=httpx.MockTransport(handler))
    ).fetch("owner")

    assert data["active_parts"] == {
        "night": 1,
        "morning": 1,
        "afternoon": 1,
        "evening": 1,
    }


def test_github_contributions_are_null_without_token() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/users/owner":
            return httpx.Response(200, json={"public_repos": 0})
        if request.url.path == "/users/owner/repos":
            return httpx.Response(200, json=[])
        if request.url.path == "/users/owner/events/public":
            return httpx.Response(200, json=[])
        return httpx.Response(404)

    data = GithubAdapter(
        client=httpx.Client(transport=httpx.MockTransport(handler))
    ).fetch("owner")

    assert data["contributions_last_year"] is None
