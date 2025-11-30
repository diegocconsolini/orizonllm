"""
Orizon API Proxy

Transparently forwards OpenAI-compatible API requests to LiteLLM,
injecting authentication for both internal and external users.
"""

from .routes import router

__all__ = ["router"]
