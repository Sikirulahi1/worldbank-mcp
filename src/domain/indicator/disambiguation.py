"""disambiguation.py — Determines auto-resolve vs ask-user outcomes."""
from src.core.constants import NOT_FOUND_SCORE_FLOOR, STANDOUT_SCORE_RATIO, WEAK_MATCH_SCORE_THRESHOLD
from src.core.result import ClarificationNeeded, NotFound
from src.domain.indicator.entities import IndicatorCandidate


def disambiguate_candidates(
    candidates: list[IndicatorCandidate],
    query: str = ""
) -> IndicatorCandidate | ClarificationNeeded | NotFound:
    # Exact ID match heuristic: if the query perfectly matches an indicator ID, auto-resolve it
    query_upper = query.strip().upper()
    for c in candidates:
        if c.idno.upper() == query_upper:
            return c
            
    valid_candidates = [c for c in candidates if c.search_score >= NOT_FOUND_SCORE_FLOOR]
    
    if not valid_candidates:
        return NotFound(reason="No indicators found with a relevant search score.")
        
    all_same_concept = len({c.name.strip().lower() for c in valid_candidates}) == 1
    
    is_clear_standout = False
    if len(valid_candidates) > 1:
        top_score = valid_candidates[0].search_score
        runner_up = valid_candidates[1].search_score
        if runner_up > 0 and top_score >= runner_up * STANDOUT_SCORE_RATIO:
            is_clear_standout = True

    if len(valid_candidates) == 1 or all_same_concept or is_clear_standout:
        top_candidate = valid_candidates[0]
        
        if top_candidate.search_score >= WEAK_MATCH_SCORE_THRESHOLD:
            return top_candidate
            
        return ClarificationNeeded(
            candidates=[top_candidate],
            context="Found one potential match, but relevance score is low. Please confirm."
        )
            
    return ClarificationNeeded(
        candidates=valid_candidates,
        context="Multiple distinct indicators matched the query. Please clarify."
    )
