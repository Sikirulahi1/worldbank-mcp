"""test_get_indicator_data_pipeline.py — Tests for the get indicator data pipeline."""
import pytest
from unittest.mock import AsyncMock

from src.application.get_indicator_data.dto import GetIndicatorDataRequest
from src.application.get_indicator_data.pipeline import GetIndicatorDataPipeline
from src.application.ports.data_port import IDataPort
from src.core.exceptions import IndicatorValidationError
from src.core.result import DataResult
from src.domain.indicator.entities import Observation


class FakeDataPort(IDataPort):
    def __init__(self, observations: list[Observation]):
        self.observations = observations
        
    async def fetch(self, indicator_code: str, country_code: str, start_year: int, end_year: int, dimensions: dict[str, str] | None = None) -> list[Observation]:
        return self.observations


@pytest.fixture
def fake_observations():
    return [
        Observation(indicator="GDP", ref_area="NGA", time_period="2020", obs_value="21.06"),
        # 2021 missing
        Observation(indicator="GDP", ref_area="NGA", time_period="2022", obs_value="24.12"),
    ]


@pytest.mark.asyncio
async def test_get_indicator_data_clean(fake_observations):
    port = FakeDataPort(observations=fake_observations)
    pipeline = GetIndicatorDataPipeline(data_port=port)
    request = GetIndicatorDataRequest(indicator_code="GDP", country_code="NGA", start_year=2020, end_year=2022)
    
    result = await pipeline.execute(request)
    
    assert isinstance(result, DataResult)
    assert result.series.country == "NGA"
    assert result.series.data["2020"] == "21.06"
    assert result.series.data["2021"] is None
    assert result.series.data["2022"] == "24.12"
    
    assert "Missing data for year 2021." in result.coverage_warnings


@pytest.mark.asyncio
async def test_get_indicator_data_zero_results():
    port = FakeDataPort(observations=[])
    pipeline = GetIndicatorDataPipeline(data_port=port)
    request = GetIndicatorDataRequest(indicator_code="GDP", country_code="NGA", start_year=2020, end_year=2022)
    
    result = await pipeline.execute(request)
    
    assert isinstance(result, DataResult)
    assert result.series.data["2020"] is None
    assert result.series.data["2021"] is None
    assert result.series.data["2022"] is None
    
    assert any("No data returned" in w for w in result.coverage_warnings)


@pytest.mark.asyncio
async def test_get_indicator_data_out_of_range(fake_observations):
    port = FakeDataPort(observations=fake_observations)
    pipeline = GetIndicatorDataPipeline(data_port=port)
    # Requesting 2019 to 2023, but actual is 2020 to 2022
    request = GetIndicatorDataRequest(indicator_code="GDP", country_code="NGA", start_year=2019, end_year=2023)
    result = await pipeline.execute(request)
    
    assert isinstance(result, DataResult)
    assert any("Requested start 2019 is before data begins in 2020" in w for w in result.coverage_warnings)
    assert any("Requested end 2023 is after data ends in 2022" in w for w in result.coverage_warnings)


@pytest.mark.asyncio
async def test_get_indicator_data_validation_error():
    port = FakeDataPort(observations=[])
    pipeline = GetIndicatorDataPipeline(data_port=port)
    
    # Invalid country code
    with pytest.raises(IndicatorValidationError):
        request = GetIndicatorDataRequest(indicator_code="GDP", country_code="INVALID", start_year=2020, end_year=2022)
        await pipeline.execute(request)
        
    # Invalid years
    with pytest.raises(IndicatorValidationError):
        request = GetIndicatorDataRequest(indicator_code="GDP", country_code="NGA", start_year=2022, end_year=2020)
        await pipeline.execute(request)
