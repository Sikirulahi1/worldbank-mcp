"""test_get_country_indicator_pipeline.py — Tests for the get country indicator pipeline."""
import pytest

from src.application.get_country_indicator.dto import GetCountryIndicatorRequest
from src.application.get_country_indicator.pipeline import GetCountryIndicatorPipeline
from src.application.ports.data_port import IDataPort
from src.application.ports.search_port import ISearchPort
from src.core.result import ClarificationNeeded, DataResult, NotFound
from src.domain.indicator.entities import IndicatorCandidate, Observation


class FakeSearchPort(ISearchPort):
    def __init__(self, candidates: list[IndicatorCandidate]):
        self.candidates = candidates
        
    async def search(self, topic: str) -> list[IndicatorCandidate]:
        return self.candidates


class FakeDataPort(IDataPort):
    def __init__(self, observations: list[Observation]):
        self.observations = observations
        
    async def fetch(self, indicator_code: str, country_code: str, start_year: int, end_year: int, dimensions: dict[str, str] | None = None) -> list[Observation]:
        return self.observations


@pytest.fixture
def fake_search_candidates():
    return [
        IndicatorCandidate(idno="1", name="GDP", database_id="WB_WDI", search_score=50.0),
    ]


@pytest.fixture
def fake_observations():
    return [
        Observation(indicator="GDP", ref_area="NGA", time_period="2020", obs_value="21.06"),
    ]


@pytest.mark.asyncio
async def test_get_country_indicator_clean(fake_search_candidates, fake_observations):
    search_port = FakeSearchPort(candidates=fake_search_candidates)
    data_port = FakeDataPort(observations=fake_observations)
    pipeline = GetCountryIndicatorPipeline(search_port, data_port)
    request = GetCountryIndicatorRequest(country_name="Nigeria", indicator_topic="GDP", start_year=2020, end_year=2021)
    
    result = await pipeline.execute(request)
    
    assert isinstance(result, DataResult)
    assert result.series.country == "NGA"
    assert result.series.indicator == "1" # idno from Candidate


@pytest.mark.asyncio
async def test_get_country_indicator_ambiguous_country(fake_search_candidates, fake_observations):
    search_port = FakeSearchPort(candidates=fake_search_candidates)
    data_port = FakeDataPort(observations=fake_observations)
    pipeline = GetCountryIndicatorPipeline(search_port, data_port)
    request = GetCountryIndicatorRequest(country_name="Korea", indicator_topic="GDP", start_year=2020, end_year=2021)
    
    result = await pipeline.execute(request)
    
    assert isinstance(result, ClarificationNeeded)
    assert "Korea" in result.context
    assert len(result.candidates) > 1


@pytest.mark.asyncio
async def test_get_country_indicator_not_found_country(fake_search_candidates, fake_observations):
    search_port = FakeSearchPort(candidates=fake_search_candidates)
    data_port = FakeDataPort(observations=fake_observations)
    pipeline = GetCountryIndicatorPipeline(search_port, data_port)
    request = GetCountryIndicatorRequest(country_name="Nonsenselandia", indicator_topic="GDP", start_year=2020, end_year=2021)
    
    result = await pipeline.execute(request)
    
    assert isinstance(result, NotFound)
    assert "Nonsenselandia" in result.reason


@pytest.mark.asyncio
async def test_get_country_indicator_ambiguous_indicator(fake_observations):
    candidates = [
        IndicatorCandidate(idno="1", name="GDP Current", database_id="WB_WDI", search_score=50.0),
        IndicatorCandidate(idno="2", name="GDP Constant", database_id="WB_WDI", search_score=48.0),
    ]
    search_port = FakeSearchPort(candidates=candidates)
    data_port = FakeDataPort(observations=fake_observations)
    pipeline = GetCountryIndicatorPipeline(search_port, data_port)
    request = GetCountryIndicatorRequest(country_name="Nigeria", indicator_topic="GDP", start_year=2020, end_year=2021)
    
    result = await pipeline.execute(request)
    
    assert isinstance(result, ClarificationNeeded)
    assert "Multiple distinct indicators" in result.context


@pytest.mark.asyncio
async def test_get_country_indicator_not_found_indicator(fake_observations):
    search_port = FakeSearchPort(candidates=[])
    data_port = FakeDataPort(observations=fake_observations)
    pipeline = GetCountryIndicatorPipeline(search_port, data_port)
    request = GetCountryIndicatorRequest(country_name="Nigeria", indicator_topic="NonsenseTopic", start_year=2020, end_year=2021)
    
    result = await pipeline.execute(request)
    
    assert isinstance(result, NotFound)
    assert "NonsenseTopic" in result.reason
