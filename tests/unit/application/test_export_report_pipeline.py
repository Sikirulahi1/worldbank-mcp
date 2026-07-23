"""test_export_report_pipeline.py — Tests for the export report pipeline."""
import os
import pytest
from pathlib import Path
from typing import Any

from src.application.export_report.dto import ExportReportRequest
from src.application.export_report.pipeline import ExportReportPipeline
from src.application.ports.data_port import IDataPort
from src.application.ports.file_port import IFileWriter
from src.application.ports.search_port import ISearchPort
from src.core.exceptions import UnsupportedFormatError
from src.core.result import ClarificationNeeded, DataResult, NotFound
from src.domain.indicator.entities import IndicatorCandidate, Observation


class FakeSearchPort(ISearchPort):
    def __init__(self, candidates_by_topic: dict[str, list[IndicatorCandidate]]):
        self.candidates_by_topic = candidates_by_topic
        
    async def search(self, topic: str) -> list[IndicatorCandidate]:
        return self.candidates_by_topic.get(topic, [])


class FakeDataPort(IDataPort):
    def __init__(self, observations: list[Observation]):
        self.observations = observations
        
    async def fetch(self, indicator_code: str, country_code: str, start_year: int, end_year: int, dimensions: dict[str, str] | None = None) -> list[Observation]:
        return self.observations


class FakeFileWriter(IFileWriter):
    async def write(self, rows: list[dict[str, Any]], destination: str) -> str:
        with open(destination, 'w') as f:
            f.write(f"Wrote {len(rows)} rows")
        return os.path.abspath(destination)


@pytest.fixture
def fake_writers():
    return {"csv": FakeFileWriter()}


@pytest.fixture
def fake_search_port():
    return FakeSearchPort(candidates_by_topic={
        "GDP": [IndicatorCandidate(idno="1", name="GDP", database_id="WB", search_score=50.0)],
        "Pop": [IndicatorCandidate(idno="2", name="Pop", database_id="WB", search_score=50.0)],
        "Ambiguous": [
            IndicatorCandidate(idno="3", name="A1", database_id="WB", search_score=50.0),
            IndicatorCandidate(idno="4", name="A2", database_id="WB", search_score=48.0)
        ],
        "Empty": []
    })


@pytest.fixture
def fake_data_port():
    return FakeDataPort(observations=[
        Observation(indicator="IND", ref_area="NGA", time_period="2020", obs_value="100"),
    ])


@pytest.mark.asyncio
async def test_export_report_clean(tmp_path: Path, fake_search_port, fake_data_port, fake_writers):
    dest = tmp_path / "report.csv"
    pipeline = ExportReportPipeline(fake_search_port, fake_data_port, fake_writers)
    request = ExportReportRequest(
        country_name="Nigeria", 
        indicator_topics=["GDP", "Pop"], 
        start_year=2020, 
        end_year=2021, 
        format="csv", 
        destination=str(dest)
    )
    result = await pipeline.execute(request)
    
    assert isinstance(result, str)
    assert os.path.exists(result)


@pytest.mark.asyncio
async def test_export_report_unsupported_format(fake_search_port, fake_data_port, fake_writers):
    pipeline = ExportReportPipeline(fake_search_port, fake_data_port, fake_writers)
    request = ExportReportRequest(
        country_name="Nigeria", 
        indicator_topics=["GDP"], 
        start_year=2020, 
        end_year=2021, 
        format="pdf", 
        destination="report.pdf"
    )
    with pytest.raises(UnsupportedFormatError):
        await pipeline.execute(request)


@pytest.mark.asyncio
async def test_export_report_partial_failure_ambiguous(fake_search_port, fake_data_port, fake_writers):
    pipeline = ExportReportPipeline(fake_search_port, fake_data_port, fake_writers)
    request = ExportReportRequest(
        country_name="Nigeria", 
        indicator_topics=["GDP", "Ambiguous"], 
        start_year=2020, 
        end_year=2021, 
        format="csv", 
        destination="report.csv"
    )
    result = await pipeline.execute(request)
    
    assert isinstance(result, ClarificationNeeded)
    assert "Partial failure" in result.context
    assert len(result.candidates) == 2


@pytest.mark.asyncio
async def test_export_report_total_failure(fake_search_port, fake_data_port, fake_writers):
    pipeline = ExportReportPipeline(fake_search_port, fake_data_port, fake_writers)
    request = ExportReportRequest(
        country_name="Nigeria", 
        indicator_topics=["Empty"], 
        start_year=2020, 
        end_year=2021, 
        format="csv", 
        destination="report.csv"
    )
    result = await pipeline.execute(request)
    
    assert isinstance(result, NotFound)
    assert "All requested indicators failed" in result.reason
