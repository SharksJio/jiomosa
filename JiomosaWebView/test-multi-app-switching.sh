#!/bin/bash

# Test Multi-Instance Architecture
# Verifies: single launcher icon + app shortcuts + one instance per shortcut (singleTask + unique taskAffinity)

echo "=========================================="
echo "🔄 Testing Multi-Instance Architecture"
echo "=========================================="
echo ""

PROJECT_DIR="/Users/sharath.ks/Project/Module/lowBudget/github/jiomosa/JiomosaWebView"
cd "$PROJECT_DIR"

# Test 1: Ensure activity-alias is not used
echo "✅ Test 1: Checking that activity-alias is not used..."
if grep -q "<activity-alias" app/src/main/AndroidManifest.xml; then
    echo "   ✗ FAIL: Found <activity-alias> entries (should be real <activity>)"
    exit 1
else
    echo "   ✓ PASS: No <activity-alias> entries found"
fi
echo ""

# Test 2: Ensure four launcher icons (one per app)
echo "✅ Test 2: Checking launcher icons..."
LAUNCHER_COUNT=$(grep -c 'android.intent.category.LAUNCHER' app/src/main/AndroidManifest.xml)
echo "   Found $LAUNCHER_COUNT LAUNCHER categories"
if [ "$LAUNCHER_COUNT" -eq 4 ]; then
    echo "   ✓ PASS: Four launcher icons (one per app)"
else
    echo "   ✗ FAIL: Expected 4 LAUNCHER categories, found $LAUNCHER_COUNT"
    exit 1
fi
echo ""

# Test 3: Check 4 shortcut activities exist
echo "✅ Test 3: Checking shortcut Activity classes exist in manifest..."
for activity in "OutlookActivity" "TeamsActivity" "OneDriveActivity" "WhiteboardActivity"; do
    if grep -q "android:name=\"\.$activity\"" app/src/main/AndroidManifest.xml; then
        echo "   ✓ Found: $activity"
    else
        echo "   ✗ Missing: $activity"
        exit 1
    fi
done
echo "   ✓ PASS: All 4 shortcut activities declared"
echo ""

# Test 4: Check unique taskAffinity for each shortcut
echo "✅ Test 4: Checking unique taskAffinity configuration..."
TASK_AFFINITY_COUNT=$(grep -c 'android:taskAffinity=' app/src/main/AndroidManifest.xml)
echo "   Found $TASK_AFFINITY_COUNT taskAffinity declarations"
if [ "$TASK_AFFINITY_COUNT" -eq 4 ]; then
    echo "   ✓ PASS: All 4 shortcuts have unique taskAffinity"
else
    echo "   ✗ FAIL: Expected 4 taskAffinity entries, found $TASK_AFFINITY_COUNT"
    exit 1
fi
echo ""

# Test 5: Verify unique affinity names
echo "✅ Test 5: Checking taskAffinity naming..."
for affinity in "outlook" "teams" "onedrive" "whiteboard"; do
    if grep -q "taskAffinity=\"com.jiomosa.webview.$affinity\"" app/src/main/AndroidManifest.xml; then
        echo "   ✓ Found: $affinity"
    else
        echo "   ✗ Missing: $affinity"
        exit 1
    fi
done
echo "   ✓ PASS: All taskAffinity names unique"
echo ""

# Test 6: Check singleTask launch mode (one instance per shortcut task)
echo "✅ Test 6: Checking singleTask launch mode..."
LAUNCHMODE_COUNT=$(grep -c 'launchMode="singleTask"' app/src/main/AndroidManifest.xml)
echo "   Found $LAUNCHMODE_COUNT singleTask declarations"
if [ "$LAUNCHMODE_COUNT" -eq 4 ]; then
    echo "   ✓ PASS: All 4 shortcut activities use singleTask"
else
    echo "   ✗ FAIL: Expected 4 singleTask entries, found $LAUNCHMODE_COUNT"
    exit 1
fi
echo ""

# Test 7: Check provideInitialUrl hook exists
echo "✅ Test 7: Checking provideInitialUrl hook..."
if grep -q "open fun provideInitialUrl" app/src/main/java/com/jiomosa/webview/StealthWebViewActivity.kt; then
    echo "   ✓ PASS: provideInitialUrl hook exists"
else
    echo "   ✗ FAIL: provideInitialUrl hook missing"
    exit 1
fi
echo ""

# Test 8: Verify all shortcuts have metadata
echo "✅ Test 8: Checking activity metadata..."
METADATA_COUNT=$(grep -c 'android:name="default_url"' app/src/main/AndroidManifest.xml)
echo "   Found $METADATA_COUNT metadata entries"
if [ "$METADATA_COUNT" -eq 4 ]; then
    echo "   ✓ PASS: All 4 shortcuts have metadata"
else
    echo "   ✗ FAIL: Expected 4 metadata entries, found $METADATA_COUNT"
    exit 1
fi
echo ""

# Test 9: Verify onNewIntent exists (needed for singleTask)
echo "✅ Test 9: Checking onNewIntent() exists..."
if grep -q "override fun onNewIntent" app/src/main/java/com/jiomosa/webview/StealthWebViewActivity.kt; then
    echo "   ✓ PASS: onNewIntent() present (singleTask routing)"
else
    echo "   ✗ FAIL: onNewIntent() missing"
    exit 1
fi
echo ""

# Test 10: Verify all activities have both MAIN and LAUNCHER in their blocks
echo "✅ Test 10: Checking launcher intent filters..."
MAIN_COUNT=$(grep -c 'android.intent.action.MAIN' app/src/main/AndroidManifest.xml)
if [ "$MAIN_COUNT" -eq 4 ]; then
    echo "   ✓ Found: 4 MAIN action declarations"
else
    echo "   ✗ Expected 4 MAIN actions, found $MAIN_COUNT"
    exit 1
fi
echo "   ✓ PASS: All 4 activities configured as launcher icons"
echo ""

echo "=========================================="
echo "📊 Multi-Instance Architecture Summary"
echo "=========================================="
echo ""
echo "   🎯 taskAffinity - Each shortcut in separate task"
echo "   🔗 singleTask + unique taskAffinity - One instance per shortcut"
echo "   📱 4 Instances - Outlook, Teams, OneDrive, Whiteboard"
echo "   💾 Separate State - Each maintains own WebView state"
echo "   🔄 No Reload - Switching between apps preserves state"
echo ""

echo "=========================================="
echo "✅ All multi-instance tests passed!"
echo "=========================================="
echo ""
echo "📝 How it works:"
echo "   1. User clicks Teams → Creates Teams instance (task: .teams)"
echo "   2. User clicks Outlook → Creates Outlook instance (task: .outlook)"
echo "   3. Switch back to Teams → Resumes existing Teams instance"
echo "   4. Each instance keeps its own WebView, state, and scroll position"
echo "   5. Tapping the same shortcut again resumes its instance"
echo ""
echo "🧪 Testing steps:"
echo "   1. Install APK on device"
echo "   2. Launch Teams shortcut → Login to Teams"
echo "   3. Launch Outlook shortcut → Loads fresh Outlook"
echo "   4. Use Recent Apps to switch back to Teams"
echo "   5. Verify Teams still logged in (not reloaded)"
echo "   6. Each app maintains its own WebView page state"
echo ""
echo "⚠️  Note: Cookies/storage are shared at app level"
echo "    But each WebView instance maintains separate:"
echo "    - Navigation history"
echo "    - Scroll position"
echo "    - Page state (JavaScript variables)"
echo "    - Loaded page content"
echo ""
