# Jiomosa Android WebView - Stealth Browser

A production-ready Android WebView application with advanced bot detection evasion techniques for accessing websites like Microsoft Outlook that employ automation detection mechanisms.

## 🎯 Overview

This Android app is part of the Jiomosa cloud website rendering platform. It provides a stealth WebView implementation that applies browser fingerprint evasion techniques similar to the server-side Playwright stealth configuration.

## ✨ Features

- **Stealth Mode**: Advanced bot detection evasion
- **Desktop User-Agent**: Spoofs desktop Chrome browser
- **WebDriver Override**: Removes automation detection flags
- **Chrome Object Simulation**: Creates complete `window.chrome` structure
- **Plugin/MIME Type Spoofing**: Simulates real browser plugins
- **WebGL Parameter Override**: Consistent GPU fingerprinting
- **Permissions API Override**: Handles permission queries gracefully
- **Hardware Acceleration**: Optimized rendering performance

## 📋 Requirements

- **Android Studio**: Arctic Fox (2020.3.1) or later
- **Minimum SDK**: API 21 (Android 5.0 Lollipop)
- **Target SDK**: API 34 (Android 14)
- **Gradle**: 8.2+
- **Kotlin**: 1.9.20+

## 🚀 Quick Start

### 1. Open in Android Studio

```bash
cd JiomosaWebView
# Open this folder in Android Studio
```

### 2. Sync Gradle

Android Studio will automatically prompt you to sync Gradle. Click "Sync Now".

### 3. Run the App

1. Connect an Android device or start an emulator
2. Click the "Run" button (▶️) in Android Studio
3. Select your device/emulator

The app will launch and automatically load Microsoft Outlook (https://outlook.office.com/mail) with stealth parameters enabled.

## 📱 Usage

### Basic Usage

The app starts with the default URL (Outlook). To load a different URL:

```kotlin
// From another Activity
val intent = Intent(this, StealthWebViewActivity::class.java)
intent.putExtra("url", "https://your-target-website.com")
startActivity(intent)
```

### Configuration

#### Change Default URL

Edit `StealthWebViewActivity.kt`:

```kotlin
companion object {
    private const val DEFAULT_URL = "https://your-website.com"
}
```

#### Modify User-Agent

Edit `StealthWebViewActivity.kt`:

```kotlin
companion object {
    private const val STEALTH_USER_AGENT = "Your custom User-Agent string"
}
```

#### Network Security (for local Jiomosa server)

Edit `res/xml/network_security_config.xml`:

```xml
<domain-config cleartextTrafficPermitted="true">
    <domain includeSubdomains="true">your-jiomosa-server.com</domain>
</domain-config>
```

## 🛠️ Project Structure

```
JiomosaWebView/
├── app/
│   ├── build.gradle                 # App-level build configuration
│   ├── proguard-rules.pro          # ProGuard rules
│   └── src/
│       └── main/
│           ├── AndroidManifest.xml          # App manifest
│           ├── java/com/jiomosa/webview/
│           │   └── StealthWebViewActivity.kt # Main activity
│           └── res/
│               ├── layout/
│               │   └── activity_stealth_webview.xml  # Layout
│               ├── values/
│               │   ├── strings.xml          # String resources
│               │   ├── colors.xml           # Color resources
│               │   └── themes.xml           # App themes
│               ├── drawable/
│               │   └── progress_bar_gradient.xml     # Progress bar
│               └── xml/
│                   └── network_security_config.xml   # Network config
├── build.gradle                     # Project-level build config
├── settings.gradle                  # Gradle settings
├── gradle.properties                # Gradle properties
└── README.md                        # This file
```

## 🔍 Testing

### Testing Stealth Features

Test the stealth implementation with these websites:

1. **Outlook Mail** (Primary target): https://outlook.office.com/mail
2. **Bot Detection Test**: https://bot.sannysoft.com
3. **CreepJS**: https://abrahamjuliot.github.io/creepjs/
4. **Browser Leaks**: https://browserleaks.com
5. **FingerprintJS**: https://fingerprintjs.github.io/fingerprintjs/

### Remote Debugging

Enable Chrome DevTools for debugging:

1. Connect device via USB with USB debugging enabled
2. Open Chrome on your computer
3. Navigate to `chrome://inspect/#devices`
4. Click "Inspect" next to your WebView

> **Note**: WebView debugging is enabled in the app. For production, set:
> ```kotlin
> WebView.setWebContentsDebuggingEnabled(false)
> ```

## 🔧 Build Variants

### Debug Build

```bash
./gradlew assembleDebug
```

- WebView debugging enabled
- No code obfuscation
- Output: `app/build/outputs/apk/debug/app-debug.apk`

### Release Build

```bash
./gradlew assembleRelease
```

- WebView debugging disabled
- Code obfuscation enabled
- Output: `app/build/outputs/apk/release/app-release-unsigned.apk`

## 📦 Dependencies

```gradle
dependencies {
    // AndroidX Core
    implementation 'androidx.core:core-ktx:1.12.0'
    implementation 'androidx.appcompat:appcompat:1.6.1'
    
    // Material Design
    implementation 'com.google.android.material:material:1.11.0'
    
    // WebKit
    implementation 'androidx.webkit:webkit:1.9.0'
}
```

## 🔐 Security Considerations

### For Development

- Cleartext traffic is allowed for localhost and local servers
- WebView debugging is enabled
- Network security config allows test domains

### For Production

**Before releasing to production:**

1. **Disable WebView Debugging**:
   ```kotlin
   WebView.setWebContentsDebuggingEnabled(false)
   ```

2. **Restrict Cleartext Traffic**:
   - Remove localhost entries from `network_security_config.xml`
   - Only allow HTTPS for production servers

3. **Enable ProGuard/R8**:
   ```gradle
   buildTypes {
       release {
           minifyEnabled true
           shrinkResources true
           proguardFiles getDefaultProguardFile('proguard-android-optimize.txt'), 'proguard-rules.pro'
       }
   }
   ```

4. **Sign Your APK**:
   - Create a keystore
   - Configure signing in `build.gradle`

## 🐛 Troubleshooting

### App Crashes on Start

- Check that minimum SDK is API 21+
- Verify all dependencies are synced
- Check logcat for specific errors

### Website Still Detects Automation

1. Verify stealth scripts are injecting (check logs)
2. Ensure User-Agent is set correctly
3. Test on different Android versions
4. Some sites have advanced detection that may still work

### Network Security Error

- Check `network_security_config.xml` for domain configuration
- Ensure cleartext traffic is allowed for HTTP sites
- For HTTPS sites, verify certificate trust chain

### WebView Not Loading

- Verify internet permission in manifest
- Check network connectivity
- Enable WebView debugging and check console errors

## 📄 License

Part of the Jiomosa project. See main repository for license information.

## 🔗 Related Resources

- [Jiomosa Main Repository](https://github.com/SharksJio/jiomosa)
- [Android WebView Documentation](https://developer.android.com/reference/android/webkit/WebView)
- [Playwright Stealth](https://github.com/AtuboDad/playwright_stealth)

## 👥 Contributing

This is part of the Jiomosa project. Contributions should be made to the main repository.

## 📞 Support

For issues and questions, please use the GitHub issue tracker in the main Jiomosa repository.

---

**Built with ❤️ for accessing websites on any device**
