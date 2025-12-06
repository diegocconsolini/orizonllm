# OrizonLLM

**Enterprise LLM Gateway with All Features Unlocked**

Fork of [LiteLLM](https://github.com/BerriAI/litellm) with enterprise features enabled and custom branding.

---

## Table of Contents

- [What is OrizonLLM?](#what-is-orizonllm)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Enterprise Features](#enterprise-features)
- [Update Workflow](#update-workflow)
- [Container Registry](#container-registry)
- [API Usage](#api-usage)
- [Development](#development)
- [Architecture](#architecture)
- [Customizations](#customizations)

---

## What is OrizonLLM?

OrizonLLM is a **customized fork of LiteLLM** that provides:

| Feature | Status |
|---------|--------|
| All Enterprise Features Unlocked | Enabled |
| Custom Branding (OrizonLLM) | Enabled |
| SSO (Azure AD, Okta, Google) | Enabled |
| Audit Logs | Enabled |
| Semantic Cache (pgvector) | Enabled |
| Azure Key Vault Integration | Enabled |

---

## Quick Start

### Option 1: Using Docker Compose (Development)

```bash
# Clone the repo
git clone https://github.com/diegocconsolini/orizonllm.git
cd orizonllm

# Copy environment template
cp .env.example .env

# Edit .env with your settings
# Required: LITELLM_MASTER_KEY, POSTGRES_PASSWORD, REDIS_PASSWORD

# Start services
docker compose up -d

# Access the UI
open http://localhost:4010/ui/
```

### Option 2: Pull from Container Registry (Production)

```bash
# Pull the image
docker pull ghcr.io/diegocconsolini/orizonllm:latest

# Run with environment variables
docker run -d \
  -p 4000:4000 \
  -e LITELLM_MASTER_KEY=sk-your-key \
  -e DATABASE_URL=postgresql://user:pass@host:5432/db \
  ghcr.io/diegocconsolini/orizonllm:latest
```

---

## Configuration

### Default Ports

| Service | Port | URL |
|---------|------|-----|
| OrizonLLM Proxy | 4010 | http://localhost:4010 |
| PostgreSQL | 5442 | localhost:5442 |
| Redis | 6390 | localhost:6390 |

### URLs

| Page | URL | Description |
|------|-----|-------------|
| Admin Dashboard | `/ui/` | Full admin UI (enterprise features) |
| API Docs | `/` | Swagger/OpenAPI documentation |
| Health Check | `/health/readiness` | Health endpoint |
| Metrics | `/metrics` | Prometheus metrics |

### Admin Login

```
URL: http://localhost:4010/ui/
Username: admin
Password: <your LITELLM_MASTER_KEY from .env>
```

### Environment Variables

```bash
# Required
LITELLM_MASTER_KEY=sk-your-master-key      # Admin password & API key
LITELLM_SALT_KEY=sk-your-salt-key          # Encryption salt
POSTGRES_PASSWORD=your-postgres-password
REDIS_PASSWORD=your-redis-password

# LLM Providers (add at least one)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
AZURE_API_KEY=...

# SSO - Azure AD (optional)
MICROSOFT_CLIENT_ID=...
MICROSOFT_CLIENT_SECRET=...
MICROSOFT_TENANT=...

# SSO - GitHub OAuth (optional)
GITHUB_CLIENT_ID=...
GITHUB_CLIENT_SECRET=...

# Azure Key Vault (optional)
USE_AZURE_KEY_VAULT=true
AZURE_KEY_VAULT_URI=https://your-vault.vault.azure.net/
```

### config.yaml

Models and settings are configured in `config.yaml`:

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

---

## Enterprise Features

All features that normally require a LiteLLM Enterprise license are enabled:

| Feature | Description |
|---------|-------------|
| SSO | Azure AD, Okta, Google authentication |
| Audit Logs | Complete audit trail of all API calls |
| Custom Branding | OrizonLLM branding throughout UI |
| Tag Budgets | Budget limits per tag/team |
| Admin-only Routes | Restricted admin endpoints |
| OAuth2 Token Validation | JWT token validation |
| Enforced Params | Force parameters on requests |
| Allowed Routes per Key | Restrict API keys to specific routes |
| Secret Managers | Google, Hashicorp, CyberArk integration |
| Semantic Cache | pgvector-based similarity caching |

---

## Update Workflow

OrizonLLM stays in sync with upstream LiteLLM through a semi-automated workflow.

### Quick Update

```bash
# Run the update tool
./scripts/maintenance/update-orizon.sh

# Select option:
# 1) Full update (sync + build + push)
# 2) Sync upstream only
# 3) Build and push only
# 4) Check upstream status
```

### Manual Steps

```bash
# 1. Check how far behind upstream
./scripts/maintenance/update-orizon.sh
# Select option 4

# 2. Sync with upstream LiteLLM
./scripts/maintenance/sync-upstream.sh

# 3. If conflicts, resolve them (usually just litellm_license.py)
git status
# Edit conflicting files
git add .
git commit

# 4. Build and push new image
./scripts/maintenance/build-and-push.sh v1.60.0
```

### Update Scripts

| Script | Purpose |
|--------|---------|
| `scripts/maintenance/update-orizon.sh` | Main menu - complete workflow |
| `scripts/maintenance/sync-upstream.sh` | Fetch & merge upstream changes |
| `scripts/maintenance/build-and-push.sh` | Build Docker image & push to registry |

### Conflict Resolution

When merging upstream, conflicts typically occur in:

| File | Resolution |
|------|------------|
| `litellm_license.py` | Re-apply `is_premium() return True` |
| Branding files | Keep OrizonLLM branding |
| `logo.jpg` | Keep our logo: `git checkout --ours litellm/proxy/logo.jpg` |

See [CUSTOMIZATIONS.md](CUSTOMIZATIONS.md) for full details.

---

## Container Registry

### Setup GitHub Container Registry (One-time)

```bash
# 1. Create a GitHub Personal Access Token
# Go to: GitHub → Settings → Developer Settings → Personal Access Tokens
# Permissions: write:packages, read:packages, delete:packages

# 2. Login to registry
echo $GITHUB_TOKEN | docker login ghcr.io -u YOUR_USERNAME --password-stdin

# 3. Configure the build script
export GHCR_USERNAME=your-github-username
export REGISTRY_TYPE=ghcr
```

### Build and Push

```bash
# Build and push with version tag
./scripts/maintenance/build-and-push.sh v1.60.0

# Images created:
# - ghcr.io/username/orizonllm:v1.60.0
# - ghcr.io/username/orizonllm:20251206
# - ghcr.io/username/orizonllm:latest
```

### Deploy from Registry

```bash
# On any server
docker pull ghcr.io/diegocconsolini/orizonllm:v1.60.0

docker run -d \
  --name orizonllm \
  -p 4000:4000 \
  -e LITELLM_MASTER_KEY=sk-your-key \
  -e DATABASE_URL=postgresql://... \
  -e REDIS_HOST=redis-host \
  ghcr.io/diegocconsolini/orizonllm:v1.60.0
```

### Alternative Registries

```bash
# Azure Container Registry
export REGISTRY_TYPE=acr
export ACR_REGISTRY=yourregistry.azurecr.io
az acr login --name yourregistry
./scripts/maintenance/build-and-push.sh

# Docker Hub
export REGISTRY_TYPE=dockerhub
export DOCKERHUB_USERNAME=yourusername
./scripts/maintenance/build-and-push.sh
```

---

## API Usage

### Authentication

```bash
# Use your LITELLM_MASTER_KEY or a generated API key
export API_KEY=sk-your-api-key
```

### List Models

```bash
curl http://localhost:4010/v1/models \
  -H "Authorization: Bearer $API_KEY"
```

### Chat Completion

```bash
curl http://localhost:4010/v1/chat/completions \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

### Create API Key (Admin)

```bash
curl http://localhost:4010/key/generate \
  -H "Authorization: Bearer $LITELLM_MASTER_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "duration": "30d",
    "models": ["gpt-4", "claude-3-5-sonnet"],
    "max_budget": 100
  }'
```

---

## Development

### Local Development

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Run locally (without Docker)
litellm --config config.yaml --port 4000
```

### Rebuild Container

```bash
# After code changes
docker compose build orizon
docker compose up -d orizon

# View logs
docker logs -f orizon-proxy
```

### Project Structure

```
orizonllm/
├── litellm/                    # LiteLLM source (with our modifications)
│   └── proxy/
│       ├── auth/
│       │   └── litellm_license.py  # Enterprise unlock
│       └── logo.jpg                 # Orizon logo
├── ui/                         # Dashboard UI
├── scripts/
│   └── maintenance/            # Update workflow scripts
│       ├── update-orizon.sh    # Main update tool
│       ├── sync-upstream.sh    # Sync with LiteLLM
│       └── build-and-push.sh   # Build & push Docker
├── docker-compose.yml          # Local development
├── Dockerfile                  # Container build
├── config.yaml                 # Model configuration
├── CUSTOMIZATIONS.md           # What we changed
└── README.md                   # This file
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     ORIZONLLM STACK                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              orizon-proxy (port 4010)               │   │
│  │  ┌─────────────────────────────────────────────┐    │   │
│  │  │  LiteLLM Proxy (enterprise features)        │    │   │
│  │  │  - /v1/chat/completions                     │    │   │
│  │  │  - /v1/models                               │    │   │
│  │  │  - /ui/ (admin dashboard)                   │    │   │
│  │  └─────────────────────────────────────────────┘    │   │
│  └─────────────────────────────────────────────────────┘   │
│                            │                                │
│              ┌─────────────┴─────────────┐                 │
│              ▼                           ▼                  │
│  ┌───────────────────┐       ┌───────────────────┐         │
│  │ orizon-postgres   │       │   orizon-redis    │         │
│  │ (port 5442)       │       │   (port 6390)     │         │
│  │ + pgvector        │       │                   │         │
│  │ - users, keys     │       │ - rate limiting   │         │
│  │ - usage, budgets  │       │ - caching         │         │
│  │ - semantic cache  │       │ - sessions        │         │
│  └───────────────────┘       └───────────────────┘         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
              ┌───────────────────────────────┐
              │       LLM Providers           │
              │  OpenAI, Anthropic, Azure,    │
              │  Bedrock, Vertex AI, etc.     │
              └───────────────────────────────┘
```

---

## Customizations

OrizonLLM includes the following modifications from upstream LiteLLM:

| Modification | File | Purpose |
|--------------|------|---------|
| Enterprise Unlock | `litellm/proxy/auth/litellm_license.py` | `is_premium()` returns `True` |
| Logo | `litellm/proxy/logo.jpg` | Orizon branding |
| Login Page | `litellm/proxy/common_utils/html_forms/ui_login.py` | OrizonLLM title |
| SSO Pages | `cli_sso_success.py`, `jwt_display_template.py` | OrizonLLM branding |
| Dashboard | `ui/litellm-dashboard/src/app/layout.tsx` | OrizonLLM title |

For complete details, see [CUSTOMIZATIONS.md](CUSTOMIZATIONS.md).

### Privacy & Security

| Concern | Status |
|---------|--------|
| License phone-home | Disabled (is_premium bypass) |
| Telemetry | None (flag unused) |
| GitHub cost map | Safe (BerriAI cannot track) |
| External calls | Only your configured LLM providers |

---

## Support

- **Documentation**: [LiteLLM Docs](https://docs.litellm.ai/)
- **Issues**: Private repository
- **Updates**: Run `./scripts/maintenance/update-orizon.sh`

---

**Note:** This is a private fork with enterprise features unlocked. Not affiliated with BerriAI.
