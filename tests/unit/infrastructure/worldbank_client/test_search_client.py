"""test_search_client.py — Tests for the search client."""
import json
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import httpx
import pytest

from src.core.exceptions import (
    WorldBankConnectionError,
    WorldBankHTTPStatusError,
    WorldBankTimeoutError,
)
from src.infrastructure.worldbank_client.search_client import SearchClient


def load_fixture(name: str) -> dict:
    path = Path("tests/fixtures/sample_responses") / name
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def mock_client():
    client = AsyncMock(spec=httpx.AsyncClient)
    return client


@pytest.mark.asyncio
async def test_search_clean(mock_client):
    payload = load_fixture("search_gdp_clean.json")
    
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = payload
    mock_client.get.return_value = mock_response
    
    client = SearchClient(client=mock_client)
    candidates = await client.search("GDP")
    
    assert len(candidates) > 0
    assert candidates[0].idno == "WB_HNP_SP_POP_TOTL_ZS"
    
    mock_client.get.assert_called_once_with(
        "/api/data360/searchv2", 
        params={"searchType": "exact", "q": "GDP", "format": "json"}
    )


@pytest.mark.asyncio
async def test_search_timeout(mock_client):
    mock_client.get.side_effect = httpx.TimeoutException("Timeout")
    
    client = SearchClient(client=mock_client)
    with pytest.raises(WorldBankTimeoutError, match="timed out for topic 'GDP'"):
        await client.search("GDP")


@pytest.mark.asyncio
async def test_search_connection_error(mock_client):
    mock_client.get.side_effect = httpx.ConnectError("Connection failed")
    
    client = SearchClient(client=mock_client)
    with pytest.raises(WorldBankConnectionError, match="Connection failed while searching for 'GDP'"):
        await client.search("GDP")


@pytest.mark.asyncio
async def test_search_http_error(mock_client):
    mock_response = Mock()
    mock_response.status_code = 500
    mock_response.text = "Internal Server Error"
    mock_client.get.return_value = mock_response
    
    client = SearchClient(client=mock_client)
    with pytest.raises(WorldBankHTTPStatusError, match="returned status 500: Internal Server Error"):
        await client.search("GDP")
