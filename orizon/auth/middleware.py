"""
Orizon Authentication Middleware

FastAPI middleware that:
1. Extracts oauth2-proxy headers for internal users
2. Auto-provisions users in LiteLLM
3. Generates/retrieves virtual keys
4. Adds Authorization header for LiteLLM
"""

import logging
from typing import Callable, MutableMapping

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.datastructures import MutableHeaders

from .utils import get_user_email, get_or_create_user_key

logger = logging.getLogger(__name__)


class OrizonAuthMiddleware(BaseHTTPMiddleware):
    """Middleware for Orizon authentication.

    For internal users (oauth2-proxy):
    - Extracts X-Auth-Request-Email header
    - Auto-provisions user in LiteLLM if not exists
    - Generates virtual key for user
    - Adds Authorization header with virtual key

    For external users:
    - Passes through existing Bearer token
    - LiteLLM validates the token
    """

    # Paths that skip authentication
    SKIP_AUTH_PATHS = (
        "/health",
        "/v1/health",
        "/docs",
        "/openapi.json",
        "/redoc",
    )

    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        """Process each request through auth middleware."""

        # Skip auth for health and docs endpoints
        if any(request.url.path.startswith(p) for p in self.SKIP_AUTH_PATHS):
            return await call_next(request)

        # Check for internal user (oauth2-proxy headers)
        user_email = get_user_email(request)

        if user_email:
            # Internal user detected
            logger.info(f"Internal user detected: {user_email}")

            try:
                # Auto-provision user and get virtual key
                user_data, virtual_key = await get_or_create_user_key(user_email)

                if virtual_key:
                    # Inject Authorization header into request
                    # We need to modify the ASGI scope directly
                    headers = MutableHeaders(scope=request.scope)
                    headers["Authorization"] = f"Bearer {virtual_key}"

                    # Store user info in request state for downstream access
                    request.state.orizon_user = user_data
                    request.state.orizon_email = user_email

                    logger.info(f"Injected auth for user: {user_email}")
                else:
                    logger.warning(f"No virtual key for user: {user_email}")

            except Exception as e:
                logger.error(f"Failed to provision user {user_email}: {e}")
                # Continue without modification - LiteLLM will reject if needed

        else:
            # External user or no auth headers
            auth_header = request.headers.get("Authorization")
            if auth_header:
                logger.debug("External user with Bearer token")
            else:
                logger.debug("No authentication headers found")

        # Continue to next middleware/route
        response = await call_next(request)
        return response
