"""Tests for orizon.proxy.routes module."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import Request
from fastapi.responses import JSONResponse

from orizon.proxy.routes import proxy_v1_endpoint, list_models, list_models_v1


class TestProxyV1Endpoint:
    """Tests for /v1/{path} proxy endpoint."""

    @pytest.mark.asyncio
    async def test_requires_authentication(self):
        """Should return 401 for unauthenticated requests."""
        mock_request = MagicMock(spec=Request)

        with patch(
            "orizon.proxy.routes.get_user_virtual_key_from_request",
            new_callable=AsyncMock,
            return_value=None,
        ):
            with pytest.raises(Exception) as exc_info:
                await proxy_v1_endpoint(mock_request, "chat/completions")

            assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_forwards_authenticated_request(self):
        """Should forward authenticated request to LiteLLM."""
        mock_request = MagicMock(spec=Request)
        mock_response = JSONResponse(content={"result": "success"})

        with patch(
            "orizon.proxy.routes.get_user_virtual_key_from_request",
            new_callable=AsyncMock,
            return_value="sk-test-key-123",
        ):
            with patch(
                "orizon.proxy.routes.forward_request",
                new_callable=AsyncMock,
                return_value=mock_response,
            ) as mock_forward:
                response = await proxy_v1_endpoint(mock_request, "chat/completions")

                # Verify forward_request was called
                mock_forward.assert_called_once_with(
                    mock_request, "/v1/chat/completions", "sk-test-key-123"
                )
                assert response == mock_response

    @pytest.mark.asyncio
    async def test_handles_different_paths(self):
        """Should handle different API paths."""
        mock_request = MagicMock(spec=Request)
        mock_response = JSONResponse(content={})

        paths = [
            "chat/completions",
            "embeddings",
            "models",
            "completions",
        ]

        with patch(
            "orizon.proxy.routes.get_user_virtual_key_from_request",
            new_callable=AsyncMock,
            return_value="sk-test-key",
        ):
            with patch(
                "orizon.proxy.routes.forward_request",
                new_callable=AsyncMock,
                return_value=mock_response,
            ) as mock_forward:
                for path in paths:
                    await proxy_v1_endpoint(mock_request, path)

                # Verify all paths were forwarded
                assert mock_forward.call_count == len(paths)


class TestListModels:
    """Tests for /models endpoints."""

    @pytest.mark.asyncio
    async def test_list_models_requires_auth(self):
        """Should require authentication."""
        mock_request = MagicMock(spec=Request)

        with patch(
            "orizon.proxy.routes.get_user_virtual_key_from_request",
            new_callable=AsyncMock,
            return_value=None,
        ):
            with pytest.raises(Exception) as exc_info:
                await list_models(mock_request)

            assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_list_models_forwards_request(self):
        """Should forward to LiteLLM /models."""
        mock_request = MagicMock(spec=Request)
        mock_response = JSONResponse(content={"data": []})

        with patch(
            "orizon.proxy.routes.get_user_virtual_key_from_request",
            new_callable=AsyncMock,
            return_value="sk-test-key",
        ):
            with patch(
                "orizon.proxy.routes.forward_request",
                new_callable=AsyncMock,
                return_value=mock_response,
            ) as mock_forward:
                response = await list_models(mock_request)

                mock_forward.assert_called_once_with(
                    mock_request, "/models", "sk-test-key"
                )

    @pytest.mark.asyncio
    async def test_list_models_v1_forwards_request(self):
        """Should forward to LiteLLM /v1/models."""
        mock_request = MagicMock(spec=Request)
        mock_response = JSONResponse(content={"data": []})

        with patch(
            "orizon.proxy.routes.get_user_virtual_key_from_request",
            new_callable=AsyncMock,
            return_value="sk-test-key",
        ):
            with patch(
                "orizon.proxy.routes.forward_request",
                new_callable=AsyncMock,
                return_value=mock_response,
            ) as mock_forward:
                response = await list_models_v1(mock_request)

                mock_forward.assert_called_once_with(
                    mock_request, "/v1/models", "sk-test-key"
                )
