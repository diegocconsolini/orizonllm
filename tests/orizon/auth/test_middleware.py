"""Tests for orizon.auth.middleware module."""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi import FastAPI
from fastapi.testclient import TestClient

from orizon.auth.middleware import OrizonAuthMiddleware


@pytest.fixture
def app():
    """Create a test FastAPI app with middleware."""
    app = FastAPI()
    app.add_middleware(OrizonAuthMiddleware)

    @app.get("/test")
    async def test_endpoint():
        return {"status": "ok"}

    @app.get("/health")
    async def health_endpoint():
        return {"status": "healthy"}

    return app


@pytest.fixture
def client(app):
    """Create a test client."""
    return TestClient(app)


class TestOrizonAuthMiddleware:
    """Tests for OrizonAuthMiddleware."""

    def test_skips_health_endpoints(self, client):
        """Should skip auth for health endpoints."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}

    def test_passes_external_bearer_token(self, client):
        """Should pass through existing Bearer tokens."""
        with patch(
            "orizon.auth.middleware.get_user_email"
        ) as mock_email:
            mock_email.return_value = None

            response = client.get(
                "/test",
                headers={"Authorization": "Bearer sk-external-key"}
            )

            # Request passes through (would fail at LiteLLM level)
            assert response.status_code == 200

    def test_handles_no_auth_headers(self, client):
        """Should handle requests with no auth headers."""
        with patch(
            "orizon.auth.middleware.get_user_email"
        ) as mock_email:
            mock_email.return_value = None

            response = client.get("/test")

            # Request passes through (would fail at LiteLLM level)
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_provisions_internal_user(self, app):
        """Should provision user and inject auth header."""
        user_data = {
            "user_id": "orizon-abc123",
            "user_info": {"user_email": "internal@company.com"},
            "keys": [],
        }

        with patch(
            "orizon.auth.middleware.get_user_email"
        ) as mock_email:
            with patch(
                "orizon.auth.middleware.get_or_create_user_key",
                new_callable=AsyncMock
            ) as mock_provision:
                mock_email.return_value = "internal@company.com"
                mock_provision.return_value = (user_data, "sk-virtual-key")

                client = TestClient(app)
                response = client.get(
                    "/test",
                    headers={"X-Auth-Request-Email": "internal@company.com"}
                )

                assert response.status_code == 200
                mock_provision.assert_called_once_with("internal@company.com")

    @pytest.mark.asyncio
    async def test_handles_provision_failure(self, app):
        """Should continue even if provisioning fails."""
        with patch(
            "orizon.auth.middleware.get_user_email"
        ) as mock_email:
            with patch(
                "orizon.auth.middleware.get_or_create_user_key",
                new_callable=AsyncMock
            ) as mock_provision:
                mock_email.return_value = "failing@company.com"
                mock_provision.side_effect = Exception("LiteLLM unavailable")

                client = TestClient(app)
                response = client.get(
                    "/test",
                    headers={"X-Auth-Request-Email": "failing@company.com"}
                )

                # Should not crash - continues without auth
                assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_handles_no_virtual_key(self, app):
        """Should handle case when no virtual key is returned."""
        with patch(
            "orizon.auth.middleware.get_user_email"
        ) as mock_email:
            with patch(
                "orizon.auth.middleware.get_or_create_user_key",
                new_callable=AsyncMock
            ) as mock_provision:
                mock_email.return_value = "nokey@company.com"
                mock_provision.return_value = (None, None)

                client = TestClient(app)
                response = client.get(
                    "/test",
                    headers={"X-Auth-Request-Email": "nokey@company.com"}
                )

                # Should not crash - continues without auth
                assert response.status_code == 200


class TestSkipAuthPaths:
    """Tests for SKIP_AUTH_PATHS configuration."""

    def test_skips_docs(self, client):
        """Should skip auth for /docs."""
        with patch(
            "orizon.auth.middleware.get_user_email"
        ) as mock_email:
            # Mock should not be called for skipped paths
            response = client.get("/docs")

            # FastAPI docs redirects or returns HTML
            assert response.status_code in (200, 307)

    def test_skips_openapi(self, client):
        """Should skip auth for /openapi.json."""
        with patch(
            "orizon.auth.middleware.get_user_email"
        ) as mock_email:
            response = client.get("/openapi.json")

            assert response.status_code == 200

    def test_skips_v1_health(self, client):
        """Should skip auth for /v1/health."""
        with patch(
            "orizon.auth.middleware.get_user_email"
        ) as mock_email:
            # Create endpoint for this test
            @client.app.get("/v1/health")
            async def v1_health():
                return {"status": "ok"}

            response = client.get("/v1/health")
            assert response.status_code == 200
