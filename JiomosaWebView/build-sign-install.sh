#!/bin/bash
# Quick script to build, sign, and install the APK with platform keys

set -e  # Exit on error

echo "================================================"
echo "Building and Signing APK with Platform Keys"
echo "================================================"

# Navigate to project directory
cd "$(dirname "$0")"

# Build and sign debug APK
echo "→ Building and signing debug APK..."
./gradlew clean signApkWithPlatformKeys

# Get the signed APK path
SIGNED_APK="app/build/outputs/apk/debug/app-debug-signed.apk"

# Check if APK exists
if [ ! -f "$SIGNED_APK" ]; then
    echo "❌ Error: Signed APK not found at $SIGNED_APK"
    exit 1
fi

echo "✅ APK signed successfully: $SIGNED_APK"

# Ask user if they want to install
read -p "Install APK to connected device? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "→ Installing APK..."
    adb install -r "$SIGNED_APK"

    echo "→ Launching app..."
    adb shell am start -n com.jiomosa.webview/.StealthWebViewActivity

    echo "✅ App installed and launched!"
else
    echo "Skipping installation."
fi

echo "================================================"
echo "Done!"
echo "================================================"

