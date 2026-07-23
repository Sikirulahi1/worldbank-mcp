"""entities.py — Indicator domain entities."""
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class IndicatorCandidate:
    idno:         str
    name:         str
    database_id:  str
    search_score: float


@dataclass(frozen=True)
class Observation:
    indicator:   str
    ref_area:    str
    time_period: str
    obs_value:   str | None
    raw_fields:  dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class IndicatorSeries:
    indicator: str
    country:   str
    data:      dict[str, str | None]
    metadata:  dict[str, Any]
