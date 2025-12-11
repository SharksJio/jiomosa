# APK Signing with Platform Keys

## Overview

Custom Gradle tasks have been added to sign the APK with platform keys using `apksigner`.

## Prerequisites

1. **apksigner tool** must be installed and available in your PATH
   - Usually located at: `$ANDROID_HOME/build-tools/<version>/apksigner`
   - Add to PATH or use full path

2. **Platform keys** must exist at:
   - Key: `/Users/sharath.ks/Project/tools/PlatformSign/keys/platform.pk8`
   - Certificate: `/Users/sharath.ks/Project/tools/PlatformSign/keys/platform.x509.pem`

## Available Tasks

### 1. Sign Debug APK
```bash
./gradlew signApkWithPlatformKeys
```

**What it does:**
- Builds the debug APK (`assembleDebug`)
- Signs it with platform keys using apksigner
- Verifies the signature
- Output: `app/build/outputs/apk/debug/app-debug-signed.apk`

### 2. Sign Release APK
```bash
./gradlew signReleaseApkWithPlatformKeys
```

**What it does:**
- Builds the release APK (`assembleRelease`)
- Signs it with platform keys using apksigner
- Verifies the signature
- Output: `app/build/outputs/apk/release/app-release-signed.apk`

## Signing Configuration

The tasks use the following apksigner parameters:

```bash
apksigner sign \
  --key /Users/sharath.ks/Project/tools/PlatformSign/keys/platform.pk8 \
  --cert /Users/sharath.ks/Project/tools/PlatformSign/keys/platform.x509.pem \
  --v1-signing-enabled true \
  --v2-signing-enabled true \
  --v3-signing-enabled true \
  --v4-signing-enabled false \
  <apk-file>
```

### Signature Scheme Details

- **v1 (JAR signing)**: Enabled ✅ - For Android 4.4 and older compatibility
- **v2 (APK Signature Scheme v2)**: Enabled ✅ - For Android 7.0+
- **v3 (APK Signature Scheme v3)**: Enabled ✅ - For Android 9.0+ (supports key rotation)
- **v4 (APK Signature Scheme v4)**: Disabled ❌ - Not needed for most use cases

## Task Features

### Automatic Validation
- ✅ Checks if platform keys exist before signing
- ✅ Checks if APK was built successfully
- ✅ Verifies signature after signing
- ✅ Detailed console output with progress

### Console Output Example
```
================================================
Signing APK with Platform Keys
================================================
Input APK:  /path/to/app-debug.apk
Output APK: /path/to/app-debug-signed.apk
Key:        /Users/sharath.ks/Project/tools/PlatformSign/keys/platform.pk8
Cert:       /Users/sharath.ks/Project/tools/PlatformSign/keys/platform.x509.pem
================================================
✅ APK signed successfully!
Signed APK: /path/to/app-debug-signed.apk
================================================
```

## Usage Examples

### Basic Usage
```bash
# Sign debug APK
./gradlew signApkWithPlatformKeys

# Sign release APK
./gradlew signReleaseApkWithPlatformKeys
```

### Clean Build and Sign
```bash
# Clean, build, and sign debug APK
./gradlew clean signApkWithPlatformKeys

# Clean, build, and sign release APK
./gradlew clean signReleaseApkWithPlatformKeys
```

### Install Signed APK
```bash
# Build, sign, and install debug APK
./gradlew signApkWithPlatformKeys && adb install -r app/build/outputs/apk/debug/app-debug-signed.apk

# Build, sign, and install release APK
./gradlew signReleaseApkWithPlatformKeys && adb install -r app/build/outputs/apk/release/app-release-signed.apk
```

## Verify Signature Manually

To manually verify the APK signature:

```bash
# Verify debug APK
apksigner verify --verbose app/build/outputs/apk/debug/app-debug-signed.apk

# Verify release APK
apksigner verify --verbose app/build/outputs/apk/release/app-release-signed.apk

# Check signature details
apksigner verify --print-certs app/build/outputs/apk/debug/app-debug-signed.apk
```

## Troubleshooting

### Error: "apksigner: command not found"

**Solution:** Add Android SDK build-tools to your PATH:

```bash
# Add to ~/.zshrc or ~/.bash_profile
export ANDROID_HOME=$HOME/Library/Android/sdk
export PATH=$PATH:$ANDROID_HOME/build-tools/34.0.0
```

Then reload:
```bash
source ~/.zshrc  # or source ~/.bash_profile
```

### Error: "Platform key not found"

**Solution:** Verify the key paths in `app/build.gradle`:

```groovy
def keystorePath = '/Users/sharath.ks/Project/tools/PlatformSign/keys'
def platformKey = "${keystorePath}/platform.pk8"
def platformCert = "${keystorePath}/platform.x509.pem"
```

Update these paths if your keys are in a different location.

### Error: "APK not found"

**Solution:** Make sure the APK was built successfully:

```bash
# For debug
./gradlew assembleDebug

# For release
./gradlew assembleRelease
```

Then run the signing task again.

## Customization

### Change Key Location

Edit `app/build.gradle` and update the `keystorePath`:

```groovy
def keystorePath = '/path/to/your/keys'
```

### Add Custom Signing Task

To create a custom signing task for a different build variant:

```groovy
task signCustomApkWithPlatformKeys(type: Exec) {
    group = 'signing'
    description = 'Sign custom APK variant with platform keys'
    
    def keystorePath = '/Users/sharath.ks/Project/tools/PlatformSign/keys'
    def platformKey = "${keystorePath}/platform.pk8"
    def platformCert = "${keystorePath}/platform.x509.pem"
    def buildDir = "${project.buildDir}/outputs/apk/custom"
    def signedApk = "${buildDir}/app-custom-signed.apk"
    
    dependsOn 'assembleCustom'
    
    commandLine 'apksigner', 'sign',
            '--key', platformKey,
            '--cert', platformCert,
            '--v1-signing-enabled', 'true',
            '--v2-signing-enabled', 'true',
            '--v3-signing-enabled', 'true',
            '--v4-signing-enabled', 'false',
            signedApk
}
```

## Platform Key Permissions

Platform-signed APKs have special system permissions:
- Can request `android:sharedUserId="android.uid.system"`
- Can use `signature|privileged` protection level permissions
- Required for system apps that need elevated privileges

## Security Notes

⚠️ **Important:**
- Keep platform keys secure and never commit them to version control
- Only use platform keys for apps that require system-level access
- Platform keys should match the Android system where the app will be installed
- Different device manufacturers may have different platform keys

## References

- [APK Signature Scheme v2](https://source.android.com/security/apksigning/v2)
- [APK Signature Scheme v3](https://source.android.com/security/apksigning/v3)
- [apksigner Tool](https://developer.android.com/studio/command-line/apksigner)

