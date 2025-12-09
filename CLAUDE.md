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

### Documentation

- `UPDATE_PLAN.md` - Full upstream sync procedure and conflict resolution
- `scripts/check-license-changes.sh` - Detect new license checks in upstream
- `scripts/sync-upstream.sh` - Automated sync with protected file handling