from abc import ABC, abstractmethod
from typing import Any


class BaseStatsAdapter(ABC):
    provider: str

    @abstractmethod
    def fetch(self, account: str) -> dict[str, Any]:
        """Fetch normalized statistics for an account."""
