# OrizonLLM Rebranding Plan

## Executive Summary

This plan outlines the safe rebranding of LiteLLM references to OrizonLLM throughout the codebase. The approach prioritizes safety by categorizing changes into risk tiers and executing them in phases.

## Risk Assessment Categories

### SAFE TO CHANGE (Low Risk)
User-visible text that doesn't affect functionality:
- UI display text (headers, titles, descriptions)
- Documentation files (README, markdown docs)
- Comments in code
- Log messages (cosmetic)
- HTML page titles

### CHANGE WITH CAUTION (Medium Risk)
References that may have dependencies:
- Environment variable names (`LITELLM_*`)
- Configuration file key names
- API response fields that clients may parse
- Directory/folder names

### DO NOT CHANGE (High Risk - Breaking)
Core framework references that would break the system:
- Python package imports (`import litellm`, `from litellm import`)
- Python module names (`litellm/`)
- Internal function/class names in litellm core
- Database schema references
- PyPI package dependencies

## Scope Analysis

### Files to Modify

#### Phase 1: Documentation & Comments (SAFE)
| File | Changes |
|------|---------|
| `README.md` | Already updated |
| `config.yaml` | Comments only |
| `.env.example` | Comments only |
| `orizon/README.md` | Full rebrand |
| `CONTRIBUTING.md` | Display text |
| `security.md` | Display text |

#### Phase 2: UI Components (SAFE)
| File | Changes |
|------|---------|
| `ui/litellm-dashboard/src/app/page.tsx` | "LiteLLM" → "OrizonLLM" display |
| `ui/litellm-dashboard/src/components/*.tsx` | UI text, tooltips, headers |
| Various dashboard components | Display names only |

#### Phase 3: Environment Variables (MEDIUM RISK)
| Old Name | New Name | Risk |
|----------|----------|------|
| `LITELLM_MASTER_KEY` | `ORIZON_MASTER_KEY` | Medium - widely used |
| `LITELLM_SALT_KEY` | `ORIZON_SALT_KEY` | Medium |

**Strategy**: Keep backwards compatibility by checking for both old and new names.

#### Phase 4: Configuration Keys (MEDIUM RISK)
| File | Key | Notes |
|------|-----|-------|
| `config.yaml` | `litellm_settings` | Used by proxy_server.py |
| `config.yaml` | `litellm_params` | Model configuration |

**Strategy**: These are parsed by the LiteLLM proxy core - DO NOT CHANGE.

### DO NOT CHANGE (Critical)

```
litellm/                    # Python package - breaks imports
├── proxy/                  # Core proxy module
├── llms/                   # LLM handlers
├── integrations/           # Third-party integrations
└── *.py                    # All Python files

ui/litellm-dashboard/       # Folder name - breaks builds
├── package.json            # NPM package references
└── next.config.js          # Build configuration

Docker image references:
- FROM ghcr.io/berriai/litellm...  # Base images
- litellm CLI commands
```

## Execution Plan

### Phase 1: Safe Documentation Changes
**Risk: LOW | Time: 30 min**

1. Update all markdown documentation
2. Update code comments
3. Update HTML page titles
4. Update UI display text only

### Phase 2: UI Rebranding
**Risk: LOW-MEDIUM | Time: 1 hour**

1. Create `orizon-branding.ts` constants file
2. Update dashboard header/footer
3. Update login page branding
4. Update email templates (if any)

### Phase 3: Environment Variable Migration
**Risk: MEDIUM | Time: 2 hours**

1. Add backwards-compatible aliases:
   ```python
   # Support both old and new names
   MASTER_KEY = os.getenv("ORIZON_MASTER_KEY") or os.getenv("LITELLM_MASTER_KEY")
   ```
2. Update .env.example with new names
3. Update docker-compose.yml
4. Add deprecation warnings for old names

### Phase 4: Testing
**Risk: N/A | Time: 1 hour**

1. Run existing test suite
2. Verify health endpoints
3. Verify UI loads correctly
4. Verify API calls work
5. Verify admin login

## What NOT to Change

| Item | Reason |
|------|--------|
| `litellm/` directory | Python package structure |
| `import litellm` statements | Would break all imports |
| `litellm_params` in config | Parsed by proxy core |
| `litellm_settings` in config | Parsed by proxy core |
| `ui/litellm-dashboard/` folder | Build paths depend on it |
| NPM package names | Build system references |
| Database table names | Schema dependencies |
| `litellm` CLI command | Entrypoint in setup.py |

## Recommended Approach

### Minimal Rebrand (Recommended)
Focus only on user-visible elements:
- Dashboard title/header → "OrizonLLM"
- Page titles → "OrizonLLM Admin"
- Documentation → "OrizonLLM"
- Keep all internal references as-is

### Full Rebrand (Not Recommended)
Would require:
- Forking and renaming entire litellm package
- Updating hundreds of import statements
- Breaking compatibility with upstream updates
- Significant ongoing maintenance burden

## Conclusion

**Recommendation**: Proceed with **Minimal Rebrand** (Phases 1-2 only).

This approach:
- Provides clear OrizonLLM branding to users
- Maintains system stability
- Preserves ability to merge upstream fixes
- Minimizes maintenance burden

Environment variable changes (Phase 3) should only be done if absolutely necessary for branding consistency.

---

## Approval

- [ ] Plan reviewed
- [ ] Phase 1 approved
- [ ] Phase 2 approved
- [ ] Phase 3 approved (optional)

**Created**: 2025-12-05
**Author**: Claude Code
