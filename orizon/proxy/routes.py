"""
Orizon Proxy Routes

Handles OpenAI-compatible API endpoints by proxying to LiteLLM.
"""

import logging
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse, JSONResponse

from .client import forward_request, get_user_virtual_key_from_request

logger = logging.getLogger(__name__)

router = APIRouter(tags=["proxy"])


@router.api_route(
    "/v1/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
)
async def proxy_v1_endpoint(request: Request, path: str):
    """Proxy OpenAI-compatible v1 API endpoints to LiteLLM.

    Handles all /v1/* endpoints (chat/completions, embeddings, etc.)
    Requires authentication via oauth2-proxy headers or session cookie.
    """
    # Get user's virtual key
    virtual_key = await get_user_virtual_key_from_request(request)

    if not virtual_key:
        raise HTTPException(
            status_code=401,
            detail="Authentication required. Please login or provide valid credentials.",
        )

    # Forward request to LiteLLM
    full_path = f"/v1/{path}"
    return await forward_request(request, full_path, virtual_key)


@router.get("/models")
async def list_models(request: Request):
    """List available models.

    Proxies to LiteLLM /models endpoint.
    """
    virtual_key = await get_user_virtual_key_from_request(request)

    if not virtual_key:
        raise HTTPException(
            status_code=401,
            detail="Authentication required",
        )

    return await forward_request(request, "/models", virtual_key)


@router.get("/v1/models")
async def list_models_v1(request: Request):
    """List available models (v1 path).

    Proxies to LiteLLM /v1/models endpoint.
    """
    virtual_key = await get_user_virtual_key_from_request(request)

    if not virtual_key:
        raise HTTPException(
            status_code=401,
            detail="Authentication required",
        )

    return await forward_request(request, "/v1/models", virtual_key)
