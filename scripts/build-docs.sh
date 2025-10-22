#!/bin/bash
# Build Documentation Site with MkDocs Material
#
# This script builds the documentation static site using MkDocs
# and outputs it to the public_collected/docs directory where
# Django can serve it via WhiteNoise.

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Building Documentation Site${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Get the project root directory
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

echo -e "${BLUE}📁 Project root: ${PROJECT_ROOT}${NC}"
echo ""

# Check if MkDocs is installed
if ! command -v mkdocs &> /dev/null; then
    echo -e "${RED}❌ Error: MkDocs is not installed${NC}"
    echo -e "${BLUE}   Install with: pip install mkdocs mkdocs-material pymdown-extensions${NC}"
    exit 1
fi

echo -e "${BLUE}✅ MkDocs found: $(mkdocs --version)${NC}"
echo ""

# Check if mkdocs.yml exists
if [ ! -f "mkdocs.yml" ]; then
    echo -e "${RED}❌ Error: mkdocs.yml not found${NC}"
    exit 1
fi

echo -e "${BLUE}✅ Configuration found: mkdocs.yml${NC}"
echo ""

# Create output directory if it doesn't exist
mkdir -p public_collected/docs

echo -e "${BLUE}🔨 Building documentation site...${NC}"
echo ""

# Build the documentation
if mkdocs build -d public_collected/docs --clean; then
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}  ✅ Documentation built successfully!${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo -e "${BLUE}📦 Output directory: ${PROJECT_ROOT}/public_collected/docs/${NC}"
    echo ""
    echo -e "${BLUE}To preview locally:${NC}"
    echo -e "   mkdocs serve"
    echo ""
    echo -e "${BLUE}To serve via Django:${NC}"
    echo -e "   Access at /static/docs/ after collectstatic"
    echo ""
else
    echo ""
    echo -e "${RED}========================================${NC}"
    echo -e "${RED}  ❌ Build failed!${NC}"
    echo -e "${RED}========================================${NC}"
    exit 1
fi
