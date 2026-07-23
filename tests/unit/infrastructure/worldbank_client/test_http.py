"""test_http.py — Tests for the shared HTTP client."""
import httpx

from src.core.config import settings
from src.infrastructure.worldbank_client.http import worldbank_http_client


def test_http_client_configuration():
    assert isinstance(worldbank_http_client, httpx.AsyncClient)
    assert str(worldbank_http_client.base_url) == settings.worldbank_base_url
    assert worldbank_http_client.timeout.read == settings.worldbank_timeout_seconds
    assert worldbank_http_client.headers.get("Accept") == "application/json"
