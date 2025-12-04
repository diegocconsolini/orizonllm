"""
Orizon Rate Limiting

Redis-based rate limiting for authentication endpoints.
Protects against brute force attacks on login/signup.
"""

import logging
import os
from datetime import timedelta
from typing import Optional, Tuple

import redis.asyncio as redis
from fastapi import Request, HTTPException

logger = logging.getLogger(__name__)

# Redis configuration
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")

# Rate limit configuration
# Format: (max_requests, window_seconds)
RATE_LIMITS = {
    "login": (5, 60),       # 5 attempts per minute
    "signup": (3, 300),     # 3 signups per 5 minutes
    "magic_link": (3, 60),  # 3 magic links per minute
    "oauth": (10, 60),      # 10 OAuth attempts per minute
    "default": (30, 60),    # 30 requests per minute default
}

# Redis connection pool
_redis_pool: Optional[redis.Redis] = None


async def get_redis() -> redis.Redis:
    """Get Redis connection with connection pooling."""
    global _redis_pool

    if _redis_pool is None:
        _redis_pool = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            password=REDIS_PASSWORD or None,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
        )
        logger.info(f"Created Redis connection pool: {REDIS_HOST}:{REDIS_PORT}")

    return _redis_pool


async def close_redis():
    """Close Redis connection pool."""
    global _redis_pool

    if _redis_pool is not None:
        await _redis_pool.close()
        _redis_pool = None
        logger.info("Closed Redis connection pool")


def get_client_ip(request: Request) -> str:
    """Extract client IP from request, handling proxies."""
    # Check for forwarded headers (nginx, load balancers)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # Take the first IP (original client)
        return forwarded_for.split(",")[0].strip()

    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip

    # Fall back to direct connection
    if request.client:
        return request.client.host

    return "unknown"


async def check_rate_limit(
    request: Request,
    action: str = "default",
    identifier: Optional[str] = None,
) -> Tuple[bool, int, int]:
    """Check if request is within rate limits.

    Args:
        request: FastAPI request object
        action: Type of action (login, signup, etc.)
        identifier: Optional custom identifier (default: client IP)

    Returns:
        Tuple of (allowed, remaining, reset_seconds)
    """
    # Get rate limit config
    max_requests, window_seconds = RATE_LIMITS.get(action, RATE_LIMITS["default"])

    # Build rate limit key
    client_id = identifier or get_client_ip(request)
    key = f"ratelimit:{action}:{client_id}"

    try:
        redis_client = await get_redis()

        # Use Redis INCR with expiry for sliding window
        current = await redis_client.incr(key)

        if current == 1:
            # First request - set expiry
            await redis_client.expire(key, window_seconds)

        # Get TTL for reset time
        ttl = await redis_client.ttl(key)
        reset_seconds = max(ttl, 0)

        # Check if over limit
        remaining = max(0, max_requests - current)
        allowed = current <= max_requests

        if not allowed:
            logger.warning(
                f"Rate limit exceeded: {action} from {client_id} "
                f"({current}/{max_requests})"
            )

        return allowed, remaining, reset_seconds

    except redis.RedisError as e:
        logger.error(f"Redis error in rate limiter: {e}")
        # Fail open - allow request if Redis is down
        return True, max_requests, 0


async def rate_limit(
    request: Request,
    action: str = "default",
    identifier: Optional[str] = None,
) -> None:
    """Apply rate limiting to a request.

    Raises HTTPException 429 if rate limit exceeded.

    Args:
        request: FastAPI request object
        action: Type of action (login, signup, etc.)
        identifier: Optional custom identifier
    """
    allowed, remaining, reset_seconds = await check_rate_limit(
        request, action, identifier
    )

    # Add rate limit headers to response (via request state)
    request.state.ratelimit_remaining = remaining
    request.state.ratelimit_reset = reset_seconds

    if not allowed:
        # Record rate limit hit in metrics
        try:
            from orizon.metrics import record_rate_limit_hit
            endpoint = request.url.path
            record_rate_limit_hit(endpoint, action)
        except ImportError:
            pass  # Metrics module not available

        raise HTTPException(
            status_code=429,
            detail={
                "error": "Too many requests",
                "message": f"Rate limit exceeded. Try again in {reset_seconds} seconds.",
                "retry_after": reset_seconds,
            },
            headers={
                "Retry-After": str(reset_seconds),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(reset_seconds),
            },
        )


async def rate_limit_by_email(
    request: Request,
    email: str,
    action: str = "default",
) -> None:
    """Apply rate limiting by email address.

    This provides additional protection against attacks targeting
    specific accounts, even from different IPs.

    Args:
        request: FastAPI request object
        email: Email address to rate limit
        action: Type of action
    """
    # Rate limit by both IP and email
    await rate_limit(request, action)  # IP-based
    await rate_limit(request, f"{action}:email", email.lower())  # Email-based
