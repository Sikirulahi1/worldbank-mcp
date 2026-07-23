"""data_client.py — World Bank API implementation of IDataPort."""
import httpx

from src.application.ports.data_port import IDataPort
from src.core.constants import DATABASE_PRIORITY, WORLDBANK_DATA_PATH
from src.core.exceptions import (
    WorldBankConnectionError,
    WorldBankHTTPStatusError,
    WorldBankTimeoutError,
)
from src.domain.indicator.entities import Observation
from src.infrastructure.resilience.retry_policy import worldbank_retry_policy
from src.infrastructure.worldbank_client.http import worldbank_http_client
from src.infrastructure.worldbank_client.response_parser import parse_observations


def _extract_database_id(indicator_code: str) -> str:
    for db_id in DATABASE_PRIORITY:
        if indicator_code.startswith(db_id + "_"):
            return db_id
    parts = indicator_code.split("_")
    if len(parts) >= 2 and parts[0] == "WB":
        return f"{parts[0]}_{parts[1]}"
    return parts[0] if parts else ""


class DataClient(IDataPort):
    def __init__(self, client: httpx.AsyncClient | None = None) -> None:
        self._client = client or worldbank_http_client
        
    @worldbank_retry_policy
    async def fetch(
        self, 
        indicator_code: str, 
        country_code: str, 
        start_year: int, 
        end_year: int,
        dimensions: dict[str, str] | None = None
    ) -> list[Observation]:
        all_observations = []
        page = 1
        database_id = _extract_database_id(indicator_code)
        
        while True:
            # Note: timeframes can be comma-separated or range depending on API, but let's use comma separated based on what works, or just timePeriodFrom and timePeriodTo
            params = {
                "DATABASE_ID": database_id,
                "INDICATOR": indicator_code,
                "REF_AREA": country_code,
                "timePeriodFrom": str(start_year),
                "timePeriodTo": str(end_year),
                "skip": (page - 1) * 1000
            }
            if dimensions:
                params.update(dimensions)
            
            try:
                response = await self._client.get(WORLDBANK_DATA_PATH, params=params)
            except httpx.TimeoutException as e:
                raise WorldBankTimeoutError(f"Data request timed out for {indicator_code} ({country_code})") from e
            except httpx.RequestError as e:
                raise WorldBankConnectionError(f"Connection failed while fetching data for {indicator_code}") from e
                
            if response.status_code != 200:
                raise WorldBankHTTPStatusError(f"Data API returned status {response.status_code}: {response.text}")
                
            payload = response.json()
            
            page_obs = parse_observations(payload, indicator_code, country_code)
            all_observations.extend(page_obs)
            
            values = payload.get("value", [])
            if not values:
                break
                
            # data360api paginates by 1000 records at a time
            if len(values) < 1000:
                break
                
            page += 1
            
        return all_observations
