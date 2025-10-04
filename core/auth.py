"""Authentication and authorization utilities for API."""

import base64
import hashlib
import hmac

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from core.config import settings

# HTTPBasic security for admin endpoints
_security = HTTPBasic()


def _b64u_encode(data: bytes) -> str:
    """Base64-URL encode without padding."""
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def verify_bot_signature(body: bytes, signature: str) -> bool:
    """
    Verify HMAC-SHA256 signature of request body.

    Args:
        body: Raw request body bytes
        signature: Base64-URL encoded HMAC signature

    Returns:
        True if signature is valid
    """
    mac = hmac.new(settings.internal_bot_secret.encode(), body, hashlib.sha256).digest()
    expected = _b64u_encode(mac)
    return hmac.compare_digest(expected, signature or "")


async def admin_basic_auth(credentials: HTTPBasicCredentials = Depends(_security)) -> str:
    """
    Validate HTTP Basic Auth credentials for admin endpoints.

    Args:
        credentials: HTTP Basic credentials from request

    Returns:
        Username if authentication successful

    Raises:
        HTTPException: If credentials are invalid
    """
    if credentials.username != settings.admin_user or credentials.password != settings.admin_pass:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return str(credentials.username)


async def bot_auth(request: Request) -> int:
    """
    Authenticate bot->API requests using HMAC signature.

    Expects headers:
    - X-Tg-User-Id: Telegram user ID making the request
    - X-Bot-Signature: HMAC-SHA256 signature of request body

    Args:
        request: FastAPI request object

    Returns:
        Telegram user ID (caller_tg)

    Raises:
        HTTPException: If authentication fails
    """
    caller_tg_str = request.headers.get("X-Tg-User-Id")
    signature = request.headers.get("X-Bot-Signature")

    if not caller_tg_str or not signature:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing auth headers (X-Tg-User-Id, X-Bot-Signature)"
        )

    # Cache body for FastAPI to re-read during JSON parsing
    if not hasattr(request.state, "_body_cache"):
        request.state._body_cache = await request.body()

    body = request.state._body_cache

    if not verify_bot_signature(body, signature):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid signature")

    try:
        return int(caller_tg_str)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid X-Tg-User-Id format") from None
