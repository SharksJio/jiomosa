#!/bin/bash
# Test rendering of various websites

set -e

echo "=================================="
echo "Testing Multiple Website Scenarios"
echo "=================================="

BASE_URL="http://localhost:5000"

# Array of test websites
declare -a websites=(
    "https://example.com"
    "https://www.wikipedia.org"
    "https://github.com"
    "https://news.google.com"
)

# Test each website
for i in "${!websites[@]}"; do
    url="${websites[$i]}"
    session_id="test_session_$i"
    
    echo ""
    echo "Test $((i+1)): Loading $url"
    echo "--------------------------------"
    
    # Create session
    echo "Creating session $session_id..."
    create_response=$(curl -s -X POST "$BASE_URL/api/session/create" \
        -H "Content-Type: application/json" \
        -d "{\"session_id\": \"$session_id\"}")
    
    if echo "$create_response" | grep -q "success"; then
        echo "✓ Session created"
    else
        echo "✗ Failed to create session"
        echo "$create_response"
        continue
    fi
    
    # Load URL
    echo "Loading $url..."
    load_response=$(curl -s -X POST "$BASE_URL/api/session/$session_id/load" \
        -H "Content-Type: application/json" \
        -d "{\"url\": \"$url\"}")
    
    if echo "$load_response" | grep -q "success"; then
        echo "✓ Website loaded"
    else
        echo "✗ Failed to load website"
        echo "$load_response"
    fi
    
    # Wait a bit for page to settle
    sleep 2
    
    # Get page info
    info_response=$(curl -s "$BASE_URL/api/session/$session_id/info")
    title=$(echo "$info_response" | grep -o '"title":"[^"]*"' | head -1 | cut -d'"' -f4)
    echo "Page title: $title"
    
    # Close session
    echo "Closing session..."
    curl -s -X POST "$BASE_URL/api/session/$session_id/close" > /dev/null
    echo "✓ Session closed"
    
    echo "Test $((i+1)) complete!"
done

echo ""
echo "=================================="
echo "All website tests completed!"
echo "=================================="
