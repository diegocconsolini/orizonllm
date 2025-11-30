"""Tests for profile endpoint and page."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import Request

from orizon.auth.routes import get_profile, ProfileResponse


class TestGetProfile:
    """Tests for GET /api/auth/me endpoint."""

    @pytest.mark.asyncio
    async def test_returns_profile_for_authenticated_user(self):
        """Should return profile data for authenticated user."""
        mock_request = MagicMock(spec=Request)

        session_data = {
            "email": "user@example.com",
            "name": "Test User",
            "user_id": "orizon-abc123",
            "virtual_key": "sk-test-key-123",
        }

        with patch(
            "orizon.auth.routes.get_current_session",
            new_callable=AsyncMock,
            return_value=session_data,
        ):
            response = await get_profile(mock_request)

            assert response.email == "user@example.com"
            assert response.name == "Test User"
            assert response.user_id == "orizon-abc123"
            assert response.virtual_key == "sk-test-key-123"

    @pytest.mark.asyncio
    async def test_returns_401_for_unauthenticated_user(self):
        """Should return 401 when no session exists."""
        mock_request = MagicMock(spec=Request)

        with patch(
            "orizon.auth.routes.get_current_session",
            new_callable=AsyncMock,
            return_value=None,
        ):
            with pytest.raises(Exception) as exc_info:
                await get_profile(mock_request)

            assert exc_info.value.status_code == 401
            assert "Not authenticated" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_handles_missing_optional_fields(self):
        """Should handle missing optional fields gracefully."""
        mock_request = MagicMock(spec=Request)

        # Session with only required fields
        session_data = {
            "email": "user@example.com",
        }

        with patch(
            "orizon.auth.routes.get_current_session",
            new_callable=AsyncMock,
            return_value=session_data,
        ):
            response = await get_profile(mock_request)

            assert response.email == "user@example.com"
            assert response.name is None
            assert response.user_id is None
            assert response.virtual_key is None


class TestProfileResponse:
    """Tests for ProfileResponse model."""

    def test_creates_valid_response(self):
        """Should create valid response with all fields."""
        response = ProfileResponse(
            email="user@example.com",
            name="Test User",
            user_id="orizon-abc123",
            virtual_key="sk-test-key",
        )

        assert response.email == "user@example.com"
        assert response.name == "Test User"
        assert response.user_id == "orizon-abc123"
        assert response.virtual_key == "sk-test-key"

    def test_allows_optional_fields_to_be_none(self):
        """Should allow optional fields to be None."""
        response = ProfileResponse(
            email="user@example.com",
        )

        assert response.email == "user@example.com"
        assert response.name is None
        assert response.user_id is None
        assert response.virtual_key is None
