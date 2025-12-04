"""
Orizon Secrets Management

Provides unified secret retrieval from multiple sources:
1. Azure Key Vault (production) - preferred for cloud deployments
2. Environment variables (fallback) - for local development

Usage:
    from orizon.secrets import get_secret

    # Get secret - tries Azure KV first, falls back to env
    redis_password = await get_secret("REDIS_PASSWORD")

    # Force environment variable only
    redis_password = await get_secret("REDIS_PASSWORD", use_keyvault=False)

Configuration:
    Set USE_AZURE_KEY_VAULT=true and AZURE_KEY_VAULT_URI to enable Azure KV.
    Secrets in Azure KV should be named with dashes (e.g., "redis-password")
    and will be mapped from env var format (e.g., "REDIS_PASSWORD").
"""

import logging
import os
from functools import lru_cache
from typing import Optional

logger = logging.getLogger(__name__)

# Azure Key Vault configuration
USE_AZURE_KEY_VAULT = os.getenv("USE_AZURE_KEY_VAULT", "false").lower() == "true"
AZURE_KEY_VAULT_URI = os.getenv("AZURE_KEY_VAULT_URI", "")

# Cache for the Key Vault client
_keyvault_client = None


def _convert_to_keyvault_name(env_name: str) -> str:
    """Convert environment variable name to Azure Key Vault secret name.

    Azure KV names must be 1-127 characters containing only 0-9, a-z, A-Z, and -.

    Examples:
        REDIS_PASSWORD -> redis-password
        LITELLM_MASTER_KEY -> litellm-master-key
        DATABASE_URL -> database-url
    """
    return env_name.lower().replace("_", "-")


def _get_keyvault_client():
    """Get or create Azure Key Vault client (lazy initialization)."""
    global _keyvault_client

    if _keyvault_client is not None:
        return _keyvault_client

    if not AZURE_KEY_VAULT_URI:
        logger.warning("AZURE_KEY_VAULT_URI not set, Azure Key Vault disabled")
        return None

    try:
        from azure.identity import DefaultAzureCredential
        from azure.keyvault.secrets import SecretClient

        credential = DefaultAzureCredential()
        _keyvault_client = SecretClient(
            vault_url=AZURE_KEY_VAULT_URI,
            credential=credential,
        )
        logger.info(f"Azure Key Vault client initialized for: {AZURE_KEY_VAULT_URI}")
        return _keyvault_client

    except ImportError:
        logger.warning(
            "Azure Key Vault packages not installed. "
            "Install with: pip install azure-identity azure-keyvault-secrets"
        )
        return None
    except Exception as e:
        logger.error(f"Failed to initialize Azure Key Vault client: {e}")
        return None


async def get_secret(
    name: str,
    default: Optional[str] = None,
    use_keyvault: bool = True,
) -> Optional[str]:
    """Get a secret value from Azure Key Vault or environment variable.

    Args:
        name: Secret name (in UPPER_SNAKE_CASE format)
        default: Default value if secret not found
        use_keyvault: Whether to try Azure Key Vault first

    Returns:
        Secret value or default if not found

    Priority:
        1. Azure Key Vault (if enabled and use_keyvault=True)
        2. Environment variable
        3. Default value
    """
    # Try Azure Key Vault first if enabled
    if use_keyvault and USE_AZURE_KEY_VAULT:
        keyvault_value = await get_secret_from_keyvault(name)
        if keyvault_value is not None:
            return keyvault_value

    # Fall back to environment variable
    env_value = os.getenv(name)
    if env_value is not None:
        return env_value

    # Return default
    if default is not None:
        logger.debug(f"Secret '{name}' not found, using default")
    else:
        logger.warning(f"Secret '{name}' not found and no default provided")

    return default


async def get_secret_from_keyvault(name: str) -> Optional[str]:
    """Get a secret directly from Azure Key Vault.

    Args:
        name: Secret name (in UPPER_SNAKE_CASE format)

    Returns:
        Secret value or None if not found
    """
    client = _get_keyvault_client()
    if client is None:
        return None

    keyvault_name = _convert_to_keyvault_name(name)

    try:
        secret = client.get_secret(keyvault_name)
        logger.debug(f"Retrieved secret '{keyvault_name}' from Azure Key Vault")
        return secret.value
    except Exception as e:
        # Don't log full error for missing secrets (common case)
        if "SecretNotFound" in str(type(e).__name__) or "not found" in str(e).lower():
            logger.debug(f"Secret '{keyvault_name}' not found in Azure Key Vault")
        else:
            logger.warning(f"Error retrieving secret '{keyvault_name}' from Azure Key Vault: {e}")
        return None


def get_secret_sync(
    name: str,
    default: Optional[str] = None,
    use_keyvault: bool = True,
) -> Optional[str]:
    """Synchronous version of get_secret for use at module import time.

    Args:
        name: Secret name (in UPPER_SNAKE_CASE format)
        default: Default value if secret not found
        use_keyvault: Whether to try Azure Key Vault first

    Returns:
        Secret value or default if not found
    """
    # Try Azure Key Vault first if enabled
    if use_keyvault and USE_AZURE_KEY_VAULT:
        keyvault_value = _get_secret_from_keyvault_sync(name)
        if keyvault_value is not None:
            return keyvault_value

    # Fall back to environment variable
    env_value = os.getenv(name)
    if env_value is not None:
        return env_value

    return default


def _get_secret_from_keyvault_sync(name: str) -> Optional[str]:
    """Synchronous version of get_secret_from_keyvault."""
    client = _get_keyvault_client()
    if client is None:
        return None

    keyvault_name = _convert_to_keyvault_name(name)

    try:
        secret = client.get_secret(keyvault_name)
        logger.debug(f"Retrieved secret '{keyvault_name}' from Azure Key Vault")
        return secret.value
    except Exception as e:
        if "SecretNotFound" in str(type(e).__name__) or "not found" in str(e).lower():
            logger.debug(f"Secret '{keyvault_name}' not found in Azure Key Vault")
        else:
            logger.warning(f"Error retrieving secret '{keyvault_name}' from Azure Key Vault: {e}")
        return None


# Pre-defined secret names for documentation and IDE autocomplete
class SecretNames:
    """Standard secret names used by Orizon."""

    # Database
    POSTGRES_PASSWORD = "POSTGRES_PASSWORD"
    DATABASE_URL = "DATABASE_URL"

    # Redis
    REDIS_PASSWORD = "REDIS_PASSWORD"
    REDIS_HOST = "REDIS_HOST"

    # LiteLLM
    LITELLM_MASTER_KEY = "LITELLM_MASTER_KEY"
    LITELLM_SALT_KEY = "LITELLM_SALT_KEY"

    # Email
    SMTP_HOST = "SMTP_HOST"
    SMTP_PORT = "SMTP_PORT"
    SMTP_USER = "SMTP_USER"
    SMTP_PASSWORD = "SMTP_PASSWORD"

    # OAuth
    GITHUB_CLIENT_ID = "GITHUB_CLIENT_ID"
    GITHUB_CLIENT_SECRET = "GITHUB_CLIENT_SECRET"

    # LLM Providers (loaded by LiteLLM directly via use_azure_key_vault)
    OPENAI_API_KEY = "OPENAI_API_KEY"
    ANTHROPIC_API_KEY = "ANTHROPIC_API_KEY"
    AZURE_API_KEY = "AZURE_API_KEY"


# Convenience function to load all secrets at startup
async def load_secrets_to_env() -> dict:
    """Load all standard secrets from Azure Key Vault into environment.

    This is useful for services that read from environment variables.
    Call this early in application startup.

    Returns:
        Dict of loaded secret names to boolean (True if loaded from KV)
    """
    if not USE_AZURE_KEY_VAULT:
        logger.info("Azure Key Vault disabled, using environment variables only")
        return {}

    loaded = {}
    standard_secrets = [
        SecretNames.POSTGRES_PASSWORD,
        SecretNames.REDIS_PASSWORD,
        SecretNames.LITELLM_MASTER_KEY,
        SecretNames.LITELLM_SALT_KEY,
        SecretNames.SMTP_PASSWORD,
        SecretNames.GITHUB_CLIENT_SECRET,
    ]

    for secret_name in standard_secrets:
        # Only load if not already set in environment
        if os.getenv(secret_name) is None:
            value = await get_secret_from_keyvault(secret_name)
            if value:
                os.environ[secret_name] = value
                loaded[secret_name] = True
                logger.info(f"Loaded secret '{secret_name}' from Azure Key Vault")
            else:
                loaded[secret_name] = False
        else:
            loaded[secret_name] = False  # Already set in env
            logger.debug(f"Secret '{secret_name}' already set in environment")

    return loaded
