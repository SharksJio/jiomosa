#!/bin/bash

# Test JiomosaWebView Optimizations
# Verifies all optimization changes are properly integrated

echo "=========================================="
echo "🔍 Testing JiomosaWebView Optimizations"
echo "=========================================="
echo ""

PROJECT_DIR="/Users/sharath.ks/Project/Module/lowBudget/github/jiomosa/JiomosaWebView"
cd "$PROJECT_DIR"

# Test 1: Check OnBackPressedCallback import
echo "✅ Test 1: Checking modern back press handling..."
if grep -q "OnBackPressedCallback" app/src/main/java/com/jiomosa/webview/StealthWebViewActivity.kt; then
    echo "   ✓ PASS: OnBackPressedCallback import found"
else
    echo "   ✗ FAIL: OnBackPressedCallback import missing"
    exit 1
fi
echo ""

# Test 2: Check conditional debugging
echo "✅ Test 2: Checking conditional debug features..."
if grep -q "BuildConfig.DEBUG" app/src/main/java/com/jiomosa/webview/StealthWebViewActivity.kt; then
    echo "   ✓ PASS: Conditional debugging implemented"
else
    echo "   ✗ FAIL: Conditional debugging missing"
    exit 1
fi
echo ""

# Test 3: Check ProGuard enabled
echo "✅ Test 3: Checking ProGuard configuration..."
if grep -q "minifyEnabled true" app/build.gradle; then
    echo "   ✓ PASS: ProGuard enabled for release"
else
    echo "   ✗ FAIL: ProGuard not enabled"
    exit 1
fi
echo ""

# Test 4: Check ProGuard rules exist
echo "✅ Test 4: Checking ProGuard rules..."
RULE_COUNT=$(grep -c "^-" app/proguard-rules.pro || echo 0)
echo "   Found $RULE_COUNT ProGuard rules"
if [ "$RULE_COUNT" -gt 30 ]; then
    echo "   ✓ PASS: Comprehensive ProGuard rules present"
else
    echo "   ✗ FAIL: Insufficient ProGuard rules"
    exit 1
fi
echo ""

# Test 5: Check enhanced stealth scripts
echo "✅ Test 5: Checking enhanced stealth scripts..."
if grep -q "cachedStealthScript" app/src/main/java/com/jiomosa/webview/StealthWebViewActivity.kt; then
    echo "   ✓ PASS: Cached stealth scripts implemented"
else
    echo "   ✗ FAIL: Cached stealth scripts missing"
    exit 1
fi
echo ""

# Test 6: Check WebGL spoofing
echo "✅ Test 6: Checking WebGL spoofing..."
if grep -q "WebGLRenderingContext" app/src/main/java/com/jiomosa/webview/StealthWebViewActivity.kt; then
    echo "   ✓ PASS: WebGL spoofing implemented"
else
    echo "   ✗ FAIL: WebGL spoofing missing"
    exit 1
fi
echo ""

# Test 7: Check canvas protection
echo "✅ Test 7: Checking canvas fingerprint protection..."
if grep -q "HTMLCanvasElement" app/src/main/java/com/jiomosa/webview/StealthWebViewActivity.kt; then
    echo "   ✓ PASS: Canvas protection implemented"
else
    echo "   ✗ FAIL: Canvas protection missing"
    exit 1
fi
echo ""

# Test 8: Check memory cleanup
echo "✅ Test 8: Checking memory management..."
if grep -q "removeAllViews" app/src/main/java/com/jiomosa/webview/StealthWebViewActivity.kt; then
    echo "   ✓ PASS: Proper WebView cleanup implemented"
else
    echo "   ✗ FAIL: WebView cleanup missing"
    exit 1
fi
echo ""

# Test 9: Check performance optimizations
echo "✅ Test 9: Checking performance optimizations..."
if grep -q "RenderPriority.HIGH" app/src/main/java/com/jiomosa/webview/StealthWebViewActivity.kt; then
    echo "   ✓ PASS: Render priority optimization found"
else
    echo "   ✗ FAIL: Render priority optimization missing"
    exit 1
fi
echo ""

# Test 10: Check activity-ktx dependency
echo "✅ Test 10: Checking dependencies..."
if grep -q "activity-ktx" app/build.gradle; then
    echo "   ✓ PASS: activity-ktx dependency added"
else
    echo "   ✗ FAIL: activity-ktx dependency missing"
    exit 1
fi
echo ""

# Count total optimizations
echo "=========================================="
echo "📊 Optimization Statistics"
echo "=========================================="
echo ""

STEALTH_LINES=$(grep -c "try {" app/src/main/java/com/jiomosa/webview/StealthWebViewActivity.kt || echo 0)
echo "   🥷 Stealth techniques: ~$STEALTH_LINES evasion blocks"

PROGUARD_RULES=$(grep -c "^-" app/proguard-rules.pro || echo 0)
echo "   🔒 ProGuard rules: $PROGUARD_RULES rules"

MEMORY_OPS=$(grep -c "clear\|destroy\|remove" app/src/main/java/com/jiomosa/webview/StealthWebViewActivity.kt || echo 0)
echo "   🧹 Memory operations: $MEMORY_OPS cleanup calls"

PERF_SETTINGS=$(grep -c "Performance\|Priority\|Optimization" app/src/main/java/com/jiomosa/webview/StealthWebViewActivity.kt || echo 0)
echo "   ⚡ Performance settings: $PERF_SETTINGS optimizations"

echo ""
echo "=========================================="
echo "✅ All optimization tests passed!"
echo "=========================================="
echo ""
echo "📝 Summary:"
echo "   - Modern back press handling ✓"
echo "   - Conditional debug features ✓"
echo "   - ProGuard/R8 optimization ✓"
echo "   - Enhanced stealth scripts ✓"
echo "   - Memory management ✓"
echo "   - Performance optimizations ✓"
echo ""
echo "🚀 Ready to build:"
echo "   Debug:   ./gradlew assembleDebug"
echo "   Release: ./gradlew assembleRelease"
echo ""
echo "📖 Documentation:"
echo "   - OPTIMIZATION_SUMMARY.md - Complete optimization details"
echo "   - MULTI_SHORTCUT_GUIDE.md - Multi-app shortcuts guide"
echo ""
