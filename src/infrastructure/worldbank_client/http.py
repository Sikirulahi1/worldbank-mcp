"""http.py — Shared HTTP client configured for World Bank API."""
import httpx

from src.core.config import settings

worldbank_http_client = httpx.AsyncClient(
    base_url=settings.worldbank_base_url,
    timeout=httpx.Timeout(settings.worldbank_timeout_seconds),
    headers={"Accept": "application/json"}
)
