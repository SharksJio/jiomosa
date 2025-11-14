#!/bin/bash
# Quick demo script for Jiomosa Device Simulator
# This script demonstrates the complete workflow

set -e

echo "============================================================"
echo "  Jiomosa Device Simulator - Quick Demo"
echo "============================================================"
echo ""

# Check if Jiomosa is running
if ! curl -s http://localhost:5000/health > /dev/null 2>&1; then
    echo "Error: Jiomosa server is not running"
    echo "Please start it first: docker compose up -d"
    exit 1
fi

echo "✓ Jiomosa server is running"
echo ""

# Check if simulator is running
if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "Starting device simulator..."
    cd "$(dirname "$0")"
    ./run_simulator.sh &
    SIMULATOR_PID=$!
    sleep 10
    echo "✓ Device simulator started (PID: $SIMULATOR_PID)"
else
    echo "✓ Device simulator is already running"
fi

echo ""
echo "============================================================"
echo "  Demo Instructions"
echo "============================================================"
echo ""
echo "1. Open your browser to: http://localhost:8000"
echo ""
echo "2. In the simulator interface:"
echo "   - Click the '➕ New Session' button"
echo "   - Enter a URL or click a quick action button"
echo "   - Click '🚀 Load Website'"
echo "   - Watch the website render in the device screen!"
echo ""
echo "3. Try different device profiles using the dropdown:"
echo "   - ThreadX RTOS (512MB) - embedded devices"
echo "   - IoT Device (256MB) - constrained IoT"
echo "   - Thin Client (1GB) - kiosks"
echo "   - Legacy System (2GB) - older computers"
echo ""
echo "4. Quick test websites to try:"
echo "   - Example.com (simple)"
echo "   - Wikipedia (complex)"
echo "   - Hacker News (minimalist)"
echo "   - GitHub (modern)"
echo ""
echo "============================================================"
echo ""
echo "Key Features:"
echo "  ✓ No browser UI visible - only website content"
echo "  ✓ Multiple device profiles"
echo "  ✓ Real-time streaming"
echo "  ✓ Automatic session keepalive"
echo ""
echo "Press Ctrl+C to stop"
echo "============================================================"
echo ""

# Keep script running
if [ -n "$SIMULATOR_PID" ]; then
    wait $SIMULATOR_PID
else
    # If simulator was already running, just wait
    tail -f /dev/null
fi
