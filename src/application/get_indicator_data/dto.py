"""dto.py — Request/response DTOs for the Get Indicator Data pipeline."""
from dataclasses import dataclass


@dataclass(frozen=True)
class GetIndicatorDataRequest:
    indicator_code: str
    country_code: str
    start_year: int
    end_year: int
    dimensions: dict[str, str] | None = None
