"""test_metadata_client.py — Tests for the metadata client."""
import json
from pathlib import Path
from unittest.mock import AsyncMock, Mock

import httpx
import pytest

from src.core.exceptions import (
    MetadataParseError,
    WorldBankConnectionError,
    WorldBankHTTPStatusError,
    WorldBankTimeoutError,
)
from src.infrastructure.worldbank_client.metadata_client import MetadataClient


def load_fixture(name: str) -> dict:
    path = Path("tests/fixtures/sample_responses") / name
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def mock_client():
    client = AsyncMock(spec=httpx.AsyncClient)
    return client


@pytest.mark.asyncio
async def test_get_coverage_clean(mock_client):
    payload = load_fixture("metadata_gdp_coverage.json")
    
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = payload
    mock_client.get.return_value = mock_response
    
    client = MetadataClient(client=mock_client)
    start_year, end_year = await client.get_coverage("WB_ESG_NY_GDP_MKTP_KD_ZG")
    
    assert isinstance(start_year, int)
    assert isinstance(end_year, int)
    assert start_year <= end_year


@pytest.mark.asyncio
async def test_get_coverage_malformed(mock_client):
    # Missing time_periods entirely
    payload = {"value": [{}]}
    
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = payload
    mock_client.get.return_value = mock_response
    
    client = MetadataClient(client=mock_client)
    with pytest.raises(MetadataParseError, match="missing time_periods"):
        await client.get_coverage("IND1")


@pytest.mark.asyncio
async def test_get_coverage_timeout(mock_client):
    mock_client.get.side_effect = httpx.TimeoutException("Timeout")
    
    client = MetadataClient(client=mock_client)
    with pytest.raises(WorldBankTimeoutError, match="Metadata request timed out for IND1"):
        await client.get_coverage("IND1")


@pytest.mark.asyncio
async def test_get_coverage_connection_error(mock_client):
    mock_client.get.side_effect = httpx.ConnectError("Connection failed")
    
    client = MetadataClient(client=mock_client)
    with pytest.raises(WorldBankConnectionError, match="Connection failed while fetching metadata for IND1"):
        await client.get_coverage("IND1")


@pytest.mark.asyncio
async def test_get_coverage_http_error(mock_client):
    mock_response = Mock()
    mock_response.status_code = 404
    mock_response.text = "Not Found"
    mock_client.get.return_value = mock_response
    
    client = MetadataClient(client=mock_client)
    with pytest.raises(WorldBankHTTPStatusError, match="returned status 404: Not Found"):
        await client.get_coverage("IND1")
