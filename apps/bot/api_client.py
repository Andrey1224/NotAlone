"""API client for bot to communicate with the API service."""

import logging
from typing import Any

import httpx

from core.config import settings

logger = logging.getLogger(__name__)


class ApiClient:
    """HTTP client for API service."""

    def __init__(self) -> None:
        # In Docker, use service name instead of localhost
        self.base_url = f"http://api:{settings.api_port}"
        self.client = httpx.AsyncClient(base_url=self.base_url, timeout=30.0)

    async def close(self) -> None:
        """Close the HTTP client."""
        await self.client.aclose()

    async def post(self, endpoint: str, json: dict[str, Any] | None = None) -> dict[str, Any]:
        """Make POST request to API."""
        try:
            response = await self.client.post(endpoint, json=json)
            response.raise_for_status()
            return response.json()  # type: ignore[no-any-return]
        except httpx.HTTPError as e:
            logger.error(f"API request failed: {endpoint} - {e}")
            raise

    async def get(self, endpoint: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Make GET request to API."""
        try:
            response = await self.client.get(endpoint, params=params)
            response.raise_for_status()
            return response.json()  # type: ignore[no-any-return]
        except httpx.HTTPError as e:
            logger.error(f"API request failed: {endpoint} - {e}")
            raise


# Global API client instance
api_client = ApiClient()
