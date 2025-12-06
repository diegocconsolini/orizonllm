#!/bin/bash
#
# sync-upstream.sh - Fetch and merge latest LiteLLM updates
#
# This script fetches the latest changes from the upstream LiteLLM repository
# and attempts to merge them into your OrizonLLM fork.
#
# Usage: ./scripts/maintenance/sync-upstream.sh [version]
# Example: ./scripts/maintenance/sync-upstream.sh v1.60.0
#          ./scripts/maintenance/sync-upstream.sh  (defaults to main branch)
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
UPSTREAM_URL="git@github.com:BerriAI/litellm.git"
UPSTREAM_REMOTE="upstream"
TARGET_BRANCH="${1:-main}"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}   OrizonLLM - Upstream Sync Tool${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if we're in a git repository
if ! git rev-parse --is-inside-work-tree > /dev/null 2>&1; then
    echo -e "${RED}Error: Not inside a git repository${NC}"
    exit 1
fi

# Get repo root
REPO_ROOT=$(git rev-parse --show-toplevel)
cd "$REPO_ROOT"

echo -e "${YELLOW}Step 1: Checking upstream remote...${NC}"

# Add upstream remote if it doesn't exist
if ! git remote | grep -q "^${UPSTREAM_REMOTE}$"; then
    echo -e "  Adding upstream remote: ${UPSTREAM_URL}"
    git remote add "$UPSTREAM_REMOTE" "$UPSTREAM_URL"
    echo -e "${GREEN}  ✓ Upstream remote added${NC}"
else
    echo -e "${GREEN}  ✓ Upstream remote already configured${NC}"
fi

# Show current status
echo ""
echo -e "${YELLOW}Step 2: Checking working directory status...${NC}"
if ! git diff-index --quiet HEAD --; then
    echo -e "${RED}  Warning: You have uncommitted changes${NC}"
    echo -e "  Please commit or stash your changes before syncing"
    echo ""
    git status --short
    echo ""
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo -e "${GREEN}  ✓ Working directory clean${NC}"
fi

# Fetch upstream
echo ""
echo -e "${YELLOW}Step 3: Fetching upstream changes...${NC}"
git fetch "$UPSTREAM_REMOTE" --tags
echo -e "${GREEN}  ✓ Upstream fetched${NC}"

# Show what will be merged
echo ""
echo -e "${YELLOW}Step 4: Analyzing changes...${NC}"

CURRENT_COMMIT=$(git rev-parse HEAD)
UPSTREAM_COMMIT=$(git rev-parse "${UPSTREAM_REMOTE}/${TARGET_BRANCH}" 2>/dev/null || echo "")

if [ -z "$UPSTREAM_COMMIT" ]; then
    echo -e "${RED}  Error: Cannot find ${UPSTREAM_REMOTE}/${TARGET_BRANCH}${NC}"
    echo -e "  Available branches:"
    git branch -r | grep upstream | head -10
    exit 1
fi

# Count commits behind
COMMITS_BEHIND=$(git rev-list --count HEAD.."${UPSTREAM_REMOTE}/${TARGET_BRANCH}")
echo -e "  Current commit: ${CURRENT_COMMIT:0:8}"
echo -e "  Upstream commit: ${UPSTREAM_COMMIT:0:8}"
echo -e "  Commits behind upstream: ${COMMITS_BEHIND}"

if [ "$COMMITS_BEHIND" -eq 0 ]; then
    echo -e "${GREEN}  ✓ Already up to date!${NC}"
    exit 0
fi

# Show files that might conflict (files we've modified)
echo ""
echo -e "${YELLOW}Step 5: Checking potential conflicts...${NC}"
echo -e "  Files modified in OrizonLLM (potential conflicts):"

# List our customized files
CUSTOM_FILES=(
    "litellm/proxy/auth/litellm_license.py"
    "litellm/proxy/logo.jpg"
    "litellm/proxy/common_utils/html_forms/ui_login.py"
    "litellm/proxy/common_utils/html_forms/cli_sso_success.py"
    "litellm/proxy/common_utils/html_forms/jwt_display_template.py"
    "ui/litellm-dashboard/src/app/layout.tsx"
)

CONFLICT_FILES=()
for file in "${CUSTOM_FILES[@]}"; do
    if git diff --name-only "${UPSTREAM_REMOTE}/${TARGET_BRANCH}" -- "$file" 2>/dev/null | grep -q .; then
        echo -e "    ${YELLOW}⚠ $file${NC} (modified in both)"
        CONFLICT_FILES+=("$file")
    fi
done

if [ ${#CONFLICT_FILES[@]} -eq 0 ]; then
    echo -e "    ${GREEN}✓ No conflicts expected${NC}"
fi

# Confirm merge
echo ""
echo -e "${YELLOW}Step 6: Ready to merge...${NC}"
echo -e "  This will merge ${COMMITS_BEHIND} commits from upstream/${TARGET_BRANCH}"
echo ""
read -p "Proceed with merge? (y/N) " -n 1 -r
echo

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Merge cancelled${NC}"
    exit 0
fi

# Perform merge
echo ""
echo -e "${YELLOW}Step 7: Merging upstream changes...${NC}"

if git merge "${UPSTREAM_REMOTE}/${TARGET_BRANCH}" --no-edit; then
    echo -e "${GREEN}  ✓ Merge successful!${NC}"

    # Show summary
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}   Sync Complete!${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo -e "Next steps:"
    echo -e "  1. Review changes: ${BLUE}git log --oneline -10${NC}"
    echo -e "  2. Run tests: ${BLUE}pytest tests/ -v${NC}"
    echo -e "  3. Build image: ${BLUE}./scripts/maintenance/build-and-push.sh${NC}"
    echo ""
else
    echo -e "${RED}  ✗ Merge conflicts detected${NC}"
    echo ""
    echo -e "Conflicting files:"
    git diff --name-only --diff-filter=U
    echo ""
    echo -e "${YELLOW}To resolve:${NC}"
    echo -e "  1. Edit the conflicting files"
    echo -e "  2. Run: ${BLUE}git add <resolved-file>${NC}"
    echo -e "  3. Run: ${BLUE}git commit${NC}"
    echo ""
    echo -e "${YELLOW}To abort merge:${NC}"
    echo -e "  Run: ${BLUE}git merge --abort${NC}"
    exit 1
fi
