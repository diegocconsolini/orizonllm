"""
Orizon Security Headers

Provides security middleware for adding security headers to responses:
- Content-Security-Policy (CSP)
- X-Content-Type-Options
- X-Frame-Options
- X-XSS-Protection
- Strict-Transport-Security (HSTS)
- Referrer-Policy
- Permissions-Policy

These headers help protect against common web vulnerabilities.
"""

import logging
import os
from typing import Callable, Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger(__name__)

# Environment configuration
SECURITY_HEADERS_ENABLED = os.getenv("ORIZON_SECURITY_HEADERS", "true").lower() == "true"
HSTS_ENABLED = os.getenv("ORIZON_HSTS_ENABLED", "true").lower() == "true"
HSTS_MAX_AGE = int(os.getenv("ORIZON_HSTS_MAX_AGE", "31536000"))  # 1 year default

# CSP directives configuration
# Can be customized via environment variables
CSP_DIRECTIVES = {
    "default-src": os.getenv("ORIZON_CSP_DEFAULT_SRC", "'self'"),
    "script-src": os.getenv("ORIZON_CSP_SCRIPT_SRC", "'self'"),
    "style-src": os.getenv("ORIZON_CSP_STYLE_SRC", "'self' 'unsafe-inline'"),
    "img-src": os.getenv("ORIZON_CSP_IMG_SRC", "'self' data: https:"),
    "font-src": os.getenv("ORIZON_CSP_FONT_SRC", "'self'"),
    "connect-src": os.getenv("ORIZON_CSP_CONNECT_SRC", "'self'"),
    "frame-ancestors": os.getenv("ORIZON_CSP_FRAME_ANCESTORS", "'none'"),
    "form-action": os.getenv("ORIZON_CSP_FORM_ACTION", "'self'"),
    "base-uri": os.getenv("ORIZON_CSP_BASE_URI", "'self'"),
    "object-src": os.getenv("ORIZON_CSP_OBJECT_SRC", "'none'"),
}

# Paths that should have relaxed CSP (e.g., API endpoints)
CSP_RELAXED_PATHS = [
    "/v1/",  # LiteLLM API endpoints
    "/health",
    "/metrics",
]


def build_csp_header(strict: bool = True) -> str:
    """Build Content-Security-Policy header value.

    Args:
        strict: If True, use strict CSP. If False, use relaxed CSP for APIs.

    Returns:
        CSP header value
    """
    if not strict:
        # Relaxed CSP for API endpoints
        return "default-src 'none'; frame-ancestors 'none'"

    directives = []
    for directive, value in CSP_DIRECTIVES.items():
        if value:
            directives.append(f"{directive} {value}")

    return "; ".join(directives)


def get_security_headers(
    request_path: str,
    is_https: bool = True,
) -> dict:
    """Get security headers for a request.

    Args:
        request_path: The request path
        is_https: Whether the request is over HTTPS

    Returns:
        Dict of security headers
    """
    headers = {}

    if not SECURITY_HEADERS_ENABLED:
        return headers

    # Determine if we should use strict or relaxed CSP
    is_api_path = any(request_path.startswith(path) for path in CSP_RELAXED_PATHS)

    # Content-Security-Policy
    headers["Content-Security-Policy"] = build_csp_header(strict=not is_api_path)

    # X-Content-Type-Options - prevents MIME type sniffing
    headers["X-Content-Type-Options"] = "nosniff"

    # X-Frame-Options - prevents clickjacking
    headers["X-Frame-Options"] = "DENY"

    # X-XSS-Protection - legacy browser XSS protection
    headers["X-XSS-Protection"] = "1; mode=block"

    # Referrer-Policy - controls referrer information
    headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

    # Permissions-Policy - controls browser features
    headers["Permissions-Policy"] = (
        "accelerometer=(), "
        "camera=(), "
        "geolocation=(), "
        "gyroscope=(), "
        "magnetometer=(), "
        "microphone=(), "
        "payment=(), "
        "usb=()"
    )

    # HSTS - only for HTTPS connections
    if HSTS_ENABLED and is_https:
        headers["Strict-Transport-Security"] = (
            f"max-age={HSTS_MAX_AGE}; includeSubDomains; preload"
        )

    return headers


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add security headers to all responses.

    Usage:
        from orizon.security import SecurityHeadersMiddleware
        app.add_middleware(SecurityHeadersMiddleware)
    """

    async def dispatch(
        self,
        request: Request,
        call_next: Callable,
    ) -> Response:
        """Add security headers to the response."""
        response = await call_next(request)

        # Determine if HTTPS (check for forwarded proto header)
        is_https = (
            request.url.scheme == "https"
            or request.headers.get("X-Forwarded-Proto") == "https"
        )

        # Get security headers
        security_headers = get_security_headers(
            request_path=request.url.path,
            is_https=is_https,
        )

        # Add headers to response
        for header, value in security_headers.items():
            response.headers[header] = value

        return response


def setup_security_middleware(app) -> None:
    """Setup security middleware on a FastAPI app.

    Args:
        app: FastAPI application instance
    """
    if SECURITY_HEADERS_ENABLED:
        app.add_middleware(SecurityHeadersMiddleware)
        logger.info("Security headers middleware enabled")
    else:
        logger.info("Security headers middleware disabled (ORIZON_SECURITY_HEADERS=false)")
