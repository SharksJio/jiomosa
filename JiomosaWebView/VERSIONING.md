# JiomosaWebView Versioning Guide

## Overview

This project uses **Semantic Versioning** (SemVer) to track releases and changes.

## Version Format

**MAJOR.MINOR.PATCH** (e.g., 1.2.3)

- **MAJOR**: Breaking changes, significant API changes, major feature overhauls
- **MINOR**: New features, backward-compatible additions
- **PATCH**: Bug fixes, security patches, minor improvements

## Version Files

### 1. `app/build.gradle`
Contains the actual version used by Android:
```gradle
versionCode 1          // Integer, increments with each release (Google Play requirement)
versionName "1.0.0"    // User-facing version string
```

### 2. `VERSION.md`
Comprehensive changelog documenting all releases:
- Features added
- Security improvements
- Known issues
- Testing status

### 3. `make-release.sh`
Automated script to create new releases with security checks.

## Creating a Release

### Option 1: Using the Automated Script (Recommended)

```bash
./make-release.sh
```

The script will:
1. Show current version
2. Ask for version bump type (PATCH/MINOR/MAJOR)
3. Run security checks
4. Update version numbers in build.gradle
5. Update VERSION.md with new entry
6. Build release APK
7. Provide next steps

### Option 2: Manual Release Process

1. **Update version in build.gradle**:
   ```gradle
   versionCode 2
   versionName "1.0.1"
   ```

2. **Update VERSION.md**:
   - Add new version entry at the top
   - Document all changes
   - Note any security fixes
   - List known issues

3. **Security Review**:
   - Check for hardcoded secrets
   - Review permissions in AndroidManifest
   - Verify ProGuard configuration
   - Test runtime permission handling

4. **Build Release**:
   ```bash
   ./gradlew clean assembleRelease
   ```

5. **Sign APK** (if you have keystore):
   ```bash
   ./build-sign-install.sh
   ```

6. **Commit and Tag**:
   ```bash
   git add .
   git commit -m "Release v1.0.1"
   git tag v1.0.1
   git push origin main --tags
   ```

## Security Checklist

Before each release, verify:

- [ ] No hardcoded passwords, API keys, or secrets
- [ ] Proper permission declarations in AndroidManifest
- [ ] Runtime permissions requested appropriately
- [ ] ProGuard rules configured for release builds
- [ ] Debug logging minimized (or removed in production code paths)
- [ ] File URI handling secure (no world-readable files)
- [ ] WebView security settings enabled
- [ ] SSL/TLS properly configured
- [ ] No exposed internal APIs

## Version History

All versions are documented in [VERSION.md](VERSION.md).

Current version: **1.0.0**

## When to Bump Versions

### PATCH (1.0.0 → 1.0.1)
- Bug fixes
- Security patches
- Performance improvements
- Documentation updates
- Code cleanup (no behavior change)

### MINOR (1.0.0 → 1.1.0)
- New features (backward-compatible)
- New app support (e.g., adding Gmail support)
- Enhanced functionality (e.g., improved file handling)
- Dependency updates (minor versions)

### MAJOR (1.0.0 → 2.0.0)
- Breaking changes to API
- Major architecture changes
- Minimum SDK version changes
- Significant behavior changes
- Dependency updates (major versions)

## Build Outputs

Release builds are located at:
```
app/build/outputs/apk/release/app-release-unsigned.apk  (unsigned)
app/build/outputs/apk/release/app-release.apk           (signed, if keystore configured)
```

## Testing Releases

After creating a release:

1. **Install and test on multiple devices**:
   - Different Android versions (API 21-34)
   - Different manufacturers (Samsung, Pixel, OnePlus, etc.)
   
2. **Test all major features**:
   - File attachments in Outlook
   - Teams functionality
   - OneDrive access
   - Permission handling
   
3. **Verify WebView functionality**:
   - Page loading
   - JavaScript execution
   - File uploads
   - Back button behavior

4. **Check for regressions**:
   - Compare with previous version
   - Verify all reported bugs are fixed
   - Ensure no new issues introduced

## Rollback Procedure

If a release has critical issues:

1. Immediately revert to previous version:
   ```bash
   git revert <commit-hash>
   ```

2. Build and distribute previous stable version

3. Document the issue in VERSION.md

4. Fix the issue and prepare a new patch release

## Version Tracking in Runtime

The app version is accessible at runtime:

```kotlin
val versionName = BuildConfig.VERSION_NAME
val versionCode = BuildConfig.VERSION_CODE
```

You can display this in About screen or logs:
```kotlin
Log.d(TAG, "JiomosaWebView v$versionName (build $versionCode)")
```

## Questions?

For version-related questions:
- Check VERSION.md for changelog
- Review this guide for process
- Contact maintainer for clarification
