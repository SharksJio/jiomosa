# Quick Start - APK Signing

## ⚡ Fastest Way to Sign APK

### Using the Shell Script (Recommended)
```bash
./build-sign-install.sh
```
This script will:
1. Clean the project
2. Build the debug APK
3. Sign it with platform keys
4. Ask if you want to install to device
5. Launch the app

### Using Gradle Directly

**Debug APK:**
```bash
./gradlew signApkWithPlatformKeys
```

**Release APK:**
```bash
./gradlew signReleaseApkWithPlatformKeys
```

## 📦 Output Locations

After running the signing task:

- **Debug**: `app/build/outputs/apk/debug/app-debug-signed.apk`
- **Release**: `app/build/outputs/apk/release/app-release-signed.apk`

## 📱 Install to Device

```bash
# Debug
adb install -r app/build/outputs/apk/debug/app-debug-signed.apk

# Release
adb install -r app/build/outputs/apk/release/app-release-signed.apk
```

## 🎯 All-in-One Command

Build, sign, install, and launch in one command:

```bash
./gradlew clean signApkWithPlatformKeys && \
  adb install -r app/build/outputs/apk/debug/app-debug-signed.apk && \
  adb shell am start -n com.jiomosa.webview/.StealthWebViewActivity
```

## 🔍 Verify Signature

```bash
apksigner verify --verbose app/build/outputs/apk/debug/app-debug-signed.apk
```

## 📚 Full Documentation

For detailed information, see:
- **APK_SIGNING.md** - Complete signing guide
- **build.gradle** - Task implementation

## ⚙️ Configuration

Platform keys location (configured in `app/build.gradle`):
- Key: `/Users/sharath.ks/Project/tools/PlatformSign/keys/platform.pk8`
- Cert: `/Users/sharath.ks/Project/tools/PlatformSign/keys/platform.x509.pem`

## 🆘 Troubleshooting

**Problem:** `apksigner: command not found`
**Solution:** Add to PATH:
```bash
export PATH=$PATH:$HOME/Library/Android/sdk/build-tools/35.0.1
```

**Problem:** Keys not found
**Solution:** Check paths in `app/build.gradle` and verify files exist

---

**That's it!** 🎉 Just run `./build-sign-install.sh` to get started.

