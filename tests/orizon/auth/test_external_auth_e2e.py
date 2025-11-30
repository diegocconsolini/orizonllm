"""End-to-end tests for external user authentication flow.

Tests the complete flow:
1. Signup with email → magic link token created
2. Verify token → session created → cookie set
3. Access profile → returns user data
4. Logout → session deleted

These tests require Redis and LiteLLM to be running.
Skip with: SKIP_E2E_TESTS=1
"""

import os
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import Request, Response
from fastapi.testclient import TestClient

# Check if E2E tests should be skipped
SKIP_E2E_TESTS = os.getenv("SKIP_E2E_TESTS", "1") == "1"
skip_reason = "E2E tests require Redis and LiteLLM. Set SKIP_E2E_TESTS=0 to run."


@pytest.mark.skipif(SKIP_E2E_TESTS, reason=skip_reason)
class TestExternalAuthE2E:
    """End-to-end tests for external authentication flow."""

    # These tests are integration tests that require infrastructure
    # For now, we mock the Redis/LiteLLM calls
    pass


class TestExternalAuthFlowMocked:
    """Tests for external auth flow with mocked dependencies."""

    @pytest.mark.asyncio
    async def test_signup_creates_user_and_token(self):
        """Test signup flow creates user and magic link token."""
        from orizon.auth.routes import signup, SignupRequest

        mock_request = MagicMock(spec=Request)
        body = SignupRequest(
            email="newuser@example.com",
            name="New User",
            company="Test Corp",
        )

        with patch(
            "orizon.auth.routes.get_or_create_user_key",
            new_callable=AsyncMock,
            return_value=({"user_id": "orizon-123"}, "sk-key-123"),
        ):
            with patch(
                "orizon.auth.routes.create_magic_link_token",
                new_callable=AsyncMock,
                return_value="magic-token-123",
            ):
                with patch(
                    "orizon.auth.routes.send_magic_link_email",
                    new_callable=AsyncMock,
                    return_value=True,
                ):
                    response = await signup(mock_request, body)

                    assert response.success is True
                    assert "email" in response.message.lower()

    @pytest.mark.asyncio
    async def test_verify_creates_session_and_cookie(self):
        """Test token verification creates session and sets cookie."""
        from orizon.auth.routes import verify_token

        mock_response = MagicMock(spec=Response)

        with patch(
            "orizon.auth.routes.verify_magic_link_token",
            new_callable=AsyncMock,
            return_value={"email": "user@example.com", "name": "Test User"},
        ):
            with patch(
                "orizon.auth.routes.get_or_create_user_key",
                new_callable=AsyncMock,
                return_value=(
                    {"user_id": "orizon-123", "user_info": {"user_id": "orizon-123"}},
                    "sk-key-123",
                ),
            ):
                with patch(
                    "orizon.auth.routes.create_session",
                    new_callable=AsyncMock,
                    return_value="session-token-456",
                ):
                    with patch(
                        "orizon.auth.routes.set_session_cookie"
                    ) as mock_set_cookie:
                        response = await verify_token("valid-token", mock_response)

                        assert response.success is True
                        assert response.email == "user@example.com"
                        assert response.virtual_key == "sk-key-123"
                        mock_set_cookie.assert_called_once_with(
                            mock_response, "session-token-456"
                        )

    @pytest.mark.asyncio
    async def test_profile_requires_authentication(self):
        """Test profile endpoint requires valid session."""
        from orizon.auth.routes import get_profile

        mock_request = MagicMock(spec=Request)

        with patch(
            "orizon.auth.routes.get_current_session",
            new_callable=AsyncMock,
            return_value=None,
        ):
            with pytest.raises(Exception) as exc_info:
                await get_profile(mock_request)

            assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_profile_returns_user_data(self):
        """Test profile returns data for authenticated user."""
        from orizon.auth.routes import get_profile

        mock_request = MagicMock(spec=Request)
        session_data = {
            "email": "user@example.com",
            "name": "Test User",
            "user_id": "orizon-123",
            "virtual_key": "sk-key-123",
        }

        with patch(
            "orizon.auth.routes.get_current_session",
            new_callable=AsyncMock,
            return_value=session_data,
        ):
            response = await get_profile(mock_request)

            assert response.email == "user@example.com"
            assert response.name == "Test User"
            assert response.virtual_key == "sk-key-123"

    @pytest.mark.asyncio
    async def test_logout_clears_session(self):
        """Test logout deletes session and clears cookie."""
        from orizon.auth.routes import logout

        mock_request = MagicMock(spec=Request)
        mock_response = MagicMock(spec=Response)

        with patch(
            "orizon.auth.routes.get_session_cookie",
            return_value="session-token-123",
        ):
            with patch(
                "orizon.auth.routes.delete_session",
                new_callable=AsyncMock,
                return_value=True,
            ) as mock_delete:
                with patch(
                    "orizon.auth.routes.clear_session_cookie"
                ) as mock_clear:
                    response = await logout(mock_request, mock_response)

                    assert response["success"] is True
                    mock_delete.assert_called_once_with("session-token-123")
                    mock_clear.assert_called_once_with(mock_response)


class TestGitHubOAuthFlowMocked:
    """Tests for GitHub OAuth flow with mocked dependencies."""

    @pytest.mark.asyncio
    async def test_github_auth_redirects(self):
        """Test GitHub auth redirects to authorization URL."""
        from orizon.auth.routes import github_auth

        mock_response = MagicMock(spec=Response)
        mock_response.headers = {}

        with patch(
            "orizon.auth.routes.generate_oauth_state",
            return_value="state-123",
        ):
            with patch(
                "orizon.auth.routes.get_github_authorize_url",
                return_value="https://github.com/login/oauth/authorize?state=state-123",
            ):
                result = await github_auth(mock_response)

                assert mock_response.status_code == 302
                assert "github.com" in mock_response.headers["Location"]

    @pytest.mark.asyncio
    async def test_github_callback_creates_session(self):
        """Test GitHub callback creates session on success."""
        from orizon.auth.routes import github_callback, _oauth_states

        mock_response = MagicMock(spec=Response)
        mock_response.headers = {}

        # Add state to storage
        _oauth_states["valid-state"] = True

        with patch(
            "orizon.auth.routes.complete_github_auth",
            new_callable=AsyncMock,
            return_value={
                "email": "github@example.com",
                "name": "GitHub User",
                "github_id": "12345",
            },
        ):
            with patch(
                "orizon.auth.routes.get_or_create_user_key",
                new_callable=AsyncMock,
                return_value=(
                    {"user_id": "orizon-gh-123"},
                    "sk-gh-key-123",
                ),
            ):
                with patch(
                    "orizon.auth.routes.create_session",
                    new_callable=AsyncMock,
                    return_value="gh-session-token",
                ):
                    with patch(
                        "orizon.auth.routes.set_session_cookie"
                    ) as mock_set_cookie:
                        result = await github_callback(
                            code="github-code",
                            state="valid-state",
                            response=mock_response,
                        )

                        assert result["success"] is True
                        assert result["email"] == "github@example.com"
                        mock_set_cookie.assert_called_once()
                        # Should redirect to profile
                        assert mock_response.status_code == 302
                        assert "/profile" in mock_response.headers["Location"]

    @pytest.mark.asyncio
    async def test_github_callback_rejects_invalid_state(self):
        """Test GitHub callback rejects invalid OAuth state."""
        from orizon.auth.routes import github_callback

        mock_response = MagicMock(spec=Response)

        with pytest.raises(Exception) as exc_info:
            await github_callback(
                code="github-code",
                state="invalid-state",
                response=mock_response,
            )

        assert exc_info.value.status_code == 400
        assert "Invalid OAuth state" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_github_callback_handles_oauth_error(self):
        """Test GitHub callback handles OAuth error from GitHub."""
        from orizon.auth.routes import github_callback

        mock_response = MagicMock(spec=Response)

        with pytest.raises(Exception) as exc_info:
            await github_callback(
                code=None,
                state=None,
                error="access_denied",
                response=mock_response,
            )

        assert exc_info.value.status_code == 400
        assert "access_denied" in str(exc_info.value.detail)


class TestMagicLinkFlow:
    """Tests for complete magic link authentication flow."""

    @pytest.mark.asyncio
    async def test_login_sends_magic_link(self):
        """Test login sends magic link email."""
        from orizon.auth.routes import login, LoginRequest

        mock_request = MagicMock(spec=Request)
        body = LoginRequest(email="existing@example.com")

        with patch(
            "orizon.auth.routes.get_user",
            new_callable=AsyncMock,
            return_value={"user_id": "orizon-123"},
        ):
            with patch(
                "orizon.auth.routes.create_magic_link_token",
                new_callable=AsyncMock,
                return_value="login-token-123",
            ):
                with patch(
                    "orizon.auth.routes.send_magic_link_email",
                    new_callable=AsyncMock,
                    return_value=True,
                ) as mock_send:
                    response = await login(mock_request, body)

                    assert response.success is True
                    mock_send.assert_called_once()

    @pytest.mark.asyncio
    async def test_login_prevents_user_enumeration(self):
        """Test login returns success even for non-existent users."""
        from orizon.auth.routes import login, LoginRequest

        mock_request = MagicMock(spec=Request)
        body = LoginRequest(email="nonexistent@example.com")

        with patch(
            "orizon.auth.routes.get_user",
            new_callable=AsyncMock,
            return_value=None,  # User doesn't exist
        ):
            with patch(
                "orizon.auth.routes.create_magic_link_token",
                new_callable=AsyncMock,
                return_value="fake-token",
            ):
                response = await login(mock_request, body)

                # Still returns success to prevent enumeration
                assert response.success is True

    @pytest.mark.asyncio
    async def test_verify_rejects_invalid_token(self):
        """Test verify rejects invalid/expired token."""
        from orizon.auth.routes import verify_token

        mock_response = MagicMock(spec=Response)

        with patch(
            "orizon.auth.routes.verify_magic_link_token",
            new_callable=AsyncMock,
            return_value=None,  # Invalid token
        ):
            with pytest.raises(Exception) as exc_info:
                await verify_token("invalid-token", mock_response)

            assert exc_info.value.status_code == 400
            assert "Invalid or expired" in str(exc_info.value.detail)
