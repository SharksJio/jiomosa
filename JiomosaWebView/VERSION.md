# JiomosaWebView Version History

## Version 1.0.0 (2026-01-08) - Initial Release

### Features
- ✅ Stealth WebView with fingerprint evasion techniques
- ✅ Multiple app support (Outlook, Teams, OneDrive)
- ✅ File attachment support with external storage permissions
- ✅ Native file chooser integration for modern web apps
- ✅ Runtime permission handling (storage, camera, media)
- ✅ JavaScript bridge for file input monitoring
- ✅ Action bar with back button for all activities
- ✅ WebView session persistence across activities
- ✅ Custom user agent for stealth browsing

### Security
- ✅ Granular media permissions for Android 13+
- ✅ Legacy storage permissions for older Android versions
- ✅ Camera permission for image capture
- ✅ Runtime permission requests with user consent
- ✅ Secure file URI handling with proper grants

### Technical Details
- **Min SDK**: 21 (Android 5.0 Lollipop)
- **Target SDK**: 34 (Android 14)
- **Compile SDK**: 34
- **Build Tools**: Gradle 8.11.1
- **Language**: Kotlin
- **WebView**: androidx.webkit:webkit:1.9.0

### Known Issues
- None reported

### Testing
- ✅ File attachments working in Outlook Mail
- ✅ Microsoft Teams web app functional
- ✅ OneDrive access working

---

## Versioning Scheme

This project follows [Semantic Versioning](https://semver.org/):
- **MAJOR.MINOR.PATCH** (e.g., 1.0.0)
  - **MAJOR**: Breaking changes or significant feature overhauls
  - **MINOR**: New features, backward-compatible
  - **PATCH**: Bug fixes, security patches, backward-compatible

**versionCode** increments with each release (Google Play requirement).
