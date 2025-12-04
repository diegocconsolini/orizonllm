"""
Orizon - Custom AI Gateway

Built on LiteLLM with dual authentication (internal + external users).
"""

from orizon.app import setup_orizon, create_app
from orizon.secrets import get_secret, get_secret_sync, SecretNames
from orizon.metrics import (
    record_auth_request,
    record_auth_latency,
    record_rate_limit_hit,
    record_oauth_flow,
    record_magic_link,
    track_auth_endpoint,
)

__version__ = "1.0.0"
__all__ = [
    "setup_orizon",
    "create_app",
    "get_secret",
    "get_secret_sync",
    "SecretNames",
    "record_auth_request",
    "record_auth_latency",
    "record_rate_limit_hit",
    "record_oauth_flow",
    "record_magic_link",
    "track_auth_endpoint",
]
