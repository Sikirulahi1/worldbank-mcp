"""search_port.py — Abstract interface for indicator search."""
from typing import Protocol

from src.domain.indicator.entities import IndicatorCandidate


class ISearchPort(Protocol):
    """Interface for indicator search operations."""
    
    async def search(self, topic: str) -> list[IndicatorCandidate]:
        ...
