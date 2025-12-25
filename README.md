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

OrizonLLM stays in sync with upstream LiteLLM through automated scripts that preserve your customizations.

### Quick Update (Recommended)

```bash
# 1. Check for license changes FIRST (important!)
./scripts/check-license-changes.sh

# 2. Run the full sync workflow
./scripts/sync-upstream.sh
```

### Manual Steps

```bash
# 1. Check how far behind upstream
git fetch upstream
git rev-list --count main..upstream/main  # Shows commits behind

# 2. Check for license-related changes
./scripts/check-license-changes.sh

# 3. Merge upstream
git merge upstream/main --no-commit

# 4. Auto-resolve protected files (CRITICAL)
git checkout --ours litellm/proxy/auth/litellm_license.py && git add litellm/proxy/auth/litellm_license.py
git checkout --ours README.md && git add README.md
git checkout --ours CLAUDE.md && git add CLAUDE.md

# 5. Resolve remaining conflicts manually
git status
# Edit conflicting files...

# 6. Commit and push
git commit -m "chore: sync with upstream LiteLLM"
git push origin main
```

### Update Scripts

| Script | Purpose |
|--------|---------|
| `scripts/check-license-changes.sh` | **Run first!** Detect new license checks in upstream |
| `scripts/sync-upstream.sh` | Full sync workflow with auto-protection of key files |
| `scripts/sync-ui-build.sh` | Sync UI build after upstream merge (auto-called by sync-upstream.sh) |

### Protected Files (Never Accept Upstream Version)

These files are automatically preserved by `sync-upstream.sh`:

| File | Reason |
|------|--------|
| `litellm/proxy/auth/litellm_license.py` | **License bypass** - `is_premium()` returns `True` |
| `README.md` | OrizonLLM branding |
| `CLAUDE.md` | Custom development guide |
| `litellm/proxy/_experimental/out/**` | UI build artifacts (synced from ui/litellm-dashboard/out) |

**⚠️ UI Build Artifacts:** The `_experimental/out` directory contains pre-built Next.js files that cannot be merged. Merging corrupts HTML files causing 404 errors. The sync script automatically copies clean builds from `ui/litellm-dashboard/out/`.

### License Bypass Details

The enterprise unlock is a single modification in `litellm/proxy/auth/litellm_license.py`:

```python
def is_premium(self) -> bool:
    """
    ORIZON: Enterprise features unlocked.
    All premium features are enabled without license validation.
    """
    return True
```

Upstream's version does actual license validation against `https://license.litellm.ai`.
Your bypass simply returns `True` - skipping all validation.

**⚠️ Always run `./scripts/check-license-changes.sh` before merging** to detect if upstream added new license checks elsewhere.

See [UPDATE_PLAN.md](UPDATE_PLAN.md) for complete documentation.

---

## Container Registry

### Setup (One-time)

```bash
# 1. Configure SSH for GitHub (if not already done)
# Your SSH key should be added to GitHub → Settings → SSH Keys
ssh -T git@github.com  # Test: should say "Hi username!"

# 2. Create a GitHub Personal Access Token for Container Registry
# Go to: GitHub → Settings → Developer Settings → Personal Access Tokens
# Permissions: write:packages, read:packages, delete:packages

# 3. Login to container registry
echo $GITHUB_TOKEN | docker login ghcr.io -u YOUR_USERNAME --password-stdin

# 4. Configure the build script
export GHCR_USERNAME=your-github-username
export REGISTRY_TYPE=ghcr
```

### Build and Push

```bash
# Non-interactive build and push
./scripts/maintenance/build-and-push.sh -y

# Or with specific version
./scripts/maintenance/build-and-push.sh -y v1.60.0

# Manual build with SHA tag (recommended for Railway)
SHA=$(git rev-parse --short HEAD)
docker build -t ghcr.io/diegocconsolini/orizonllm:$SHA \
             -t ghcr.io/diegocconsolini/orizonllm:latest \
             -f Dockerfile .
docker push ghcr.io/diegocconsolini/orizonllm:$SHA
docker push ghcr.io/diegocconsolini/orizonllm:latest

# Images created:
# - ghcr.io/diegocconsolini/orizonllm:{sha}     (e.g., c361f664b5)
# - ghcr.io/diegocconsolini/orizonllm:YYYYMMDD
# - ghcr.io/diegocconsolini/orizonllm:latest
```

### Deploy to Railway

```bash
# Update image reference (use SHA for guaranteed version)
railway variables --set "RAILWAY_DOCKER_IMAGE=ghcr.io/diegocconsolini/orizonllm:$SHA" -s orizonllm

# Redeploy
railway service orizonllm && railway redeploy --yes
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
│   ├── check-license-changes.sh  # Detect upstream license changes
│   ├── sync-upstream.sh          # Sync with LiteLLM (auto-protects files)
│   ├── sync-ui-build.sh          # Sync UI after merge
│   └── maintenance/
│       └── build-and-push.sh     # Build & push Docker (-y for non-interactive)
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

## Production Deployment (Railway)

OrizonLLM is deployed on Railway for AudiVidi.

### Live Deployment

| Resource | URL/Value |
|----------|-----------|
| **API Endpoint** | https://api.audividi.ai |
| **Admin UI** | https://api.audividi.ai/ui/ |
| **Admin Login** | `admin` / `<LITELLM_MASTER_KEY>` |
| **Railway Project** | AudiVidi-LLM |

### Services

| Service | Image/Source | Port |
|---------|--------------|------|
| orizonllm | `ghcr.io/diegocconsolini/orizonllm:latest` (private) | 4000 |
| pgvector | `pgvector/pgvector:pg17` (vector search enabled) | 5432 |
| Redis | Railway managed | 6379 |

### Environment Variables (Railway)

```bash
# Database (auto-set via Railway references)
DATABASE_URL=${{pgvector.DATABASE_URL}}
REDIS_URL=${{Redis.REDIS_URL}}
REDIS_HOST=${{Redis.REDISHOST}}
REDIS_PASSWORD=${{Redis.REDIS_PASSWORD}}

# OrizonLLM
LITELLM_MASTER_KEY=sk-...        # Admin password
LITELLM_SALT_KEY=...             # Encryption salt
STORE_MODEL_IN_DB=True
PORT=4000

# Security - CORS (restrict allowed origins)
CORS_ALLOW_ORIGIN=https://audividi.ai,https://app.audividi.ai,https://orizonqa.guatemaltek.com

# AI Providers (add your keys)
OPENAI_API_KEY=sk-...
GROQ_API_KEY=gsk_...
DEEPGRAM_API_KEY=...
```

### Configured Models

| Model Name | Provider | Type |
|------------|----------|------|
| `whisper-1` | OpenAI | audio_transcription |
| `groq/whisper-large-v3` | Groq | audio_transcription |
| `deepgram/nova-2` | Deepgram | audio_transcription |
| `gpt-4o-mini` | OpenAI | chat |
| `groq/llama-3.1-8b-instant` | Groq | chat |

### Manual Deployment

**Build and deploy steps:**

```bash
# 1. Build and push to GHCR
./scripts/maintenance/build-and-push.sh -y

# 2. Get the SHA tag
SHA=$(git rev-parse --short HEAD)

# 3. Update Railway and redeploy
railway variables --set "RAILWAY_DOCKER_IMAGE=ghcr.io/diegocconsolini/orizonllm:$SHA" -s orizonllm
railway redeploy --yes -s orizonllm
```

### Railway Registry Credentials

Railway pulls from private GHCR. Configured in:
- Railway → orizonllm → Settings → Source → Registry Credentials
- Username: `diegocconsolini`
- Password: GitHub PAT with `read:packages` scope

### Custom Domain

- Domain: `api.audividi.ai`
- DNS: CNAME → `3rpn2pun.up.railway.app` (Cloudflare)
- SSL: Auto-managed by Railway

### Security (Cloudflare)

| Protection | Status |
|------------|--------|
| Geographic blocking | RU, IR, KP, CU, SY, UA, CN, VN, BY, MM |
| Bot/scraper blocking | python-requests, wget, curl, sqlmap |
| AI crawler blocking | ChatGPT, Perplexity, MistralAI, etc. |
| API docs blocked | /openapi.json, /routes, /redoc |
| Rate limiting | 60 req/min on /v1/* and auth endpoints |
| Leaked credential check | Blocks compromised passwords |
| OWASP WAF | Cloudflare managed ruleset |
| CORS restriction | Only allowed origins (see env vars) |

**Custom Rules:**
1. Block high-risk countries
2. Block malicious user agents
3. Block AI crawlers
4. Block public API documentation
5. Rate limit API & auth endpoints

**Environment Variable:**
```bash
CORS_ALLOW_ORIGIN=https://audividi.ai,https://app.audividi.ai,https://orizonqa.guatemaltek.com
```

---

## Support

- **Documentation**: [LiteLLM Docs](https://docs.litellm.ai/)
- **Issues**: Private repository
- **Updates**: Run `./scripts/sync-upstream.sh`

---

**Note:** This is a private fork with enterprise features unlocked. Not affiliated with BerriAI.
