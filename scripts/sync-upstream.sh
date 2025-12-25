#!/bin/bash
# OrizonLLM - Upstream Sync Script
# Safely merges upstream LiteLLM changes while preserving your customizations
#
# Usage: ./scripts/sync-upstream.sh

set -e

DATE=$(date +%Y%m%d)
BACKUP_BRANCH="backup-before-sync-$DATE"
UPDATE_BRANCH="update/upstream-sync-$DATE"

# Files that MUST always keep our version (license bypass, branding)
PROTECTED_FILES=(
    "litellm/proxy/auth/litellm_license.py"
    "README.md"
    "CLAUDE.md"
    "UPDATE_PLAN.md"
)

echo "=========================================="
echo "  OrizonLLM Upstream Sync"
echo "=========================================="
echo ""

# Configure the 'ours' merge driver (for .gitattributes merge=ours)
git config merge.ours.driver true 2>/dev/null || true

# Check for uncommitted changes
if ! git diff-index --quiet HEAD --; then
    echo "ERROR: You have uncommitted changes. Commit or stash them first."
    exit 1
fi

# Ensure we're on main
CURRENT_BRANCH=$(git branch --show-current)
if [[ "$CURRENT_BRANCH" != "main" ]]; then
    echo "Switching to main branch..."
    git checkout main
fi

# Create backup
echo "Creating backup branch: $BACKUP_BRANCH"
git branch "$BACKUP_BRANCH" 2>/dev/null || {
    echo "Backup branch already exists. Using existing backup."
}

# Add upstream if not exists
if ! git remote | grep -q upstream; then
    echo "Adding upstream remote..."
    git remote add upstream git@github.com:BerriAI/litellm.git
fi

# Fetch upstream
echo "Fetching upstream..."
git fetch upstream

# Show stats
echo ""
echo "--- Sync Statistics ---"
COMMITS_BEHIND=$(git rev-list --count main..upstream/main)
COMMITS_AHEAD=$(git rev-list --count upstream/main..main)
echo "Commits behind upstream: $COMMITS_BEHIND"
echo "Your custom commits: $COMMITS_AHEAD"
echo ""

if [[ $COMMITS_BEHIND -eq 0 ]]; then
    echo "Already up to date with upstream!"
    exit 0
fi

# Run license check first
echo "--- Running License Change Detection ---"
echo ""
if ./scripts/check-license-changes.sh; then
    echo ""
else
    EXIT_CODE=$?
    if [[ $EXIT_CODE -eq 2 ]]; then
        echo ""
        echo "CRITICAL: License file changed upstream!"
        read -p "Continue anyway? (y/N): " CONTINUE
        if [[ "$CONTINUE" != "y" && "$CONTINUE" != "Y" ]]; then
            echo "Aborted."
            exit 1
        fi
    fi
fi

# Show recent upstream commits
echo ""
echo "--- Recent upstream commits ---"
git log --oneline main..upstream/main | head -20
echo "..."
echo "(showing 20 of $COMMITS_BEHIND commits)"
echo ""

# Create update branch
echo "Creating update branch: $UPDATE_BRANCH"
git checkout -b "$UPDATE_BRANCH" 2>/dev/null || {
    echo "Branch exists. Deleting and recreating..."
    git branch -D "$UPDATE_BRANCH"
    git checkout -b "$UPDATE_BRANCH"
}

# Attempt merge
echo ""
echo "--- Attempting merge ---"
if git merge upstream/main --no-commit --no-ff; then
    echo "Merge successful with no conflicts!"
else
    echo ""
    echo "Conflicts detected. Auto-resolving protected files..."
fi

# Auto-resolve protected files (keep ours)
echo ""
echo "--- Auto-resolving protected files (keeping ours) ---"
for file in "${PROTECTED_FILES[@]}"; do
    if git ls-files -u 2>/dev/null | grep -q "$file"; then
        echo "  Keeping ours: $file"
        git checkout --ours "$file" 2>/dev/null && git add "$file"
    fi
done

# Auto-resolve UI build artifacts (keep ours, then sync from source)
echo ""
echo "--- Syncing UI build artifacts ---"
# First, resolve any _experimental/out conflicts by keeping ours
if git ls-files -u 2>/dev/null | grep -q "_experimental/out"; then
    echo "  Resolving _experimental/out conflicts (keeping ours)..."
    git checkout --ours "litellm/proxy/_experimental/out" 2>/dev/null || true
    git add "litellm/proxy/_experimental/out" 2>/dev/null || true
fi

# Then sync from the source UI build to ensure consistency
if [ -d "ui/litellm-dashboard/out" ]; then
    echo "  Syncing UI from ui/litellm-dashboard/out..."
    rm -rf "litellm/proxy/_experimental/out"
    cp -r "ui/litellm-dashboard/out" "litellm/proxy/_experimental/out"
    git add "litellm/proxy/_experimental/out"
    echo "  UI sync complete"
else
    echo "  WARNING: ui/litellm-dashboard/out not found. Run 'npm run build' in ui/litellm-dashboard after merge."
fi

# Check for remaining conflicts
REMAINING_CONFLICTS=$(git ls-files -u 2>/dev/null | cut -f2 | sort -u)

echo ""
if [ -n "$REMAINING_CONFLICTS" ]; then
    echo "=========================================="
    echo "  REMAINING CONFLICTS"
    echo "=========================================="
    echo ""
    echo "$REMAINING_CONFLICTS"
    echo ""
    echo "Resolve these conflicts manually, then run:"
    echo "  git add ."
    echo "  git commit -m 'chore: sync with upstream LiteLLM'"
    echo "  git checkout main && git merge $UPDATE_BRANCH"
    echo "  git push origin main"
    echo ""
    echo "To abort:"
    echo "  git merge --abort"
    echo "  git checkout main"
    echo "  git branch -D $UPDATE_BRANCH"
else
    echo "=========================================="
    echo "  ALL CONFLICTS RESOLVED"
    echo "=========================================="
    echo ""
    echo "Review staged changes with:"
    echo "  git diff --staged"
    echo ""
    echo "If everything looks good, commit and merge:"
    echo "  git commit -m 'chore: sync with upstream LiteLLM ($(git log -1 --format=%h upstream/main))'"
    echo "  git checkout main && git merge $UPDATE_BRANCH"
    echo "  git push origin main"
fi

echo ""
echo "Backup branch available at: $BACKUP_BRANCH"
