<h1 align="center">
    🚀 Orizon LLM
</h1>
<p align="center">
    <strong>Enterprise LLM Gateway with All Features Unlocked</strong>
    <br>
    Fork of LiteLLM with enterprise features enabled and custom extensions
</p>

<p align="center">
    <img src="https://img.shields.io/badge/Enterprise-Unlocked-green?style=flat-square" alt="Enterprise Unlocked">
    <img src="https://img.shields.io/badge/Based%20on-LiteLLM%201.80.7-blue?style=flat-square" alt="LiteLLM Version">
    <img src="https://img.shields.io/badge/License-Private-red?style=flat-square" alt="License">
</p>

---

## What is Orizon?

Orizon is a **customized fork of LiteLLM** with:

- ✅ **All Enterprise Features Unlocked** - SSO, Audit Logs, Custom Branding, Tag Budgets, etc.
- ✅ **Custom Authentication** - GitHub OAuth, Magic Link, Custom Signup/Login pages
- ✅ **Security Hardening** - CSP headers, HSTS, security middleware
- ✅ **Observability** - Prometheus metrics, structured JSON logging, sensitive data redaction
- ✅ **Azure Key Vault Integration** - Secure secrets management
- ✅ **Custom Portal** - `/signup`, `/login`, `/profile` pages

## Quick Start

```bash
# Clone the repo
git clone https://github.com/diegocconsolini/orizonllm.git
cd orizonllm

# Copy environment template
cp .env.example .env

# Edit .env with your settings
# Required: LITELLM_MASTER_KEY, POSTGRES_PASSWORD, REDIS_PASSWORD
# Optional: OPENAI_API_KEY, ANTHROPIC_API_KEY, GITHUB_CLIENT_ID, etc.

# Start services
docker compose up -d

# Access the UI
open http://localhost:4010/ui/
```

## Default Ports

| Service | Port | URL |
|---------|------|-----|
| Orizon Proxy | 4010 | http://localhost:4010 |
| PostgreSQL | 5442 | localhost:5442 |
| Redis | 6390 | localhost:6390 |

## URLs

| Page | URL | Description |
|------|-----|-------------|
| Admin Dashboard | `/ui/` | LiteLLM Admin UI (all enterprise features) |
| API Docs | `/` | Swagger/OpenAPI documentation |
| Signup | `/signup` | Custom Orizon signup page |
| Login | `/login` | Custom Orizon login page |
| Profile | `/profile` | User profile with API key |
| Metrics | `/metrics` | Prometheus metrics endpoint |
| Health | `/health/readiness` | Health check endpoint |

## Admin Login

```
URL: http://localhost:4010/ui/
Username: admin
Password: <your LITELLM_MASTER_KEY from .env>
```

## Enterprise Features (Unlocked)

All features that normally require a LiteLLM Enterprise license are enabled:

| Feature | Status |
|---------|--------|
| SSO (Azure AD, Okta, Google) | ✅ Enabled |
| Audit Logs | ✅ Enabled |
| Custom Branding | ✅ Enabled |
| Tag Budgets | ✅ Enabled |
| Admin-only Routes | ✅ Enabled |
| OAuth2 Token Validation | ✅ Enabled |
| Max Request/Response Size Limits | ✅ Enabled |
| Enforced Params | ✅ Enabled |
| Allowed Routes per Key | ✅ Enabled |
| Google/Hashicorp/CyberArk Secret Managers | ✅ Enabled |

## Configuration

### Environment Variables

```bash
# Required
LITELLM_MASTER_KEY=sk-your-master-key
LITELLM_SALT_KEY=sk-your-salt-key
POSTGRES_PASSWORD=your-postgres-password
REDIS_PASSWORD=your-redis-password

# LLM Providers (add at least one)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# GitHub OAuth (optional)
GITHUB_CLIENT_ID=...
GITHUB_CLIENT_SECRET=...

# Azure AD SSO (optional)
MICROSOFT_CLIENT_ID=...
MICROSOFT_CLIENT_SECRET=...
MICROSOFT_TENANT=...

# Azure Key Vault (optional)
USE_AZURE_KEY_VAULT=true
AZURE_KEY_VAULT_URI=https://your-vault.vault.azure.net/
```

### config.yaml

Models and LiteLLM settings are configured in `config.yaml`:

```yaml
model_list:
  - model_name: gpt-4
    litellm_params:
      model: gpt-4
      api_key: os.environ/OPENAI_API_KEY

  - model_name: claude-3-5-sonnet
    litellm_params:
      model: claude-3-5-sonnet-20241022
      api_key: os.environ/ANTHROPIC_API_KEY

litellm_settings:
  callbacks:
    - prometheus

general_settings:
  master_key: os.environ/LITELLM_MASTER_KEY
```

## Orizon Extensions

Custom code lives in the `orizon/` directory:

```
orizon/
├── auth/           # Custom authentication (GitHub OAuth, magic link)
├── portal/         # Custom signup/login/profile pages
├── security.py     # CSP headers, security middleware
├── metrics.py      # Custom Prometheus metrics
├── logging.py      # Structured JSON logging with redaction
├── secrets.py      # Azure Key Vault integration
└── app.py          # Orizon setup and initialization
```

## API Usage

```bash
# List models
curl http://localhost:4010/v1/models \
  -H "Authorization: Bearer sk-your-api-key"

# Chat completion
curl http://localhost:4010/v1/chat/completions \
  -H "Authorization: Bearer sk-your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

## Development

```bash
# Run tests
source .venv/bin/activate
pytest tests/orizon/ -v

# Rebuild container after code changes
docker compose build orizon
docker compose up -d orizon

# View logs
docker logs -f orizon-proxy
```

## Architecture

```
┌─────────────────────────────────────────────┐
│              ORIZON STACK                   │
├─────────────────────────────────────────────┤
│  orizon-proxy (container)                   │
│  ├── LiteLLM Proxy (enterprise unlocked)    │
│  ├── orizon/auth/* (custom auth)            │
│  ├── orizon/portal/* (custom UI pages)      │
│  ├── orizon/security.py (CSP headers)       │
│  ├── orizon/metrics.py (Prometheus)         │
│  └── orizon/logging.py (structured logs)    │
├─────────────────────────────────────────────┤
│  orizon-postgres (user data, keys, usage)   │
│  orizon-redis (rate limiting, sessions)     │
└─────────────────────────────────────────────┘
```

## Technical Details

### Enterprise Unlock

The enterprise license check is bypassed in `litellm/proxy/auth/litellm_license.py`:

```python
def is_premium(self) -> bool:
    """ORIZON: Enterprise features unlocked."""
    return True
```

### Key File Locations

| File | Purpose |
|------|---------|
| `litellm/proxy/auth/litellm_license.py` | Enterprise unlock |
| `orizon/security.py` | CSP headers, HSTS |
| `orizon/auth/` | GitHub OAuth, magic link |
| `config.yaml` | Model configuration |

## Repository

- **URL**: https://github.com/diegocconsolini/orizonllm
- **Private**: Yes
- **Standalone**: Disconnected from upstream LiteLLM

---

**Note:** This is a private, standalone fork with enterprise features unlocked. Not affiliated with BerriAI.
