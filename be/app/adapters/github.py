from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Any
from zoneinfo import ZoneInfo

import httpx

from app.adapters.base import BaseStatsAdapter

GITHUB_API = "https://api.github.com"
USER_AGENT = "portfolio-stats-sync"
LOCAL_ZONE = ZoneInfo("Asia/Ho_Chi_Minh")


class GithubAdapter(BaseStatsAdapter):
    provider = "github"

    def __init__(
        self,
        token: str | None = None,
        client: httpx.Client | None = None,
    ) -> None:
        self.token = token
        self.client = client or httpx.Client(
            timeout=httpx.Timeout(10.0),
            headers={
                "Accept": "application/vnd.github+json",
                "User-Agent": USER_AGENT,
                **({"Authorization": f"Bearer {token}"} if token else {}),
            },
        )

    def fetch(self, account: str) -> dict[str, Any]:
        user = self._get(f"/users/{account}")
        repositories = self._repositories(account)
        public_repos = int(user.get("public_repos", 0))
        stars = sum(
            int(repository.get("stargazers_count", 0))
            for repository in repositories
            if not repository.get("fork", False)
        )
        languages = self._languages(repositories)
        return {
            "public_repos": public_repos,
            "stars": stars,
            "top_languages": [
                language
                for language, _ in languages.most_common(3)
            ],
            "contributions_last_year": self._contributions(account),
            "active_parts": self._active_parts(account),
        }

    def _get(self, path: str, **params: Any) -> Any:
        try:
            response = self.client.get(f"{GITHUB_API}{path}", params=params)
            response.raise_for_status()
            return response.json()
        except Exception as error:
            raise RuntimeError("GitHub request failed") from error

    def _repositories(self, account: str) -> list[dict[str, Any]]:
        repositories: list[dict[str, Any]] = []
        page = 1
        while True:
            batch = self._get(
                f"/users/{account}/repos",
                per_page=100,
                page=page,
                type="owner",
                sort="updated",
            )
            if not isinstance(batch, list):
                raise RuntimeError("GitHub returned invalid repositories")
            repositories.extend(batch)
            if len(batch) < 100:
                return repositories
            page += 1

    def _languages(self, repositories: list[dict[str, Any]]) -> Counter[str]:
        counts: Counter[str] = Counter()
        for repository in repositories:
            if repository.get("fork", False):
                continue
            language_data = self._get(f"/repos/{repository['full_name']}/languages")
            if isinstance(language_data, dict):
                counts.update(str(language) for language in language_data)
        return counts

    def _contributions(self, account: str) -> int | None:
        if not self.token:
            return None
        try:
            response = self.client.post(
                f"{GITHUB_API}/graphql",
                json={
                    "query": (
                        "query($login:String!) { user(login:$login) { "
                        "contributionsCollection { contributionCalendar "
                        "{ totalContributions } } } }"
                    ),
                    "variables": {"login": account},
                },
                headers={"Authorization": f"Bearer {self.token}"},
            )
            response.raise_for_status()
            payload = response.json()
            return payload["data"]["user"]["contributionsCollection"][
                "contributionCalendar"
            ]["totalContributions"]
        except Exception:
            return None

    def _active_parts(self, account: str) -> dict[str, int]:
        cutoff = datetime.now(timezone.utc) - timedelta(days=90)
        events = self._get(f"/users/{account}/events/public", per_page=100)
        counts = {
            "night": 0,
            "morning": 0,
            "afternoon": 0,
            "evening": 0,
        }
        if not isinstance(events, list):
            return counts
        for event in events:
            if event.get("type") != "PushEvent":
                continue
            created_at = event.get("created_at")
            if not isinstance(created_at, str):
                continue
            try:
                created = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            except ValueError:
                continue
            if created < cutoff:
                continue
            hour = created.astimezone(LOCAL_ZONE).hour
            bucket = (
                "night"
                if hour < 6
                else "morning"
                if hour < 12
                else "afternoon"
                if hour < 18
                else "evening"
            )
            counts[bucket] += 1
        return counts
