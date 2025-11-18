# WebSocket Streaming and Session Management

This document describes the WebSocket-based streaming and session management features in Jiomosa, designed specifically for ThreadX and other embedded systems integration.

## Overview

Jiomosa provides real-time website rendering via WebSocket streaming:

1. **WebSocket Streaming**: Real-time bidirectional frame streaming at 30 FPS
2. **Session Keepalive**: Maintain browser sessions with heartbeat signals
3. **Adaptive Quality**: Automatic bandwidth detection and quality adjustment
4. **Interactive Input**: Click, scroll, and text input via WebSocket events

These features enable low-end devices (like ThreadX RTOS systems) to view cloud-rendered websites through a WebSocket-enabled WebView without needing VNC clients.

## Primary Method: WebSocket Streaming (Recommended)

### Features

- **Real-time Streaming**: 30 FPS frame delivery
- **Bidirectional**: Frames from server, input events from client
- **Adaptive Quality**: JPEG quality 10-90 based on bandwidth
- **Low Latency**: ~50-100ms local network
- **Interactive**: Click, scroll, text input support

### Quick Start

#### 1. Create a Session

```bash
curl -X POST http://localhost:5000/api/session/create \
  -H "Content-Type: application/json" \
  -d '{"session_id": "threadx_session"}'
```

#### 2. Load a URL

```bash
curl -X POST http://localhost:5000/api/session/threadx_session/load \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'
```

#### 3. Connect WebSocket Client

```javascript
// Using Socket.IO client (recommended)
const socket = io('http://localhost:5000');

// Subscribe to session frames
socket.emit('subscribe', { session_id: 'threadx_session' });

// Receive frames at 30 FPS
socket.on('frame', (data) => {
    // data.image: base64-encoded JPEG
    // data.timestamp: frame timestamp  
    // data.size: frame size in bytes
    
    const img = document.getElementById('browser-view');
    img.src = `data:image/jpeg;base64,${data.image}`;
});

// Send input events
socket.emit('input:click', { x: 100, y: 200 });
socket.emit('input:scroll', { deltaX: 0, deltaY: 50 });
socket.emit('input:text', { text: 'hello world' });

// Quality control
socket.emit('quality:set', { quality: 75 });  // 10-100
socket.emit('fps:set', { fps: 30 });  // 1-60
socket.emit('adaptive:toggle', { enabled: true });

// Session management
socket.emit('unsubscribe');
```

### WebSocket Events Reference

#### Client → Server

| Event | Data | Description |
|-------|------|-------------|
| `subscribe` | `{session_id: string}` | Subscribe to session frames |
| `unsubscribe` | - | Unsubscribe from session |
| `input:click` | `{x: number, y: number}` | Send click at coordinates |
| `input:scroll` | `{deltaX: number, deltaY: number}` | Send scroll delta |
| `input:text` | `{text: string}` | Send text input |
| `quality:set` | `{quality: number}` | Set JPEG quality (10-100) |
| `fps:set` | `{fps: number}` | Set target FPS (1-60) |
| `adaptive:toggle` | `{enabled: boolean}` | Toggle adaptive mode |

#### Server → Client

| Event | Data | Description |
|-------|------|-------------|
| `frame` | `{image: string, timestamp: number, size: number}` | Frame data (base64 JPEG) |
| `subscribed` | `{session_id: string, fps: number, quality: number}` | Subscription confirmed |
| `unsubscribed` | - | Unsubscription confirmed |
| `input:acknowledged` | `{type: string}` | Input event processed |
| `quality:updated` | `{quality: number}` | Quality changed |
| `fps:updated` | `{fps: number}` | FPS changed |
| `adaptive:updated` | `{enabled: boolean}` | Adaptive mode toggled |
| `error` | `{message: string}` | Error occurred |
| `status` | `{message: string}` | Status update |

### ThreadX Integration Example

```c
// ThreadX C/C++ example using WebView
#include "webview.h"

void jiomosa_streaming_view() {
    // Create session via HTTP
    http_post("http://server:5000/api/session/create", 
              "{\"session_id\": \"threadx1\"}");
    http_post("http://server:5000/api/session/threadx1/load",
              "{\"url\": \"https://example.com\"}");
    
    // Load WebView with streaming client
    webview_t wv = webview_create(0, NULL);
    webview_set_size(wv, 800, 600, WEBVIEW_HINT_NONE);
    
    // Inject Socket.IO client and streaming code
    webview_navigate(wv, 
        "data:text/html," \
        "<script src='https://cdn.socket.io/4.5.4/socket.io.min.js'></script>" \
        "<img id='view' style='width:100%;height:100%'/>" \
        "<script>" \
        "const socket = io('http://server:5000');" \
        "socket.emit('subscribe', {session_id: 'threadx1'});" \
        "socket.on('frame', d => {" \
        "  document.getElementById('view').src = 'data:image/jpeg;base64,' + d.image;" \
        "});" \
        "</script>"
    );
    
    webview_run(wv);
    webview_destroy(wv);
}
```

### Python Client Example

```python
import socketio
import base64
from PIL import Image
from io import BytesIO

# Create Socket.IO client
sio = socketio.Client()

@sio.on('frame')
def on_frame(data):
    """Handle incoming frame"""
    # Decode base64 JPEG
    img_data = base64.b64decode(data['image'])
    img = Image.open(BytesIO(img_data))
    
    # Display or process frame
    img.show()  # or save, analyze, etc.
    
    print(f"Frame {data['timestamp']}: {data['size']} bytes")

@sio.on('subscribed')
def on_subscribed(data):
    print(f"Subscribed to {data['session_id']}")
    print(f"FPS: {data['fps']}, Quality: {data['quality']}")

# Connect to server
sio.connect('http://localhost:5000')

# Subscribe to session
sio.emit('subscribe', {'session_id': 'my_session'})

# Send input events
sio.emit('input:click', {'x': 100, 'y': 200})

# Keep connection alive
try:
    sio.wait()
except KeyboardInterrupt:
    sio.disconnect()
```

## Session Keepalive

Sessions automatically expire after inactivity (default: 300 seconds). Send keepalive signals to prevent timeout.

### REST API Method

```bash
# Send keepalive every 60 seconds
curl -X POST http://localhost:5000/api/session/my_session/keepalive
```

### WebSocket Method (Automatic)

When using WebSocket streaming, frame subscriptions automatically act as keepalive signals. No manual keepalive needed.

### Python Keepalive Loop

```python
import requests
import time
import threading

def keepalive_loop(session_id, interval=60):
    """Background keepalive thread"""
    while True:
        try:
            requests.post(f'http://localhost:5000/api/session/{session_id}/keepalive')
            print(f"Keepalive sent for {session_id}")
        except Exception as e:
            print(f"Keepalive error: {e}")
        time.sleep(interval)

# Start keepalive thread
thread = threading.Thread(target=keepalive_loop, args=('my_session',), daemon=True)
thread.start()
```

## Legacy Method: Polling (Fallback)

For clients that cannot use WebSocket, polling endpoints are available (but not recommended due to higher latency and server load).

### Polling Endpoints

#### GET `/api/session/{id}/frame`

Get current frame as PNG image (binary).

```bash
# Poll for frames
while true; do
    curl http://localhost:5000/api/session/my_session/frame -o frame.png
    # Display frame.png
    sleep 0.1  # 10 FPS
done
```

#### GET `/api/session/{id}/frame/data`

Get current frame as JSON with base64-encoded PNG.

```bash
curl http://localhost:5000/api/session/my_session/frame/data
```

Response:
```json
{
    "success": true,
    "session_id": "my_session",
    "timestamp": 1763462068.71,
    "frame": "base64_encoded_png_data...",
    "format": "png"
}
```

#### GET `/api/session/{id}/viewer`

HTML5 auto-refresh viewer (1 FPS polling).

```bash
# Open in browser
http://localhost:5000/api/session/my_session/viewer
```

### Polling vs WebSocket Comparison

| Feature | WebSocket | Polling |
|---------|-----------|---------|
| Frame Rate | 30 FPS | 1-10 FPS |
| Latency | 50-100ms | 200-500ms |
| Server Load | Low | High |
| Network Usage | Efficient | Wasteful |
| Interactivity | Real-time | Delayed |
| Recommended | ✅ Yes | ❌ Fallback only |

## Configuration

### Environment Variables

```bash
# Session timeout (seconds)
SESSION_TIMEOUT=300  # 5 minutes default

# Legacy: Frame capture interval for polling (not used by WebSocket)
FRAME_CAPTURE_INTERVAL=1.0  # 1 second
```

### Docker Compose

```yaml
renderer:
  environment:
    - SESSION_TIMEOUT=600  # 10 minutes
```

## Performance Tuning

### For Fast Networks (>5 Mbps)

```javascript
// Maximize quality and frame rate
socket.emit('quality:set', { quality: 90 });
socket.emit('fps:set', { fps: 30 });
socket.emit('adaptive:toggle', { enabled: false });  // Manual control
```

### For Slow Networks (<2 Mbps)

```javascript
// Reduce bandwidth usage
socket.emit('quality:set', { quality: 50 });
socket.emit('fps:set', { fps: 15 });
socket.emit('adaptive:toggle', { enabled: true });  // Let system adapt
```

### Adaptive Mode (Recommended)

```javascript
// Enable automatic quality adjustment (default)
socket.emit('adaptive:toggle', { enabled: true });

// System automatically adjusts:
// - Fast (>5 Mbps): Quality 90, FPS 30
// - Normal (2-5 Mbps): Quality 75, FPS 20
// - Slow (<2 Mbps): Quality 50, FPS 10
```

## Troubleshooting

### WebSocket Connection Fails

1. Check firewall allows port 5000
2. Verify Socket.IO client version matches server (4.x)
3. Check CORS settings if cross-origin
4. Use `ws://` (not `wss://`) for local testing

```bash
# Test WebSocket endpoint
curl -i -N \
  -H "Connection: Upgrade" \
  -H "Upgrade: websocket" \
  -H "Sec-WebSocket-Key: test" \
  -H "Sec-WebSocket-Version: 13" \
  http://localhost:5000/socket.io/
```

### Low Frame Rate

1. Check network bandwidth
2. Verify CPU usage on server
3. Lower quality or FPS manually
4. Enable adaptive mode

```javascript
// Monitor statistics
socket.on('frame', (data) => {
    console.log(`Frame: ${data.size} bytes, Latency: ${Date.now() - data.timestamp}ms`);
});
```

### High Latency

1. Use local network deployment
2. Reduce quality to 60-70
3. Check server CPU usage
4. Verify no network throttling

### Session Timeout

1. Enable WebSocket streaming (automatic keepalive)
2. Send manual keepalive every 60 seconds
3. Increase `SESSION_TIMEOUT` environment variable

## Security Considerations

### Production Deployment

1. **Use WSS (WebSocket Secure)**
   ```javascript
   const socket = io('https://server:5000', {
       secure: true,
       rejectUnauthorized: true
   });
   ```

2. **Add Authentication**
   ```javascript
   const socket = io('https://server:5000', {
       auth: {
           token: 'your-jwt-token'
       }
   });
   ```

3. **Rate Limiting**: Limit frame rate per client
4. **Input Validation**: Sanitize all input events
5. **Session Limits**: Limit concurrent sessions per user/IP

## Use Cases

1. **ThreadX RTOS**: Embedded systems with WebView
2. **IoT Devices**: Low-power devices with web browsing needs
3. **Thin Clients**: Kiosks and workstations
4. **Mobile Apps**: Android/iOS apps with WebView
5. **Testing**: Automated website testing and monitoring

## Additional Resources

- [Architecture Documentation](ARCHITECTURE.md) - Detailed system design
- [README](README.md) - Getting started guide
- [Android WebApp](android_webapp/README.md) - Mobile app integration
- [Device Simulator](device_simulator/README.md) - Test tool

## Future Enhancements

- [x] WebSocket streaming (completed)
- [x] Adaptive quality (completed)
- [x] Interactive input (completed)
- [ ] WebRTC for P2P streaming
- [ ] Multi-user collaboration
- [ ] Session recording and playback
- [ ] Browser extensions support

---

**WebSocket streaming provides the best experience for real-time website rendering on low-end devices.**
