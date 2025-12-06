# OrizonLLM Customizations

This document tracks all modifications made to the LiteLLM codebase in the OrizonLLM fork.

## Summary

| Category | Files Modified | Purpose |
|----------|----------------|---------|
| Enterprise Unlock | 1 | Enable all premium features |
| Branding | 6 | Rebrand to OrizonLLM |
| Configuration | 3 | Custom Docker/deployment setup |

---

## 1. Enterprise Features Unlock

### File: `litellm/proxy/auth/litellm_license.py`

**Change:** Modified `is_premium()` method to always return `True`

```python
def is_premium(self) -> bool:
    """
    ORIZON: Enterprise features unlocked.
    All premium features are enabled without license validation.
    """
    return True
```

**Effect:** Enables all enterprise features without requiring a LiteLLM license:
- SSO (Azure AD, Okta, Google)
- Audit Logs
- Custom Branding
- Tag Budgets
- Admin-only Routes
- OAuth2 Token Validation
- Enforced Params
- Secret Managers (Google, Hashicorp, CyberArk)

---

## 2. Branding Changes

### File: `litellm/proxy/logo.jpg`

**Change:** Replaced LiteLLM logo with Orizon logo
- Original: LiteLLM logo (1000x257)
- New: Orizon logo (1000x1000)
- Source: `LogoFull_Transp_Blue_Black.png` converted to JPEG

### File: `litellm/proxy/common_utils/html_forms/ui_login.py`

**Change:** Updated login form branding
- Title: "LiteLLM Login" → "OrizonLLM Login"
- Heading text updated

### File: `litellm/proxy/common_utils/html_forms/cli_sso_success.py`

**Change:** Updated CLI SSO success page branding
- Title: "LiteLLM" → "OrizonLLM"

### File: `litellm/proxy/common_utils/html_forms/jwt_display_template.py`

**Change:** Updated JWT display template branding
- Title: "LiteLLM" → "OrizonLLM"

### File: `ui/litellm-dashboard/src/app/layout.tsx`

**Change:** Updated dashboard metadata
- Title: "LiteLLM Dashboard" → "OrizonLLM Dashboard"

### File: `ui/litellm-dashboard/out/index.html`

**Change:** Pre-built dashboard with OrizonLLM branding

---

## 3. Configuration Files

### File: `docker-compose.yml`

**Changes:**
- Custom port mappings (4010, 5442, 6390) to avoid conflicts
- PostgreSQL with pgvector extension for semantic cache
- Environment variables for OrizonLLM
- Volume mounts for configuration

### File: `config.yaml`

**Changes:**
- Custom model configurations
- Orizon-specific settings

### File: `Dockerfile`

**Changes:**
- Build configuration for OrizonLLM
- Custom entry points

---

## 4. Privacy/Security Verification

### Verified Safe:
- ✅ License server (`license.litellm.ai`) - Never called (is_premium() returns True)
- ✅ Telemetry flag - Exists but unused
- ✅ GitHub cost map fetching - Safe (BerriAI cannot track)

### External Calls:
- GitHub raw content for model pricing (optional, can be disabled)
- Your configured LLM providers (OpenAI, Anthropic, etc.)

---

## Merge Conflict Risk Assessment

When merging upstream LiteLLM updates, these files may have conflicts:

| File | Risk | Reason |
|------|------|--------|
| `litellm_license.py` | **HIGH** | Core modification |
| `logo.jpg` | LOW | Binary file, just replace |
| `ui_login.py` | MEDIUM | HTML template changes |
| `cli_sso_success.py` | LOW | Rarely changes upstream |
| `jwt_display_template.py` | LOW | Rarely changes upstream |
| `layout.tsx` | MEDIUM | UI framework updates |

---

## Update Procedure

When conflicts occur during upstream merge:

1. **litellm_license.py**: Re-apply the `is_premium()` modification
2. **Branding files**: Check for new text strings, update OrizonLLM branding
3. **logo.jpg**: Just keep our logo (git checkout --ours)

See `scripts/maintenance/` for automated update tools.

---

## Version History

| Date | LiteLLM Version | Changes |
|------|-----------------|---------|
| 2025-12-05 | v1.55.x | Initial fork, enterprise unlock, branding |
| 2025-12-06 | v1.55.x | Added pgvector, logo replacement |

---

*Last updated: 2025-12-06*
