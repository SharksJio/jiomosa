#!/bin/bash

# Jiomosa Android WebApp Launcher Script

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}Jiomosa Android WebApp${NC}"
echo -e "${BLUE}================================${NC}"
echo ""

# Default values
JIOMOSA_SERVER=${JIOMOSA_SERVER:-"http://localhost:5000"}
WEBAPP_PORT=${WEBAPP_PORT:-9000}

# Check if Jiomosa renderer is running
echo -e "${YELLOW}Checking Jiomosa renderer service...${NC}"
if curl -s "${JIOMOSA_SERVER}/health" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Jiomosa renderer is running${NC}"
else
    echo -e "${YELLOW}⚠ Warning: Cannot connect to Jiomosa renderer at ${JIOMOSA_SERVER}${NC}"
    echo "  Make sure Jiomosa is running: docker compose up -d"
    echo ""
fi

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${YELLOW}⚠ Python 3 is not installed${NC}"
    exit 1
fi

# Install dependencies if needed
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv venv
fi

echo -e "${YELLOW}Activating virtual environment...${NC}"
source venv/bin/activate

echo -e "${YELLOW}Installing dependencies...${NC}"
pip install -q -r requirements.txt

echo ""
echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}Starting Android WebApp${NC}"
echo -e "${GREEN}================================${NC}"
echo -e "Jiomosa Server: ${JIOMOSA_SERVER}"
echo -e "WebApp URL: ${GREEN}http://localhost:${WEBAPP_PORT}${NC}"
echo -e "================================"
echo ""
echo -e "${YELLOW}Open the URL above in your browser or Android WebView${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop the server${NC}"
echo ""

# Export environment variables
export JIOMOSA_SERVER="${JIOMOSA_SERVER}"

# Run the webapp
python webapp.py
