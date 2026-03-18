"""
API Key authentication middleware for Document Intelligence API.
"""
import logging
import os
from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader

logger = logging.getLogger(__name__)

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)


def get_api_key() -> str:
    """Get API key from environment variable."""
    api_key = os.environ.get("API_KEY", "dev-api-key-12345")
    return api_key


async def verify_api_key(api_key: str = Security(API_KEY_HEADER)) -> str:
    """
    Verify the API key from request header.

    Args:
        api_key: API key from X-API-Key header

    Returns:
        Validated API key

    Raises:
        HTTPException: If API key is missing or invalid
    """
    expected_key = get_api_key()

    if api_key is None:
        logger.warning("API key missing from request")
        raise HTTPException(
            status_code=401,
            detail={
                "error": "Unauthorized",
                "detail": "Missing X-API-Key header",
                "code": "MISSING_API_KEY"
            }
        )

    if api_key != expected_key:
        logger.warning("Invalid API key attempted")
        raise HTTPException(
            status_code=401,
            detail={
                "error": "Unauthorized",
                "detail": "Invalid API key",
                "code": "INVALID_API_KEY"
            }
        )

    return api_key
