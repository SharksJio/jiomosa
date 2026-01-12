#!/bin/bash
# Test File Attachment Feature
# This script builds and installs the app, then provides testing instructions

set -e

echo "========================================"
echo "JiomosaWebView - File Attachment Test"
echo "========================================"
echo ""

# Navigate to project directory
cd "$(dirname "$0")"

# Check if we're in the right directory
if [ ! -f "app/build.gradle" ]; then
    echo "Error: Must run from JiomosaWebView project root"
    exit 1
fi

# Build the app
echo "📦 Building debug APK..."
./gradlew assembleDebug

if [ $? -ne 0 ]; then
    echo "❌ Build failed!"
    exit 1
fi

echo "✅ Build successful!"
echo ""

# Check if device is connected
echo "📱 Checking for connected devices..."
DEVICES=$(adb devices | grep -v "List" | grep "device" | wc -l)

if [ "$DEVICES" -eq 0 ]; then
    echo "❌ No Android device connected"
    echo "Please connect a device or start an emulator"
    exit 1
fi

echo "✅ Device connected"
echo ""

# Install the app
echo "📲 Installing app..."
adb install -r app/build/outputs/apk/debug/app-debug.apk

if [ $? -ne 0 ]; then
    echo "❌ Installation failed!"
    exit 1
fi

echo "✅ App installed successfully!"
echo ""

# Grant permissions automatically (for testing)
echo "🔐 Granting storage permissions..."
adb shell pm grant com.jiomosa.webview android.permission.READ_EXTERNAL_STORAGE 2>/dev/null || true
adb shell pm grant com.jiomosa.webview android.permission.CAMERA 2>/dev/null || true

# For Android 13+
adb shell pm grant com.jiomosa.webview android.permission.READ_MEDIA_IMAGES 2>/dev/null || true
adb shell pm grant com.jiomosa.webview android.permission.READ_MEDIA_VIDEO 2>/dev/null || true
adb shell pm grant com.jiomosa.webview android.permission.READ_MEDIA_AUDIO 2>/dev/null || true

echo "✅ Permissions granted"
echo ""

# Display testing menu
echo "========================================"
echo "Testing Options:"
echo "========================================"
echo ""
echo "Choose an app to test file attachments:"
echo ""
echo "1. Outlook Mail (Email attachments)"
echo "2. Microsoft Teams (File sharing)"
echo "3. OneDrive (File uploads)"
echo "4. View logs (Monitor file operations)"
echo "5. Exit"
echo ""

while true; do
    read -p "Enter choice (1-5): " choice
    
    case $choice in
        1)
            echo ""
            echo "🚀 Launching Outlook Mail..."
            adb shell am start -n com.jiomosa.webview/.OutlookActivity
            echo ""
            echo "📝 Test Steps:"
            echo "   1. Tap 'New message' to compose email"
            echo "   2. Tap the attachment (📎) icon"
            echo "   3. Select files from storage or camera"
            echo "   4. Verify files are attached"
            echo ""
            ;;
        2)
            echo ""
            echo "🚀 Launching Microsoft Teams..."
            adb shell am start -n com.jiomosa.webview/.TeamsActivity
            echo ""
            echo "📝 Test Steps:"
            echo "   1. Open a chat or channel"
            echo "   2. Click the file upload icon"
            echo "   3. Select files to share"
            echo "   4. Verify files are uploaded"
            echo ""
            ;;
        3)
            echo ""
            echo "🚀 Launching OneDrive..."
            adb shell am start -n com.jiomosa.webview/.OneDriveActivity
            echo ""
            echo "📝 Test Steps:"
            echo "   1. Navigate to a folder"
            echo "   2. Tap the upload (+) button"
            echo "   3. Select files from storage"
            echo "   4. Verify files are uploaded"
            echo ""
            ;;
        4)
            echo ""
            echo "📋 Starting logcat (Ctrl+C to stop)..."
            echo "Looking for file chooser and upload events..."
            echo ""
            adb logcat -s StealthWebView:D WebView:D chromium:I ActivityManager:I
            ;;
        5)
            echo ""
            echo "👋 Goodbye!"
            exit 0
            ;;
        *)
            echo "❌ Invalid choice. Please enter 1-5."
            ;;
    esac
done
