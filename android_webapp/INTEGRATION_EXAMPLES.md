# Android WebApp Integration Examples

This document provides practical examples of integrating the Jiomosa Android WebApp into various applications.

## Table of Contents
1. [Basic Android WebView Integration](#basic-android-webview-integration)
2. [React Native Integration](#react-native-integration)
3. [Flutter Integration](#flutter-integration)
4. [Cordova/PhoneGap Integration](#cordovaphonegap-integration)
5. [Progressive Web App (PWA)](#progressive-web-app-pwa)
6. [Testing the WebApp](#testing-the-webapp)

---

## Basic Android WebView Integration

### MainActivity.java

```java
package com.example.jiomosaapp;

import android.os.Bundle;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import androidx.appcompat.app.AppCompatActivity;

public class MainActivity extends AppCompatActivity {
    private WebView webView;
    private static final String JIOMOSA_URL = "http://YOUR_SERVER:9000/";
    
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);
        
        webView = findViewById(R.id.webView);
        setupWebView();
        loadJiomosaApp();
    }
    
    private void setupWebView() {
        WebSettings settings = webView.getSettings();
        
        // Enable JavaScript (required)
        settings.setJavaScriptEnabled(true);
        
        // Enable DOM storage (required)
        settings.setDomStorageEnabled(true);
        
        // Enable database (recommended)
        settings.setDatabaseEnabled(true);
        
        // Enable caching for better performance
        settings.setCacheMode(WebSettings.LOAD_DEFAULT);
        settings.setAppCacheEnabled(true);
        
        // Set user agent
        settings.setUserAgentString("JiomosaAndroidApp/1.0 " + settings.getUserAgentString());
        
        // Allow file access
        settings.setAllowFileAccess(true);
        settings.setAllowContentAccess(true);
        
        // Enable zoom (optional)
        settings.setSupportZoom(false);
        settings.setBuiltInZoomControls(false);
        settings.setDisplayZoomControls(false);
        
        // Set WebViewClient to handle navigation
        webView.setWebViewClient(new WebViewClient() {
            @Override
            public boolean shouldOverrideUrlLoading(WebView view, String url) {
                // Handle all navigation within the WebView
                view.loadUrl(url);
                return true;
            }
            
            @Override
            public void onPageFinished(WebView view, String url) {
                super.onPageFinished(view, url);
                // Page finished loading
            }
        });
    }
    
    private void loadJiomosaApp() {
        webView.loadUrl(JIOMOSA_URL);
    }
    
    @Override
    public void onBackPressed() {
        if (webView.canGoBack()) {
            webView.goBack();
        } else {
            super.onBackPressed();
        }
    }
    
    @Override
    protected void onDestroy() {
        if (webView != null) {
            webView.destroy();
        }
        super.onDestroy();
    }
}
```

### activity_main.xml

```xml
<?xml version="1.0" encoding="utf-8"?>
<RelativeLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:layout_width="match_parent"
    android:layout_height="match_parent">
    
    <WebView
        android:id="@+id/webView"
        android:layout_width="match_parent"
        android:layout_height="match_parent" />
</RelativeLayout>
```

### AndroidManifest.xml

```xml
<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    package="com.example.jiomosaapp">

    <!-- Required permissions -->
    <uses-permission android:name="android.permission.INTERNET" />
    <uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />
    
    <application
        android:allowBackup="true"
        android:icon="@mipmap/ic_launcher"
        android:label="@string/app_name"
        android:usesCleartextTraffic="true"
        android:theme="@style/Theme.AppCompat.Light.NoActionBar">
        
        <activity
            android:name=".MainActivity"
            android:configChanges="orientation|screenSize|keyboardHidden"
            android:exported="true">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>
    </application>
</manifest>
```

---

## React Native Integration

### WebViewComponent.js

```javascript
import React from 'react';
import { WebView } from 'react-native-webview';
import { StyleSheet, View } from 'react-native';

const JIOMOSA_URL = 'http://YOUR_SERVER:9000/';

const JiomosaWebView = () => {
  return (
    <View style={styles.container}>
      <WebView
        source={{ uri: JIOMOSA_URL }}
        style={styles.webview}
        javaScriptEnabled={true}
        domStorageEnabled={true}
        startInLoadingState={true}
        scalesPageToFit={true}
        onError={(syntheticEvent) => {
          const { nativeEvent } = syntheticEvent;
          console.warn('WebView error: ', nativeEvent);
        }}
      />
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  webview: {
    flex: 1,
  },
});

export default JiomosaWebView;
```

### Installation

```bash
npm install react-native-webview
# or
yarn add react-native-webview
```

---

## Flutter Integration

### main.dart

```dart
import 'package:flutter/material.dart';
import 'package:webview_flutter/webview_flutter.dart';

void main() {
  runApp(MyApp());
}

class MyApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Jiomosa App',
      theme: ThemeData(
        primarySwatch: Colors.blue,
      ),
      home: JiomosaWebViewPage(),
    );
  }
}

class JiomosaWebViewPage extends StatefulWidget {
  @override
  _JiomosaWebViewPageState createState() => _JiomosaWebViewPageState();
}

class _JiomosaWebViewPageState extends State<JiomosaWebViewPage> {
  late final WebViewController controller;
  static const String jiomosaUrl = 'http://YOUR_SERVER:9000/';
  
  @override
  void initState() {
    super.initState();
    
    controller = WebViewController()
      ..setJavaScriptMode(JavaScriptMode.unrestricted)
      ..setBackgroundColor(const Color(0x00000000))
      ..setNavigationDelegate(
        NavigationDelegate(
          onProgress: (int progress) {
            // Update loading bar
          },
          onPageStarted: (String url) {
            print('Page started loading: $url');
          },
          onPageFinished: (String url) {
            print('Page finished loading: $url');
          },
          onWebResourceError: (WebResourceError error) {
            print('Page resource error: ${error.description}');
          },
        ),
      )
      ..loadRequest(Uri.parse(jiomosaUrl));
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: WebViewWidget(controller: controller),
      ),
    );
  }
}
```

### pubspec.yaml

```yaml
dependencies:
  flutter:
    sdk: flutter
  webview_flutter: ^4.4.2
```

---

## Cordova/PhoneGap Integration

### config.xml

```xml
<?xml version='1.0' encoding='utf-8'?>
<widget id="com.example.jiomosaapp" version="1.0.0">
    <name>Jiomosa App</name>
    <description>Browse websites through Jiomosa</description>
    
    <content src="http://YOUR_SERVER:9000/" />
    
    <access origin="*" />
    <allow-navigation href="*" />
    
    <preference name="DisallowOverscroll" value="true" />
    <preference name="BackupWebStorage" value="local" />
    
    <platform name="android">
        <preference name="android-minSdkVersion" value="22" />
    </platform>
</widget>
```

---

## Progressive Web App (PWA)

### index.html

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Jiomosa App</title>
    <link rel="manifest" href="manifest.json">
    <meta name="theme-color" content="#667eea">
    <style>
        * {
            margin: 0;
            padding: 0;
        }
        body, html {
            height: 100%;
            overflow: hidden;
        }
        iframe {
            width: 100%;
            height: 100%;
            border: none;
        }
    </style>
</head>
<body>
    <iframe src="http://YOUR_SERVER:9000/" allow="fullscreen"></iframe>
    
    <script>
        // Register service worker for offline support
        if ('serviceWorker' in navigator) {
            navigator.serviceWorker.register('sw.js');
        }
    </script>
</body>
</html>
```

### manifest.json

```json
{
  "name": "Jiomosa Web Browser",
  "short_name": "Jiomosa",
  "description": "Browse websites through cloud rendering",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#667eea",
  "theme_color": "#667eea",
  "icons": [
    {
      "src": "icon-192.png",
      "sizes": "192x192",
      "type": "image/png"
    },
    {
      "src": "icon-512.png",
      "sizes": "512x512",
      "type": "image/png"
    }
  ]
}
```

---

## Testing the WebApp

### Manual Testing on Android Device

1. **Using Chrome DevTools (Desktop)**
   ```bash
   # Open Chrome DevTools
   # Press F12 → Click device toolbar (Ctrl+Shift+M)
   # Select a mobile device
   # Navigate to http://localhost:9000
   ```

2. **Using Android Device via USB Debugging**
   ```bash
   # Enable USB debugging on Android device
   # Connect device to computer
   # Open Chrome and navigate to chrome://inspect
   # Click "inspect" on your device's browser
   ```

3. **Using Android Emulator**
   ```bash
   # Start Android Studio emulator
   # Access localhost using 10.0.2.2
   # URL: http://10.0.2.2:9000
   ```

### Automated Testing

```python
# test_integration.py
import requests
import time

def test_webapp_integration():
    """Test complete webapp integration flow"""
    base_url = "http://localhost:9000"
    
    # 1. Health check
    response = requests.get(f"{base_url}/health")
    assert response.status_code == 200
    
    # 2. Get apps list
    response = requests.get(f"{base_url}/api/apps")
    apps = response.json()
    assert len(apps) > 0
    
    # 3. Create session
    session_id = f"test_{int(time.time())}"
    response = requests.post(
        f"{base_url}/proxy/api/session/create",
        json={"session_id": session_id}
    )
    assert response.status_code == 201
    
    # 4. Load website
    response = requests.post(
        f"{base_url}/proxy/api/session/{session_id}/load",
        json={"url": "https://example.com"}
    )
    assert response.status_code == 200
    assert response.json()["success"] == True
    
    # 5. Close session
    requests.post(f"{base_url}/proxy/api/session/{session_id}/close")
    
    print("✅ All integration tests passed!")

if __name__ == "__main__":
    test_webapp_integration()
```

---

## Environment Configuration

### Production Configuration

```bash
# .env file
JIOMOSA_SERVER=https://renderer.yourdomain.com
FLASK_ENV=production
```

### Development Configuration

```bash
# .env.development
JIOMOSA_SERVER=http://localhost:5000
FLASK_ENV=development
FLASK_DEBUG=true
```

---

## Troubleshooting

### Common Issues

1. **"Cannot connect to server"**
   - Ensure Jiomosa services are running
   - Check network connectivity
   - Verify URL is accessible from the device

2. **"JavaScript not working"**
   - Ensure JavaScript is enabled in WebView settings
   - Check browser console for errors

3. **"Page not loading"**
   - Check if renderer service is healthy
   - Verify Selenium/Chrome is running
   - Check logs: `docker compose logs renderer`

4. **"Mixed content warning"**
   - Use HTTPS for production
   - Or enable cleartext traffic in Android manifest

---

## Security Considerations

For production deployments:

1. Use HTTPS for all connections
2. Implement authentication/authorization
3. Add rate limiting
4. Validate and sanitize URLs
5. Implement CSP headers
6. Use secure WebSocket connections
7. Regular security audits

---

## Support

For issues and questions:
- GitHub Issues: https://github.com/SharksJio/jiomosa/issues
- Documentation: See README.md files in the repository
