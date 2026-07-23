"""search_client.py — World Bank API implementation of ISearchPort."""
import httpx

from src.application.ports.search_port import ISearchPort
from src.core.constants import MAX_CANDIDATES, WORLDBANK_SEARCH_PATH
from src.core.exceptions import (
    WorldBankConnectionError,
    WorldBankHTTPStatusError,
    WorldBankTimeoutError,
)
from src.domain.indicator.entities import IndicatorCandidate
from src.infrastructure.resilience.retry_policy import worldbank_retry_policy
from src.infrastructure.worldbank_client.http import worldbank_http_client
from src.infrastructure.worldbank_client.response_parser import parse_search_candidates


class SearchClient(ISearchPort):
    def __init__(self, client: httpx.AsyncClient | None = None) -> None:
        self._client = client or worldbank_http_client
        
    @worldbank_retry_policy
    async def search(self, topic: str) -> list[IndicatorCandidate]:
        payload = {
            "count": True,
            "select": "series_description/idno, series_description/name, series_description/database_id",
            "search": topic,
            "top": MAX_CANDIDATES
        }
        
        try:
            response = await self._client.post(WORLDBANK_SEARCH_PATH, json=payload)
        except httpx.TimeoutException as e:
            raise WorldBankTimeoutError(f"Search request timed out for topic '{topic}'") from e
        except httpx.RequestError as e:
            raise WorldBankConnectionError(f"Connection failed while searching for '{topic}'") from e
            
        if response.status_code != 200:
            raise WorldBankHTTPStatusError(f"Search API returned status {response.status_code}: {response.text}")
            
        return parse_search_candidates(response.json())
