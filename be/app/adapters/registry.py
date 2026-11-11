from app.adapters.base import BaseStatsAdapter
from app.adapters.github import GithubAdapter


def get_adapters(github_token: str | None = None) -> dict[str, BaseStatsAdapter]:
    return {"github": GithubAdapter(token=github_token)}
