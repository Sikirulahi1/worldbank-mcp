"""metadata_client.py — World Bank API implementation of IMetadataPort."""
import httpx

from src.application.ports.metadata_port import IMetadataPort
from src.core.constants import WORLDBANK_METADATA_PATH
from src.core.exceptions import (
    MetadataParseError,
    WorldBankConnectionError,
    WorldBankHTTPStatusError,
    WorldBankTimeoutError,
)
from src.infrastructure.resilience.retry_policy import worldbank_retry_policy
from src.infrastructure.worldbank_client.http import worldbank_http_client


class MetadataClient(IMetadataPort):
    def __init__(self, client: httpx.AsyncClient | None = None) -> None:
        self._client = client or worldbank_http_client
        
    @worldbank_retry_policy
    async def get_coverage(self, indicator_code: str) -> tuple[int, int]:
        try:
            response = await self._client.get(
                WORLDBANK_METADATA_PATH,
                params={"$filter": f"series_description/idno eq '{indicator_code}'"}
            )
        except httpx.TimeoutException as e:
            raise WorldBankTimeoutError(f"Metadata request timed out for {indicator_code}") from e
        except httpx.RequestError as e:
            raise WorldBankConnectionError(f"Connection failed while fetching metadata for {indicator_code}") from e
            
        if response.status_code != 200:
            raise WorldBankHTTPStatusError(f"Metadata API returned status {response.status_code}: {response.text}")
            
        payload = response.json()
        
        if not isinstance(payload, dict):
            raise MetadataParseError("Metadata response payload must be a JSON object.")
            
        values = payload.get("value")
        if not isinstance(values, list) or not values:
            raise MetadataParseError("Metadata response is missing a valid 'value' array or is empty.")
            
        item = values[0]
        series_desc = item.get("series_description", {})
        time_periods = series_desc.get("time_periods", [])
        if not time_periods:
            raise MetadataParseError(f"Indicator {indicator_code} metadata is missing time_periods.")
            
        start = time_periods[0].get("start")
        end = time_periods[0].get("end")
        
        if start is None or end is None:
            raise MetadataParseError(f"Indicator {indicator_code} metadata is missing time_periods.start or end.")
            
        try:
            start_year = int(start)
            end_year = int(end)
        except (ValueError, TypeError) as e:
            raise MetadataParseError(f"Malformed year in time_periods: {e}")
            
        return start_year, end_year
