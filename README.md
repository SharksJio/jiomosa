# Jiomosa - Cloud Website Renderer

A cloud-based solution that uses **WebSocket streaming** and **Selenium** to render rich websites with minimal latency, designed for low-end devices like RTOS systems (e.g., ThreadX) with limited resources (512MB RAM).

## 🎯 Overview

Jiomosa enables rendering of complex, resource-intensive websites on powerful cloud infrastructure and streams the visual output to low-end devices in real-time via WebSocket. This approach is similar to cloud gaming services but optimized for web browsing.

### Key Features

- **WebSocket Streaming**: Real-time bidirectional streaming with Socket.IO at 30 FPS
- **Cloud-Based Rendering**: Websites run on powerful servers, not on the client device
- **Adaptive Quality**: Automatic bandwidth detection and quality adjustment (10-90 JPEG quality)
- **Low Latency**: Direct frame streaming optimized for smooth experience
- **Interactive Input**: Click, scroll, and text input support via WebSocket
- **Resource Efficient**: Client devices only display frames, minimal CPU/memory usage
- **Scalable**: Docker-based architecture that can be deployed anywhere
- **Multiple Sessions**: Support for concurrent browser sessions
- **Session Keepalive**: Maintain browser sessions with heartbeat signals
- **ThreadX Integration**: Perfect for embedded systems with WebView support
- **Device Simulator**: Test device emulator for demonstrating integration
- **Android WebApp**: Mobile-friendly app launcher with popular website shortcuts
- **Easy Testing**: Built-in CI/CD pipeline for automated testing

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Client Device                         │
│                    (Low-end hardware)                        │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  WebSocket Client (Socket.IO)                        │  │
│  │  - Receives JPEG frames at 30 FPS                    │  │
│  │  - Sends input events (click, scroll, text)          │  │
│  │  - Adaptive quality based on bandwidth               │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────┬────────────────────────────────────────┘
                     │ WebSocket (bidirectional, Socket.IO)
                     │ 
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                      Cloud Infrastructure                    │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │   Renderer Service (Flask + Socket.IO)               │  │
│  │   Port: 5000                                         │  │
│  │   - WebSocket server for real-time streaming        │  │
│  │   - REST API for session management                 │  │
│  │   - Adaptive quality control (bandwidth monitor)    │  │
│  │   - Input event processing                          │  │
│  │   - Frame capture at 30 FPS                         │  │
│  └─────────┬────────────────────────────────────────────┘  │
│            │ Selenium WebDriver Protocol                    │
│            ▼                                                 │
│  ┌──────────────────────────────────────────────────────┐  │
│  │   Selenium Grid + Chrome Browser                     │  │
│  │   Ports: 4444 (Selenium), 7900 (noVNC - optional)   │  │
│  │   - Renders actual websites with full JS support    │  │
│  │   - Captures screenshots at 30 FPS                   │  │
│  │   - Executes input commands (click, scroll, type)   │  │
│  │   - noVNC for direct browser viewing (alternative)  │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │   Android WebApp (Flask)                             │  │
│  │   Port: 9000                                         │  │
│  │   - Mobile app launcher UI with website shortcuts   │  │
│  │   - WebSocket client integration                    │  │
│  │   - Perfect for Android WebView embedding           │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Components

1. **Renderer Service** (Python/Flask + Socket.IO)
   - WebSocket server for real-time 30 FPS streaming
   - REST API for session lifecycle management
   - Selenium WebDriver integration for browser control
   - Adaptive quality with bandwidth monitoring
   - JPEG compression with quality range 10-90
   - Input event processing (click, scroll, text)
   - Session keepalive and timeout management

2. **Selenium Grid + Chrome**
   - Chromium browser in Docker container
   - Screenshot capture at 30 FPS for streaming
   - JavaScript execution and modern web standards
   - noVNC server (port 7900) for optional direct viewing
   - Multiple concurrent sessions support

3. **Android WebApp** (Flask web app)
   - Mobile-friendly app launcher interface
   - 16+ popular website shortcuts (Facebook, YouTube, Gmail, etc.)
   - WebSocket client for real-time streaming
   - Designed for Android WebView integration
   - Custom URL support

4. **Device Simulator** (Standalone test tool)
   - Emulates ThreadX, IoT, and other low-end devices
   - Shows website content without browser UI
   - Multiple device profiles (512MB-2GB RAM)
   - Perfect for testing and demos

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- 4GB+ RAM recommended
- Ports 5000, 4444, 7900, 9000 available

### Installation

1. Clone the repository:
```bash
git clone https://github.com/SharksJio/jiomosa.git
cd jiomosa
```

2. Start all services:
```bash
docker compose up -d
```

3. Wait 30-60 seconds for services to initialize:
```bash
docker compose ps
```

### Using the Android WebApp (Recommended)

The easiest way to get started:

```bash
# Open in browser
http://localhost:9000

# Features:
# - Tap any app icon to launch that website
# - WebSocket streaming at 30 FPS
# - Adaptive quality based on bandwidth
# - Interactive touch support
```

### Using the REST API + WebSocket

#### 1. Create a browser session:
```bash
curl -X POST http://localhost:5000/api/session/create \
  -H "Content-Type: application/json" \
  -d '{"session_id": "my_session"}'
```

Response:
```json
{
  "success": true,
  "session_id": "my_session",
  "created_at": 1763462068.71,
  "websocket_url": "ws://localhost:5000/socket.io/"
}
```

#### 2. Load a website:
```bash
curl -X POST http://localhost:5000/api/session/my_session/load \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'
```

#### 3. Connect WebSocket client to receive frames:

```javascript
// Using Socket.IO client
const socket = io('http://localhost:5000');

// Subscribe to session
socket.emit('subscribe', { session_id: 'my_session' });

// Receive frames at 30 FPS
socket.on('frame', (data) => {
    // data.image: base64-encoded JPEG
    // data.timestamp: frame timestamp
    // data.size: frame size in bytes
    document.getElementById('browser-view').src = 
        `data:image/jpeg;base64,${data.image}`;
});

// Send click input
socket.emit('input:click', { x: 100, y: 200 });

// Send scroll input
socket.emit('input:scroll', { deltaX: 0, deltaY: 50 });

// Send text input
socket.emit('input:text', { text: 'hello world' });

// Set quality (10-100, disables adaptive mode)
socket.emit('quality:set', { quality: 75 });

// Set FPS (1-60, disables adaptive mode)
socket.emit('fps:set', { fps: 30 });

// Toggle adaptive mode back on
socket.emit('adaptive:toggle', { enabled: true });
```

#### 4. Close the session:
```bash
curl -X POST http://localhost:5000/api/session/my_session/close
```

### Alternative: Direct Browser Viewing via noVNC

For debugging or direct viewing:
```
http://localhost:7900
Password: secret
```

## 📡 API Endpoints

### REST API (Session Management)

#### Service Information
- `GET /health` - Health check
- `GET /api/info` - Service information and endpoints

#### Session Management
- `POST /api/session/create` - Create a new browser session
- `POST /api/session/{id}/load` - Load a URL
- `GET /api/session/{id}/info` - Get session info
- `POST /api/session/{id}/keepalive` - Send keepalive heartbeat
- `POST /api/session/{id}/close` - Close session
- `GET /api/sessions` - List all active sessions

#### Legacy Polling Endpoints (for compatibility)
- `GET /api/session/{id}/frame` - Get current frame as PNG (polling)
- `GET /api/session/{id}/frame/data` - Get frame as base64 JSON
- `GET /api/session/{id}/viewer` - HTML5 viewer with auto-refresh

### WebSocket API (Real-time Streaming)

**Connection**: `ws://localhost:5000/socket.io/`

#### Client → Server Events
- `subscribe` - Subscribe to session frames
  - Data: `{session_id: "session_id"}`
- `unsubscribe` - Unsubscribe from session
- `input:click` - Send click event
  - Data: `{x: number, y: number}`
- `input:scroll` - Send scroll event
  - Data: `{deltaX: number, deltaY: number}`
- `input:text` - Send text input
  - Data: `{text: string}`
- `quality:set` - Set JPEG quality (10-100)
  - Data: `{quality: number}`
- `fps:set` - Set target FPS (1-60)
  - Data: `{fps: number}`
- `adaptive:toggle` - Toggle adaptive mode
  - Data: `{enabled: boolean}`

#### Server → Client Events
- `frame` - Frame data (30 FPS)
  - Data: `{image: base64_jpeg, timestamp: number, size: number}`
- `subscribed` - Subscription confirmed
- `unsubscribed` - Unsubscription confirmed
- `input:acknowledged` - Input event processed
- `quality:updated` - Quality changed
- `fps:updated` - FPS changed
- `adaptive:updated` - Adaptive mode toggled
- `error` - Error message
- `status` - Status update

## 🖥️ Device Simulator

Test the renderer with a device simulator:

```bash
# Start Jiomosa services
docker compose up -d

# Start device simulator (separate terminal)
cd device_simulator
./run_simulator.sh

# Open simulator
http://localhost:8000

# Try different device profiles:
# - ThreadX RTOS (512MB RAM, 1024x600)
# - IoT Device (256MB RAM, 800x480)
# - Thin Client (1GB RAM, 1280x720)
# - Legacy System (2GB RAM, 1366x768)
```

## 🧪 Testing

### Run Tests

```bash
# Start services first
docker compose up -d
sleep 30

# Run integration tests
python tests/test_renderer.py
python tests/test_websocket_connection.py
python tests/test_integration_phase2_3.py
python tests/test_android_webapp.py

# Test with real websites
bash tests/test_websites.sh
bash tests/test_external_websites.sh

# Stop services
docker compose down
```

### Manual Testing

```bash
# Test health
curl http://localhost:5000/health

# Create session and load website
curl -X POST http://localhost:5000/api/session/create \
  -H "Content-Type: application/json" \
  -d '{"session_id": "test1"}'

curl -X POST http://localhost:5000/api/session/test1/load \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.example.com"}'

# View in Android WebApp
http://localhost:9000
```

## 🔧 Configuration

### Environment Variables

Configure via `docker-compose.yml`:

```yaml
renderer:
  environment:
    - SELENIUM_HOST=chrome
    - SELENIUM_PORT=4444
    - SESSION_TIMEOUT=300          # Session timeout (seconds)
    - FRAME_CAPTURE_INTERVAL=1.0   # Not used (WebSocket streams at configured FPS)
    - FLASK_DEBUG=false            # Enable debug mode (not recommended)
```

### Scaling

Scale Chrome instances for more concurrent sessions:

```bash
docker compose up -d --scale chrome=3
```

## 🎯 Use Cases

1. **IoT Devices**: Browse modern websites on resource-constrained devices
2. **Legacy Systems**: Access modern web on old hardware (ThreadX, FreeRTOS)
3. **Thin Clients**: Deploy in environments with minimal client resources
4. **Android Apps**: Build mobile apps that browse websites without embedded browsers
5. **Embedded Systems**: Integrate web browsing into embedded devices
6. **Testing**: Automated website testing and screenshot capture
7. **Remote Access**: Provide web browsing in restricted environments
8. **Kiosks**: Build touch-screen kiosk applications

## 🛠️ Development

### Project Structure

```
jiomosa/
├── docker-compose.yml            # Service orchestration
├── renderer/                     # Renderer service (WebSocket streaming)
│   ├── app.py                   # Flask app with Socket.IO
│   ├── websocket_handler.py     # WebSocket streaming logic
│   ├── requirements.txt
│   └── Dockerfile
├── android_webapp/               # Android WebApp
│   ├── webapp.py                # Flask webapp
│   ├── static/
│   │   └── streaming.js         # WebSocket client library
│   ├── requirements.txt
│   └── Dockerfile
├── device_simulator/             # Device simulator
│   ├── simulator.py
│   ├── run_simulator.sh
│   └── README.md
├── tests/                        # Integration tests
│   ├── test_renderer.py
│   ├── test_websocket_connection.py
│   ├── test_integration_phase2_3.py
│   ├── test_android_webapp.py
│   └── test_device_simulator.py
├── .github/workflows/ci.yml      # CI/CD pipeline
└── README.md
```

### Building Locally

```bash
# Build renderer
docker compose build renderer

# Build android webapp
docker compose build android-webapp

# Start all services
docker compose up -d
```

### Debugging

```bash
# View logs
docker compose logs -f renderer
docker compose logs -f chrome
docker compose logs -f android-webapp

# Access container shell
docker exec -it jiomosa-renderer bash

# Check Selenium status
curl http://localhost:4444/status
```

## 📊 Performance

### Streaming Performance
- **Frame Rate**: 30 FPS (adjustable 1-60 FPS)
- **Quality**: JPEG 10-90 (adaptive based on bandwidth)
- **Latency**: ~50-100ms (local network)
- **Bandwidth**:
  - High quality (90): ~2-5 Mbps
  - Medium quality (75): ~1-2 Mbps
  - Low quality (50): ~0.5-1 Mbps

### Resource Usage
- **Renderer**: ~100MB RAM, <5% CPU
- **Chrome**: ~500MB RAM per session, ~30% CPU while rendering
- **Android WebApp**: ~50MB RAM, <1% CPU
- **Client**: Minimal (just displays frames)

### Optimization Tips
1. Enable adaptive quality mode (enabled by default)
2. Adjust FPS based on use case (30 for smooth, 15 for bandwidth savings)
3. Use lower resolution for mobile devices
4. Enable compression in Socket.IO transport

## 🔒 Security Considerations

This is a **PoC/Demo** - add these for production:

1. **Authentication**: Add JWT or OAuth to Renderer API and WebSocket
2. **HTTPS/WSS**: Use TLS for encrypted connections
3. **Rate Limiting**: Prevent API and WebSocket abuse
4. **Firewall Rules**: Restrict port access
5. **Session Limits**: Limit sessions per user/IP
6. **Input Validation**: Sanitize all URL and input parameters
7. **CORS**: Configure proper CORS policies
8. **Container Security**: Run as non-root, use security profiles

## 🚀 CI/CD Pipeline

GitHub Actions automatically:
1. Builds Docker images
2. Starts services
3. Runs integration tests
4. Tests WebSocket connectivity
5. Tests multiple websites
6. Reports results

Workflow triggers:
- Push to main/develop branches
- Pull requests
- Manual dispatch

## 📚 Documentation

- [Architecture Details](ARCHITECTURE.md) - Detailed architecture documentation
- [Deployment Guide](DEPLOYMENT.md) - Production deployment instructions
- [Quick Start](QUICKSTART.md) - Getting started guide
- [Usage Guide](USAGE.md) - Detailed usage examples
- [Codespaces](CODESPACES.md) - GitHub Codespaces setup

## 💡 Future Enhancements

- [x] WebSocket-based frame streaming (completed)
- [x] Adaptive quality control (completed)
- [x] Real-time input events (completed)
- [ ] Multi-user collaboration (shared sessions)
- [ ] Recording and playback
- [ ] Performance metrics dashboard
- [ ] WebRTC support for P2P streaming
- [ ] Load balancing across browser nodes
- [ ] Kubernetes deployment manifests
- [ ] Browser extensions support

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📝 License

This project is provided as-is for educational and demonstration purposes.

## 🔗 References

- [Socket.IO](https://socket.io/) - WebSocket library
- [Selenium WebDriver](https://www.selenium.dev/)
- [Docker Selenium](https://github.com/SeleniumHQ/docker-selenium)
- [ThreadX RTOS](https://azure.microsoft.com/services/rtos/)
- [Flask-SocketIO](https://flask-socketio.readthedocs.io/)

---

**Built with ❤️ for low-end devices everywhere**
