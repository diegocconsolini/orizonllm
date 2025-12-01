"""
Orizon - Custom AI Gateway

Built on LiteLLM with dual authentication (internal + external users).
"""

from orizon.app import setup_orizon, create_app

__version__ = "1.0.0"
__all__ = ["setup_orizon", "create_app"]
