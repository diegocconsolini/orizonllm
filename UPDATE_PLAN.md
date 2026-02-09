# OrizonLLM Update Plan: Safely Syncing with Upstream LiteLLM

## Current Situation

- **Current version**: v1.81.0 (synced 2026-02-09)
- **Previous version**: v1.80.11 (synced 2025-12-26)
- **Upstream remote**: `upstream` pointing to `https://github.com/BerriAI/litellm.git`

### Sync History

| Date | From | To | Commits | Notes |
|------|------|----|---------|-------|
| 2026-02-09 | v1.80.11 | v1.81.0-stable | ~1200 | A2A agents, MCP global mode, 25% CPU reduction |
| 2025-12-26 | fork point | v1.80.11 | ~499 | Initial upstream sync |

## Goal

Update your OrizonLLM fork with upstream LiteLLM changes while:
1. Preserving your modifications (rebranding, custom features)
2. **Preserving the license bypass** (enterprise features unlocked)
3. Maintaining no direct runtime dependency on upstream
4. Being able to repeat this process for future updates

---

## Strategy: Rebase vs Merge

### Option A: Merge (Recommended for your case)
- **Pros**: Preserves your commit history, easier conflict resolution, safer
- **Cons**: Creates merge commits, history shows both branches

### Option B: Rebase
- **Pros**: Cleaner linear history
- **Cons**: Rewrites history, more complex conflict resolution, risky with 78 commits

**Recommendation**: Use **Merge** since you have significant rebranding changes and many auto-commits.

---

## Step-by-Step Update Procedure

### Phase 1: Preparation (Do Once)

```bash
# 1. Configure the 'ours' merge driver (one-time setup)
git config merge.ours.driver true

# 2. Create a backup branch of your current state
git checkout main
git branch backup-before-upstream-sync-$(date +%Y%m%d)

# 3. Ensure upstream is configured (already done in your case)
git remote -v
# Should show: upstream git@github.com:BerriAI/litellm.git

# 4. Fetch latest upstream changes
git fetch upstream
```

**Note:** The `.gitattributes` file marks protected files with `merge=ours`, which tells git to keep our version during conflicts. The `git config merge.ours.driver true` command enables this driver.

### Phase 2: Create Update Branch

```bash
# 1. Create a new branch for the merge work
git checkout main
git checkout -b update/upstream-sync-$(date +%Y%m%d)

# 2. Check what will change
git log --oneline main..upstream/main | head -50
```

### Phase 3: Merge Upstream Changes

```bash
# 1. Merge upstream/main into your branch
git merge upstream/main --no-commit

# 2. Review conflicts (if any)
git status

# 3. Resolve conflicts carefully:
#    - Keep YOUR changes for branding/custom features
#    - Accept UPSTREAM changes for bug fixes/new features
#    - Manually merge where both sides have valid changes
```

### Phase 4: Conflict Resolution Strategy

#### CRITICAL: Files to ALWAYS keep YOUR version (--ours)

These files contain your customizations and MUST be preserved:

```bash
# License bypass - CRITICAL: keeps enterprise features unlocked
git checkout --ours litellm/proxy/auth/litellm_license.py
git add litellm/proxy/auth/litellm_license.py

# Branding files
git checkout --ours README.md
git checkout --ours CLAUDE.md
git add README.md CLAUDE.md

# Email templates (customized branding)
git checkout --ours litellm/integrations/email_templates/email_footer.py
git checkout --ours litellm/integrations/email_templates/user_invitation_email.py
git checkout --ours litellm/integrations/email_templates/key_created_email.py
git checkout --ours litellm/integrations/email_templates/key_rotated_email.py
git add litellm/integrations/email_templates/*.py

# HTML forms (login, SSO)
git checkout --ours litellm/proxy/common_utils/html_forms/ui_login.py
git checkout --ours litellm/proxy/common_utils/html_forms/cli_sso_success.py
git checkout --ours litellm/proxy/common_utils/html_forms/jwt_display_template.py
git add litellm/proxy/common_utils/html_forms/*.py

# UI dashboard customizations
git checkout --ours ui/litellm-dashboard/src/app/layout.tsx
git checkout --ours ui/litellm-dashboard/src/components/navbar.tsx
git checkout --ours ui/litellm-dashboard/src/app/favicon.ico
git add ui/litellm-dashboard/src/app/layout.tsx ui/litellm-dashboard/src/components/navbar.tsx ui/litellm-dashboard/src/app/favicon.ico
```

**Your license bypass** (`litellm/proxy/auth/litellm_license.py`):
```python
def is_premium(self) -> bool:
    """
    ORIZON: Enterprise features unlocked.
    All premium features are enabled without license validation.
    """
    return True
```

**Upstream's version** does actual validation:
1. Checks `LITELLM_LICENSE` env var
2. Verifies against public key (air-gapped)
3. Falls back to API call to `https://license.litellm.ai`
4. Returns `False` if no valid license

**Your bypass simply returns `True`** - skipping all validation.

This bypasses the license check and enables:
- Tag Budgets
- Audit Logs
- Custom Email Branding
- Allowed Routes per key
- Max Request Size limits
- Callback Controls via headers
- Secret Manager integrations (Google/AWS/HashiCorp)
- SSO features

---

**Files likely to conflict (prioritize YOUR version):**
- `litellm/proxy/auth/litellm_license.py` - **ALWAYS KEEP YOURS** (license bypass)
- `README.md` - Keep your OrizonLLM branding
- `pyproject.toml` - Keep your package name, merge dependency updates
- `litellm/_version.py` - Keep your versioning scheme
- `CLAUDE.md` - Keep yours
- Any files with "OrizonLLM" branding

**Files likely to conflict (prioritize UPSTREAM version):**
- Provider implementations in `litellm/llms/`
- Bug fixes in core logic
- New features you want

**Conflict resolution commands:**
```bash
# Accept your version for a file
git checkout --ours path/to/file

# Accept upstream version for a file
git checkout --theirs path/to/file

# Manual merge (open in editor)
code path/to/conflicting/file
```

#### Quick Resolution Script

Run this after `git merge upstream/main --no-commit` to auto-resolve critical files:

```bash
# Auto-resolve files that MUST keep your version
git checkout --ours litellm/proxy/auth/litellm_license.py 2>/dev/null && git add litellm/proxy/auth/litellm_license.py
git checkout --ours README.md 2>/dev/null && git add README.md
git checkout --ours CLAUDE.md 2>/dev/null && git add CLAUDE.md

echo "Critical files resolved. Review remaining conflicts with: git status"
```

### Phase 5: Testing

```bash
# 1. Run tests to ensure nothing broke
make test-unit

# 2. Run linting
make lint

# 3. Test key functionality manually
poetry run python -c "import litellm; print(litellm.__version__)"
```

### Phase 6: Finalize

```bash
# 1. Commit the merge
git add .
git commit -m "chore: sync with upstream LiteLLM ($(git log -1 --format=%h upstream/main))"

# 2. If tests pass, merge to main
git checkout main
git merge update/upstream-sync-$(date +%Y%m%d)

# 3. Push to your origin
git push origin main
```

---

## Removing Upstream Link (If Desired)

If you want to completely remove the upstream connection after syncing:

```bash
# Remove the upstream remote
git remote remove upstream

# Verify
git remote -v
# Should only show: origin git@github.com:diegocconsolini/orizonllm.git
```

**Note**: You can always re-add it later when you want to sync again:
```bash
git remote add upstream git@github.com:BerriAI/litellm.git
```

---

## Future Update Workflow (Repeatable)

Create this script as `scripts/sync-upstream.sh`:

```bash
#!/bin/bash
set -e

DATE=$(date +%Y%m%d)
BACKUP_BRANCH="backup-before-sync-$DATE"
UPDATE_BRANCH="update/upstream-sync-$DATE"

# Files that MUST always keep our version (license bypass, branding)
PROTECTED_FILES=(
    "litellm/proxy/auth/litellm_license.py"
    "README.md"
    "CLAUDE.md"
)

echo "=== OrizonLLM Upstream Sync ==="

# Ensure we're on main
git checkout main

# Create backup
echo "Creating backup branch: $BACKUP_BRANCH"
git branch $BACKUP_BRANCH

# Add upstream if not exists
if ! git remote | grep -q upstream; then
    echo "Adding upstream remote..."
    git remote add upstream git@github.com:BerriAI/litellm.git
fi

# Fetch upstream
echo "Fetching upstream..."
git fetch upstream

# Show what's new
echo ""
echo "=== New commits from upstream ==="
git log --oneline main..upstream/main | head -20
echo "..."
echo "Total new commits: $(git rev-list --count main..upstream/main)"
echo ""

# Create update branch
git checkout -b $UPDATE_BRANCH

# Attempt merge
echo "Attempting merge..."
git merge upstream/main --no-commit || true

# Auto-resolve protected files (keep ours)
echo ""
echo "=== Auto-resolving protected files (keeping ours) ==="
for file in "${PROTECTED_FILES[@]}"; do
    if git ls-files -u | grep -q "$file"; then
        echo "  Keeping ours: $file"
        git checkout --ours "$file" 2>/dev/null && git add "$file"
    fi
done

# Check for remaining conflicts
if git ls-files -u | grep -v -E "$(IFS=\|; echo "${PROTECTED_FILES[*]}")" | grep -q .; then
    echo ""
    echo "=== REMAINING CONFLICTS ==="
    git ls-files -u | cut -f2 | sort -u
    echo ""
    echo "Resolve remaining conflicts, then run:"
    echo "  git add ."
    echo "  git commit -m 'chore: sync with upstream LiteLLM'"
    echo "  git checkout main && git merge $UPDATE_BRANCH"
else
    echo ""
    echo "All conflicts resolved!"
    echo "Review changes with: git diff --staged"
    echo "Commit with: git commit -m 'chore: sync with upstream LiteLLM'"
fi
```

---

## License Check Monitoring

### Files That Reference the License System

These files contain `premium_user`, `is_premium`, `LicenseCheck`, or license validation logic.
**Monitor these for new license checks when upstream updates:**

#### Core License Files (72 total files reference licensing)

**Main license implementation:**
- `litellm/proxy/auth/litellm_license.py` - **YOUR BYPASS IS HERE**

**Files that CHECK license status (import premium_user or call is_premium):**
```
litellm/proxy/proxy_server.py
litellm/proxy/utils.py
litellm/proxy/auth/auth_utils.py
litellm/proxy/auth/route_checks.py
litellm/proxy/auth/user_api_key_auth.py
litellm/proxy/auth/oauth2_check.py
litellm/proxy/litellm_pre_call_utils.py
litellm/proxy/common_utils/callback_utils.py
litellm/proxy/guardrails/init_guardrails.py
litellm/proxy/hooks/dynamic_rate_limiter.py
litellm/proxy/hooks/dynamic_rate_limiter_v3.py
litellm/proxy/health_endpoints/_health_endpoints.py
litellm/proxy/fine_tuning_endpoints/endpoints.py
litellm/proxy/pass_through_endpoints/pass_through_endpoints.py
litellm/proxy/spend_tracking/spend_management_endpoints.py
litellm/proxy/management_endpoints/key_management_endpoints.py
litellm/proxy/management_endpoints/team_endpoints.py
litellm/proxy/management_endpoints/model_management_endpoints.py
litellm/proxy/management_endpoints/ui_sso.py
litellm/proxy/management_endpoints/common_utils.py
litellm/proxy/management_endpoints/scim/scim_v2.py
litellm/proxy/management_helpers/audit_logs.py
litellm/router_strategy/budget_limiter.py
litellm/secret_managers/google_secret_manager.py
litellm/secret_managers/aws_secret_manager.py
litellm/secret_managers/cyberark_secret_manager.py
litellm/secret_managers/hashicorp_secret_manager.py
litellm/integrations/gcs_bucket/gcs_bucket.py
litellm/integrations/gcs_pubsub/pub_sub.py
litellm/integrations/custom_guardrail.py
litellm/integrations/email_alerting.py
litellm/integrations/azure_storage/azure_storage.py
litellm/integrations/SlackAlerting/slack_alerting.py
enterprise/litellm_enterprise/proxy/proxy_server.py
enterprise/litellm_enterprise/proxy/utils.py
enterprise/litellm_enterprise/proxy/auth/route_checks.py
enterprise/litellm_enterprise/proxy/auth/custom_sso_handler.py
enterprise/litellm_enterprise/proxy/management_endpoints/internal_user_endpoints.py
enterprise/litellm_enterprise/enterprise_callbacks/callback_controls.py
enterprise/litellm_enterprise/enterprise_callbacks/send_emails/base_email.py
enterprise/litellm_enterprise/integrations/custom_guardrail.py
```

### Script: Detect New License Checks

Create `scripts/check-license-changes.sh` to run BEFORE merging:

```bash
#!/bin/bash
# Compares license-related files between your branch and upstream
# Run this BEFORE merging to see if upstream added new license checks

echo "=== License Change Detection ==="
echo ""

# Fetch upstream first
git fetch upstream 2>/dev/null

# Files known to contain license checks
LICENSE_FILES=(
    "litellm/proxy/auth/litellm_license.py"
    "litellm/proxy/proxy_server.py"
    "litellm/proxy/utils.py"
    "litellm/proxy/auth/auth_utils.py"
    "litellm/proxy/auth/route_checks.py"
    "litellm/proxy/litellm_pre_call_utils.py"
    "litellm/router_strategy/budget_limiter.py"
    "litellm/proxy/guardrails/init_guardrails.py"
    "litellm/proxy/management_endpoints/key_management_endpoints.py"
    "litellm/proxy/management_endpoints/team_endpoints.py"
)

echo "Checking for license-related changes in upstream..."
echo ""

CHANGES_FOUND=0

for file in "${LICENSE_FILES[@]}"; do
    # Check if file changed in upstream
    if git diff main..upstream/main --name-only | grep -q "^$file$"; then
        echo ">>> CHANGED: $file"

        # Show specific license-related changes
        echo "    License-related diffs:"
        git diff main..upstream/main -- "$file" | grep -E "premium_user|is_premium|LicenseCheck|not_premium_user|Enterprise.*feature" | head -10
        echo ""
        CHANGES_FOUND=1
    fi
done

# Search for NEW files with license checks
echo ""
echo "Searching for NEW license checks in upstream..."
NEW_LICENSE_REFS=$(git diff main..upstream/main --name-only -- '*.py' | while read f; do
    git show "upstream/main:$f" 2>/dev/null | grep -l -E "premium_user|is_premium\(\)|LicenseCheck" >/dev/null && echo "$f"
done)

if [ -n "$NEW_LICENSE_REFS" ]; then
    echo ">>> Files with potential NEW license checks:"
    echo "$NEW_LICENSE_REFS"
    CHANGES_FOUND=1
fi

echo ""
if [ $CHANGES_FOUND -eq 1 ]; then
    echo "=== ACTION REQUIRED ==="
    echo "Review the above files for new license checks that may need bypassing."
    echo "Your current bypass only covers: litellm/proxy/auth/litellm_license.py"
else
    echo "=== NO LICENSE CHANGES DETECTED ==="
    echo "Safe to merge - no new license checks found in upstream."
fi
```

### Quick One-Liner Check

Run this before any merge to see license-related changes:

```bash
git diff main..upstream/main -- '*.py' | grep -E "premium_user|is_premium|LicenseCheck|not_premium_user" | head -30
```

---

## Key Files to Watch During Merges

These files are most likely to have conflicts:

| File | Strategy |
|------|----------|
| `litellm/proxy/auth/litellm_license.py` | **ALWAYS KEEP YOURS** (license bypass) |
| `README.md` | Keep yours |
| `pyproject.toml` | Merge carefully (keep name, update deps) |
| `CLAUDE.md` | Keep yours |
| `litellm/__init__.py` | Merge carefully |
| `litellm/proxy/proxy_server.py` | Accept upstream, re-apply branding |
| `ui/litellm-dashboard/*` | Accept upstream if you haven't modified |

---

## Rollback Plan

If something goes wrong:

```bash
# Reset to backup
git checkout main
git reset --hard backup-before-upstream-sync-YYYYMMDD

# Or reset to origin
git reset --hard origin/main
```

---

## Quick Reference Commands

```bash
# Check for license changes before merging
./scripts/check-license-changes.sh

# Full sync workflow (recommended)
./scripts/sync-upstream.sh

# Manual quick sync
git fetch upstream
git merge upstream/main --no-commit
git checkout --ours litellm/proxy/auth/litellm_license.py && git add litellm/proxy/auth/litellm_license.py
git checkout --ours README.md && git add README.md
# resolve remaining conflicts...
git commit -m "chore: sync with upstream LiteLLM"
```

---

## Summary

1. **Always backup first** (`git branch backup-...`)
2. **Run license check** before merging (`./scripts/check-license-changes.sh`)
3. **Use merge, not rebase** for your situation
4. **Always keep your version** of `litellm/proxy/auth/litellm_license.py` (license bypass)
5. **Resolve conflicts favoring your branding** in identity files
6. **Test thoroughly** before merging to main
7. **Upstream remote can be added/removed** as needed - it has no runtime impact
