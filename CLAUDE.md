# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Installation
- `make install-dev` - Install core development dependencies
- `make install-proxy-dev` - Install proxy development dependencies with full feature set
- `make install-test-deps` - Install all test dependencies

### Testing
- `make test` - Run all tests
- `make test-unit` - Run unit tests (tests/test_litellm) with 4 parallel workers
- `make test-integration` - Run integration tests (excludes unit tests)
- `pytest tests/` - Direct pytest execution

### Code Quality
- `make lint` - Run all linting (Ruff, MyPy, Black, circular imports, import safety)
- `make format` - Apply Black code formatting
- `make lint-ruff` - Run Ruff linting only
- `make lint-mypy` - Run MyPy type checking only

### Single Test Files
- `poetry run pytest tests/path/to/test_file.py -v` - Run specific test file
- `poetry run pytest tests/path/to/test_file.py::test_function -v` - Run specific test

### Running Scripts
- `poetry run python script.py` - Run Python scripts (use for non-test files)

### GitHub Issue & PR Templates
When contributing to the project, use the appropriate templates:

**Bug Reports** (`.github/ISSUE_TEMPLATE/bug_report.yml`):
- Describe what happened vs. what you expected
- Include relevant log output
- Specify your LiteLLM version

**Feature Requests** (`.github/ISSUE_TEMPLATE/feature_request.yml`):
- Describe the feature clearly
- Explain the motivation and use case

**Pull Requests** (`.github/pull_request_template.md`):
- Add at least 1 test in `tests/litellm/`
- Ensure `make test-unit` passes

## Architecture Overview

LiteLLM is a unified interface for 100+ LLM providers with two main components:

### Core Library (`litellm/`)
- **Main entry point**: `litellm/main.py` - Contains core completion() function
- **Provider implementations**: `litellm/llms/` - Each provider has its own subdirectory
- **Router system**: `litellm/router.py` + `litellm/router_utils/` - Load balancing and fallback logic
- **Type definitions**: `litellm/types/` - Pydantic models and type hints
- **Integrations**: `litellm/integrations/` - Third-party observability, caching, logging
- **Caching**: `litellm/caching/` - Multiple cache backends (Redis, in-memory, S3, etc.)

### Proxy Server (`litellm/proxy/`)
- **Main server**: `proxy_server.py` - FastAPI application
- **Authentication**: `auth/` - API key management, JWT, OAuth2
- **Database**: `db/` - Prisma ORM with PostgreSQL/SQLite support
- **Management endpoints**: `management_endpoints/` - Admin APIs for keys, teams, models
- **Pass-through endpoints**: `pass_through_endpoints/` - Provider-specific API forwarding
- **Guardrails**: `guardrails/` - Safety and content filtering hooks
- **UI Dashboard**: Served from `_experimental/out/` (Next.js build)

## Key Patterns

### Provider Implementation
- Providers inherit from base classes in `litellm/llms/base.py`
- Each provider has transformation functions for input/output formatting
- Support both sync and async operations
- Handle streaming responses and function calling

### Error Handling
- Provider-specific exceptions mapped to OpenAI-compatible errors
- Fallback logic handled by Router system
- Comprehensive logging through `litellm/_logging.py`

### Configuration
- YAML config files for proxy server (see `proxy/example_config_yaml/`)
- Environment variables for API keys and settings
- Database schema managed via Prisma (`proxy/schema.prisma`)

## Development Notes

### Code Style
- Uses Black formatter, Ruff linter, MyPy type checker
- Pydantic v2 for data validation
- Async/await patterns throughout
- Type hints required for all public APIs

### Testing Strategy
- Unit tests in `tests/test_litellm/`
- Integration tests for each provider in `tests/llm_translation/`
- Proxy tests in `tests/proxy_unit_tests/`
- Load tests in `tests/load_tests/`

### Database Migrations
- Prisma handles schema migrations
- Migration files auto-generated with `prisma migrate dev`
- Always test migrations against both PostgreSQL and SQLite

### Enterprise Features
- Enterprise-specific code in `enterprise/` directory
- Optional features enabled via environment variables
- **License bypass enabled** - see Fork Maintenance section below

## Fork Maintenance (OrizonLLM)

This is a fork of [BerriAI/litellm](https://github.com/BerriAI/litellm) with custom modifications.

### CRITICAL: Never Interact with Upstream Repository

**NEVER create issues, PRs, comments, or any interaction on `BerriAI/litellm`.**

- All GitHub operations (issues, PRs, etc.) → `diegocconsolini/orizonllm` ONLY
- The `upstream` remote is for fetching code only, never for pushing or creating issues
- Any visible activity on the upstream repo exposes this fork's existence

### Key Customizations

1. **License Bypass** (`litellm/proxy/auth/litellm_license.py`)
   - `is_premium()` returns `True` unconditionally
   - Enables all enterprise features without license validation
   - **CRITICAL**: Always preserve this file during upstream syncs

2. **Branding** - OrizonLLM rebranding throughout

### Upstream Sync Commands

```bash
# Check for license-related changes BEFORE merging
./scripts/check-license-changes.sh

# Full sync workflow (recommended)
./scripts/sync-upstream.sh

# Manual sync
git fetch upstream
git merge upstream/main --no-commit
git checkout --ours litellm/proxy/auth/litellm_license.py && git add litellm/proxy/auth/litellm_license.py
git checkout --ours README.md && git add README.md
git checkout --ours CLAUDE.md && git add CLAUDE.md
# resolve remaining conflicts, then commit
```

### Protected Files (Never Accept Upstream Version)

| File | Reason |
|------|--------|
| `litellm/proxy/auth/litellm_license.py` | License bypass |
| `README.md` | OrizonLLM branding |
| `CLAUDE.md` | Custom development guide |
| `pyproject.toml` | Package name (merge deps carefully) |
| `litellm/integrations/email_templates/email_footer.py` | OrizonLLM email footer |
| `litellm/integrations/email_templates/user_invitation_email.py` | Custom email branding |
| `litellm/integrations/email_templates/key_created_email.py` | Custom email branding |
| `litellm/integrations/email_templates/key_rotated_email.py` | Custom email branding |
| `litellm/proxy/common_utils/html_forms/ui_login.py` | OrizonLLM login page |
| `litellm/proxy/common_utils/html_forms/cli_sso_success.py` | OrizonLLM SSO success |
| `litellm/proxy/common_utils/html_forms/jwt_display_template.py` | OrizonLLM JWT display |
| `ui/litellm-dashboard/src/app/layout.tsx` | Page title & meta |
| `ui/litellm-dashboard/src/components/navbar.tsx` | Logo size customization |
| `ui/litellm-dashboard/src/app/favicon.ico` | OrizonLLM favicon |
| `litellm/proxy/proxy_server.py` | CORS customization (line 929-937) |
| `litellm/proxy/_experimental/out/**` | UI build artifacts (sync after merge) |

### Documentation

- `UPDATE_PLAN.md` - Full upstream sync procedure and conflict resolution
- `scripts/check-license-changes.sh` - Detect new license checks in upstream
- `scripts/sync-upstream.sh` - Automated sync with protected file handling
- `scripts/sync-ui-build.sh` - Sync UI build after upstream merge

### UI Build Artifacts (CRITICAL)

The `litellm/proxy/_experimental/out/` directory contains pre-built Next.js UI files.
**These files CANNOT be safely merged** - merging causes HTML corruption and 404 errors.

**What happens if merged incorrectly:**
- HTML files get two `<!DOCTYPE>` declarations concatenated
- Chunk hashes mismatch (e.g., `2117-bb4323b3c0b11a1f.js` vs `2117-26a589a1115bdd0a.js`)
- Browser gets 404 errors for JS chunks
- UI completely breaks

**The sync-upstream.sh script handles this automatically by:**
1. Resolving _experimental/out conflicts with `--ours`
2. Copying clean build from `ui/litellm-dashboard/out/`
3. Staging the changes

**If UI breaks after merge, fix with:**
```bash
./scripts/sync-ui-build.sh
git add litellm/proxy/_experimental/out
git commit -m "fix: sync UI build"
```

## Docker Deployment (GHCR + Railway)

### Building and Pushing to GHCR

```bash
# Get current commit SHA for unique tag
SHA=$(git rev-parse --short HEAD)

# Build with commit SHA tag
docker build -t ghcr.io/diegocconsolini/orizonllm:$SHA \
             -t ghcr.io/diegocconsolini/orizonllm:latest \
             -f Dockerfile .

# Push to GitHub Container Registry
docker push ghcr.io/diegocconsolini/orizonllm:$SHA
docker push ghcr.io/diegocconsolini/orizonllm:latest
```

### Non-Interactive Build Script

```bash
# Uses -y flag for non-interactive mode
./scripts/maintenance/build-and-push.sh -y

# Or with specific version
./scripts/maintenance/build-and-push.sh -y v1.60.0
```

### Railway Deployment

```bash
# Update image reference on Railway
railway variables --set "RAILWAY_DOCKER_IMAGE=ghcr.io/diegocconsolini/orizonllm:$SHA" -s orizonllm

# Redeploy with new image
railway service orizonllm && railway redeploy --yes
```

### Railway Service References

Use `${{service.VARIABLE}}` syntax to create service links in Railway:

```bash
# Set DATABASE_URL on pgvector service first
railway variables --set 'DATABASE_URL=postgresql://${{POSTGRES_USER}}:${{POSTGRES_PASSWORD}}@${{RAILWAY_PRIVATE_DOMAIN}}:5432/${{POSTGRES_DB}}' -s pgvector

# Reference it from orizonllm (creates visual link)
railway variables --set 'DATABASE_URL=${{pgvector.DATABASE_URL}}' -s orizonllm
```

### Image Tags Convention

| Tag | Description |
|-----|-------------|
| `latest` | Most recent build |
| `YYYYMMDD` | Date-based tag |
| `{short-sha}` | Git commit SHA (e.g., `d9d5efc617`) |

Always use SHA tags for Railway deployments to ensure the correct version is pulled.

## Vector Stores (pgvector)

OrizonLLM includes a pgvector connector for RAG (Retrieval-Augmented Generation) workflows.

### Architecture

```
OrizonLLM Proxy (api.audividi.ai)
  └─> pgvector Connector (pgvector-connector-production.up.railway.app)
        └─> PostgreSQL + pgvector extension
```

### Connector Repository

- **Fork**: `github.com/diegocconsolini/litellm-pgvector`
- **Image**: `ghcr.io/diegocconsolini/litellm-pgvector:latest`
- **Auto-builds**: On push to main via GitHub Actions

### Railway Configuration

```bash
# pgvector-connector service variables
DATABASE_URL=${{pgvector.DATABASE_URL}}
SERVER_API_KEY=<your-connector-api-key>
EMBEDDING__MODEL=text-embedding-3-small
EMBEDDING__BASE_URL=http://orizonllm.railway.internal:4000
EMBEDDING__API_KEY=<orizonllm-api-key-with-embedding-access>
PORT=8000
```

### Key Endpoints

| Endpoint | Description |
|----------|-------------|
| `POST /v1/vector_stores` | Create vector store |
| `POST /v1/vector_stores/{id}/embeddings` | Add embedding |
| `POST /v1/vector_stores/{id}/search` | Search vectors |
| `GET /health` | Health check |

### Documentation

Full manual: https://github.com/diegocconsolini/orizonllm/wiki/Vector-Stores