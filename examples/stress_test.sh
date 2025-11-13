#!/bin/bash
# Stress test script for Jiomosa - creates multiple concurrent sessions

set -e

API_BASE="http://localhost:5000"
NUM_SESSIONS=${1:-5}
SESSION_PREFIX="stress_test"

echo "========================================"
echo "   Jiomosa Stress Test"
echo "   Sessions to create: $NUM_SESSIONS"
echo "========================================"
echo ""

# Test websites
declare -a URLS=(
    "https://example.com"
    "https://www.wikipedia.org"
    "https://news.ycombinator.com"
    "https://github.com"
    "https://stackoverflow.com"
)

# Create and load sessions
echo "Creating $NUM_SESSIONS concurrent sessions..."
for i in $(seq 1 $NUM_SESSIONS); do
    SESSION_ID="${SESSION_PREFIX}_${i}"
    URL="${URLS[$((i % ${#URLS[@]}))]}"
    
    echo "[$i/$NUM_SESSIONS] Creating $SESSION_ID and loading $URL"
    
    # Create session
    curl -s -X POST "$API_BASE/api/session/create" \
        -H "Content-Type: application/json" \
        -d "{\"session_id\": \"$SESSION_ID\"}" > /dev/null
    
    # Load URL (in background to parallelize)
    (
        curl -s -X POST "$API_BASE/api/session/$SESSION_ID/load" \
            -H "Content-Type: application/json" \
            -d "{\"url\": \"$URL\"}" > /dev/null
    ) &
    
    # Small delay to avoid overwhelming the service
    sleep 0.5
done

# Wait for all background jobs
echo ""
echo "Waiting for all pages to load..."
wait

# Check active sessions
echo ""
echo "Checking active sessions..."
SESSIONS_INFO=$(curl -s "$API_BASE/api/sessions")
ACTIVE_COUNT=$(echo "$SESSIONS_INFO" | grep -o '"active_sessions":[0-9]*' | grep -o '[0-9]*')
echo "Active sessions: $ACTIVE_COUNT"

# Show session details
echo ""
echo "Session details:"
for i in $(seq 1 $NUM_SESSIONS); do
    SESSION_ID="${SESSION_PREFIX}_${i}"
    INFO=$(curl -s "$API_BASE/api/session/$SESSION_ID/info" 2>/dev/null || echo "{}")
    TITLE=$(echo "$INFO" | grep -o '"title":"[^"]*"' | head -1 | cut -d'"' -f4)
    echo "  $SESSION_ID: $TITLE"
done

# Monitor for a bit
echo ""
echo "Monitoring for 10 seconds..."
sleep 10

# Cleanup
echo ""
echo "Cleaning up sessions..."
for i in $(seq 1 $NUM_SESSIONS); do
    SESSION_ID="${SESSION_PREFIX}_${i}"
    curl -s -X POST "$API_BASE/api/session/$SESSION_ID/close" > /dev/null
    echo "  Closed $SESSION_ID"
done

echo ""
echo "========================================"
echo "Stress test completed!"
echo "Successfully created and cleaned up $NUM_SESSIONS sessions"
echo "========================================"
