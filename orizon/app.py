"""
Orizon Application Entry Point

Integrates Orizon authentication, proxy, and portal into LiteLLM's FastAPI application.
"""

import logging
import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

logger = logging.getLogger(__name__)

# CORS configuration from environment
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")
CORS_ALLOW_CREDENTIALS = os.getenv("CORS_ALLOW_CREDENTIALS", "true").lower() == "true"


def setup_orizon(app: FastAPI) -> None:
    """Setup Orizon modules on the LiteLLM FastAPI application.

    This function:
    1. Mounts CORS middleware
    2. Mounts authentication middleware
    3. Registers auth API routes
    4. Registers portal routes
    5. Mounts static files

    Args:
        app: LiteLLM's FastAPI application instance
    """
    logger.info("🔧 Setting up Orizon...")

    # Import modules
    from orizon.auth.middleware import OrizonAuthMiddleware
    from orizon.auth import routes as auth_routes
    from orizon.portal import routes as portal_routes

    # 1. Mount CORS middleware
    # This must be added before other middleware
    logger.info(f"  ↳ Mounting CORS middleware (origins: {CORS_ORIGINS})...")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_ORIGINS,
        allow_credentials=CORS_ALLOW_CREDENTIALS,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
        allow_headers=["*"],
        expose_headers=["X-RateLimit-Remaining", "X-RateLimit-Reset", "Retry-After"],
    )

    # 2. Mount authentication middleware
    # This injects Authorization headers for authenticated users
    logger.info("  ↳ Mounting auth middleware...")
    app.add_middleware(OrizonAuthMiddleware)

    # 3. Register auth routes (/api/auth/*)
    logger.info("  ↳ Registering auth routes...")
    app.include_router(auth_routes.router)

    # NOTE: Proxy routes (/v1/*, /models) are NOT registered in integrated mode.
    # When running inside LiteLLM, LiteLLM's native routes handle /v1/* requests.
    # The auth middleware injects the Authorization header, which LiteLLM validates.
    #
    # For standalone proxy mode (Orizon in front of LiteLLM), use:
    #   from orizon.proxy import router as proxy_router
    #   app.include_router(proxy_router)

    # 3. Register portal routes (/signup, /login, /profile)
    logger.info("  ↳ Registering portal routes...")
    app.include_router(portal_routes.router)

    # 4. Mount static files (/static)
    logger.info("  ↳ Mounting static files...")
    portal_routes.setup_static_files(app)

    logger.info("✅ Orizon setup complete!")


def create_app() -> FastAPI:
    """Create a standalone Orizon FastAPI application.

    This is used when running Orizon independently (not integrated with LiteLLM).
    For LiteLLM integration, use setup_orizon() instead.

    Returns:
        FastAPI application with all Orizon modules configured
    """
    from fastapi import FastAPI

    app = FastAPI(
        title="Orizon AI Gateway",
        description="Custom AI gateway built on LiteLLM",
        version="1.0.0",
    )

    setup_orizon(app)

    return app


# Export for convenience
__all__ = ["setup_orizon", "create_app"]
