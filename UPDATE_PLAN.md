# OrizonLLM Update Plan: Safely Syncing with Upstream LiteLLM

## Current Situation

- **Your fork point**: `4fffd33ccf36` (from BerriAI/litellm)
- **Your custom commits**: 78 commits (including rebranding to "OrizonLLM")
- **Upstream commits ahead**: 499 commits
- **Upstream remote**: Already configured as `upstream` pointing to `git@github.com:BerriAI/litellm.git`

## Goal

Update your OrizonLLM fork with upstream LiteLLM changes while:
1. Preserving your modifications (rebranding, custom features)
2. Maintaining no direct runtime dependency on upstream
3. Being able to repeat this process for future updates

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
# 1. Create a backup branch of your current state
git checkout main
git branch backup-before-upstream-sync-$(date +%Y%m%d)

# 2. Ensure upstream is configured (already done in your case)
git remote -v
# Should show: upstream git@github.com:BerriAI/litellm.git

# 3. Fetch latest upstream changes
git fetch upstream
```

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

**Files likely to conflict (prioritize YOUR version):**
- `README.md` - Keep your OrizonLLM branding
- `pyproject.toml` - Keep your package name, merge dependency updates
- `litellm/_version.py` - Keep your versioning scheme
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
if git merge upstream/main --no-commit; then
    echo "Merge successful with no conflicts!"
else
    echo ""
    echo "=== CONFLICTS DETECTED ==="
    echo "Resolve conflicts, then run:"
    echo "  git add ."
    echo "  git commit -m 'chore: sync with upstream LiteLLM'"
    echo "  git checkout main && git merge $UPDATE_BRANCH"
    exit 1
fi

echo ""
echo "Review changes with: git diff --staged"
echo "Commit with: git commit -m 'chore: sync with upstream LiteLLM'"
```

---

## Key Files to Watch During Merges

These files are most likely to have conflicts:

| File | Strategy |
|------|----------|
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

## Summary

1. **Always backup first** (`git branch backup-...`)
2. **Use merge, not rebase** for your situation
3. **Resolve conflicts favoring your branding** in identity files
4. **Test thoroughly** before merging to main
5. **Keep the sync script** for future updates
6. **Upstream remote can be added/removed** as needed - it has no runtime impact
