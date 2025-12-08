# Jio Cloud Apps Android WebApp

A mobile-friendly web application designed to be loaded in an Android WebView. It provides an "all apps" style launcher interface where users can tap website icons to browse cloud-rendered websites through Jio Cloud Apps.

## Features

- **App Launcher Interface**: Grid layout similar to Android's app drawer
- **Popular Website Shortcuts**: Pre-configured icons for Facebook, Twitter, YouTube, Instagram, WhatsApp, LinkedIn, Reddit, GitHub, Wikipedia, Google, Gmail, Amazon, Netflix, Spotify, BBC News, and Google Maps
- **Custom URL Support**: Users can enter any URL they want to browse
- **Search Functionality**: Filter apps or enter URLs directly in the search bar
- **Mobile-Optimized**: Fully responsive design optimized for mobile devices
- **Cloud Rendering**: All websites are rendered on powerful cloud infrastructure
- **Session Management**: Automatic session creation and management
- **WebSocket Streaming**: Real-time frame streaming at 30 FPS with interactive input support

## Architecture

```
┌─────────────────────────────────────────┐
│         Android App (WebView)           │
│                                         │
│  ┌───────────────────────────────────┐ │
│  │    Jiomosa Android WebApp         │ │
│  │    (HTML/CSS/JavaScript)          │ │
│  │                                   │ │
│  │  - App Launcher UI                │ │
│  │  - Website Icons Grid             │ │
│  │  - WebSocket Client (Socket.IO)  │ │
│  │  - Session Management             │ │
│  └───────────────┬───────────────────┘ │
└──────────────────┼─────────────────────┘
                   │ WebSocket + REST API
                   ▼
┌─────────────────────────────────────────┐
│        Jiomosa Renderer Service         │
│        (Flask + Socket.IO)              │
│                                         │
│  - WebSocket Server (30 FPS streaming) │
│  - Session Creation                     │
│  - URL Loading                          │
│  - Browser Control                      │
│  - Adaptive Quality                     │
└────────────────┬────────────────────────┘
                 │ Selenium WebDriver
                 ▼
┌─────────────────────────────────────────┐
│      Selenium + Chrome Browser          │
│      (Website Rendering)                │
└─────────────────────────────────────────┘
```

## Quick Start

### Option 1: Docker Compose (Recommended)

The webapp is integrated into the main docker-compose setup:

```bash
# Start all services including the Android webapp
docker compose up -d

# Access the webapp
# Open http://localhost:9000 in your browser
```

### Option 2: Standalone

```bash
# Install dependencies
cd android_webapp
pip install -r requirements.txt

# Set Jiomosa server URL (if different from default)
export JIOMOSA_SERVER=http://localhost:5000

# Run the webapp
python webapp.py

# Access at http://localhost:9000
```

## Usage

### In a Web Browser

1. Navigate to http://localhost:9000
2. You'll see an "all apps" style grid with website icons
3. Tap any icon to launch that website
4. The website will load in a viewer with full interaction
5. Use the back button to return to the launcher

### In an Android WebView

To integrate into your Android app:

```java
// In your Android Activity
WebView webView = findViewById(R.id.webView);
WebSettings webSettings = webView.getSettings();
webSettings.setJavaScriptEnabled(true);
webSettings.setDomStorageEnabled(true);

// Load the Jiomosa Android WebApp
webView.loadUrl("http://YOUR_JIOMOSA_SERVER:9000/");
```

**Important**: Replace `YOUR_JIOMOSA_SERVER` with your actual server address.

### Environment Variables

- `JIOMOSA_SERVER` - URL of the Jiomosa renderer service (default: `http://renderer:5000`)

## API Endpoints

### Main Endpoints

- `GET /` - Main launcher page
- `GET /viewer` - Website viewer page
  - Query params: `session` (session ID), `app` (app name)
- `GET /api/apps` - Get list of available website shortcuts
- `GET /health` - Health check endpoint

### Proxy Endpoints

- `POST /proxy/api/session/create` - Create browser session (proxied to renderer)
- `POST /proxy/api/session/{id}/load` - Load URL (proxied to renderer)
- `POST /proxy/api/session/{id}/keepalive` - Keep session alive (proxied to renderer)

## Customization

### Adding More Website Shortcuts

Edit `webapp.py` and add entries to the `WEBSITE_APPS` list:

```python
{
    'id': 'mysite',
    'name': 'My Site',
    'url': 'https://mysite.com',
    'icon': '🌐',  # Any emoji
    'color': '#FF5733',  # Hex color
    'category': 'custom'
}
```

### Changing Colors and Theme

Modify the CSS in the `LAUNCHER_TEMPLATE` variable in `webapp.py`:

```css
/* Main gradient */
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);

/* Icon colors are defined per-app in WEBSITE_APPS */
```

### Mobile Optimizations

The webapp is already optimized for mobile, but you can adjust:

- Grid columns: Modify `grid-template-columns` in `.apps-grid`
- Icon size: Adjust `.app-icon` width/height
- Touch targets: Minimum 44x44px for accessibility

## Testing

### Manual Testing

1. Start all services:
```bash
docker compose up -d
```

2. Open the webapp in a mobile browser or Chrome DevTools (mobile mode):
```bash
# In Chrome DevTools:
# 1. Press F12
# 2. Click device toolbar icon (Ctrl+Shift+M)
# 3. Select a mobile device
# 4. Navigate to http://localhost:9000
```

3. Test functionality:
   - Tap various app icons
   - Try the search feature
   - Enter a custom URL
   - Verify website loads in the viewer
   - Test back button

### Automated Testing

```bash
# Run webapp tests
cd tests
python test_android_webapp.py
```

## Android Integration Guide

### Basic WebView Setup

```java
public class MainActivity extends AppCompatActivity {
    private WebView webView;
    
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);
        
        webView = findViewById(R.id.webView);
        setupWebView();
        
        // Load Jiomosa webapp
        webView.loadUrl("http://YOUR_SERVER:9000/");
    }
    
    private void setupWebView() {
        WebSettings settings = webView.getSettings();
        
        // Enable JavaScript (required)
        settings.setJavaScriptEnabled(true);
        
        // Enable DOM storage (required)
        settings.setDomStorageEnabled(true);
        
        // Enable caching for better performance
        settings.setCacheMode(WebSettings.LOAD_DEFAULT);
        
        // Set user agent (optional)
        settings.setUserAgentString("JiomosaAndroidApp/1.0");
        
        // Enable zoom controls (optional)
        settings.setBuiltInZoomControls(false);
        
        // Set WebView client
        webView.setWebViewClient(new WebViewClient() {
            @Override
            public boolean shouldOverrideUrlLoading(WebView view, String url) {
                view.loadUrl(url);
                return true;
            }
        });
    }
    
    @Override
    public void onBackPressed() {
        if (webView.canGoBack()) {
            webView.goBack();
        } else {
            super.onBackPressed();
        }
    }
}
```

### Manifest Permissions

```xml
<uses-permission android:name="android.permission.INTERNET" />
<uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />
```

### Layout XML

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

## Deployment

### Production Considerations

1. **HTTPS**: Use HTTPS in production for secure communication
2. **Authentication**: Add authentication to restrict access
3. **Domain**: Use a proper domain name instead of IP:PORT
4. **Scaling**: Deploy with load balancing for multiple users
5. **CDN**: Use a CDN for static assets
6. **Monitoring**: Add error tracking and analytics

### Example Production Setup

```bash
# Use environment variables for production
export JIOMOSA_SERVER=https://renderer.yourdomain.com
export FLASK_ENV=production

# Run with production server (gunicorn)
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:9000 webapp:app
```

## Troubleshooting

### Webapp not loading
- Check if all services are running: `docker compose ps`
- Verify renderer service is healthy: `curl http://localhost:5000/health`
- Check webapp logs: `docker compose logs android-webapp`

### "Cannot connect to Jiomosa Server"
- Ensure renderer service is accessible from the webapp container
- Check network connectivity: `docker compose exec android-webapp curl http://renderer:5000/health`

### Websites not loading
- Check Selenium/Chrome service: `docker compose logs chrome`
- Optionally verify noVNC is accessible: Navigate to http://localhost:7900
- Check renderer logs: `docker compose logs renderer`
- Test WebSocket connection using browser DevTools

### Android WebView Issues
- Ensure JavaScript is enabled in WebView settings
- Check for mixed content warnings (HTTP vs HTTPS)
- Verify internet permissions in AndroidManifest.xml
- Test in a regular mobile browser first

## Performance Tips

1. **Session Reuse**: The webapp reuses sessions to reduce load times
2. **Caching**: Enable WebView caching in your Android app
3. **Connection Pooling**: The webapp maintains persistent connections
4. **Lazy Loading**: Apps load only when tapped
5. **Resource Limits**: Configure Selenium session limits in docker-compose.yml

## Security

⚠️ **Important Security Notes:**

This is a proof-of-concept. For production:

1. Add authentication/authorization
2. Implement rate limiting
3. Validate and sanitize all URLs
4. Use HTTPS everywhere
5. Implement CORS properly
6. Add CSP headers
7. Secure WebSocket connections with WSS
8. Regular security audits

## Contributing

Contributions are welcome! Areas for improvement:

- Additional website shortcuts
- Improved mobile UI/UX
- Better error handling
- Offline mode
- Bookmarks/favorites
- History tracking
- Custom app categories
- Dark mode support

## License

Part of the Jiomosa project - see main repository for license information.

## Support

For issues and questions:
- GitHub Issues: https://github.com/SharksJio/jiomosa/issues
- Documentation: See main README.md and other docs in the repository
