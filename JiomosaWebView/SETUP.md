# Jiomosa Android WebView - Setup Guide

## Prerequisites Installation

Before you begin, ensure you have the following installed:

### 1. Java Development Kit (JDK)

```bash
# Check if JDK is installed
java -version

# Should show Java 11 or later
# If not installed, download from:
# https://www.oracle.com/java/technologies/downloads/
```

### 2. Android Studio

1. Download from: https://developer.android.com/studio
2. Run the installer
3. Follow the setup wizard to install:
   - Android SDK
   - Android SDK Platform
   - Android Virtual Device

### 3. Android SDK Components

Open Android Studio → Settings/Preferences → Appearance & Behavior → System Settings → Android SDK

Install:
- ✅ Android API 34 (Android 14)
- ✅ Android API 21 (Android 5.0) - Minimum
- ✅ Android SDK Build-Tools
- ✅ Android SDK Platform-Tools
- ✅ Android SDK Tools

## Project Setup

### Method 1: Open Existing Project

1. **Open Android Studio**
2. **Click "Open"**
3. **Navigate to** `JiomosaWebView` **folder**
4. **Click "OK"**

Android Studio will:
- Import the project
- Download Gradle wrapper
- Sync dependencies
- Index files

This process may take 5-10 minutes on first run.

### Method 2: Import from Version Control

If cloning from Git:

```bash
git clone https://github.com/SharksJio/jiomosa.git
cd jiomosa/JiomosaWebView
```

Then open in Android Studio as described in Method 1.

## First Build

### Step 1: Gradle Sync

After opening the project:

1. Android Studio will show: **"Gradle files have changed..."**
2. Click **"Sync Now"**
3. Wait for sync to complete (progress shown in bottom status bar)

**Common Issues:**
- **Gradle version mismatch**: Update `gradle-wrapper.properties` if prompted
- **SDK not found**: Install missing SDK versions in SDK Manager
- **Kotlin plugin**: Update Kotlin plugin if prompted

### Step 2: Build Project

1. Click **Build → Make Project** (or press `Ctrl+F9` / `Cmd+F9`)
2. Wait for build to complete
3. Check **Build** tab for any errors

**Build successful** = ✅ Ready to run!

## Running the App

### Option 1: Physical Device

1. **Enable Developer Options** on your Android device:
   - Settings → About Phone → Tap "Build Number" 7 times
   
2. **Enable USB Debugging**:
   - Settings → Developer Options → USB Debugging (ON)
   
3. **Connect Device**:
   - Connect via USB cable
   - Authorize computer on device popup
   
4. **Run**:
   - Click ▶️ **Run** button
   - Select your device
   - Click OK

### Option 2: Android Emulator

1. **Create Virtual Device**:
   - Tools → Device Manager
   - Click **"Create Device"**
   - Select device (e.g., Pixel 6)
   - Select system image (API 34 recommended)
   - Click Finish

2. **Start Emulator**:
   - Click ▶ next to your virtual device
   - Wait for emulator to boot

3. **Run App**:
   - Click ▶️ **Run** button
   - Select emulator
   - Click OK

## Configuration

### Change Target Website

Edit `StealthWebViewActivity.kt`:

```kotlin
companion object {
    // Change this line:
    private const val DEFAULT_URL = "https://your-website.com"
}
```

### Allow Local Server Access

If connecting to local Jiomosa server:

1. **Find your local IP**:
   ```bash
   # On Mac/Linux
   ifconfig | grep "inet "
   
   # On Windows
   ipconfig
   ```

2. **Update** `network_security_config.xml`:
   ```xml
   <domain-config cleartextTrafficPermitted="true">
       <domain includeSubdomains="false">192.168.1.100</domain>
   </domain-config>
   ```

3. **Rebuild the app**

### Connect to Jiomosa Server

To use with Jiomosa cloud rendering:

```kotlin
// In StealthWebViewActivity.kt
companion object {
    private const val DEFAULT_URL = "http://YOUR_JIOMOSA_IP:9000"
}
```

## Testing

### Test Stealth Features

1. **Run the app**
2. **Navigate to test sites**:
   - https://bot.sannysoft.com
   - https://abrahamjuliot.github.io/creepjs/
   
3. **Check results**:
   - Should NOT show "Headless" or "Automation" warnings
   - navigator.webdriver should be undefined

### Debug with Chrome DevTools

1. **Connect device via USB**
2. **Run app** with device connected
3. **Open Chrome** on computer
4. **Navigate to** `chrome://inspect/#devices`
5. **Click "Inspect"** next to Jiomosa WebView
6. **Use DevTools** to debug JavaScript, inspect elements, etc.

## Troubleshooting

### Gradle Sync Failed

```
Error: Could not find com.android.tools.build:gradle:X.X.X
```

**Solution**: Check internet connection and retry sync.

---

```
Error: Minimum supported Gradle version is X.X
```

**Solution**: Update `gradle-wrapper.properties`:
```properties
distributionUrl=https\://services.gradle.org/distributions/gradle-8.2-bin.zip
```

### Build Failed

```
Error: SDK location not found
```

**Solution**: 
1. File → Project Structure → SDK Location
2. Set Android SDK location (usually `~/Android/Sdk` or `C:\Users\YourName\AppData\Local\Android\Sdk`)

---

```
Error: Kotlin plugin version mismatch
```

**Solution**: Update Kotlin plugin:
1. File → Settings → Plugins
2. Search "Kotlin"
3. Update plugin

### App Crashes

**Check Logcat**:
1. Run → Debug
2. View Logcat tab
3. Filter by "StealthWebView"
4. Look for error messages

**Common Crashes**:
- **WebView not initialized**: Ensure `setContentView()` is called before accessing WebView
- **JavaScript disabled**: Check that `javaScriptEnabled = true`
- **Network permission**: Verify `INTERNET` permission in manifest

### WebView Shows Blank Page

1. **Check internet connection**
2. **Check URL is correct** (starts with http:// or https://)
3. **Enable remote debugging** and check console
4. **Check network security config** allows the domain

### Device Not Detected

1. **Check USB cable** (must support data transfer)
2. **Enable USB debugging** in Developer Options
3. **Authorize computer** on device
4. **Try different USB port**
5. **Restart ADB**:
   ```bash
   adb kill-server
   adb start-server
   adb devices
   ```

## Building APK for Distribution

### Debug APK (for testing)

```bash
./gradlew assembleDebug
```

Output: `app/build/outputs/apk/debug/app-debug.apk`

### Release APK (for production)

1. **Create keystore**:
   ```bash
   keytool -genkey -v -keystore jiomosa-release-key.jks \
     -keyalg RSA -keysize 2048 -validity 10000 \
     -alias jiomosa
   ```

2. **Configure signing** in `app/build.gradle`:
   ```gradle
   android {
       signingConfigs {
           release {
               storeFile file("../jiomosa-release-key.jks")
               storePassword "your_password"
               keyAlias "jiomosa"
               keyPassword "your_password"
           }
       }
       buildTypes {
           release {
               signingConfig signingConfigs.release
           }
       }
   }
   ```

3. **Build release**:
   ```bash
   ./gradlew assembleRelease
   ```

Output: `app/build/outputs/apk/release/app-release.apk`

## Next Steps

- ✅ App is running successfully
- 🔗 Connect to Jiomosa server
- 🧪 Test with target websites
- 📱 Build release APK
- 🚀 Deploy to devices

## Support

For issues:
1. Check this guide first
2. Search existing issues: https://github.com/SharksJio/jiomosa/issues
3. Create new issue with:
   - Android Studio version
   - Android version (device/emulator)
   - Error messages
   - Steps to reproduce

Happy coding! 🚀
