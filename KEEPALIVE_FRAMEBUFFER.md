# Keepalive and Framebuffer Features

This document describes the keepalive and HTML5 framebuffer streaming features added to Jiomosa, designed specifically for ThreadX and other embedded systems integration.

## Overview

The enhanced Jiomosa renderer now provides:

1. **Session Keepalive**: Maintain browser sessions with heartbeat signals to prevent automatic timeout
2. **Framebuffer Capture**: Capture browser frames/screenshots as PNG images
3. **HTML5 Viewer**: Stream browser frames through an HTML5 interface suitable for WebView embedding

These features enable low-end devices (like ThreadX RTOS systems) to view cloud-rendered websites through a simple HTML5 WebView without needing VNC clients.

## Features

### 1. Session Keepalive

Sessions now automatically expire after a configurable timeout period (default: 300 seconds / 5 minutes). The keepalive endpoint allows clients to signal that a session is still active.

#### Configuration

Set the session timeout via environment variable:

```bash
SESSION_TIMEOUT=600  # 10 minutes
```

#### Endpoint

**POST** `/api/session/<session_id>/keepalive`

Send a keepalive signal to prevent session timeout.

**Response:**
```json
{
    "success": true,
    "session_id": "my_session",
    "last_activity": 1763112667.2196052,
    "message": "Keepalive successful"
}
```

#### Example Usage

```bash
# Send keepalive every minute to maintain session
curl -X POST http://localhost:5000/api/session/my_session/keepalive
```

```python
import requests
import time

def maintain_session(session_id, interval=60):
    """Keep session alive by sending keepalive every interval seconds"""
    while True:
        try:
            response = requests.post(
                f"http://localhost:5000/api/session/{session_id}/keepalive"
            )
            if response.status_code == 200:
                print(f"Keepalive sent: {response.json()}")
            else:
                print(f"Keepalive failed: {response.status_code}")
        except Exception as e:
            print(f"Error: {e}")
        
        time.sleep(interval)
```

### 2. Framebuffer Capture

Capture the current browser display as a PNG image. This provides a "framebuffer" view of the rendered website.

#### Configuration

Set the frame capture interval via environment variable:

```bash
FRAME_CAPTURE_INTERVAL=1.0  # 1 second between captures
```

#### Endpoints

##### GET `/api/session/<session_id>/frame`

Capture and return the current browser frame as a PNG image.

**Response:** Binary PNG image data

**Example:**
```bash
# Download frame as PNG
curl http://localhost:5000/api/session/my_session/frame -o frame.png

# View in browser
xdg-open frame.png
```

##### GET `/api/session/<session_id>/frame/data`

Capture and return the frame as base64-encoded JSON data.

**Response:**
```json
{
    "success": true,
    "session_id": "my_session",
    "timestamp": 1763112667.5,
    "frame": "iVBORw0KGgoAAAANSUhEUgAA...",
    "format": "png"
}
```

**Example:**
```python
import requests
import base64
from PIL import Image
from io import BytesIO

# Get frame as base64
response = requests.get('http://localhost:5000/api/session/my_session/frame/data')
data = response.json()

# Decode and display
image_data = base64.b64decode(data['frame'])
image = Image.open(BytesIO(image_data))
image.show()
```

### 3. HTML5 Viewer

An HTML5-based viewer that automatically streams browser frames, perfect for embedding in WebViews on embedded systems.

#### Endpoint

**GET** `/api/session/<session_id>/viewer`

Returns a complete HTML5 page that displays the browser session with auto-refreshing frames.

#### Features

- **Auto-refresh streaming**: Captures frames every second by default
- **Keepalive integration**: Automatically sends keepalive signals
- **FPS counter**: Shows actual frame rate
- **Start/Stop controls**: Manual control over streaming
- **Responsive design**: Adapts to different screen sizes
- **Minimal resources**: Optimized for low-end devices

#### Usage

```bash
# Open viewer in a browser
xdg-open http://localhost:5000/api/session/my_session/viewer

# Or embed in iframe
<iframe src="http://localhost:5000/api/session/my_session/viewer" 
        width="100%" height="600"></iframe>
```

## ThreadX Integration Example

Here's how to integrate Jiomosa with a ThreadX RTOS application using a WebView:

### C/C++ Example (Conceptual)

```c
#include "tx_api.h"
#include "http_client.h"
#include "webview.h"

#define JIOMOSA_SERVER "192.168.1.100"
#define JIOMOSA_PORT 5000

typedef struct {
    char session_id[64];
    char viewer_url[256];
    void* webview;
} jiomosa_client_t;

// Initialize Jiomosa client and create session
int jiomosa_init(jiomosa_client_t* client, const char* session_name) {
    char url[256];
    char response[512];
    
    // Create session via REST API
    snprintf(url, sizeof(url), 
             "http://%s:%d/api/session/create", 
             JIOMOSA_SERVER, JIOMOSA_PORT);
    
    char payload[128];
    snprintf(payload, sizeof(payload), 
             "{\"session_id\":\"%s\"}", session_name);
    
    if (http_post(url, payload, response, sizeof(response)) != 0) {
        return -1;
    }
    
    // Parse session ID from response
    strcpy(client->session_id, session_name);
    
    // Build viewer URL
    snprintf(client->viewer_url, sizeof(client->viewer_url),
             "http://%s:%d/api/session/%s/viewer",
             JIOMOSA_SERVER, JIOMOSA_PORT, client->session_id);
    
    return 0;
}

// Load a URL in the session
int jiomosa_load_url(jiomosa_client_t* client, const char* url) {
    char api_url[256];
    char payload[512];
    char response[1024];
    
    snprintf(api_url, sizeof(api_url),
             "http://%s:%d/api/session/%s/load",
             JIOMOSA_SERVER, JIOMOSA_PORT, client->session_id);
    
    snprintf(payload, sizeof(payload), "{\"url\":\"%s\"}", url);
    
    return http_post(api_url, payload, response, sizeof(response));
}

// Show the HTML5 viewer in WebView
int jiomosa_show_viewer(jiomosa_client_t* client) {
    // Create and show WebView with the viewer URL
    client->webview = webview_create(client->viewer_url, 
                                     WEBVIEW_FULLSCREEN);
    if (client->webview == NULL) {
        return -1;
    }
    
    webview_show(client->webview);
    return 0;
}

// Main ThreadX task
void jiomosa_task(ULONG thread_input) {
    jiomosa_client_t client;
    
    // Initialize Jiomosa client
    if (jiomosa_init(&client, "threadx_device") != 0) {
        tx_thread_terminate(tx_thread_identify());
        return;
    }
    
    // Load a website
    jiomosa_load_url(&client, "https://example.com");
    
    // Show HTML5 viewer in WebView
    // This displays the cloud-rendered browser
    jiomosa_show_viewer(&client);
    
    // Keep task alive
    while(1) {
        tx_thread_sleep(100);
    }
}
```

### JavaScript WebView Integration

If your ThreadX system has a JavaScript-capable WebView:

```html
<!DOCTYPE html>
<html>
<head>
    <title>ThreadX Browser</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { margin: 0; padding: 0; overflow: hidden; }
        iframe { width: 100vw; height: 100vh; border: none; }
    </style>
</head>
<body>
    <iframe id="viewer"></iframe>
    
    <script>
        // Configuration
        const JIOMOSA_SERVER = '192.168.1.100:5000';
        
        // Create session and load viewer
        async function init() {
            try {
                // Create session
                const response = await fetch(`http://${JIOMOSA_SERVER}/api/session/create`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({session_id: 'threadx_' + Date.now()})
                });
                const data = await response.json();
                const sessionId = data.session_id;
                
                // Load website
                await fetch(`http://${JIOMOSA_SERVER}/api/session/${sessionId}/load`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({url: 'https://example.com'})
                });
                
                // Load viewer in iframe
                document.getElementById('viewer').src = 
                    `http://${JIOMOSA_SERVER}/api/session/${sessionId}/viewer`;
                
            } catch (error) {
                console.error('Initialization error:', error);
            }
        }
        
        init();
    </script>
</body>
</html>
```

## API Reference

### Updated Endpoints

All new endpoints are documented in the service info:

```bash
curl http://localhost:5000/api/info
```

**New Endpoints:**
- `POST /api/session/<session_id>/keepalive` - Send keepalive signal
- `GET /api/session/<session_id>/frame` - Get current frame as PNG
- `GET /api/session/<session_id>/frame/data` - Get current frame as base64 JSON
- `GET /api/session/<session_id>/viewer` - HTML5 viewer page

### Configuration

Environment variables for the renderer service:

| Variable | Default | Description |
|----------|---------|-------------|
| `SESSION_TIMEOUT` | 300 | Session timeout in seconds |
| `FRAME_CAPTURE_INTERVAL` | 1.0 | Default frame capture interval in seconds |

Example docker-compose configuration:

```yaml
renderer:
  build: ./renderer
  environment:
    - SESSION_TIMEOUT=600
    - FRAME_CAPTURE_INTERVAL=1.0
```

## Performance Considerations

### For Low-End Devices

1. **Frame Rate**: The HTML5 viewer captures frames every 1 second by default. This is suitable for most browsing scenarios and keeps CPU usage low.

2. **Image Size**: Frames are captured at the browser's resolution (default 1920x1080). For lower bandwidth, consider reducing the browser window size:

```python
# In renderer/app.py, modify chrome_options
chrome_options.add_argument('--window-size=1280,720')  # Lower resolution
```

3. **Compression**: PNG frames are compressed but still relatively large (~20-50KB per frame). For better performance:
   - Reduce window size
   - Increase capture interval
   - Use local network deployment

4. **Network Bandwidth**: At 1 frame/second with ~30KB frames:
   - Bandwidth: ~30 KB/s = ~240 Kbps
   - Suitable for most LAN connections
   - May need optimization for WAN

### Optimization Tips

1. **Reduce Resolution**:
```python
chrome_options.add_argument('--window-size=1024,768')
```

2. **Increase Frame Interval**:
```javascript
// In HTML5 viewer, change:
streamingInterval = setInterval(captureFrame, 2000);  // 2 seconds
```

3. **Batch Keepalives**:
```python
# Send keepalive every 60 seconds instead of with every frame
```

## Comparison with VNC

| Feature | VNC Direct | HTML5 Framebuffer |
|---------|-----------|-------------------|
| Client Complexity | VNC client required | Simple WebView |
| Network Protocol | RFB protocol | HTTP/REST |
| Frame Rate | Real-time | 1 FPS (configurable) |
| Bandwidth | Higher | Lower |
| Integration | Complex | Simple |
| ThreadX Support | Limited | Excellent |

## Troubleshooting

### Frames Not Updating

```bash
# Check renderer logs
docker logs jiomosa-renderer -f

# Verify session is active
curl http://localhost:5000/api/sessions

# Test frame capture manually
curl http://localhost:5000/api/session/my_session/frame -o test.png
```

### Session Timing Out

```bash
# Increase timeout
docker-compose down
# Edit docker-compose.yml to add SESSION_TIMEOUT=600
docker-compose up -d

# Verify keepalive is working
curl -X POST http://localhost:5000/api/session/my_session/keepalive
```

### High CPU Usage

- Reduce browser window size
- Increase frame capture interval
- Limit number of concurrent sessions

### Memory Issues

```bash
# Monitor container memory
docker stats jiomosa-renderer

# Set memory limits in docker-compose.yml
renderer:
  mem_limit: 512m
```

## Future Enhancements

- [ ] WebSocket support for lower latency
- [ ] JPEG frame format option for smaller sizes
- [ ] Configurable frame quality
- [ ] Frame caching
- [ ] Adaptive frame rate based on content changes
- [ ] Mobile-optimized viewer
- [ ] Touch event support in viewer

## See Also

- [README.md](README.md) - Main documentation
- [USAGE.md](USAGE.md) - Usage examples
- [ARCHITECTURE.md](ARCHITECTURE.md) - System architecture
- [DEPLOYMENT.md](DEPLOYMENT.md) - Deployment guide
