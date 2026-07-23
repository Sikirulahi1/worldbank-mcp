"""pipeline.py — Search Indicator pipeline."""
from src.application.ports.search_port import ISearchPort
from src.application.search_indicator.dto import SearchIndicatorRequest
from src.core.constants import MAX_CANDIDATES
from src.core.result import NotFound
from src.domain.indicator.deduplication import deduplicate_candidates
from src.domain.indicator.entities import IndicatorCandidate
from src.domain.indicator.ranking import rank_candidates


class SearchIndicatorPipeline:
    """Pipeline for searching and ranking indicators."""
    
    def __init__(self, search_port: ISearchPort):
        self._search_port = search_port

    async def execute(self, request: SearchIndicatorRequest) -> list[IndicatorCandidate] | NotFound:
        """Search for indicators matching a topic."""
        candidates = await self._search_port.search(request.topic)
        
        if not candidates:
            return NotFound(reason=f"No indicators found matching topic: '{request.topic}'")
            
        ranked = rank_candidates(candidates)
        deduplicated = deduplicate_candidates(ranked)
        final_ranked = rank_candidates(deduplicated)
        trimmed = final_ranked[:MAX_CANDIDATES]
        
        if not trimmed:
            return NotFound(reason=f"No valid indicators remained after deduplication for topic: '{request.topic}'")
            
        return trimmed
