#!/bin/bash
# Comprehensive external website testing script
# Tests various categories of websites to ensure Jiomosa works with different types of content

set -e

echo "========================================"
echo "  External Website Testing Suite"
echo "========================================"
echo ""

BASE_URL="${BASE_URL:-http://localhost:5000}"
DELAY="${DELAY:-3}"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test results
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Function to test a website
test_website() {
    local category="$1"
    local url="$2"
    local session_id="$3"
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Test #$TOTAL_TESTS: $category"
    echo "URL: $url"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    # Create session
    echo -n "Creating session '$session_id'... "
    create_response=$(curl -s -X POST "$BASE_URL/api/session/create" \
        -H "Content-Type: application/json" \
        -d "{\"session_id\": \"$session_id\"}" 2>&1)
    
    if echo "$create_response" | grep -q "success"; then
        echo -e "${GREEN}✓${NC}"
    else
        echo -e "${RED}✗${NC}"
        echo "Error: $create_response"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        return 1
    fi
    
    # Load URL
    echo -n "Loading website... "
    start_time=$(date +%s)
    load_response=$(curl -s -X POST "$BASE_URL/api/session/$session_id/load" \
        -H "Content-Type: application/json" \
        -d "{\"url\": \"$url\"}" 2>&1)
    end_time=$(date +%s)
    load_time=$((end_time - start_time))
    
    if echo "$load_response" | grep -q "success"; then
        echo -e "${GREEN}✓${NC} (${load_time}s)"
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        echo -e "${RED}✗${NC}"
        echo "Error: $load_response"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        # Try to close session anyway
        curl -s -X POST "$BASE_URL/api/session/$session_id/close" > /dev/null 2>&1 || true
        return 1
    fi
    
    # Wait for page to settle
    sleep "$DELAY"
    
    # Get page info
    echo -n "Getting page info... "
    info_response=$(curl -s "$BASE_URL/api/session/$session_id/info" 2>&1)
    
    if echo "$info_response" | grep -q "session_id"; then
        echo -e "${GREEN}✓${NC}"
        
        # Extract and display page title
        title=$(echo "$info_response" | grep -o '"title":"[^"]*"' | head -1 | cut -d'"' -f4 | head -c 60)
        current_url=$(echo "$info_response" | grep -o '"url":"[^"]*"' | head -1 | cut -d'"' -f4)
        
        echo "  Page Title: $title"
        echo "  Current URL: $current_url"
        echo "  Load Time: ${load_time}s"
        echo -e "  View at: ${YELLOW}http://localhost:7900${NC}"
    else
        echo -e "${YELLOW}⚠${NC} (Page loaded but info unavailable)"
    fi
    
    # Close session
    echo -n "Closing session... "
    close_response=$(curl -s -X POST "$BASE_URL/api/session/$session_id/close" 2>&1)
    
    if echo "$close_response" | grep -q "success"; then
        echo -e "${GREEN}✓${NC}"
    else
        echo -e "${YELLOW}⚠${NC} (Session may still be open)"
    fi
    
    echo "Result: ${GREEN}PASSED${NC}"
}

# Check if service is running
echo "Checking service health..."
if ! curl -s -f "$BASE_URL/health" > /dev/null 2>&1; then
    echo -e "${RED}✗ Service not running!${NC}"
    echo "Please start services with: docker compose up -d"
    exit 1
fi
echo -e "${GREEN}✓ Service is healthy${NC}"
echo ""

# Test Categories and Websites
echo "Starting comprehensive website tests..."
echo ""

# Category 1: Simple/Static Websites
test_website "Simple Static Site" "https://example.com" "static_1"
test_website "Info/Landing Page" "https://info.cern.ch" "static_2"

# Category 2: Search Engines
test_website "Search Engine - DuckDuckGo" "https://duckduckgo.com" "search_1"
test_website "Search Engine - Bing" "https://www.bing.com" "search_2"

# Category 3: News Sites
test_website "News Aggregator" "https://news.ycombinator.com" "news_1"
test_website "Tech News" "https://techcrunch.com" "news_2"

# Category 4: Documentation Sites
test_website "Python Documentation" "https://docs.python.org" "docs_1"
test_website "MDN Web Docs" "https://developer.mozilla.org" "docs_2"

# Category 5: Developer Platforms
test_website "GitHub" "https://github.com" "dev_1"
test_website "GitLab" "https://gitlab.com" "dev_2"
test_website "Stack Overflow" "https://stackoverflow.com" "dev_3"

# Category 6: Social Media (non-auth pages)
test_website "Reddit" "https://www.reddit.com" "social_1"
test_website "Product Hunt" "https://www.producthunt.com" "social_2"

# Category 7: Educational Sites
test_website "Wikipedia" "https://www.wikipedia.org" "edu_1"
test_website "Khan Academy" "https://www.khanacademy.org" "edu_2"

# Category 8: Media Sites
test_website "Internet Archive" "https://archive.org" "media_1"
test_website "Vimeo" "https://vimeo.com" "media_2"

# Category 9: E-commerce (home pages)
test_website "eBay" "https://www.ebay.com" "commerce_1"
test_website "Etsy" "https://www.etsy.com" "commerce_2"

# Category 10: Blogs/Content Sites
test_website "Medium" "https://medium.com" "content_1"
test_website "Dev.to" "https://dev.to" "content_2"

# Summary
echo ""
echo "========================================"
echo "  Test Summary"
echo "========================================"
echo "Total Tests:  $TOTAL_TESTS"
echo -e "Passed:       ${GREEN}$PASSED_TESTS${NC}"
echo -e "Failed:       ${RED}$FAILED_TESTS${NC}"
echo ""

if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed!${NC}"
    echo ""
    echo "All external websites loaded successfully."
    echo "The renderer can handle various types of web content."
    exit 0
else
    echo -e "${YELLOW}⚠ Some tests failed${NC}"
    echo ""
    echo "Success Rate: $(($PASSED_TESTS * 100 / $TOTAL_TESTS))%"
    echo ""
    echo "Note: Some failures may be due to:"
    echo "  - Geo-restrictions or rate limiting"
    echo "  - Network timeouts"
    echo "  - Website blocking automated access"
    echo "  - Complex JavaScript requiring more load time"
    exit 1
fi
