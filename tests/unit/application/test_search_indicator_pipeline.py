"""test_search_indicator_pipeline.py — Tests for the search indicator pipeline."""
import pytest
from unittest.mock import AsyncMock

from src.application.search_indicator.dto import SearchIndicatorRequest
from src.application.search_indicator.pipeline import SearchIndicatorPipeline
from src.application.ports.search_port import ISearchPort
from src.core.constants import MAX_CANDIDATES
from src.core.result import NotFound
from src.domain.indicator.entities import IndicatorCandidate


class FakeSearchPort(ISearchPort):
    def __init__(self, candidates: list[IndicatorCandidate]):
        self.candidates = candidates
        
    async def search(self, topic: str) -> list[IndicatorCandidate]:
        return self.candidates


@pytest.fixture
def fake_search_candidates():
    return [
        IndicatorCandidate(idno="1", name="GDP", database_id="WB_WDI", search_score=50.0),
        IndicatorCandidate(idno="2", name="GDP", database_id="WB_ESG", search_score=40.0), # Duplicate concept, worse priority
        IndicatorCandidate(idno="3", name="GDP Growth", database_id="WB_WDI", search_score=30.0),
    ]


@pytest.mark.asyncio
async def test_search_indicator_pipeline_clean(fake_search_candidates):
    port = FakeSearchPort(candidates=fake_search_candidates)
    pipeline = SearchIndicatorPipeline(search_port=port)
    request = SearchIndicatorRequest(topic="GDP")
    
    result = await pipeline.execute(request)
    
    assert isinstance(result, list)
    assert len(result) == 2
    assert result[0].idno == "1" # WDI won over ESG
    assert result[1].idno == "3"


@pytest.mark.asyncio
async def test_search_indicator_pipeline_zero_results():
    port = FakeSearchPort(candidates=[])
    pipeline = SearchIndicatorPipeline(search_port=port)
    request = SearchIndicatorRequest(topic="Nonsense")
    
    result = await pipeline.execute(request)
    
    assert isinstance(result, NotFound)
    assert "No indicators found" in result.reason


@pytest.mark.asyncio
async def test_search_indicator_pipeline_trimming():
    # Create 15 distinct candidates
    candidates = [
        IndicatorCandidate(idno=str(i), name=f"Indicator {i}", database_id="WB_WDI", search_score=float(100 - i))
        for i in range(15)
    ]
    
    port = FakeSearchPort(candidates=candidates)
    pipeline = SearchIndicatorPipeline(search_port=port)
    request = SearchIndicatorRequest(topic="Many")
    
    result = await pipeline.execute(request)
    
    assert isinstance(result, list)
    assert len(result) == MAX_CANDIDATES
    assert result[0].search_score == 100.0
