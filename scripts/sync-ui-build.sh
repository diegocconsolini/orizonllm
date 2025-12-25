#!/bin/bash
# OrizonLLM - Sync UI Build Script
# Copies the UI build from ui/litellm-dashboard/out to litellm/proxy/_experimental/out
#
# This MUST be run after upstream merges to ensure UI consistency.
# The _experimental/out directory contains pre-built Next.js files that cannot
# be safely merged - merging causes hash mismatches and 404 errors.
#
# Usage: ./scripts/sync-ui-build.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

UI_SOURCE="$REPO_ROOT/ui/litellm-dashboard/out"
UI_TARGET="$REPO_ROOT/litellm/proxy/_experimental/out"

echo "=========================================="
echo "  OrizonLLM UI Build Sync"
echo "=========================================="
echo ""

# Verify source exists
if [ ! -d "$UI_SOURCE" ]; then
    echo "ERROR: UI source not found: $UI_SOURCE"
    echo ""
    echo "You may need to build the UI first:"
    echo "  cd ui/litellm-dashboard && npm install && npm run build"
    exit 1
fi

# Count files
SOURCE_FILES=$(find "$UI_SOURCE" -type f | wc -l)
echo "Source: $UI_SOURCE ($SOURCE_FILES files)"
echo "Target: $UI_TARGET"
echo ""

# Verify source is not corrupted (should have exactly 1 DOCTYPE per HTML file)
echo "Checking source integrity..."
CORRUPTED=0
for html in "$UI_SOURCE"/*.html; do
    if [ -f "$html" ]; then
        DOCTYPE_COUNT=$(grep -c "<!DOCTYPE" "$html" 2>/dev/null || echo 0)
        if [ "$DOCTYPE_COUNT" -gt 1 ]; then
            echo "  WARNING: Corrupted file (multiple DOCTYPEs): $html"
            CORRUPTED=1
        fi
    fi
done

if [ "$CORRUPTED" -eq 1 ]; then
    echo ""
    echo "ERROR: Source UI files are corrupted. Rebuild the UI first:"
    echo "  cd ui/litellm-dashboard && npm run build"
    exit 1
fi
echo "  Source files OK"
echo ""

# Remove old target
if [ -d "$UI_TARGET" ]; then
    echo "Removing old target directory..."
    rm -rf "$UI_TARGET"
fi

# Copy new build
echo "Copying UI build..."
cp -r "$UI_SOURCE" "$UI_TARGET"

# Verify copy
TARGET_FILES=$(find "$UI_TARGET" -type f | wc -l)
echo ""
echo "=========================================="
echo "  UI Sync Complete"
echo "=========================================="
echo ""
echo "Copied $TARGET_FILES files to $UI_TARGET"
echo ""
echo "Don't forget to commit the changes:"
echo "  git add litellm/proxy/_experimental/out"
echo "  git commit -m 'chore: sync UI build after upstream merge'"
