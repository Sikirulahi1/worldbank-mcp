"""dto.py — Request/response DTOs for the Search Indicator pipeline."""
from dataclasses import dataclass


@dataclass(frozen=True)
class SearchIndicatorRequest:
    topic: str
