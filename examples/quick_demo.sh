#!/bin/bash
# Quick demo script for Jiomosa

set -e

echo "========================================"
echo "   Jiomosa Quick Demo"
echo "========================================"
echo ""

API_BASE="http://localhost:5000"

# Check if service is running
echo "Checking service health..."
if ! curl -s -f "$API_BASE/health" > /dev/null 2>&1; then
    echo "❌ Service not running. Please start with: docker compose up -d"
    exit 1
fi
echo "✓ Service is healthy"
echo ""

# Get service info
echo "Service Information:"
curl -s "$API_BASE/api/info" | python3 -m json.tool
echo ""

# Create a demo session
SESSION_ID="demo_$(date +%s)"
echo "Creating session: $SESSION_ID"
CREATE_RESULT=$(curl -s -X POST "$API_BASE/api/session/create" \
    -H "Content-Type: application/json" \
    -d "{\"session_id\": \"$SESSION_ID\"}")
echo "$CREATE_RESULT" | python3 -m json.tool
echo ""

# Load example.com
echo "Loading https://example.com..."
LOAD_RESULT=$(curl -s -X POST "$API_BASE/api/session/$SESSION_ID/load" \
    -H "Content-Type: application/json" \
    -d '{"url": "https://example.com"}')
echo "$LOAD_RESULT" | python3 -m json.tool
echo ""

# Wait for page to load
echo "Waiting for page to fully load..."
sleep 3

# Get session info
echo "Session Information:"
curl -s "$API_BASE/api/session/$SESSION_ID/info" | python3 -m json.tool
echo ""

# Show viewing options
echo "========================================"
echo "   How to View the Rendered Page"
echo "========================================"
echo ""
echo "Option 1: Android WebApp (Recommended)"
echo "  Open: http://localhost:9000"
echo "  Features: Mobile-friendly, WebSocket streaming, 30 FPS"
echo ""
echo "Option 2: WebSocket Streaming"
echo "  Connect Socket.IO client to: ws://localhost:5000/socket.io/"
echo "  Subscribe to session: $SESSION_ID"
echo ""
echo "Option 3: noVNC (Direct Browser Access - Optional)"
echo "  Open: http://localhost:7900/?autoconnect=1&resize=scale&password=secret"
echo ""
echo "========================================"
echo ""

# Prompt to close
read -p "Press Enter to close the session..."

# Close session
echo "Closing session..."
curl -s -X POST "$API_BASE/api/session/$SESSION_ID/close" | python3 -m json.tool
echo ""

echo "✓ Demo complete!"
