"""Tests for orizon.proxy.client module."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import Request

from orizon.proxy.client import (
    forward_request,
    get_user_virtual_key_from_request,
)


class TestForwardRequest:
    """Tests for forward_request function."""

    @pytest.mark.asyncio
    async def test_forwards_post_request(self):
        """Should forward POST request to LiteLLM."""
        mock_request = MagicMock(spec=Request)
        mock_request.method = "POST"
        mock_request.headers = {"content-type": "application/json"}
        mock_request.query_params = {}
        mock_request.body = AsyncMock(return_value=b'{"prompt": "test"}')

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "application/json"}
        mock_response.content = b'{"response": "ok"}'
        mock_response.json.return_value = {"response": "ok"}

        with patch("orizon.proxy.client.httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.request.return_value = mock_response
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            mock_client.return_value = mock_instance

            response = await forward_request(
                mock_request, "/v1/chat/completions", "sk-test-key"
            )

            # Verify request was made with correct parameters
            mock_instance.request.assert_called_once()
            call_kwargs = mock_instance.request.call_args[1]
            assert call_kwargs["method"] == "POST"
            assert "/v1/chat/completions" in call_kwargs["url"]
            assert call_kwargs["headers"]["authorization"] == "Bearer sk-test-key"

    @pytest.mark.asyncio
    async def test_handles_streaming_response(self):
        """Should handle streaming (SSE) responses."""
        mock_request = MagicMock(spec=Request)
        mock_request.method = "POST"
        mock_request.headers = {"content-type": "application/json"}
        mock_request.query_params = {}
        mock_request.body = AsyncMock(return_value=b'{"stream": true}')

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "text/event-stream"}
        mock_response.aiter_bytes = AsyncMock(return_value=[b"data: test\n\n"])

        with patch("orizon.proxy.client.httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.request.return_value = mock_response
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            mock_client.return_value = mock_instance

            response = await forward_request(
                mock_request, "/v1/chat/completions", "sk-test-key"
            )

            # Verify it's a streaming response
            from fastapi.responses import StreamingResponse

            assert isinstance(response, StreamingResponse)

    @pytest.mark.asyncio
    async def test_handles_timeout(self):
        """Should handle timeout errors."""
        mock_request = MagicMock(spec=Request)
        mock_request.method = "POST"
        mock_request.headers = {}
        mock_request.query_params = {}
        mock_request.body = AsyncMock(return_value=b"{}")

        with patch("orizon.proxy.client.httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            import httpx

            mock_instance.request.side_effect = httpx.TimeoutException("Timeout")
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            mock_client.return_value = mock_instance

            response = await forward_request(mock_request, "/v1/test", "sk-test-key")

            # Should return 504 Gateway Timeout
            from fastapi.responses import JSONResponse

            assert isinstance(response, JSONResponse)
            assert response.status_code == 504

    @pytest.mark.asyncio
    async def test_handles_connection_error(self):
        """Should handle connection errors."""
        mock_request = MagicMock(spec=Request)
        mock_request.method = "GET"
        mock_request.headers = {}
        mock_request.query_params = {}

        with patch("orizon.proxy.client.httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            import httpx

            mock_instance.request.side_effect = httpx.ConnectError("Connection failed")
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            mock_client.return_value = mock_instance

            response = await forward_request(mock_request, "/v1/test", "sk-test-key")

            # Should return 502 Bad Gateway
            from fastapi.responses import JSONResponse

            assert isinstance(response, JSONResponse)
            assert response.status_code == 502


class TestGetUserVirtualKeyFromRequest:
    """Tests for get_user_virtual_key_from_request function."""

    @pytest.mark.asyncio
    async def test_gets_key_from_internal_user(self):
        """Should get virtual key from internal user (oauth2-proxy)."""
        mock_request = MagicMock(spec=Request)
        mock_request.state.orizon_user = {
            "user_id": "orizon-123",
            "keys": [{"key": "sk-internal-key-123"}],
        }

        key = await get_user_virtual_key_from_request(mock_request)

        assert key == "sk-internal-key-123"

    @pytest.mark.asyncio
    async def test_gets_key_from_external_user_session(self):
        """Should get virtual key from external user session."""
        mock_request = MagicMock(spec=Request)
        # No orizon_user in state (not internal user)
        if hasattr(mock_request.state, "orizon_user"):
            delattr(mock_request.state, "orizon_user")

        session_data = {
            "email": "external@example.com",
            "virtual_key": "sk-external-key-456",
        }

        with patch(
            "orizon.auth.sessions.get_current_session",
            new_callable=AsyncMock,
            return_value=session_data,
        ):
            key = await get_user_virtual_key_from_request(mock_request)

            assert key == "sk-external-key-456"

    @pytest.mark.asyncio
    async def test_returns_none_for_unauthenticated(self):
        """Should return None for unauthenticated requests."""
        mock_request = MagicMock(spec=Request)
        # No orizon_user in state
        if hasattr(mock_request.state, "orizon_user"):
            delattr(mock_request.state, "orizon_user")

        with patch(
            "orizon.auth.sessions.get_current_session",
            new_callable=AsyncMock,
            return_value=None,
        ):
            key = await get_user_virtual_key_from_request(mock_request)

            assert key is None

    @pytest.mark.asyncio
    async def test_handles_internal_user_without_keys(self):
        """Should handle internal user without keys gracefully."""
        mock_request = MagicMock(spec=Request)
        mock_request.state.orizon_user = {
            "user_id": "orizon-123",
            "keys": [],  # No keys
        }

        # Should try session as fallback
        with patch(
            "orizon.auth.sessions.get_current_session",
            new_callable=AsyncMock,
            return_value=None,
        ):
            key = await get_user_virtual_key_from_request(mock_request)

            assert key is None
