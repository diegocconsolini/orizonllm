"""Integration tests for proxy functionality.

Tests the complete proxy flow with both internal and external users.
Skip with: SKIP_INTEGRATION_TESTS=1
"""

import os
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import Request
from fastapi.responses import JSONResponse

# Check if integration tests should be skipped
SKIP_INTEGRATION_TESTS = os.getenv("SKIP_INTEGRATION_TESTS", "1") == "1"
skip_reason = "Integration tests require LiteLLM. Set SKIP_INTEGRATION_TESTS=0 to run."


@pytest.mark.skipif(SKIP_INTEGRATION_TESTS, reason=skip_reason)
class TestProxyIntegrationLive:
    """Live integration tests with actual LiteLLM instance."""

    # These require LiteLLM running
    pass


class TestProxyIntegrationMocked:
    """Mocked integration tests for proxy flow."""

    @pytest.mark.asyncio
    async def test_internal_user_proxy_flow(self):
        """Test complete flow for internal user (oauth2-proxy)."""
        from orizon.proxy.routes import proxy_v1_endpoint

        # Setup request with internal user data (from middleware)
        mock_request = MagicMock(spec=Request)
        mock_request.state.orizon_user = {
            "user_id": "orizon-internal-123",
            "keys": [{"key": "sk-internal-key-123"}],
        }
        mock_request.method = "POST"
        mock_request.headers = {"content-type": "application/json"}
        mock_request.query_params = {}
        mock_request.body = AsyncMock(return_value=b'{"model": "gpt-4"}')

        # Mock LiteLLM response
        mock_litellm_response = MagicMock()
        mock_litellm_response.status_code = 200
        mock_litellm_response.headers = {"content-type": "application/json"}
        mock_litellm_response.content = b'{"choices": [{"message": {"content": "Hello"}}]}'
        mock_litellm_response.json.return_value = {
            "choices": [{"message": {"content": "Hello"}}]
        }

        with patch("orizon.proxy.client.httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.request.return_value = mock_litellm_response
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            mock_client.return_value = mock_instance

            # Make request through proxy
            response = await proxy_v1_endpoint(mock_request, "chat/completions")

            # Verify request was forwarded with internal user's key
            mock_instance.request.assert_called_once()
            call_kwargs = mock_instance.request.call_args[1]
            assert call_kwargs["headers"]["authorization"] == "Bearer sk-internal-key-123"
            assert "chat/completions" in call_kwargs["url"]

    @pytest.mark.asyncio
    async def test_external_user_proxy_flow(self):
        """Test complete flow for external user (session cookie)."""
        from orizon.proxy.routes import proxy_v1_endpoint

        # Setup request with NO internal user data (external user)
        mock_request = MagicMock(spec=Request)
        # No orizon_user in state
        if hasattr(mock_request.state, "orizon_user"):
            delattr(mock_request.state, "orizon_user")

        mock_request.method = "POST"
        mock_request.headers = {"content-type": "application/json"}
        mock_request.query_params = {}
        mock_request.body = AsyncMock(return_value=b'{"model": "gpt-4"}')

        # Mock session data (external user)
        session_data = {
            "email": "external@example.com",
            "virtual_key": "sk-external-key-456",
        }

        # Mock LiteLLM response
        mock_litellm_response = MagicMock()
        mock_litellm_response.status_code = 200
        mock_litellm_response.headers = {"content-type": "application/json"}
        mock_litellm_response.content = b'{"choices": [{"message": {"content": "Hello"}}]}'
        mock_litellm_response.json.return_value = {
            "choices": [{"message": {"content": "Hello"}}]
        }

        with patch(
            "orizon.auth.sessions.get_current_session",
            new_callable=AsyncMock,
            return_value=session_data,
        ):
            with patch("orizon.proxy.client.httpx.AsyncClient") as mock_client:
                mock_instance = AsyncMock()
                mock_instance.request.return_value = mock_litellm_response
                mock_instance.__aenter__.return_value = mock_instance
                mock_instance.__aexit__.return_value = None
                mock_client.return_value = mock_instance

                # Make request through proxy
                response = await proxy_v1_endpoint(mock_request, "chat/completions")

                # Verify request was forwarded with external user's key
                mock_instance.request.assert_called_once()
                call_kwargs = mock_instance.request.call_args[1]
                assert (
                    call_kwargs["headers"]["authorization"]
                    == "Bearer sk-external-key-456"
                )

    @pytest.mark.asyncio
    async def test_unauthenticated_request_rejected(self):
        """Test unauthenticated requests are rejected."""
        from orizon.proxy.routes import proxy_v1_endpoint

        # Setup request with NO authentication
        mock_request = MagicMock(spec=Request)
        if hasattr(mock_request.state, "orizon_user"):
            delattr(mock_request.state, "orizon_user")

        # No session either
        with patch(
            "orizon.auth.sessions.get_current_session",
            new_callable=AsyncMock,
            return_value=None,
        ):
            with pytest.raises(Exception) as exc_info:
                await proxy_v1_endpoint(mock_request, "chat/completions")

            assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_streaming_response_flow(self):
        """Test proxy handles streaming responses correctly."""
        from orizon.proxy.routes import proxy_v1_endpoint

        # Setup authenticated request
        mock_request = MagicMock(spec=Request)
        mock_request.state.orizon_user = {
            "user_id": "orizon-123",
            "keys": [{"key": "sk-stream-key"}],
        }
        mock_request.method = "POST"
        mock_request.headers = {"content-type": "application/json"}
        mock_request.query_params = {}
        mock_request.body = AsyncMock(return_value=b'{"stream": true}')

        # Mock streaming response from LiteLLM
        mock_litellm_response = MagicMock()
        mock_litellm_response.status_code = 200
        mock_litellm_response.headers = {"content-type": "text/event-stream"}

        async def mock_stream():
            yield b"data: chunk1\n\n"
            yield b"data: chunk2\n\n"
            yield b"data: [DONE]\n\n"

        mock_litellm_response.aiter_bytes = mock_stream

        with patch("orizon.proxy.client.httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.request.return_value = mock_litellm_response
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            mock_client.return_value = mock_instance

            response = await proxy_v1_endpoint(mock_request, "chat/completions")

            # Verify it's a streaming response
            from fastapi.responses import StreamingResponse

            assert isinstance(response, StreamingResponse)

    @pytest.mark.asyncio
    async def test_list_models_endpoint(self):
        """Test /models endpoint works with authentication."""
        from orizon.proxy.routes import list_models

        mock_request = MagicMock(spec=Request)
        mock_request.state.orizon_user = {
            "user_id": "orizon-123",
            "keys": [{"key": "sk-models-key"}],
        }
        mock_request.method = "GET"
        mock_request.headers = {}
        mock_request.query_params = {}

        mock_litellm_response = MagicMock()
        mock_litellm_response.status_code = 200
        mock_litellm_response.headers = {"content-type": "application/json"}
        mock_litellm_response.content = b'{"data": [{"id": "gpt-4"}]}'
        mock_litellm_response.json.return_value = {"data": [{"id": "gpt-4"}]}

        with patch("orizon.proxy.client.httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.request.return_value = mock_litellm_response
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            mock_client.return_value = mock_instance

            response = await list_models(mock_request)

            # Verify models endpoint was called
            mock_instance.request.assert_called_once()
            call_kwargs = mock_instance.request.call_args[1]
            assert "/models" in call_kwargs["url"]

    @pytest.mark.asyncio
    async def test_proxy_preserves_query_params(self):
        """Test proxy preserves query parameters."""
        from orizon.proxy.routes import proxy_v1_endpoint

        mock_request = MagicMock(spec=Request)
        mock_request.state.orizon_user = {
            "user_id": "orizon-123",
            "keys": [{"key": "sk-test-key"}],
        }
        mock_request.method = "GET"
        mock_request.headers = {}
        mock_request.query_params = {"limit": "10", "offset": "0"}

        mock_litellm_response = MagicMock()
        mock_litellm_response.status_code = 200
        mock_litellm_response.headers = {"content-type": "application/json"}
        mock_litellm_response.content = b"{}"
        mock_litellm_response.json.return_value = {}

        with patch("orizon.proxy.client.httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.request.return_value = mock_litellm_response
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            mock_client.return_value = mock_instance

            response = await proxy_v1_endpoint(mock_request, "test")

            # Verify query params were passed
            mock_instance.request.assert_called_once()
            call_kwargs = mock_instance.request.call_args[1]
            assert call_kwargs["params"]["limit"] == "10"
            assert call_kwargs["params"]["offset"] == "0"
