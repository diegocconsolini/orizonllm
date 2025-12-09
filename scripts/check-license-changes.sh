#!/bin/bash
# OrizonLLM - License Change Detection Script
# Run this BEFORE merging upstream to detect new license checks
#
# Usage: ./scripts/check-license-changes.sh

set -e

echo "=========================================="
echo "  OrizonLLM License Change Detection"
echo "=========================================="
echo ""

# Fetch upstream first
echo "Fetching upstream..."
git fetch upstream 2>/dev/null || {
    echo "ERROR: Could not fetch upstream. Add it with:"
    echo "  git remote add upstream git@github.com:BerriAI/litellm.git"
    exit 1
}

# Files known to contain license checks
LICENSE_FILES=(
    "litellm/proxy/auth/litellm_license.py"
    "litellm/proxy/proxy_server.py"
    "litellm/proxy/utils.py"
    "litellm/proxy/auth/auth_utils.py"
    "litellm/proxy/auth/route_checks.py"
    "litellm/proxy/auth/user_api_key_auth.py"
    "litellm/proxy/auth/oauth2_check.py"
    "litellm/proxy/litellm_pre_call_utils.py"
    "litellm/proxy/common_utils/callback_utils.py"
    "litellm/proxy/guardrails/init_guardrails.py"
    "litellm/proxy/hooks/dynamic_rate_limiter.py"
    "litellm/proxy/hooks/dynamic_rate_limiter_v3.py"
    "litellm/proxy/health_endpoints/_health_endpoints.py"
    "litellm/proxy/fine_tuning_endpoints/endpoints.py"
    "litellm/proxy/pass_through_endpoints/pass_through_endpoints.py"
    "litellm/proxy/spend_tracking/spend_management_endpoints.py"
    "litellm/proxy/management_endpoints/key_management_endpoints.py"
    "litellm/proxy/management_endpoints/team_endpoints.py"
    "litellm/proxy/management_endpoints/model_management_endpoints.py"
    "litellm/proxy/management_endpoints/ui_sso.py"
    "litellm/proxy/management_endpoints/common_utils.py"
    "litellm/proxy/management_endpoints/scim/scim_v2.py"
    "litellm/proxy/management_helpers/audit_logs.py"
    "litellm/router_strategy/budget_limiter.py"
    "litellm/secret_managers/google_secret_manager.py"
    "litellm/secret_managers/aws_secret_manager.py"
    "litellm/secret_managers/cyberark_secret_manager.py"
    "litellm/secret_managers/hashicorp_secret_manager.py"
    "litellm/integrations/gcs_bucket/gcs_bucket.py"
    "litellm/integrations/gcs_pubsub/pub_sub.py"
    "litellm/integrations/custom_guardrail.py"
    "litellm/integrations/email_alerting.py"
    "litellm/integrations/azure_storage/azure_storage.py"
    "litellm/integrations/SlackAlerting/slack_alerting.py"
    "enterprise/litellm_enterprise/proxy/proxy_server.py"
    "enterprise/litellm_enterprise/proxy/utils.py"
    "enterprise/litellm_enterprise/proxy/auth/route_checks.py"
    "enterprise/litellm_enterprise/proxy/auth/custom_sso_handler.py"
    "enterprise/litellm_enterprise/proxy/management_endpoints/internal_user_endpoints.py"
    "enterprise/litellm_enterprise/enterprise_callbacks/callback_controls.py"
    "enterprise/litellm_enterprise/enterprise_callbacks/send_emails/base_email.py"
    "enterprise/litellm_enterprise/integrations/custom_guardrail.py"
)

# License-related patterns to search for
LICENSE_PATTERNS="premium_user|is_premium|LicenseCheck|not_premium_user|CommonProxyErrors\.not_premium|Enterprise.*feature|LITELLM_LICENSE"

echo "Checking for license-related changes in upstream..."
echo ""

CHANGES_FOUND=0
CRITICAL_CHANGES=0

# Get list of changed files
CHANGED_FILES=$(git diff main..upstream/main --name-only -- '*.py' 2>/dev/null)

echo "--- Checking known license files ---"
echo ""

for file in "${LICENSE_FILES[@]}"; do
    if echo "$CHANGED_FILES" | grep -q "^$file$"; then
        echo ">>> MODIFIED: $file"

        # Check if it's the main license file
        if [[ "$file" == "litellm/proxy/auth/litellm_license.py" ]]; then
            echo "    !!! CRITICAL: Main license file changed !!!"
            echo "    Review changes carefully - your bypass may need updating"
            CRITICAL_CHANGES=1
        fi

        # Show specific license-related changes
        LICENSE_DIFFS=$(git diff main..upstream/main -- "$file" | grep -E "$LICENSE_PATTERNS" | head -5)
        if [ -n "$LICENSE_DIFFS" ]; then
            echo "    License-related changes found:"
            echo "$LICENSE_DIFFS" | sed 's/^/      /'
        fi
        echo ""
        CHANGES_FOUND=1
    fi
done

echo ""
echo "--- Searching for NEW files with license checks ---"
echo ""

# Find new files that contain license checks
for file in $CHANGED_FILES; do
    # Skip already-known license files
    SKIP=0
    for known in "${LICENSE_FILES[@]}"; do
        if [[ "$file" == "$known" ]]; then
            SKIP=1
            break
        fi
    done

    if [[ $SKIP -eq 1 ]]; then
        continue
    fi

    # Check if file contains license patterns
    if git show "upstream/main:$file" 2>/dev/null | grep -qE "$LICENSE_PATTERNS"; then
        echo ">>> NEW LICENSE CHECK IN: $file"
        git show "upstream/main:$file" 2>/dev/null | grep -E "$LICENSE_PATTERNS" | head -3 | sed 's/^/    /'
        echo ""
        CHANGES_FOUND=1
    fi
done

echo ""
echo "=========================================="

if [ $CRITICAL_CHANGES -eq 1 ]; then
    echo "!!! CRITICAL CHANGES DETECTED !!!"
    echo ""
    echo "The main license file (litellm/proxy/auth/litellm_license.py) has changed."
    echo "Your bypass may need to be updated or re-applied after merge."
    echo ""
    echo "Your current bypass:"
    echo "  def is_premium(self) -> bool:"
    echo "      return True"
    echo ""
    echo "Review with:"
    echo "  git diff main..upstream/main -- litellm/proxy/auth/litellm_license.py"
    exit 2
elif [ $CHANGES_FOUND -eq 1 ]; then
    echo "LICENSE-RELATED CHANGES DETECTED"
    echo ""
    echo "Review the above files for new license checks."
    echo "Your current bypass covers: litellm/proxy/auth/litellm_license.py"
    echo ""
    echo "If new checks were added elsewhere, you may need additional bypasses."
    exit 1
else
    echo "NO LICENSE CHANGES DETECTED"
    echo ""
    echo "Safe to merge - no new license checks found in upstream."
    exit 0
fi
