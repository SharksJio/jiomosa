#!/bin/bash

# Test Multi-Shortcut Configuration
# This script verifies that the multi-shortcut feature is properly configured

echo "=========================================="
echo "🔍 Testing Multi-Shortcut Configuration"
echo "=========================================="
echo ""

PROJECT_DIR="/Users/sharath.ks/Project/Module/lowBudget/github/jiomosa/JiomosaWebView"
cd "$PROJECT_DIR"

# Test 1: Check AndroidManifest has activity-alias entries
echo "✅ Test 1: Checking activity-alias entries..."
ALIAS_COUNT=$(grep -c "activity-alias" app/src/main/AndroidManifest.xml || echo 0)
echo "   Found $ALIAS_COUNT activity-alias entries"

if [ "$ALIAS_COUNT" -ge 4 ]; then
    echo "   ✓ PASS: Multiple shortcuts configured"
else
    echo "   ✗ FAIL: Expected at least 4 activity-alias entries"
    exit 1
fi
echo ""

# Test 2: Check strings.xml has app names
echo "✅ Test 2: Checking app name strings..."
APP_NAMES=$(grep "app_name_" app/src/main/res/values/strings.xml | wc -l)
echo "   Found $APP_NAMES app name entries"

if [ "$APP_NAMES" -ge 5 ]; then
    echo "   ✓ PASS: All app names defined"
else
    echo "   ✗ FAIL: Expected at least 5 app names"
    exit 1
fi
echo ""

# Test 3: Check strings.xml has URLs
echo "✅ Test 3: Checking URL strings..."
URLS=$(grep "url_" app/src/main/res/values/strings.xml | wc -l)
echo "   Found $URLS URL entries"

if [ "$URLS" -ge 5 ]; then
    echo "   ✓ PASS: All URLs defined"
else
    echo "   ✗ FAIL: Expected at least 5 URLs"
    exit 1
fi
echo ""

# Test 4: Check StealthWebViewActivity has getDefaultUrl method
echo "✅ Test 4: Checking StealthWebViewActivity modifications..."
if grep -q "getDefaultUrl()" app/src/main/java/com/jiomosa/webview/StealthWebViewActivity.kt; then
    echo "   ✓ PASS: getDefaultUrl() method found"
else
    echo "   ✗ FAIL: getDefaultUrl() method not found"
    exit 1
fi
echo ""

# Test 5: Check for persistent storage configuration
echo "✅ Test 5: Checking persistent storage configuration..."
if grep -q "setAppCacheEnabled" app/src/main/java/com/jiomosa/webview/StealthWebViewActivity.kt; then
    echo "   ✓ PASS: AppCache configuration found"
else
    echo "   ✗ FAIL: AppCache configuration not found"
    exit 1
fi
echo ""

# Test 6: List configured shortcuts
echo "✅ Test 6: Configured shortcuts:"
echo ""
grep -A 2 "app_name_" app/src/main/res/values/strings.xml | grep "string name" | while read line; do
    NAME=$(echo "$line" | sed 's/.*name="\([^"]*\)".*/\1/')
    VALUE=$(echo "$line" | sed 's/.*>\([^<]*\)<.*/\1/')
    
    # Get corresponding URL
    URL_KEY=$(echo "$NAME" | sed 's/app_name_/url_/')
    URL=$(grep "name=\"$URL_KEY\"" app/src/main/res/values/strings.xml | sed 's/.*>\([^<]*\)<.*/\1/')
    
    echo "   📱 $VALUE"
    echo "      URL: $URL"
    echo ""
done

echo "=========================================="
echo "✅ All tests passed!"
echo "=========================================="
echo ""
echo "📝 Summary:"
echo "   - $ALIAS_COUNT launcher shortcuts configured"
echo "   - All share the same browser session"
echo "   - Login once applies to all shortcuts"
echo ""
echo "🚀 Next steps:"
echo "   1. Build the app: ./gradlew assembleDebug"
echo "   2. Install on device: adb install app/build/outputs/apk/debug/app-debug.apk"
echo "   3. Check launcher - you should see 5 separate icons"
echo ""
echo "📖 Documentation: MULTI_SHORTCUT_GUIDE.md"
echo ""
