"""data_port.py — Abstract interface for indicator data fetching."""
from typing import Protocol

from src.domain.indicator.entities import Observation


class IDataPort(Protocol):
    """Interface for indicator data fetching."""
    
    async def fetch(
        self, 
        indicator_code: str, 
        country_code: str, 
        start_year: int, 
        end_year: int,
        dimensions: dict[str, str] | None = None
    ) -> list[Observation]:
        ...
