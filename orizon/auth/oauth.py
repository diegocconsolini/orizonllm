"""
Orizon GitHub OAuth

Handles GitHub OAuth authentication flow:
1. Redirect user to GitHub authorization
2. Handle callback with authorization code
3. Exchange code for access token
4. Fetch user info from GitHub
5. Create/update user and session
"""

import logging
import os
import secrets
from typing import Optional
from urllib.parse import urlencode

import httpx

logger = logging.getLogger(__name__)

# GitHub OAuth configuration
GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID", "")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET", "")
GITHUB_REDIRECT_URI = os.getenv(
    "GITHUB_REDIRECT_URI",
    "http://localhost:4010/api/auth/github/callback"
)

# GitHub API URLs
GITHUB_AUTHORIZE_URL = "https://github.com/login/oauth/authorize"
GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_USER_URL = "https://api.github.com/user"
GITHUB_EMAILS_URL = "https://api.github.com/user/emails"

# OAuth state for CSRF protection
OAUTH_STATE_LENGTH = 32


def generate_oauth_state() -> str:
    """Generate a random state for CSRF protection."""
    return secrets.token_urlsafe(OAUTH_STATE_LENGTH)


def get_github_authorize_url(state: str) -> str:
    """Get the GitHub OAuth authorization URL.

    Args:
        state: Random state for CSRF protection

    Returns:
        Full authorization URL
    """
    params = {
        "client_id": GITHUB_CLIENT_ID,
        "redirect_uri": GITHUB_REDIRECT_URI,
        "scope": "user:email",
        "state": state,
    }
    return f"{GITHUB_AUTHORIZE_URL}?{urlencode(params)}"


async def exchange_code_for_token(code: str) -> Optional[str]:
    """Exchange authorization code for access token.

    Args:
        code: Authorization code from GitHub callback

    Returns:
        Access token or None on failure
    """
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                GITHUB_TOKEN_URL,
                data={
                    "client_id": GITHUB_CLIENT_ID,
                    "client_secret": GITHUB_CLIENT_SECRET,
                    "code": code,
                    "redirect_uri": GITHUB_REDIRECT_URI,
                },
                headers={"Accept": "application/json"},
                timeout=10.0,
            )

            if response.status_code == 200:
                data = response.json()
                access_token = data.get("access_token")
                if access_token:
                    return access_token
                logger.error(f"GitHub OAuth error: {data.get('error')}")
                return None
            else:
                logger.error(f"GitHub token exchange failed: {response.status_code}")
                return None

        except httpx.RequestError as e:
            logger.error(f"GitHub token exchange error: {e}")
            return None


async def get_github_user(access_token: str) -> Optional[dict]:
    """Get GitHub user information.

    Args:
        access_token: GitHub access token

    Returns:
        User info dict or None on failure
    """
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                GITHUB_USER_URL,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/json",
                },
                timeout=10.0,
            )

            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"GitHub user fetch failed: {response.status_code}")
                return None

        except httpx.RequestError as e:
            logger.error(f"GitHub user fetch error: {e}")
            return None


async def get_github_primary_email(access_token: str) -> Optional[str]:
    """Get user's primary email from GitHub.

    Args:
        access_token: GitHub access token

    Returns:
        Primary email address or None
    """
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                GITHUB_EMAILS_URL,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/json",
                },
                timeout=10.0,
            )

            if response.status_code == 200:
                emails = response.json()
                # Find primary verified email
                for email_info in emails:
                    if email_info.get("primary") and email_info.get("verified"):
                        return email_info.get("email")
                # Fallback to first verified email
                for email_info in emails:
                    if email_info.get("verified"):
                        return email_info.get("email")
                return None
            else:
                logger.error(f"GitHub email fetch failed: {response.status_code}")
                return None

        except httpx.RequestError as e:
            logger.error(f"GitHub email fetch error: {e}")
            return None


async def complete_github_auth(code: str) -> Optional[dict]:
    """Complete GitHub OAuth flow.

    Exchanges code for token and fetches user info.

    Args:
        code: Authorization code from callback

    Returns:
        Dict with email, name, and github_id, or None on failure
    """
    # Exchange code for token
    access_token = await exchange_code_for_token(code)
    if not access_token:
        return None

    # Get user info
    user_info = await get_github_user(access_token)
    if not user_info:
        return None

    # Get email (might need separate API call)
    email = user_info.get("email")
    if not email:
        email = await get_github_primary_email(access_token)

    if not email:
        logger.error("Could not get email from GitHub")
        return None

    return {
        "email": email,
        "name": user_info.get("name") or user_info.get("login"),
        "github_id": str(user_info.get("id")),
        "github_login": user_info.get("login"),
        "avatar_url": user_info.get("avatar_url"),
    }
