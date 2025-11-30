"""
Orizon Auth API Routes

Handles external user authentication:
- POST /api/auth/signup - Create new account
- POST /api/auth/login - Send magic link
- GET /api/auth/verify - Verify magic link token
- GET /api/auth/github - GitHub OAuth redirect
- GET /api/auth/github/callback - GitHub OAuth callback
"""

import logging
import secrets
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel, EmailStr

from .utils import generate_user_id, get_or_create_user_key, get_user
from .tokens import create_magic_link_token, verify_magic_link_token
from .email import send_magic_link_email
from .sessions import create_session, set_session_cookie, delete_session, clear_session_cookie, get_session_cookie, get_current_session
from .oauth import generate_oauth_state, get_github_authorize_url, complete_github_auth

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["auth"])


# Request/Response models
class SignupRequest(BaseModel):
    """Signup request body."""

    email: EmailStr
    name: str
    company: Optional[str] = None


class LoginRequest(BaseModel):
    """Login request body."""

    email: EmailStr


class AuthResponse(BaseModel):
    """Auth response."""

    success: bool
    message: str
    user_id: Optional[str] = None


class TokenVerifyRequest(BaseModel):
    """Token verification request."""

    token: str


class TokenVerifyResponse(BaseModel):
    """Token verification response."""

    success: bool
    email: Optional[str] = None
    virtual_key: Optional[str] = None
    message: str


class ProfileResponse(BaseModel):
    """User profile response."""

    email: str
    name: Optional[str] = None
    user_id: Optional[str] = None
    virtual_key: Optional[str] = None


@router.get("/me", response_model=ProfileResponse)
async def get_profile(request: Request):
    """Get current user profile.

    Requires valid session cookie.
    """
    session = await get_current_session(request)

    if not session:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated",
        )

    return ProfileResponse(
        email=session.get("email", ""),
        name=session.get("name"),
        user_id=session.get("user_id"),
        virtual_key=session.get("virtual_key"),
    )


@router.post("/signup", response_model=AuthResponse)
async def signup(request: Request, body: SignupRequest):
    """Handle new user signup.

    Creates user in LiteLLM and sends magic link email.
    """
    logger.info(f"Signup request for: {body.email}")

    try:
        # Check if user already exists
        user_id = generate_user_id(body.email)

        # Create or get user in LiteLLM
        user_data, _ = await get_or_create_user_key(body.email)

        if not user_data:
            raise HTTPException(
                status_code=500,
                detail="Failed to create user account",
            )

        # Generate magic link token
        token = await create_magic_link_token(
            email=body.email,
            name=body.name,
            company=body.company,
            is_signup=True,
        )

        # Send magic link email
        email_sent = await send_magic_link_email(
            to_email=body.email,
            token=token,
            name=body.name,
            is_signup=True,
        )

        if not email_sent:
            logger.warning(f"Failed to send magic link email to {body.email}")
            # Continue anyway - token is valid, user might retry

        return AuthResponse(
            success=True,
            message="Check your email for the magic link",
            user_id=user_id,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Signup error for {body.email}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Signup failed. Please try again.",
        )


@router.post("/login", response_model=AuthResponse)
async def login(request: Request, body: LoginRequest):
    """Handle user login.

    Sends magic link email to existing user.
    """
    logger.info(f"Login request for: {body.email}")

    try:
        # Check if user exists
        user_id = generate_user_id(body.email)

        # Get user data (don't create new key yet)
        user_data = await get_user(user_id)

        if not user_data:
            # Don't reveal if user exists or not
            logger.warning(f"Login attempt for non-existent user: {body.email}")

        # Generate magic link token regardless
        # (prevents user enumeration attacks)
        token = await create_magic_link_token(
            email=body.email,
            is_signup=False,
        )

        # Send magic link email (even if user doesn't exist - prevents enumeration)
        if user_data:
            email_sent = await send_magic_link_email(
                to_email=body.email,
                token=token,
                is_signup=False,
            )

            if not email_sent:
                logger.warning(f"Failed to send magic link email to {body.email}")

        return AuthResponse(
            success=True,
            message="Check your email for the magic link",
        )

    except Exception as e:
        logger.error(f"Login error for {body.email}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Login failed. Please try again.",
        )


@router.get("/verify")
async def verify_token(token: str, response: Response):
    """Verify magic link token and create session.

    This is called when user clicks the magic link.
    """
    logger.info("Verifying magic link token")

    try:
        # Verify token
        token_data = await verify_magic_link_token(token)

        if not token_data:
            raise HTTPException(
                status_code=400,
                detail="Invalid or expired magic link",
            )

        email = token_data["email"]
        name = token_data.get("name")

        # Create/get user and generate virtual key
        user_data, virtual_key = await get_or_create_user_key(email)

        if not user_data or not virtual_key:
            raise HTTPException(
                status_code=500,
                detail="Failed to create session",
            )

        # Create session
        user_id = user_data.get("user_id") or user_data.get("user_info", {}).get("user_id")
        session_token = await create_session(
            email=email,
            user_id=user_id,
            virtual_key=virtual_key,
            name=name,
        )

        # Set session cookie
        set_session_cookie(response, session_token)

        return TokenVerifyResponse(
            success=True,
            email=email,
            virtual_key=virtual_key,
            message="Successfully authenticated",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token verification error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Verification failed. Please try again.",
        )


@router.post("/logout")
async def logout(request: Request, response: Response):
    """Log out the current user.

    Deletes session and clears cookie.
    """
    session_token = get_session_cookie(request)

    if session_token:
        await delete_session(session_token)

    clear_session_cookie(response)

    return {"success": True, "message": "Logged out successfully"}


# OAuth state storage (in-memory for simplicity, use Redis in production)
_oauth_states: dict[str, bool] = {}


@router.get("/github")
async def github_auth(response: Response):
    """Start GitHub OAuth flow.

    Redirects user to GitHub authorization page.
    """
    # Generate state for CSRF protection
    state = generate_oauth_state()
    _oauth_states[state] = True

    # Get authorization URL
    auth_url = get_github_authorize_url(state)

    # Redirect to GitHub
    response.status_code = 302
    response.headers["Location"] = auth_url
    return {"redirect": auth_url}


@router.get("/github/callback")
async def github_callback(
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None,
    response: Response = None,
):
    """Handle GitHub OAuth callback.

    Exchanges code for token and creates session.
    """
    # Check for OAuth errors
    if error:
        raise HTTPException(
            status_code=400,
            detail=f"GitHub authorization failed: {error}",
        )

    if not code or not state:
        raise HTTPException(
            status_code=400,
            detail="Missing authorization code or state",
        )

    # Verify state (CSRF protection)
    if state not in _oauth_states:
        raise HTTPException(
            status_code=400,
            detail="Invalid OAuth state",
        )
    del _oauth_states[state]

    # Complete GitHub auth flow
    github_user = await complete_github_auth(code)

    if not github_user:
        raise HTTPException(
            status_code=500,
            detail="Failed to authenticate with GitHub",
        )

    email = github_user["email"]
    name = github_user.get("name")

    # Create/get user in LiteLLM
    user_data, virtual_key = await get_or_create_user_key(email)

    if not user_data or not virtual_key:
        raise HTTPException(
            status_code=500,
            detail="Failed to create user account",
        )

    # Create session
    user_id = user_data.get("user_id") or user_data.get("user_info", {}).get("user_id")
    session_token = await create_session(
        email=email,
        user_id=user_id,
        virtual_key=virtual_key,
        name=name,
    )

    # Set session cookie
    set_session_cookie(response, session_token)

    # Redirect to profile/dashboard
    response.status_code = 302
    response.headers["Location"] = "/profile"

    return {
        "success": True,
        "email": email,
        "name": name,
    }
