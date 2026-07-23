"""dto.py — Request/response DTOs for the Export Report pipeline."""
from dataclasses import dataclass


@dataclass(frozen=True)
class ExportReportRequest:
    country_name: str
    indicator_topics: list[str]
    start_year: int
    end_year: int
    format: str
    destination: str
    dimensions: dict[str, str] | None = None
