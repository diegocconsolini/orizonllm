"""
Orizon Prometheus Metrics

Custom metrics for Orizon authentication and authorization.
These complement LiteLLM's built-in Prometheus metrics.

Available at /metrics endpoint alongside LiteLLM metrics.
"""

import logging
import os
import time
from functools import wraps
from typing import Callable, Optional

logger = logging.getLogger(__name__)

# Check if Prometheus metrics are enabled
METRICS_ENABLED = os.getenv("ORIZON_METRICS_ENABLED", "true").lower() == "true"

# Lazy-loaded metrics (initialized on first use)
_metrics_initialized = False
_auth_requests_total = None
_auth_latency = None
_active_sessions = None
_rate_limit_hits = None
_oauth_flows = None
_magic_link_requests = None


def _init_metrics():
    """Initialize Prometheus metrics (lazy initialization)."""
    global _metrics_initialized, _auth_requests_total, _auth_latency
    global _active_sessions, _rate_limit_hits, _oauth_flows, _magic_link_requests

    if _metrics_initialized:
        return True

    if not METRICS_ENABLED:
        logger.info("Orizon Prometheus metrics disabled")
        return False

    try:
        from prometheus_client import Counter, Gauge, Histogram

        # Auth request counter
        _auth_requests_total = Counter(
            "orizon_auth_requests_total",
            "Total authentication requests",
            labelnames=["endpoint", "method", "status"],
        )

        # Auth latency histogram
        _auth_latency = Histogram(
            "orizon_auth_latency_seconds",
            "Authentication endpoint latency in seconds",
            labelnames=["endpoint"],
            buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
        )

        # Active sessions gauge
        _active_sessions = Gauge(
            "orizon_active_sessions",
            "Number of active user sessions",
        )

        # Rate limit hits counter
        _rate_limit_hits = Counter(
            "orizon_rate_limit_hits_total",
            "Total rate limit violations",
            labelnames=["endpoint", "action"],
        )

        # OAuth flows counter
        _oauth_flows = Counter(
            "orizon_oauth_flows_total",
            "OAuth authentication flow attempts",
            labelnames=["provider", "status"],
        )

        # Magic link requests counter
        _magic_link_requests = Counter(
            "orizon_magic_link_requests_total",
            "Magic link authentication requests",
            labelnames=["type", "status"],  # type: signup, login
        )

        _metrics_initialized = True
        logger.info("Orizon Prometheus metrics initialized")
        return True

    except ImportError:
        logger.warning(
            "prometheus_client not installed, Orizon metrics disabled. "
            "Install with: pip install prometheus_client"
        )
        return False
    except Exception as e:
        logger.error(f"Failed to initialize Orizon metrics: {e}")
        return False


# --- Metric Recording Functions ---


def record_auth_request(endpoint: str, method: str, status: str):
    """Record an authentication request.

    Args:
        endpoint: The auth endpoint (signup, login, verify, etc.)
        method: HTTP method (GET, POST)
        status: Response status (success, error, rate_limited)
    """
    if _init_metrics() and _auth_requests_total:
        _auth_requests_total.labels(
            endpoint=endpoint,
            method=method,
            status=status,
        ).inc()


def record_auth_latency(endpoint: str, latency_seconds: float):
    """Record authentication endpoint latency.

    Args:
        endpoint: The auth endpoint
        latency_seconds: Request latency in seconds
    """
    if _init_metrics() and _auth_latency:
        _auth_latency.labels(endpoint=endpoint).observe(latency_seconds)


def set_active_sessions(count: int):
    """Set the active sessions gauge.

    Args:
        count: Number of active sessions
    """
    if _init_metrics() and _active_sessions:
        _active_sessions.set(count)


def record_rate_limit_hit(endpoint: str, action: str):
    """Record a rate limit violation.

    Args:
        endpoint: The endpoint that was rate limited
        action: The rate limit action type (login, signup, etc.)
    """
    if _init_metrics() and _rate_limit_hits:
        _rate_limit_hits.labels(endpoint=endpoint, action=action).inc()


def record_oauth_flow(provider: str, status: str):
    """Record an OAuth flow attempt.

    Args:
        provider: OAuth provider (github, google, etc.)
        status: Flow status (started, success, failed)
    """
    if _init_metrics() and _oauth_flows:
        _oauth_flows.labels(provider=provider, status=status).inc()


def record_magic_link(link_type: str, status: str):
    """Record a magic link request.

    Args:
        link_type: Type of magic link (signup, login)
        status: Request status (sent, verified, expired)
    """
    if _init_metrics() and _magic_link_requests:
        _magic_link_requests.labels(type=link_type, status=status).inc()


# --- Decorators ---


def track_auth_endpoint(endpoint: str):
    """Decorator to track auth endpoint metrics.

    Usage:
        @track_auth_endpoint("login")
        async def login(request, body):
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            status = "success"
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                status = "error"
                # Check if it's a rate limit error
                if hasattr(e, "status_code") and e.status_code == 429:
                    status = "rate_limited"
                raise
            finally:
                latency = time.time() - start_time
                record_auth_request(endpoint, "POST", status)
                record_auth_latency(endpoint, latency)

        return wrapper
    return decorator


# --- Context Manager ---


class MetricsTimer:
    """Context manager for timing operations.

    Usage:
        with MetricsTimer("login") as timer:
            # Do work
            pass
        # Metrics recorded automatically
    """

    def __init__(self, endpoint: str):
        self.endpoint = endpoint
        self.start_time: Optional[float] = None
        self.status = "success"

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.status = "error"
        latency = time.time() - (self.start_time or time.time())
        record_auth_latency(self.endpoint, latency)
        return False  # Don't suppress exceptions
