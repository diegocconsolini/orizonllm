"""
Orizon Application Entry Point

Integrates Orizon authentication, proxy, and portal into LiteLLM's FastAPI application.
"""

import logging
import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

logger = logging.getLogger(__name__)


def setup_orizon(app: FastAPI) -> None:
    """Setup Orizon modules on the LiteLLM FastAPI application.

    This function:
    1. Mounts authentication middleware
    2. Registers auth API routes
    3. Registers proxy routes
    4. Registers portal routes
    5. Mounts static files

    Args:
        app: LiteLLM's FastAPI application instance
    """
    logger.info("🔧 Setting up Orizon...")

    # Import modules
    from orizon.auth.middleware import OrizonAuthMiddleware
    from orizon.auth import routes as auth_routes
    from orizon.proxy import router as proxy_router
    from orizon.portal import routes as portal_routes

    # 1. Mount authentication middleware
    logger.info("  ↳ Mounting auth middleware...")
    app.add_middleware(OrizonAuthMiddleware)

    # 2. Register auth routes (/api/auth/*)
    logger.info("  ↳ Registering auth routes...")
    app.include_router(auth_routes.router)

    # 3. Register proxy routes (/v1/*, /models)
    logger.info("  ↳ Registering proxy routes...")
    app.include_router(proxy_router)

    # 4. Register portal routes (/signup, /login, /profile)
    logger.info("  ↳ Registering portal routes...")
    app.include_router(portal_routes.router)

    # 5. Mount static files (/static)
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
