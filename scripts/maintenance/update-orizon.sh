#!/bin/bash
#
# update-orizon.sh - Complete OrizonLLM update workflow
#
# This is the main script for updating OrizonLLM. It runs the complete
# workflow: sync upstream, test, build, and push to registry.
#
# Usage: ./scripts/maintenance/update-orizon.sh [version]
# Example: ./scripts/maintenance/update-orizon.sh v1.60.0
#          ./scripts/maintenance/update-orizon.sh
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Target version (optional)
TARGET_VERSION="${1:-main}"

echo -e "${CYAN}"
echo "  ___       _                 _     _     __  __  "
echo " / _ \ _ __(_)_______  _ __  | |   | |   |  \/  | "
echo "| | | | '__| |_  / _ \| '_ \ | |   | |   | |\/| | "
echo "| |_| | |  | |/ / (_) | | | || |___| |___| |  | | "
echo " \___/|_|  |_/___\___/|_| |_||_____|_____|_|  |_| "
echo ""
echo -e "${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}   Complete Update Workflow${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

cd "$REPO_ROOT"

# Show current state
echo -e "${YELLOW}Current State:${NC}"
echo -e "  Repository: $(pwd)"
echo -e "  Branch: $(git branch --show-current)"
echo -e "  Commit: $(git rev-parse --short HEAD)"
echo -e "  Target: ${TARGET_VERSION}"
echo ""

# Menu
echo -e "${YELLOW}What would you like to do?${NC}"
echo ""
echo -e "  ${BLUE}1)${NC} Full update (sync + build + push)"
echo -e "  ${BLUE}2)${NC} Sync upstream only"
echo -e "  ${BLUE}3)${NC} Build and push only"
echo -e "  ${BLUE}4)${NC} Check upstream status"
echo -e "  ${BLUE}5)${NC} View customizations"
echo -e "  ${BLUE}6)${NC} Exit"
echo ""
read -p "Select option [1-6]: " -n 1 -r
echo ""

case $REPLY in
    1)
        echo ""
        echo -e "${CYAN}=== STEP 1/4: Syncing upstream ===${NC}"
        echo ""
        bash "$SCRIPT_DIR/sync-upstream.sh" "$TARGET_VERSION"

        if [ $? -ne 0 ]; then
            echo -e "${RED}Sync failed. Please resolve conflicts and try again.${NC}"
            exit 1
        fi

        echo ""
        echo -e "${CYAN}=== STEP 2/4: Running tests ===${NC}"
        echo ""
        if [ -f "$REPO_ROOT/pytest.ini" ] || [ -d "$REPO_ROOT/tests" ]; then
            echo -e "${YELLOW}Running tests...${NC}"
            if command -v pytest &> /dev/null; then
                pytest tests/ -v --tb=short || {
                    echo -e "${YELLOW}Some tests failed. Continue anyway? (y/N)${NC}"
                    read -n 1 -r
                    echo
                    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                        exit 1
                    fi
                }
            else
                echo -e "${YELLOW}pytest not found, skipping tests${NC}"
            fi
        else
            echo -e "${YELLOW}No tests directory found, skipping${NC}"
        fi

        echo ""
        echo -e "${CYAN}=== STEP 3/4: Building Docker image ===${NC}"
        echo ""
        bash "$SCRIPT_DIR/build-and-push.sh" "$TARGET_VERSION"

        echo ""
        echo -e "${CYAN}=== STEP 4/4: Complete ===${NC}"
        echo ""
        echo -e "${GREEN}Update workflow completed successfully!${NC}"
        ;;

    2)
        echo ""
        bash "$SCRIPT_DIR/sync-upstream.sh" "$TARGET_VERSION"
        ;;

    3)
        echo ""
        bash "$SCRIPT_DIR/build-and-push.sh" "$TARGET_VERSION"
        ;;

    4)
        echo ""
        echo -e "${YELLOW}Checking upstream status...${NC}"
        echo ""

        # Add upstream if needed
        if ! git remote | grep -q "^upstream$"; then
            git remote add upstream git@github.com:BerriAI/litellm.git
        fi

        git fetch upstream --quiet

        CURRENT=$(git rev-parse HEAD)
        UPSTREAM=$(git rev-parse upstream/main)
        BEHIND=$(git rev-list --count HEAD..upstream/main)
        AHEAD=$(git rev-list --count upstream/main..HEAD)

        echo -e "  Current commit:  ${CURRENT:0:12}"
        echo -e "  Upstream commit: ${UPSTREAM:0:12}"
        echo ""
        echo -e "  Commits behind upstream: ${YELLOW}${BEHIND}${NC}"
        echo -e "  Commits ahead (your changes): ${GREEN}${AHEAD}${NC}"
        echo ""

        if [ "$BEHIND" -gt 0 ]; then
            echo -e "${YELLOW}Recent upstream commits:${NC}"
            git log --oneline HEAD..upstream/main | head -10
        else
            echo -e "${GREEN}You are up to date with upstream!${NC}"
        fi
        ;;

    5)
        echo ""
        echo -e "${YELLOW}OrizonLLM Customizations:${NC}"
        echo ""
        if [ -f "$REPO_ROOT/CUSTOMIZATIONS.md" ]; then
            cat "$REPO_ROOT/CUSTOMIZATIONS.md"
        else
            echo -e "${YELLOW}Key modified files:${NC}"
            echo ""
            echo -e "  ${BLUE}Enterprise Unlock:${NC}"
            echo "    litellm/proxy/auth/litellm_license.py"
            echo ""
            echo -e "  ${BLUE}Branding:${NC}"
            echo "    litellm/proxy/logo.jpg"
            echo "    litellm/proxy/common_utils/html_forms/ui_login.py"
            echo "    litellm/proxy/common_utils/html_forms/cli_sso_success.py"
            echo "    litellm/proxy/common_utils/html_forms/jwt_display_template.py"
            echo "    ui/litellm-dashboard/src/app/layout.tsx"
            echo ""
            echo -e "  ${BLUE}Configuration:${NC}"
            echo "    docker-compose.yml"
            echo "    config.yaml"
            echo "    Dockerfile"
        fi
        ;;

    6)
        echo -e "${GREEN}Goodbye!${NC}"
        exit 0
        ;;

    *)
        echo -e "${RED}Invalid option${NC}"
        exit 1
        ;;
esac
