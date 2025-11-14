#!/bin/bash
# Jiomosa Device Simulator Launcher
# This script starts the device simulator for testing website rendering

set -e

echo "============================================================"
echo "  Jiomosa Device Simulator"
echo "============================================================"
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "Error: python3 is not installed"
    exit 1
fi

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Check if virtual environment exists
if [ ! -d "$SCRIPT_DIR/venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$SCRIPT_DIR/venv"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source "$SCRIPT_DIR/venv/bin/activate"

# Install dependencies if needed
if [ ! -f "$SCRIPT_DIR/venv/.deps_installed" ]; then
    echo "Installing dependencies..."
    pip install -q -r "$SCRIPT_DIR/requirements.txt"
    touch "$SCRIPT_DIR/venv/.deps_installed"
fi

# Parse command line arguments
JIOMOSA_SERVER="${JIOMOSA_SERVER:-http://localhost:5000}"
DEVICE_PROFILE="${DEVICE_PROFILE:-threadx_512mb}"
PORT="${PORT:-8000}"

# Check if Jiomosa server is running
echo ""
echo "Checking Jiomosa server at $JIOMOSA_SERVER..."
if curl -s "$JIOMOSA_SERVER/health" > /dev/null; then
    echo "✓ Jiomosa server is running"
else
    echo "✗ Cannot connect to Jiomosa server at $JIOMOSA_SERVER"
    echo ""
    echo "Please start Jiomosa first:"
    echo "  cd $(dirname $SCRIPT_DIR)"
    echo "  docker compose up -d"
    echo ""
    exit 1
fi

echo ""
echo "Starting Device Simulator..."
echo "  Server: $JIOMOSA_SERVER"
echo "  Profile: $DEVICE_PROFILE"
echo "  Port: $PORT"
echo ""
echo "============================================================"
echo "  Open your browser to: http://localhost:$PORT"
echo "============================================================"
echo ""

# Run the simulator
python3 "$SCRIPT_DIR/simulator.py" \
    --server "$JIOMOSA_SERVER" \
    --profile "$DEVICE_PROFILE" \
    --port "$PORT"
