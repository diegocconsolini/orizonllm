"""Tests for orizon.auth.utils module."""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch

from orizon.auth.utils import (
    get_user_email,
    get_user_name,
    get_auth_headers,
    generate_user_id,
    get_user,
    create_user,
    get_or_create_user,
)


class TestGetUserEmail:
    """Tests for get_user_email function."""

    def test_extracts_x_auth_request_email(self):
        """Should extract email from X-Auth-Request-Email header."""
        request = MagicMock()
        request.headers.get = lambda h: (
            "user@example.com" if h == "X-Auth-Request-Email" else None
        )

        result = get_user_email(request)
        assert result == "user@example.com"

    def test_extracts_x_email_fallback(self):
        """Should fallback to X-Email header."""
        request = MagicMock()
        request.headers.get = lambda h: (
            "user@example.com" if h == "X-Email" else None
        )

        result = get_user_email(request)
        assert result == "user@example.com"

    def test_prefers_x_auth_request_email(self):
        """Should prefer X-Auth-Request-Email over X-Email."""
        request = MagicMock()
        headers = {
            "X-Auth-Request-Email": "primary@example.com",
            "X-Email": "fallback@example.com",
        }
        request.headers.get = lambda h: headers.get(h)

        result = get_user_email(request)
        assert result == "primary@example.com"

    def test_returns_none_when_no_header(self):
        """Should return None when no email header present."""
        request = MagicMock()
        request.headers.get = lambda h: None

        result = get_user_email(request)
        assert result is None


class TestGetUserName:
    """Tests for get_user_name function."""

    def test_extracts_x_auth_request_user(self):
        """Should extract username from X-Auth-Request-User header."""
        request = MagicMock()
        request.headers.get = lambda h: (
            "johndoe" if h == "X-Auth-Request-User" else None
        )

        result = get_user_name(request)
        assert result == "johndoe"

    def test_extracts_x_user_fallback(self):
        """Should fallback to X-User header."""
        request = MagicMock()
        request.headers.get = lambda h: (
            "johndoe" if h == "X-User" else None
        )

        result = get_user_name(request)
        assert result == "johndoe"

    def test_returns_none_when_no_header(self):
        """Should return None when no user header present."""
        request = MagicMock()
        request.headers.get = lambda h: None

        result = get_user_name(request)
        assert result is None


class TestGetAuthHeaders:
    """Tests for get_auth_headers function."""

    def test_extracts_all_headers(self):
        """Should extract all auth-related headers."""
        request = MagicMock()
        headers = {
            "X-Auth-Request-Email": "user@example.com",
            "X-Auth-Request-User": "johndoe",
            "X-Auth-Request-Groups": "admin,users",
            "X-Auth-Request-Access-Token": "token123",
        }
        request.headers.get = lambda h: headers.get(h)

        result = get_auth_headers(request)

        assert result["email"] == "user@example.com"
        assert result["user"] == "johndoe"
        assert result["groups"] == "admin,users"
        assert result["access_token"] == "token123"

    def test_handles_missing_headers(self):
        """Should handle missing headers gracefully."""
        request = MagicMock()
        request.headers.get = lambda h: None

        result = get_auth_headers(request)

        assert result["email"] is None
        assert result["user"] is None
        assert result["groups"] is None
        assert result["access_token"] is None


class TestGenerateUserId:
    """Tests for generate_user_id function."""

    def test_generates_deterministic_id(self):
        """Should generate same ID for same email."""
        email = "user@example.com"
        id1 = generate_user_id(email)
        id2 = generate_user_id(email)
        assert id1 == id2

    def test_different_emails_different_ids(self):
        """Should generate different IDs for different emails."""
        id1 = generate_user_id("user1@example.com")
        id2 = generate_user_id("user2@example.com")
        assert id1 != id2

    def test_case_insensitive(self):
        """Should treat emails case-insensitively."""
        id1 = generate_user_id("User@Example.COM")
        id2 = generate_user_id("user@example.com")
        assert id1 == id2

    def test_has_orizon_prefix(self):
        """Should prefix IDs with orizon-."""
        user_id = generate_user_id("user@example.com")
        assert user_id.startswith("orizon-")


class TestGetUser:
    """Tests for get_user function."""

    @pytest.mark.asyncio
    async def test_returns_user_when_found(self):
        """Should return user data when user exists."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "user_id": "orizon-abc123",
            "user_info": {"user_email": "user@example.com"},
            "keys": [],
        }

        with patch("orizon.auth.utils.httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get.return_value = mock_response
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            mock_client.return_value = mock_instance

            result = await get_user("orizon-abc123")

            assert result is not None
            assert result["user_id"] == "orizon-abc123"

    @pytest.mark.asyncio
    async def test_returns_none_when_not_found(self):
        """Should return None when user doesn't exist."""
        mock_response = MagicMock()
        mock_response.status_code = 404

        with patch("orizon.auth.utils.httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get.return_value = mock_response
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            mock_client.return_value = mock_instance

            result = await get_user("nonexistent")

            assert result is None


class TestCreateUser:
    """Tests for create_user function."""

    @pytest.mark.asyncio
    async def test_creates_user_successfully(self):
        """Should create user and return data."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "user_id": "orizon-abc123",
            "user_email": "user@example.com",
            "key": "sk-test-key",
        }

        with patch("orizon.auth.utils.httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.post.return_value = mock_response
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            mock_client.return_value = mock_instance

            result = await create_user("user@example.com", "orizon-abc123")

            assert result is not None
            assert result["user_id"] == "orizon-abc123"

    @pytest.mark.asyncio
    async def test_returns_none_on_failure(self):
        """Should return None when creation fails."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"

        with patch("orizon.auth.utils.httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.post.return_value = mock_response
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            mock_client.return_value = mock_instance

            result = await create_user("user@example.com", "orizon-abc123")

            assert result is None


class TestGetOrCreateUser:
    """Tests for get_or_create_user function."""

    @pytest.mark.asyncio
    async def test_returns_existing_user(self):
        """Should return existing user without creating."""
        existing_user = {
            "user_id": "orizon-abc123",
            "user_info": {"user_email": "user@example.com"},
            "keys": [{"token": "existing-key"}],
        }

        with patch("orizon.auth.utils.get_user", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = existing_user

            result = await get_or_create_user("user@example.com")

            assert result == existing_user
            mock_get.assert_called_once()

    @pytest.mark.asyncio
    async def test_creates_new_user_when_not_found(self):
        """Should create user when not found."""
        new_user = {
            "user_id": "orizon-abc123",
            "user_info": {"user_email": "new@example.com"},
            "keys": [{"token": "new-key"}],
        }

        with patch("orizon.auth.utils.get_user", new_callable=AsyncMock) as mock_get:
            with patch(
                "orizon.auth.utils.create_user", new_callable=AsyncMock
            ) as mock_create:
                # First call returns None (user not found), second returns created
                mock_get.side_effect = [None, new_user]
                mock_create.return_value = {"user_id": "orizon-abc123"}

                result = await get_or_create_user("new@example.com")

                assert result == new_user
                mock_create.assert_called_once()
