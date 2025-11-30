"""Tests for orizon.auth.oauth module."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from orizon.auth.oauth import (
    generate_oauth_state,
    get_github_authorize_url,
    exchange_code_for_token,
    get_github_user,
    get_github_primary_email,
    complete_github_auth,
)


class TestGenerateOAuthState:
    """Tests for generate_oauth_state function."""

    def test_generates_unique_states(self):
        """Should generate unique states."""
        state1 = generate_oauth_state()
        state2 = generate_oauth_state()
        assert state1 != state2

    def test_generates_sufficient_length(self):
        """Should generate sufficiently long state."""
        state = generate_oauth_state()
        assert len(state) >= 32


class TestGetGithubAuthorizeUrl:
    """Tests for get_github_authorize_url function."""

    def test_includes_client_id(self):
        """Should include client_id in URL."""
        with patch("orizon.auth.oauth.GITHUB_CLIENT_ID", "test-client-id"):
            url = get_github_authorize_url("test-state")
            assert "client_id=test-client-id" in url

    def test_includes_state(self):
        """Should include state parameter."""
        url = get_github_authorize_url("my-state-123")
        assert "state=my-state-123" in url

    def test_includes_redirect_uri(self):
        """Should include redirect_uri."""
        with patch("orizon.auth.oauth.GITHUB_REDIRECT_URI", "https://app.com/callback"):
            url = get_github_authorize_url("test-state")
            assert "redirect_uri=" in url

    def test_requests_email_scope(self):
        """Should request user:email scope."""
        url = get_github_authorize_url("test-state")
        assert "scope=user" in url


class TestExchangeCodeForToken:
    """Tests for exchange_code_for_token function."""

    @pytest.mark.asyncio
    async def test_exchanges_code_successfully(self):
        """Should exchange code for token."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"access_token": "gho_test_token"}

        with patch("orizon.auth.oauth.httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.post.return_value = mock_response
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            mock_client.return_value = mock_instance

            result = await exchange_code_for_token("auth-code")

            assert result == "gho_test_token"

    @pytest.mark.asyncio
    async def test_returns_none_on_error(self):
        """Should return None on OAuth error."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"error": "bad_verification_code"}

        with patch("orizon.auth.oauth.httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.post.return_value = mock_response
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            mock_client.return_value = mock_instance

            result = await exchange_code_for_token("invalid-code")

            assert result is None


class TestGetGithubUser:
    """Tests for get_github_user function."""

    @pytest.mark.asyncio
    async def test_gets_user_info(self):
        """Should get user info from GitHub."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": 12345,
            "login": "testuser",
            "name": "Test User",
            "email": "test@github.com",
        }

        with patch("orizon.auth.oauth.httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get.return_value = mock_response
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            mock_client.return_value = mock_instance

            result = await get_github_user("gho_token")

            assert result["login"] == "testuser"
            assert result["name"] == "Test User"

    @pytest.mark.asyncio
    async def test_returns_none_on_failure(self):
        """Should return None on API failure."""
        mock_response = MagicMock()
        mock_response.status_code = 401

        with patch("orizon.auth.oauth.httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get.return_value = mock_response
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            mock_client.return_value = mock_instance

            result = await get_github_user("invalid-token")

            assert result is None


class TestGetGithubPrimaryEmail:
    """Tests for get_github_primary_email function."""

    @pytest.mark.asyncio
    async def test_gets_primary_email(self):
        """Should get primary verified email."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {"email": "secondary@example.com", "primary": False, "verified": True},
            {"email": "primary@example.com", "primary": True, "verified": True},
        ]

        with patch("orizon.auth.oauth.httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get.return_value = mock_response
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            mock_client.return_value = mock_instance

            result = await get_github_primary_email("gho_token")

            assert result == "primary@example.com"

    @pytest.mark.asyncio
    async def test_falls_back_to_verified_email(self):
        """Should fall back to any verified email."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {"email": "unverified@example.com", "primary": True, "verified": False},
            {"email": "verified@example.com", "primary": False, "verified": True},
        ]

        with patch("orizon.auth.oauth.httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get.return_value = mock_response
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            mock_client.return_value = mock_instance

            result = await get_github_primary_email("gho_token")

            assert result == "verified@example.com"


class TestCompleteGithubAuth:
    """Tests for complete_github_auth function."""

    @pytest.mark.asyncio
    async def test_completes_auth_flow(self):
        """Should complete full auth flow."""
        with patch(
            "orizon.auth.oauth.exchange_code_for_token",
            new_callable=AsyncMock,
            return_value="gho_token",
        ):
            with patch(
                "orizon.auth.oauth.get_github_user",
                new_callable=AsyncMock,
                return_value={
                    "id": 12345,
                    "login": "testuser",
                    "name": "Test User",
                    "email": "test@github.com",
                },
            ):
                result = await complete_github_auth("auth-code")

                assert result is not None
                assert result["email"] == "test@github.com"
                assert result["name"] == "Test User"
                assert result["github_id"] == "12345"

    @pytest.mark.asyncio
    async def test_fetches_email_if_not_in_profile(self):
        """Should fetch email separately if not in profile."""
        with patch(
            "orizon.auth.oauth.exchange_code_for_token",
            new_callable=AsyncMock,
            return_value="gho_token",
        ):
            with patch(
                "orizon.auth.oauth.get_github_user",
                new_callable=AsyncMock,
                return_value={
                    "id": 12345,
                    "login": "testuser",
                    "name": "Test User",
                    "email": None,  # Email not in profile
                },
            ):
                with patch(
                    "orizon.auth.oauth.get_github_primary_email",
                    new_callable=AsyncMock,
                    return_value="fetched@example.com",
                ):
                    result = await complete_github_auth("auth-code")

                    assert result["email"] == "fetched@example.com"

    @pytest.mark.asyncio
    async def test_returns_none_on_token_failure(self):
        """Should return None if token exchange fails."""
        with patch(
            "orizon.auth.oauth.exchange_code_for_token",
            new_callable=AsyncMock,
            return_value=None,
        ):
            result = await complete_github_auth("invalid-code")

            assert result is None

    @pytest.mark.asyncio
    async def test_returns_none_if_no_email(self):
        """Should return None if can't get email."""
        with patch(
            "orizon.auth.oauth.exchange_code_for_token",
            new_callable=AsyncMock,
            return_value="gho_token",
        ):
            with patch(
                "orizon.auth.oauth.get_github_user",
                new_callable=AsyncMock,
                return_value={"id": 12345, "login": "testuser", "email": None},
            ):
                with patch(
                    "orizon.auth.oauth.get_github_primary_email",
                    new_callable=AsyncMock,
                    return_value=None,
                ):
                    result = await complete_github_auth("auth-code")

                    assert result is None
