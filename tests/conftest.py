"""Shared pytest fixtures and env defaults for collection."""
import os

import pytest
from httpx import ASGITransport, AsyncClient

os.environ.setdefault("JWT_SECRET_KEY", "test-jwt-secret-for-unit-tests")
os.environ.setdefault("INTERNAL_API_KEY", "test-internal-api-key")
os.environ.setdefault(
    "VECTOR_STORE_URL",
    "postgresql+asyncpg://localhost/ai_vectors_test",
)


@pytest.fixture()
async def async_client(monkeypatch):
    from unittest.mock import AsyncMock

    monkeypatch.setattr("src.main.verify_vector_store_connection", AsyncMock())
    monkeypatch.setattr("src.main.close_vector_store_connection", AsyncMock())

    from src.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client
