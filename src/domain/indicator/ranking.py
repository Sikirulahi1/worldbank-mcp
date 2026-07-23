"""ranking.py — Ranks raw indicator candidates by relevance score."""
from src.domain.indicator.entities import IndicatorCandidate


def rank_candidates(candidates: list[IndicatorCandidate]) -> list[IndicatorCandidate]:
    return sorted(candidates, key=lambda c: (-c.search_score, c.idno))
