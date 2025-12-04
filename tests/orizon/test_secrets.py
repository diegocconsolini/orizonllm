"""Tests for Orizon secrets management.

Tests secret retrieval from environment variables and Azure Key Vault.
"""

import os
import pytest
from unittest.mock import MagicMock, patch

# Import module under test
from orizon.secrets import (
    get_secret,
    get_secret_sync,
    _convert_to_keyvault_name,
    SecretNames,
)


class TestConvertToKeyvaultName:
    """Test secret name conversion."""

    def test_convert_simple_name(self):
        """Should convert UPPER_SNAKE to lower-dash."""
        assert _convert_to_keyvault_name("REDIS_PASSWORD") == "redis-password"

    def test_convert_multi_word(self):
        """Should handle multiple underscores."""
        assert _convert_to_keyvault_name("LITELLM_MASTER_KEY") == "litellm-master-key"

    def test_convert_single_word(self):
        """Should handle single word."""
        assert _convert_to_keyvault_name("SECRET") == "secret"


class TestGetSecretSync:
    """Test synchronous secret retrieval."""

    def test_get_from_env(self):
        """Should get secret from environment variable."""
        with patch.dict(os.environ, {"TEST_SECRET": "test-value"}):
            result = get_secret_sync("TEST_SECRET", use_keyvault=False)
            assert result == "test-value"

    def test_get_default_when_missing(self):
        """Should return default when secret not found."""
        # Make sure the env var doesn't exist
        if "MISSING_SECRET" in os.environ:
            del os.environ["MISSING_SECRET"]

        result = get_secret_sync("MISSING_SECRET", default="default-value", use_keyvault=False)
        assert result == "default-value"

    def test_get_none_when_no_default(self):
        """Should return None when secret not found and no default."""
        if "MISSING_SECRET" in os.environ:
            del os.environ["MISSING_SECRET"]

        result = get_secret_sync("MISSING_SECRET", use_keyvault=False)
        assert result is None


class TestGetSecretAsync:
    """Test asynchronous secret retrieval."""

    @pytest.mark.asyncio
    async def test_get_from_env(self):
        """Should get secret from environment variable."""
        with patch.dict(os.environ, {"TEST_SECRET_ASYNC": "async-test-value"}):
            result = await get_secret("TEST_SECRET_ASYNC", use_keyvault=False)
            assert result == "async-test-value"

    @pytest.mark.asyncio
    async def test_get_default_when_missing(self):
        """Should return default when secret not found."""
        if "MISSING_SECRET_ASYNC" in os.environ:
            del os.environ["MISSING_SECRET_ASYNC"]

        result = await get_secret("MISSING_SECRET_ASYNC", default="default-async", use_keyvault=False)
        assert result == "default-async"


class TestSecretNames:
    """Test secret name constants."""

    def test_has_common_secrets(self):
        """Should have all common secret names defined."""
        assert SecretNames.POSTGRES_PASSWORD == "POSTGRES_PASSWORD"
        assert SecretNames.REDIS_PASSWORD == "REDIS_PASSWORD"
        assert SecretNames.LITELLM_MASTER_KEY == "LITELLM_MASTER_KEY"
        assert SecretNames.GITHUB_CLIENT_SECRET == "GITHUB_CLIENT_SECRET"


class TestAzureKeyVaultIntegration:
    """Test Azure Key Vault integration (mocked)."""

    @pytest.mark.asyncio
    @patch("orizon.secrets.USE_AZURE_KEY_VAULT", True)
    @patch("orizon.secrets.AZURE_KEY_VAULT_URI", "https://test-vault.vault.azure.net/")
    async def test_falls_back_to_env_when_keyvault_fails(self):
        """Should fall back to env when Key Vault not available."""
        with patch.dict(os.environ, {"FALLBACK_SECRET": "env-value"}):
            # Key Vault client will fail to initialize (mocked)
            with patch("orizon.secrets._get_keyvault_client", return_value=None):
                result = await get_secret("FALLBACK_SECRET")
                assert result == "env-value"
