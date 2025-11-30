"""
Orizon Authentication Module

Handles both internal (oauth2-proxy) and external (signup/login) authentication.

Components:
- middleware.py: FastAPI middleware for request authentication
- utils.py: Helper functions (header extraction, user provisioning)
- sessions.py: Session management for portal access
- email.py: Email service for magic link
- oauth.py: GitHub OAuth integration
- routes.py: Auth API endpoints
"""

from .utils import (
    get_user_email,
    get_user_name,
    get_or_create_user,
    get_or_create_user_key,
    generate_user_id,
)

__all__ = [
    "get_user_email",
    "get_user_name",
    "get_or_create_user",
    "get_or_create_user_key",
    "generate_user_id",
]
