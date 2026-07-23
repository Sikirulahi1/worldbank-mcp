"""deduplication.py — Collapses same-concept duplicates across databases."""
from collections import defaultdict

from src.core.constants import DATABASE_PRIORITY
from src.domain.indicator.entities import IndicatorCandidate


def _get_priority(database_id: str) -> tuple[int, str]:
    try:
        return (DATABASE_PRIORITY.index(database_id), database_id)
    except ValueError:
        return (999, database_id)


def deduplicate_candidates(candidates: list[IndicatorCandidate]) -> list[IndicatorCandidate]:
    if not candidates:
        return []

    groups: dict[str, list[IndicatorCandidate]] = defaultdict(list)
    for c in candidates:
        normalized_name = c.name.strip().lower()
        groups[normalized_name].append(c)

    deduplicated = []
    
    for group in groups.values():
        if len(group) == 1:
            deduplicated.append(group[0])
            continue
            
        group_sorted = sorted(group, key=lambda c: _get_priority(c.database_id))
        deduplicated.append(group_sorted[0])
        
    return deduplicated
