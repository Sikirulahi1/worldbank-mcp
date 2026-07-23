"""dto.py — Request/response DTOs for the Get Country Indicator pipeline."""
from dataclasses import dataclass


@dataclass(frozen=True)
class GetCountryIndicatorRequest:
    country_name: str
    indicator_topic: str
    start_year: int
    end_year: int
    dimensions: dict[str, str] | None = None
