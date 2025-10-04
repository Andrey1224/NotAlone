"""API client for bot to communicate with the API service."""

import json
import logging
from typing import Any

import httpx

from core.config import settings
from core.security import sign_bot_request

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

    async def post(
        self,
        endpoint: str,
        json_data: dict[str, Any] | None = None,
        auth_bot: bool = False,
        caller_tg_id: int | None = None,
    ) -> dict[str, Any]:
        """
        Make POST request to API.

        Args:
            endpoint: API endpoint path
            json_data: JSON body to send
            auth_bot: If True, sign request with HMAC and add auth headers
            caller_tg_id: Telegram user ID of caller (required if auth_bot=True)

        Returns:
            JSON response from API
        """
        try:
            headers = {}

            # Add HMAC authentication headers if requested
            if auth_bot:
                if caller_tg_id is None:
                    raise ValueError("caller_tg_id required when auth_bot=True")

                # Serialize body to bytes for signing
                body_bytes = json.dumps(json_data or {}).encode("utf-8")

                # Generate HMAC signature
                signature = sign_bot_request(body_bytes)

                # Add auth headers
                headers["X-Tg-User-Id"] = str(caller_tg_id)
                headers["X-Bot-Signature"] = signature
                headers["Content-Type"] = "application/json"

                # Send with pre-serialized content
                response = await self.client.post(endpoint, content=body_bytes, headers=headers)
            else:
                # Normal request without auth
                response = await self.client.post(endpoint, json=json_data)

            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"API request failed: {endpoint} - {e}")
            raise

    async def get(self, endpoint: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Make GET request to API."""
        try:
            response = await self.client.get(endpoint, params=params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"API request failed: {endpoint} - {e}")
            raise


# Global API client instance
api_client = ApiClient()
