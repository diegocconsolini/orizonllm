"""
Orizon Proxy HTTP Client

Handles forwarding requests to LiteLLM backend.
"""

import logging
import os
from typing import Optional, Dict, Any

import httpx
from fastapi import Request
from fastapi.responses import StreamingResponse, JSONResponse

logger = logging.getLogger(__name__)

# LiteLLM configuration
LITELLM_BASE_URL = os.getenv("LITELLM_BASE_URL", "http://localhost:4000")
PROXY_TIMEOUT = int(os.getenv("PROXY_TIMEOUT", "300"))  # 5 minutes for streaming

# Connection pool configuration
MAX_CONNECTIONS = int(os.getenv("PROXY_MAX_CONNECTIONS", "100"))
MAX_KEEPALIVE_CONNECTIONS = int(os.getenv("PROXY_MAX_KEEPALIVE", "20"))

# Module-level HTTP client with connection pooling
_http_client: Optional[httpx.AsyncClient] = None


def get_http_client() -> httpx.AsyncClient:
    """Get or create the shared HTTP client with connection pooling.

    This uses a singleton pattern to ensure we reuse connections.
    Connection pool limits:
    - max_connections: Total concurrent connections
    - max_keepalive_connections: Idle connections kept open

    Returns:
        Configured httpx.AsyncClient instance
    """
    global _http_client

    if _http_client is None:
        # Create client with connection pooling
        limits = httpx.Limits(
            max_connections=MAX_CONNECTIONS,
            max_keepalive_connections=MAX_KEEPALIVE_CONNECTIONS,
        )

        _http_client = httpx.AsyncClient(
            timeout=PROXY_TIMEOUT,
            limits=limits,
            http2=True,  # Enable HTTP/2 for better performance
        )

        logger.info(
            f"Created HTTP client pool: {MAX_CONNECTIONS} max, "
            f"{MAX_KEEPALIVE_CONNECTIONS} keepalive"
        )

    return _http_client


async def close_http_client():
    """Close the shared HTTP client and clean up connections."""
    global _http_client

    if _http_client is not None:
        await _http_client.aclose()
        _http_client = None
        logger.info("Closed HTTP client pool")


async def forward_request(
    request: Request,
    path: str,
    virtual_key: str,
) -> StreamingResponse | JSONResponse:
    """Forward a request to LiteLLM with user's virtual key.

    Args:
        request: Original FastAPI request
        path: Path to forward (e.g., "/v1/chat/completions")
        virtual_key: User's virtual API key

    Returns:
        StreamingResponse or JSONResponse from LiteLLM
    """
    # Build target URL
    target_url = f"{LITELLM_BASE_URL}{path}"

    # Get request body
    body = None
    if request.method in ("POST", "PUT", "PATCH"):
        try:
            body = await request.body()
        except Exception as e:
            logger.error(f"Failed to read request body: {e}")
            return JSONResponse(
                status_code=400,
                content={"error": "Failed to read request body"},
            )

    # Build headers
    headers = dict(request.headers)
    # Remove host header (will be set automatically)
    headers.pop("host", None)
    # Set authorization with virtual key
    headers["authorization"] = f"Bearer {virtual_key}"

    # Log request
    logger.info(f"Proxying {request.method} {path} with key {virtual_key[:10]}...")

    try:
        async with httpx.AsyncClient(timeout=PROXY_TIMEOUT) as client:
            # Forward request
            response = await client.request(
                method=request.method,
                url=target_url,
                params=dict(request.query_params),
                headers=headers,
                content=body,
            )

            # Check if response is streaming (SSE)
            content_type = response.headers.get("content-type", "")
            is_streaming = "text/event-stream" in content_type

            if is_streaming:
                # Stream the response
                return StreamingResponse(
                    content=response.aiter_bytes(),
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    media_type=content_type,
                )
            else:
                # Return JSON response
                return JSONResponse(
                    status_code=response.status_code,
                    content=response.json() if response.content else {},
                    headers=dict(response.headers),
                )

    except httpx.TimeoutException as e:
        logger.error(f"LiteLLM request timeout: {e}")
        return JSONResponse(
            status_code=504,
            content={"error": "Gateway timeout - request to LiteLLM timed out"},
        )
    except httpx.RequestError as e:
        logger.error(f"LiteLLM request error: {e}")
        return JSONResponse(
            status_code=502,
            content={"error": "Bad gateway - failed to connect to LiteLLM"},
        )
    except Exception as e:
        logger.error(f"Proxy error: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "Internal proxy error"},
        )


async def get_user_virtual_key_from_request(request: Request) -> Optional[str]:
    """Get user's virtual key from request context.

    Checks both internal (oauth2-proxy) and external (session) authentication.

    Args:
        request: FastAPI request

    Returns:
        Virtual key if authenticated, None otherwise
    """
    # Check if middleware already set this (internal user)
    if hasattr(request.state, "orizon_user"):
        user = request.state.orizon_user
        # Extract virtual key from user data
        if "keys" in user and user["keys"]:
            return user["keys"][0].get("key")

    # Check session cookie (external user)
    from orizon.auth.sessions import get_current_session

    session = await get_current_session(request)
    if session:
        return session.get("virtual_key")

    return None
