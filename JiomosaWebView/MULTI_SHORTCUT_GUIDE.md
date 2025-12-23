# Multi-Shortcut Configuration Guide

## Overview

JiomosaWebView now supports **multiple launcher shortcuts** that share the same login session, cookies, cache, and browser data. This means you can have separate app icons for different Microsoft 365 services, but they all use the same authentication and stored data.

## ✨ How It Works

### Shared Session Architecture

All shortcuts use the **same WebView data directory**, which includes:
- 🔐 **Cookies** - Authentication tokens, session cookies
- 💾 **LocalStorage/SessionStorage** - Application state and preferences
- 📁 **Cache** - Downloaded resources, images, scripts
- 🗄️ **IndexedDB/WebSQL** - Offline data storage
- 📝 **Form data** - Saved passwords and autofill data

### Login Once, Use Everywhere

1. Open any shortcut (e.g., Outlook)
2. Sign in with your Microsoft account
3. All other shortcuts automatically inherit the session
4. Switch between apps without re-authenticating

## 📱 Available Shortcuts

The app creates **5 separate launcher icons**:

| Shortcut | App Name | Default URL | Use Case |
|----------|----------|-------------|----------|
| **Intune** | Intune Company Portal | `portal.manage.microsoft.com` | Device management |
| **Outlook** | Outlook Mail | `outlook.office.com/mail` | Email and calendar |
| **Teams** | Microsoft Teams | `teams.microsoft.com` | Chat and meetings |
| **OneDrive** | OneDrive | `onedrive.live.com` | Cloud storage |
| **SharePoint** | SharePoint | `sharepoint.com` | Document collaboration |

## 🔧 Configuration

### Changing Default URLs

Edit `app/src/main/res/values/strings.xml`:

```xml
<!-- Default URLs for each shortcut -->
<string name="url_intune">https://portal.manage.microsoft.com</string>
<string name="url_outlook">https://outlook.office.com/mail</string>
<string name="url_teams">https://teams.microsoft.com</string>
<string name="url_onedrive">https://onedrive.live.com</string>
<string name="url_sharepoint">https://sharepoint.com</string>
```

### Customizing App Names

Edit the launcher labels in `strings.xml`:

```xml
<!-- Multiple App Shortcuts -->
<string name="app_name_intune">Intune Company Portal</string>
<string name="app_name_outlook">Outlook Mail</string>
<string name="app_name_teams">Microsoft Teams</string>
<string name="app_name_onedrive">OneDrive</string>
<string name="app_name_sharepoint">SharePoint</string>
```

### Adding New Shortcuts

To add a new shortcut (e.g., Azure Portal):

#### 1. Add URL to `strings.xml`:

```xml
<string name="app_name_azure">Azure Portal</string>
<string name="url_azure">https://portal.azure.com</string>
```

#### 2. Add activity-alias to `AndroidManifest.xml`:

```xml
<!-- Azure Portal Shortcut -->
<activity-alias
    android:name=".AzureShortcut"
    android:targetActivity=".StealthWebViewActivity"
    android:exported="true"
    android:label="@string/app_name_azure"
    android:icon="@mipmap/ic_launcher">
    
    <intent-filter>
        <action android:name="android.intent.action.MAIN" />
        <category android:name="android.intent.category.LAUNCHER" />
    </intent-filter>
    
    <meta-data
        android:name="default_url"
        android:value="https://portal.azure.com" />
</activity-alias>
```

**Note:** The URL is specified directly as a string value in the metadata, not as a resource reference.

#### 3. Rebuild the app

```bash
./gradlew assembleDebug
```

### Removing Shortcuts

To disable a shortcut without removing code:

#### Option 1: Set `android:enabled="false"` in manifest:

```xml
<activity-alias
    android:name=".TeamsShortcut"
    android:enabled="false"
    ...>
```

#### Option 2: Delete the entire `<activity-alias>` block

## 🎨 Custom Icons (Optional)

To use different icons for each shortcut:

### 1. Add icon resources

Place icons in `app/src/main/res/mipmap-*/`:
```
mipmap-hdpi/
  ic_outlook.png
  ic_teams.png
  ic_onedrive.png
  ic_sharepoint.png
```

### 2. Update manifest

```xml
<activity-alias
    android:name=".OutlookShortcut"
    android:icon="@mipmap/ic_outlook"
    ...>
```

## 🔐 Session Persistence

### How Sessions Are Shared

The WebView uses Android's default data directory:
```
/data/data/com.jiomosa.webview/app_webview/
```

All shortcuts access this **same directory**, ensuring:
- One login applies to all shortcuts
- Cookies persist across app restarts
- Cache is shared to reduce bandwidth

### Clearing Session Data

To clear all shared data (log out from all shortcuts):

**Settings → Apps → Jiomosa WebView → Storage → Clear Data**

Or programmatically:
```kotlin
// Clear all WebView data
webView.clearCache(true)
webView.clearFormData()
webView.clearHistory()
CookieManager.getInstance().removeAllCookies(null)
```

## 🚀 Usage Examples

### Scenario 1: Microsoft 365 Productivity Suite

1. **Open Outlook** shortcut - Sign in with work account
2. **Open Teams** shortcut - Already logged in! 
3. **Open OneDrive** shortcut - Same session, no login needed
4. Switch between apps seamlessly

### Scenario 2: Multiple Work Accounts

If you need separate accounts for different services:
- Install multiple instances of the app with different package names
- Or use Android's Work Profile feature
- Each instance maintains separate sessions

### Scenario 3: Custom Enterprise Apps

Configure shortcuts for your organization's web apps:
```xml
<string name="url_custom1">https://internal.company.com/hr</string>
<string name="url_custom2">https://internal.company.com/finance</string>
<string name="url_custom3">https://internal.company.com/tickets</string>
```

All will share SSO authentication from your company's identity provider.

## ⚡ Performance Benefits

### Shared Cache Advantages

- **Faster Loading**: Common resources (fonts, scripts, images) cached once
- **Reduced Bandwidth**: No duplicate downloads across shortcuts
- **Lower Memory**: Single WebView data directory
- **Instant Switch**: Navigation history preserved per shortcut

### Memory Management

Each shortcut runs in the **same process** but maintains its own:
- WebView instance (when active)
- Navigation history
- Back stack

When you switch shortcuts, the previous WebView is paused (not destroyed).

## 🔍 Technical Details

### Activity Launch Modes

All shortcuts use `launchMode="singleTask"`:
- Only one instance of each shortcut at a time
- Pressing the same icon brings existing instance to front
- Efficient memory usage

### Metadata Resolution

The app reads URLs in this priority order:

1. **Intent Extra**: `intent.getStringExtra("url")`
2. **Activity Metadata**: `<meta-data android:name="default_url" .../>`
3. **Fallback**: `https://portal.manage.microsoft.com`

### Example Usage from Code

```kotlin
// Launch Outlook shortcut
val intent = Intent(this, StealthWebViewActivity::class.java).apply {
    putExtra("url", "https://outlook.office.com/mail")
}
startActivity(intent)

// Or launch via component name
val intent = Intent().apply {
    component = ComponentName(
        "com.jiomosa.webview",
        "com.jiomosa.webview.OutlookShortcut"
    )
}
startActivity(intent)
```

## 🛠️ Troubleshooting

### Shortcuts Not Appearing

1. Uninstall old version completely
2. Rebuild and reinstall:
   ```bash
   ./gradlew clean assembleDebug
   adb install app/build/outputs/apk/debug/app-debug.apk
   ```
3. Check launcher settings (some launchers hide duplicate icons)

### Session Not Shared

1. Verify all shortcuts use same package name
2. Check WebView settings have persistent storage enabled
3. Clear data and sign in again

### Different Sessions Needed

If you need **separate sessions** per shortcut:
- Create separate apps with different package names
- Use Android's multi-user or work profile features
- Or disable session sharing by using different data directories

## 📊 Comparison

| Feature | Multi-Shortcut (This App) | Separate Apps |
|---------|---------------------------|---------------|
| **Shared Login** | ✅ Yes | ❌ No |
| **App Size** | ✅ ~5MB total | ❌ ~5MB × N apps |
| **Memory Usage** | ✅ Low | ❌ High |
| **Setup Time** | ✅ Login once | ❌ Login N times |
| **Updates** | ✅ Update once | ❌ Update N times |
| **Separate Sessions** | ❌ Not supported | ✅ Yes |

## 🎯 Best Practices

1. **Keep URLs in sync**: Update `strings.xml` when services change URLs
2. **Test each shortcut**: Verify all shortcuts work after changes
3. **Use HTTPS**: Always use secure URLs
4. **Handle deep links**: Configure intent filters for web URLs
5. **Monitor sessions**: Check cookie expiration and refresh tokens

## 📝 License

Same as main JiomosaWebView project.
