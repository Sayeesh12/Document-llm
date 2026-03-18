"""
Auth module for API key authentication middleware for FastAPI.
Validates X-API-Key header on all protected endpoints.
"""

import os
import logging
from typing import Optional
from starlette.requests import Request
from fastapi import HTTPException, status
from fastapi.responses import JSONResponse


logger = logging.getLogger(__name__)


class APIKeyMiddleware:
    """Middleware to validate API key from X-API-Key header."""

    def __init__(self, app, api_key: Optional[str] = None):
        """
        Initialize middleware with API key.

        Args:
            app: The ASGI application
            api_key: Expected API key. If None, loads from API_KEY environment variable.
        """
        self.app = app
        self.api_key = api_key or os.getenv("API_KEY", "dev-api-key-12345")
        logger.info("API Key middleware initialized")
    
    async def __call__(self, scope, receive, send):
        """
        ASGI middleware entry point.

        Args:
            scope: ASGI scope dict
            receive: ASGI receive callable
            send: ASGI send callable
        """
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Create request object from scope
        request = Request(scope, receive, send)

        # Allow CORS preflight requests (OPTIONS) without auth
        if request.method == "OPTIONS":
            await self.app(scope, receive, send)
            return

        # Allow health check endpoint without auth
        if request.url.path == "/health":
            await self.app(scope, receive, send)
            return

        # Check for API key in header
        api_key = request.headers.get("X-API-Key")

        if not api_key:
            logger.warning(f"Request without API key from {request.client.host if request.client else 'unknown'}")
            response = JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "X-API-Key header required"},
                headers={"WWW-Authenticate": "ApiKey"},
            )
            await response(scope, receive, send)
            return

        if api_key != self.api_key:
            logger.warning(f"Invalid API key from {request.client.host if request.client else 'unknown'}")
            response = JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Invalid API key"},
                headers={"WWW-Authenticate": "ApiKey"},
            )
            await response(scope, receive, send)
            return

        # Key is valid, proceed
        await self.app(scope, receive, send)


def verify_api_key(request: Request) -> str:
    """
    Dependency to verify API key for a specific endpoint.
    Use as: @app.get("/items") def get_items(api_key: str = Depends(verify_api_key))
    
    Args:
        request: FastAPI request object
        
    Returns:
        Valid API key
        
    Raises:
        HTTPException: If key is missing or invalid
    """
    api_key = request.headers.get("X-API-Key")
    expected_key = os.getenv("API_KEY", "dev-api-key-12345")
    
    if not api_key or api_key != expected_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing X-API-Key header",
        )
    
    return api_key
