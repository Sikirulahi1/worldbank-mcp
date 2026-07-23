"""Pipeline outcome types for the worldbank-mcp application layer."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class DataResult:
    series: object
    coverage_warnings: list[str] = field(default_factory=list)


@dataclass
class ClarificationNeeded:
    candidates: list[object]
    context: str


@dataclass
class NotFound:
    reason: str
