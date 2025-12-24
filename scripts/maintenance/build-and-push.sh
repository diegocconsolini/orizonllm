#!/bin/bash
#
# build-and-push.sh - Build and push OrizonLLM Docker image to registry
#
# This script builds the OrizonLLM Docker image and pushes it to your
# private container registry (GitHub Container Registry or Azure ACR).
#
# Usage: ./scripts/maintenance/build-and-push.sh [OPTIONS] [version]
#
# Options:
#   -y, --yes      Non-interactive mode (auto-confirm all prompts)
#   -h, --help     Show this help message
#
# Examples:
#   ./scripts/maintenance/build-and-push.sh v1.60.0
#   ./scripts/maintenance/build-and-push.sh -y           # Non-interactive with 'latest'
#   ./scripts/maintenance/build-and-push.sh -y v1.60.0   # Non-interactive with version
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ============================================
# CONFIGURATION - Edit these values
# ============================================

# Registry type: "ghcr" (GitHub) or "acr" (Azure) or "dockerhub"
REGISTRY_TYPE="${REGISTRY_TYPE:-ghcr}"

# GitHub Container Registry
GHCR_REGISTRY="ghcr.io"
GHCR_USERNAME="${GHCR_USERNAME:-diegocconsolini}"
GHCR_IMAGE_NAME="orizonllm"

# Azure Container Registry (if using ACR)
ACR_REGISTRY="${ACR_REGISTRY:-yourregistry.azurecr.io}"
ACR_IMAGE_NAME="orizonllm"

# Docker Hub (if using Docker Hub)
DOCKERHUB_USERNAME="${DOCKERHUB_USERNAME:-}"
DOCKERHUB_IMAGE_NAME="orizonllm"

# ============================================
# END CONFIGURATION
# ============================================

# Parse command line arguments
NON_INTERACTIVE=false
VERSION=""

show_help() {
    echo "Usage: $0 [OPTIONS] [version]"
    echo ""
    echo "Options:"
    echo "  -y, --yes      Non-interactive mode (auto-confirm all prompts)"
    echo "  -h, --help     Show this help message"
    echo ""
    echo "Environment variables:"
    echo "  REGISTRY_TYPE    Registry type: ghcr, acr, or dockerhub (default: ghcr)"
    echo "  GHCR_USERNAME    GitHub username (default: diegocconsolini)"
    echo "  GITHUB_TOKEN     GitHub token for authentication"
    echo ""
    echo "Examples:"
    echo "  $0 v1.60.0              # Interactive, specific version"
    echo "  $0 -y                   # Non-interactive, auto-version"
    echo "  $0 -y v1.60.0           # Non-interactive, specific version"
}

while [[ $# -gt 0 ]]; do
    case $1 in
        -y|--yes)
            NON_INTERACTIVE=true
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        -*)
            echo -e "${RED}Unknown option: $1${NC}"
            show_help
            exit 1
            ;;
        *)
            VERSION="$1"
            shift
            ;;
    esac
done

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}   OrizonLLM - Build & Push Tool${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

if [ "$NON_INTERACTIVE" = true ]; then
    echo -e "${YELLOW}Running in non-interactive mode${NC}"
    echo ""
fi

# Get repo root
REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
cd "$REPO_ROOT"

# Determine version
if [ -z "$VERSION" ]; then
    if git describe --tags --exact-match HEAD 2>/dev/null; then
        VERSION=$(git describe --tags --exact-match HEAD)
    else
        VERSION="latest"
    fi
fi

# Also create a date-based tag
DATE_TAG=$(date +%Y%m%d)
SHORT_SHA=$(git rev-parse --short HEAD)

echo -e "${YELLOW}Build Configuration:${NC}"
echo -e "  Registry type: ${REGISTRY_TYPE}"
echo -e "  Version: ${VERSION}"
echo -e "  Date tag: ${DATE_TAG}"
echo -e "  Git SHA: ${SHORT_SHA}"
echo -e "  Non-interactive: ${NON_INTERACTIVE}"
echo ""

# Set registry-specific variables
case "$REGISTRY_TYPE" in
    ghcr)
        REGISTRY="$GHCR_REGISTRY"
        IMAGE_NAME="${GHCR_REGISTRY}/${GHCR_USERNAME}/${GHCR_IMAGE_NAME}"
        echo -e "${YELLOW}Using GitHub Container Registry${NC}"
        echo -e "  Image: ${IMAGE_NAME}"
        ;;
    acr)
        REGISTRY="$ACR_REGISTRY"
        IMAGE_NAME="${ACR_REGISTRY}/${ACR_IMAGE_NAME}"
        echo -e "${YELLOW}Using Azure Container Registry${NC}"
        echo -e "  Image: ${IMAGE_NAME}"
        ;;
    dockerhub)
        REGISTRY="docker.io"
        IMAGE_NAME="${DOCKERHUB_USERNAME}/${DOCKERHUB_IMAGE_NAME}"
        echo -e "${YELLOW}Using Docker Hub${NC}"
        echo -e "  Image: ${IMAGE_NAME}"
        ;;
    *)
        echo -e "${RED}Error: Unknown registry type: ${REGISTRY_TYPE}${NC}"
        echo -e "Set REGISTRY_TYPE to: ghcr, acr, or dockerhub"
        exit 1
        ;;
esac

echo ""

# Check Docker is available
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed or not in PATH${NC}"
    exit 1
fi

# Check if logged in to registry
echo -e "${YELLOW}Step 1: Checking registry authentication...${NC}"

case "$REGISTRY_TYPE" in
    ghcr)
        if ! docker pull "${GHCR_REGISTRY}/library/hello-world" > /dev/null 2>&1; then
            echo -e "${YELLOW}  Not logged in to GitHub Container Registry${NC}"
            echo -e "  Run: ${BLUE}echo \$GITHUB_TOKEN | docker login ghcr.io -u ${GHCR_USERNAME} --password-stdin${NC}"
            echo ""
            if [ "$NON_INTERACTIVE" = true ]; then
                echo -e "${YELLOW}  Continuing anyway (non-interactive mode)...${NC}"
            else
                read -p "Try to continue anyway? (y/N) " -n 1 -r
                echo
                if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                    exit 1
                fi
            fi
        else
            echo -e "${GREEN}  ✓ Authenticated with GitHub Container Registry${NC}"
        fi
        ;;
    acr)
        if ! az acr login --name "${ACR_REGISTRY%%.*}" > /dev/null 2>&1; then
            echo -e "${YELLOW}  Not logged in to Azure Container Registry${NC}"
            echo -e "  Run: ${BLUE}az acr login --name ${ACR_REGISTRY%%.*}${NC}"
            echo ""
            if [ "$NON_INTERACTIVE" = true ]; then
                echo -e "${YELLOW}  Continuing anyway (non-interactive mode)...${NC}"
            else
                read -p "Try to continue anyway? (y/N) " -n 1 -r
                echo
                if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                    exit 1
                fi
            fi
        else
            echo -e "${GREEN}  ✓ Authenticated with Azure Container Registry${NC}"
        fi
        ;;
    dockerhub)
        echo -e "${GREEN}  ✓ Using Docker Hub (assuming logged in)${NC}"
        ;;
esac

# Build the image
echo ""
echo -e "${YELLOW}Step 2: Building Docker image...${NC}"
echo -e "  This may take a few minutes..."
echo ""

BUILD_ARGS=""
BUILD_ARGS="$BUILD_ARGS --build-arg BUILD_VERSION=${VERSION}"
BUILD_ARGS="$BUILD_ARGS --build-arg BUILD_DATE=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
BUILD_ARGS="$BUILD_ARGS --build-arg BUILD_SHA=${SHORT_SHA}"

docker build \
    $BUILD_ARGS \
    -t "${IMAGE_NAME}:${VERSION}" \
    -t "${IMAGE_NAME}:${DATE_TAG}" \
    -t "${IMAGE_NAME}:latest" \
    -f Dockerfile \
    .

if [ $? -eq 0 ]; then
    echo -e "${GREEN}  ✓ Build successful${NC}"
else
    echo -e "${RED}  ✗ Build failed${NC}"
    exit 1
fi

# Show image info
echo ""
echo -e "${YELLOW}Step 3: Image built successfully${NC}"
docker images "${IMAGE_NAME}" --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}"

# Push to registry
echo ""
echo -e "${YELLOW}Step 4: Pushing to registry...${NC}"

DO_PUSH=false
if [ "$NON_INTERACTIVE" = true ]; then
    DO_PUSH=true
else
    read -p "Push images to ${REGISTRY}? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        DO_PUSH=true
    fi
fi

if [ "$DO_PUSH" = true ]; then
    echo -e "  Pushing ${IMAGE_NAME}:${VERSION}..."
    docker push "${IMAGE_NAME}:${VERSION}"

    echo -e "  Pushing ${IMAGE_NAME}:${DATE_TAG}..."
    docker push "${IMAGE_NAME}:${DATE_TAG}"

    echo -e "  Pushing ${IMAGE_NAME}:latest..."
    docker push "${IMAGE_NAME}:latest"

    echo -e "${GREEN}  ✓ All images pushed successfully${NC}"
else
    echo -e "${YELLOW}  Skipping push${NC}"
fi

# Summary
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}   Build Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "Images available:"
echo -e "  ${BLUE}${IMAGE_NAME}:${VERSION}${NC}"
echo -e "  ${BLUE}${IMAGE_NAME}:${DATE_TAG}${NC}"
echo -e "  ${BLUE}${IMAGE_NAME}:latest${NC}"
echo ""
echo -e "To pull and run on another server:"
echo -e "  ${BLUE}docker pull ${IMAGE_NAME}:${VERSION}${NC}"
echo -e "  ${BLUE}docker run -d -p 4000:4000 ${IMAGE_NAME}:${VERSION}${NC}"
echo ""
