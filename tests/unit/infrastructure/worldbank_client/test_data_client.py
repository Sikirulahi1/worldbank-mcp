"""test_data_client.py — Tests for the data client."""
import json
from pathlib import Path
from unittest.mock import AsyncMock, Mock

import httpx
import pytest

from src.core.exceptions import (
    WorldBankConnectionError,
    WorldBankHTTPStatusError,
    WorldBankTimeoutError,
)
from src.infrastructure.worldbank_client.data_client import DataClient


def load_fixture(name: str) -> dict:
    path = Path("tests/fixtures/sample_responses") / name
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def mock_client():
    client = AsyncMock(spec=httpx.AsyncClient)
    return client


@pytest.mark.asyncio
async def test_fetch_clean(mock_client):
    payload = load_fixture("data_nigeria_gdp_1999_2010.json")
    
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = payload
    mock_client.get.return_value = mock_response
    
    client = DataClient(client=mock_client)
    obs = await client.fetch("WB_ESG_NY_GDP_MKTP_KD_ZG", "NGA", 1999, 2010)
    
    assert len(obs) > 0
    assert obs[0].indicator == "WB_ESG_NY_GDP_MKTP_KD_ZG"
    assert obs[0].ref_area == "NGA"


@pytest.mark.asyncio
async def test_fetch_with_dimensions(mock_client):
    payload = load_fixture("data_nigeria_gdp_1999_2010.json")
    
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = payload
    mock_client.get.return_value = mock_response
    
    client = DataClient(client=mock_client)
    obs = await client.fetch("WB_ESG_NY_GDP_MKTP_KD_ZG", "NGA", 1999, 2010, dimensions={"sex": "F"})
    
    assert len(obs) > 0
    mock_client.get.assert_called_once_with(
        "/data360/data",
        params={
            "DATABASE_ID": "WB_ESG",
            "INDICATOR": "WB_ESG_NY_GDP_MKTP_KD_ZG",
            "REF_AREA": "NGA",
            "timePeriodFrom": "1999",
            "timePeriodTo": "2010",
            "skip": 0,
            "sex": "F"
        }
    )


@pytest.mark.asyncio
async def test_fetch_empty(mock_client):
    payload = load_fixture("data_zero_records.json")
    
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = payload
    mock_client.get.return_value = mock_response
    
    client = DataClient(client=mock_client)
    obs = await client.fetch("IND1", "USA", 2000, 2010)
    
    assert len(obs) == 0


@pytest.mark.asyncio
async def test_fetch_timeout(mock_client):
    mock_client.get.side_effect = httpx.TimeoutException("Timeout")
    
    client = DataClient(client=mock_client)
    with pytest.raises(WorldBankTimeoutError, match="Data request timed out for IND1"):
        await client.fetch("IND1", "USA", 2000, 2010)


@pytest.mark.asyncio
async def test_fetch_connection_error(mock_client):
    mock_client.get.side_effect = httpx.ConnectError("Connection failed")
    
    client = DataClient(client=mock_client)
    with pytest.raises(WorldBankConnectionError, match="Connection failed while fetching data for IND1"):
        await client.fetch("IND1", "USA", 2000, 2010)


@pytest.mark.asyncio
async def test_fetch_http_error(mock_client):
    mock_response = Mock()
    mock_response.status_code = 400
    mock_response.text = "Bad Request"
    mock_client.get.return_value = mock_response
    
    client = DataClient(client=mock_client)
    with pytest.raises(WorldBankHTTPStatusError, match="returned status 400: Bad Request"):
        await client.fetch("IND1", "USA", 2000, 2010)
