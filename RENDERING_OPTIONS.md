# Jiomosa Rendering & Streaming Options

## Overview

Jiomosa supports multiple rendering and streaming methods, each with different trade-offs for latency, quality, and resource usage.

---

## 🎯 **Option 1: Direct Framebuffer Streaming (RECOMMENDED for Mobile)**

### How It Works
- Selenium WebDriver takes screenshots directly from Chrome
- Images encoded as PNG
- Served via REST API endpoints
- Client polls for updates (30 FPS - optimized for smooth streaming)

### Endpoints
```
GET  /api/session/{id}/frame       - PNG image (binary)
GET  /api/session/{id}/frame/data  - Base64 JSON
GET  /api/session/{id}/viewer      - HTML5 auto-refresh viewer
```

### Pros ✅
- **Zero VNC overhead** - Direct Selenium screenshots
- **No UI controls** - Clean display, perfect for WebView
- **Simple integration** - Just an `<img>` tag or fetch()
- **CORS-friendly** - Same-origin requests
- **Mobile-optimized** - Works in Android WebView
- **Lightweight** - No VNC client needed
- **Cross-platform** - Works everywhere

### Cons ❌
- Higher CPU on server (continuous screenshot encoding at 30 FPS)
- Higher bandwidth usage than 1 FPS mode
- Polling overhead (can use WebSocket for push)
- No mouse/keyboard input relay (need separate API)

### Use Cases
- 📱 Android WebView apps
- 🌐 Web-based dashboards
- 📊 Monitoring/screenshot capture
- 🤖 Automation testing
- 📸 Visual regression testing

### Example Integration
```javascript
// Auto-refreshing image viewer at 30 FPS
const img = document.getElementById('browser-frame');
setInterval(async () => {
    const response = await fetch(`/api/session/my_session/frame?t=${Date.now()}`);
    const blob = await response.blob();
    img.src = URL.createObjectURL(blob);
}, 33); // 33ms = 30 FPS
```

---

## 🖥️ **Option 2: VNC + noVNC (Current Default)**

### How It Works
- Chrome container runs VNC server (x11vnc)
- noVNC provides HTML5 VNC client
- Real-time desktop streaming protocol
- Interactive mouse/keyboard support

### Access
```
http://localhost:7900/?autoconnect=true&resize=scale
```

### Pros ✅
- Real-time streaming (15-30 FPS)
- Interactive (mouse, keyboard, clipboard)
- Low server CPU usage
- Battle-tested protocol
- Good for desktop viewing

### Cons ❌
- **Visible UI controls** (noVNC toolbar, buttons)
- CORS issues (iframe cross-origin)
- Requires VNC client or noVNC
- Higher bandwidth usage
- Not ideal for mobile WebView
- Additional port exposure (5900, 7900)

### Use Cases
- 💻 Desktop remote access
- 🎮 Interactive browsing sessions
- 🖱️ Mouse/keyboard control needed
- 🔧 Manual testing/debugging

---

## 🚀 **Option 3: Apache Guacamole (Enterprise)**

### How It Works
- Guacamole daemon (guacd) proxies VNC
- Translates VNC → Guacamole protocol
- Web-based management interface
- PostgreSQL for connection management

### Access
```
http://localhost:8080/guacamole/
Login: guacadmin / guacadmin
```

### Pros ✅
- Optimized for low bandwidth
- Better compression than raw VNC
- User authentication/authorization
- Connection sharing
- Recording capabilities
- Multi-protocol (RDP, SSH, VNC)

### Cons ❌
- Complex architecture (3+ services)
- Overkill for simple use cases
- Requires database
- More memory/CPU overhead
- Still has UI controls
- Learning curve

### Use Cases
- 🏢 Enterprise deployments
- 👥 Multi-user environments
- 🔐 Authenticated access control
- 📹 Session recording needed
- 🌐 Multiple protocol support

---

## 🔮 **Option 4: WebRTC Streaming (Future Enhancement)**

### How It Works
- Real-time peer-to-peer streaming
- Browser MediaStream API
- WebRTC server (Janus/Kurento)
- Ultra-low latency (<100ms)

### Pros ✅
- **Lowest latency possible** (sub-100ms)
- Adaptive bitrate
- Peer-to-peer (less server load)
- Native browser support
- Interactive audio/video

### Cons ❌
- Complex implementation
- NAT traversal issues
- TURN/STUN server needed
- Browser compatibility concerns
- Not yet implemented in Jiomosa

### Use Cases
- 🎮 Real-time gaming
- 🎥 Live video streaming
- 🗣️ Video conferencing
- ⚡ Latency-critical apps

---

## 📊 **Comparison Matrix**

| Feature | Framebuffer | noVNC | Guacamole | WebRTC |
|---------|------------|-------|-----------|--------|
| **Latency** | Low (33ms) | Low (60ms) | Medium (150ms) | Ultra-low (50ms) |
| **Frame Rate** | 30 FPS | 15-30 FPS | 15-30 FPS | 30-60 FPS |
| **Server CPU** | High | Low | Low | Medium |
| **Bandwidth** | High | Medium | Low | Adaptive |
| **Mobile Support** | ✅ Excellent | ⚠️ Limited | ⚠️ Limited | ✅ Good |
| **UI Controls** | ✅ None | ❌ Visible | ❌ Visible | ✅ None |
| **Interactive** | ❌ No | ✅ Yes | ✅ Yes | ✅ Yes |
| **CORS Issues** | ✅ None | ❌ Yes | ❌ Yes | ✅ None |
| **Complexity** | 🟢 Simple | 🟡 Medium | 🔴 Complex | 🔴 Complex |
| **Implementation** | ✅ Ready | ✅ Ready | ✅ Ready | ❌ TODO |

---

## 🎯 **Recommendations by Use Case**

### 📱 Android WebView App (Your Current Need)
**Use: Direct Framebuffer Streaming**
- Clean display without VNC controls
- No CORS issues
- Simple WebView integration
- Lower bandwidth for mobile

### 💻 Desktop Remote Access
**Use: noVNC or Guacamole**
- Full interactivity
- Better frame rates
- Keyboard/mouse support

### 🏢 Enterprise Multi-User
**Use: Guacamole**
- User authentication
- Session management
- Recording capabilities
- Connection sharing

### ⚡ Real-Time Gaming/Streaming
**Use: WebRTC (Future)**
- Ultra-low latency
- Adaptive quality
- P2P efficiency

---

## 🔧 **Implementation Guide**

### Switch Android Webapp to Framebuffer Streaming

Instead of embedding noVNC iframe:
```html
<!-- OLD: noVNC iframe -->
<iframe src="http://vnc-server:7900/"></iframe>

<!-- NEW: Direct framebuffer -->
<img id="browser-frame" src="/api/session/my_session/frame" />
<script>
    setInterval(() => {
        document.getElementById('browser-frame').src = 
            `/api/session/my_session/frame?t=${Date.now()}`;
    }, 1000);
</script>
```

### Enable WebSocket Push (Optional)
```python
# renderer/app.py
from flask_socketio import SocketIO

socketio = SocketIO(app)

@socketio.on('subscribe')
def handle_subscribe(session_id):
    # Push frames to client instead of polling
    emit('frame', {'data': base64_frame})
```

---

## 📈 **Performance Tuning**

### Framebuffer Streaming
```python
# Adjust capture interval (webapp.py)
streamingInterval = setInterval(captureFrame, 33);  // 30 FPS (default)
streamingInterval = setInterval(captureFrame, 16);  // 60 FPS (higher CPU)
streamingInterval = setInterval(captureFrame, 50);  // 20 FPS (lower bandwidth)

# Reduce image quality for lower bandwidth (renderer/app.py)
screenshot.save(buffer, format='JPEG', quality=70)

# Use PNG for best quality (current default)
screenshot = self.driver.get_screenshot_as_png()
```

### VNC Streaming
```bash
# Reduce color depth
VNC_COLOR_DEPTH=16

# Lower frame rate
VNC_FRAME_RATE=15

# Enable compression
VNC_COMPRESSION=9
```

---

## 🎬 **Next Steps**

1. ✅ **Immediate**: Switch Android webapp to framebuffer streaming
2. 🔄 **Short-term**: Add WebSocket support for push updates
3. 🚀 **Long-term**: Implement WebRTC for real-time streaming
4. 📊 **Optional**: Keep VNC/Guacamole for desktop access

---

## 📚 **References**

- [Selenium Screenshots](https://www.selenium.dev/documentation/webdriver/interactions/windows/#take-element-screenshot)
- [noVNC Project](https://github.com/novnc/noVNC)
- [Apache Guacamole](https://guacamole.apache.org/)
- [WebRTC API](https://developer.mozilla.org/en-US/docs/Web/API/WebRTC_API)
- [Flask-SocketIO](https://flask-socketio.readthedocs.io/)

---

**Conclusion**: For your Android WebView use case, **direct framebuffer streaming** is the optimal solution. It eliminates VNC/noVNC complexity, provides clean display, and works perfectly in WebView environments.
