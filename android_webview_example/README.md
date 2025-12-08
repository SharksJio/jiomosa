# Android WebView with Stealth Parameters

This directory contains a complete Android WebView implementation with stealth parameters to access websites like Outlook that employ bot detection mechanisms.

## Overview

Based on the Jio Cloud Apps server-side Playwright stealth implementation, this Android WebView example applies similar fingerprint evasion techniques on the client side to enable access to protected websites.

## Feasibility Analysis

### ✅ What's Feasible in Android WebView

| Feature | Feasibility | Notes |
|---------|-------------|-------|
| Custom User-Agent | ✅ Full | Set via `WebSettings.setUserAgentString()` |
| JavaScript Injection | ✅ Full | Use `evaluateJavascript()` or `addJavascriptInterface()` |
| navigator.webdriver Override | ✅ Full | Inject JS to override property |
| WebGL Parameter Override | ✅ Full | Inject JS before page load |
| Plugin/MIME Type Arrays | ✅ Full | Create fake plugin objects via JS |
| Chrome Object Simulation | ✅ Full | Inject complete chrome object structure |
| Permissions API Override | ✅ Full | Override via JS injection |
| DOM Storage | ✅ Full | Enable via `WebSettings` |
| JavaScript Enabled | ✅ Full | Required for most modern sites |
| Hardware Acceleration | ✅ Full | Enable for better performance |

### ⚠️ Limitations

| Feature | Feasibility | Workaround |
|---------|-------------|------------|
| Canvas Fingerprint | ⚠️ Partial | Can inject noise but may be detected |
| AudioContext Fingerprint | ⚠️ Partial | Can modify but detection is improving |
| Font Enumeration | ⚠️ Partial | Limited control over system fonts |
| Battery API | ❌ Limited | Not available in WebView context |
| Screen Resolution | ⚠️ Partial | Can spoof some values |

### Key Differences from Server-Side Playwright

| Aspect | Server-Side (Playwright) | Client-Side (Android WebView) |
|--------|--------------------------|-------------------------------|
| Browser Engine | Chromium (full control) | System WebView (limited control) |
| Fingerprint | Consistent, configurable | Device-dependent |
| Updates | Controlled environment | User's Android version |
| Reliability | High (controlled) | Medium (varies by device) |
| Resource Usage | Server resources | Client device resources |

## Files

- `StealthWebViewActivity.java` - Complete Activity with stealth WebView setup
- `StealthWebViewHelper.java` - Helper class for stealth JavaScript injection
- `stealth_scripts.js` - JavaScript stealth overrides (injected into pages)
- `AndroidManifest.xml` - Sample manifest with required permissions
- `activity_stealth_webview.xml` - Layout file for the activity

## Quick Start

### 1. Add Dependencies

In your `build.gradle` (app level):

```groovy
android {
    defaultConfig {
        // Minimum SDK 21 recommended for full WebView features
        minSdkVersion 21
        targetSdkVersion 34
    }
}

dependencies {
    implementation 'androidx.appcompat:appcompat:1.6.1'
    implementation 'androidx.webkit:webkit:1.9.0'
}
```

### 2. Add Permissions

In `AndroidManifest.xml`:

```xml
<uses-permission android:name="android.permission.INTERNET" />
<uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />
```

### 3. Copy the Files

Copy the Java files to your project's source directory and the layout file to your `res/layout` directory.

### 4. Usage

```java
// Start the Stealth WebView Activity - loads actual Outlook Mail URL
Intent intent = new Intent(this, StealthWebViewActivity.class);
intent.putExtra("url", "https://outlook.office.com/mail");
startActivity(intent);
```

## Implementation Details

### Stealth Features Applied

1. **User-Agent Spoofing**
   - Sets a desktop Chrome User-Agent to appear as a regular browser
   - Matches the User-Agent used in server-side Playwright stealth

2. **navigator.webdriver Override**
   - Removes the `webdriver` property from navigator
   - Essential for bypassing Selenium/automation detection

3. **Chrome Object Simulation**
   - Creates a complete `window.chrome` object
   - Includes `app`, `runtime`, `loadTimes`, `csi`, and `webstore` properties

4. **Plugin Array Simulation**
   - Creates fake PDF, Chrome PDF Viewer, and Native Client plugins
   - Matches expected plugin structure of a real Chrome browser

5. **MIME Types Simulation**
   - Creates proper MimeTypeArray with PDF and NaCl support
   - Linked to corresponding plugin objects

6. **WebGL Parameter Override**
   - Spoofs WebGL vendor and renderer strings
   - Returns consistent GPU information

7. **Permissions API Override**
   - Overrides `navigator.permissions.query` for notifications
   - Returns expected permission states

8. **Languages Override**
   - Sets navigator.languages to `['en-US', 'en']`
   - Matches typical English-speaking user

### When Scripts Are Injected

- **Page Load Start**: Initial stealth scripts injected via `onPageStarted()`
- **Page Load Finish**: Verification and additional patches via `onPageFinished()`
- **Before JavaScript Execution**: Scripts run before page's own JavaScript

## Testing

### Test Websites

Test your implementation with these detection tools:

1. **Outlook Mail**: https://outlook.office.com/mail (Primary target)
2. **Bot Detection Test**: https://bot.sannysoft.com
3. **CreepJS**: https://abrahamjuliot.github.io/creepjs/
4. **Browser Leaks**: https://browserleaks.com
5. **FingerprintJS**: https://fingerprintjs.github.io/fingerprintjs/

### Expected Results

With stealth parameters properly applied:

- ✅ Outlook should load and function normally
- ✅ Bot detection tests should show "Human-like" behavior
- ✅ No "Headless" or "Automation" warnings
- ⚠️ Some advanced fingerprinting may still detect anomalies

## Troubleshooting

### Outlook Still Blocking

1. **Check User-Agent**: Verify User-Agent is set before loading URL
2. **Script Timing**: Ensure stealth scripts inject before page loads
3. **Clear Cache**: Sometimes old detection cookies persist
4. **Check Console**: Use Remote Debugging to see errors

### Remote Debugging

Enable remote debugging to inspect WebView:

```java
WebView.setWebContentsDebuggingEnabled(true);
```

Then in Chrome DevTools, navigate to `chrome://inspect/#devices`.

### Script Not Injecting

1. Verify JavaScript is enabled: `webSettings.setJavaScriptEnabled(true)`
2. Check that stealth script is not null or empty
3. Ensure `evaluateJavascript()` is called on UI thread

## Security Considerations

⚠️ **Important**: These techniques are for legitimate use cases like accessing cloud-rendered websites. Use responsibly and in accordance with website terms of service.

- This is meant to work with Jiomosa's cloud rendering architecture
- Do not use for malicious purposes like account automation
- Respect website rate limits and terms of service

## Integration with Jiomosa

This WebView implementation can be used in two modes:

### Mode 1: Direct Access (Stealth WebView)

Use the stealth WebView to directly access websites with bot detection bypass.

### Mode 2: Jiomosa Integration

Connect to the Jiomosa Android WebApp which handles rendering server-side:

```java
// Load Jiomosa webapp instead of target website
stealthWebView.loadUrl("http://YOUR_JIOMOSA_SERVER:9000/");
```

The server-side Playwright stealth provides stronger evasion than client-side only.

## Updates and Maintenance

Bot detection evolves constantly. To keep stealth working:

1. Monitor for detection on target websites
2. Update User-Agent string periodically
3. Compare with latest browser versions
4. Check Playwright-stealth updates for new evasion techniques

## Related Resources

- [Jiomosa Main README](../README.md)
- [WebRTC Renderer with Stealth](../webrtc_renderer/browser_pool.py)
- [playwright-stealth](https://github.com/AtuboDad/playwright_stealth)
- [Android WebView Documentation](https://developer.android.com/reference/android/webkit/WebView)

## License

Part of the Jiomosa project - see main repository for license information.
