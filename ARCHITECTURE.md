# Jiomosa Architecture

## Overview

Jiomosa is a cloud-based website rendering solution that uses **WebSocket streaming** to enable low-end devices (like RTOS systems with 512MB RAM) to access modern, resource-intensive websites by offloading rendering to powerful cloud infrastructure.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     Low-End Client Device                        │
│                   (ThreadX RTOS, 512MB RAM)                      │
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │          WebSocket Client (Socket.IO)                     │  │
│  │          Minimal resource requirements                    │  │
│  │          - Receives JPEG frames at 30 FPS                 │  │
│  │          - Sends input events (click, scroll, text)       │  │
│  │          - Adaptive quality based on bandwidth            │  │
│  └──────────────┬────────────────────────────────────────────┘  │
└─────────────────┼───────────────────────────────────────────────┘
                  │
                  │ WebSocket Protocol (Socket.IO)
                  │ Bidirectional communication
                  │ - Frame streaming: Server → Client (30 FPS)
                  │ - Input events: Client → Server
                  │
                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Cloud Infrastructure                          │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │        Renderer Service (Flask + Socket.IO)               │  │
│  │        Port: 5000                                         │  │
│  │                                                           │  │
│  │  ┌────────────────────────────────────────────────────┐  │  │
│  │  │  WebSocket Server (Socket.IO)                      │  │  │
│  │  │  - Streams frames at 30 FPS                        │  │  │
│  │  │  - Processes input events                          │  │  │
│  │  │  - Manages subscriptions                           │  │  │
│  │  └────────────────────────────────────────────────────┘  │  │
│  │  ┌────────────────────────────────────────────────────┐  │  │
│  │  │  WebSocket Handler                                 │  │  │
│  │  │  - Bandwidth monitoring                            │  │  │
│  │  │  - Adaptive quality control (JPEG 10-90)          │  │  │
│  │  │  - Frame compression and encoding                  │  │  │
│  │  └────────────────────────────────────────────────────┘  │  │
│  │  ┌────────────────────────────────────────────────────┐  │  │
│  │  │  REST API                                          │  │  │
│  │  │  - Session lifecycle management                    │  │  │
│  │  │  - URL loading                                     │  │  │
│  │  │  - Session keepalive                               │  │  │
│  │  └────────────────────────────────────────────────────┘  │  │
│  └───────▲──────────────────────────────────────────────────┘  │
│          │                                                       │
│          │ Selenium WebDriver Protocol                          │
│          │                                                       │
│  ┌───────▼──────────────────────────────────────────────────┐  │
│  │     Selenium Grid + Chrome Browser                       │  │
│  │     Ports: 4444 (Selenium), 7900 (noVNC - optional)     │  │
│  │                                                           │  │
│  │  ┌────────────────────────────────────────────────────┐  │  │
│  │  │    Chrome Browser with Selenium WebDriver          │  │  │
│  │  │    - Renders actual websites                       │  │  │
│  │  │    - JavaScript execution                          │  │  │
│  │  │    - Full web standards support                    │  │  │
│  │  │    - Captures screenshots at 30 FPS                │  │  │
│  │  └────────────────────────────────────────────────────┘  │  │
│  │  ┌────────────────────────────────────────────────────┐  │  │
│  │  │    noVNC Server (Optional)                         │  │  │
│  │  │    - Direct browser viewing alternative            │  │  │
│  │  │    - Port 7900, password: secret                   │  │  │
│  │  └────────────────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │        Android WebApp (Flask)                             │  │
│  │        Port: 9000                                         │  │
│  │                                                           │  │
│  │  ┌────────────────────────────────────────────────────┐  │  │
│  │  │  Mobile App Launcher UI                            │  │  │
│  │  │  - 16+ popular website shortcuts                   │  │  │
│  │  │  - WebSocket client integration                    │  │  │
│  │  │  - Perfect for Android WebView                     │  │  │
│  │  └────────────────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. Renderer Service (Port 5000)

**Technology**: Python 3.11, Flask, Flask-SocketIO, Selenium WebDriver

**Responsibilities**:
- WebSocket server for real-time frame streaming (30 FPS)
- REST API for session lifecycle management
- Selenium WebDriver integration for browser control
- Adaptive quality and bandwidth monitoring
- Input event processing (click, scroll, text)
- Session keepalive and timeout management

**Key Features**:
- **WebSocket Streaming**: Socket.IO for bidirectional communication
- **Frame Rate**: 30 FPS default (configurable 1-60 FPS)
- **Quality**: JPEG compression with quality 10-90 (adaptive)
- **Bandwidth Monitoring**: Automatic quality adjustment based on network speed
- **Multiple Sessions**: Concurrent browser session support
- **Session Timeout**: Configurable timeout with automatic cleanup

**REST API Endpoints**:
```
GET  /health                         - Service health check
GET  /api/info                       - Service information
POST /api/session/create             - Create browser session
POST /api/session/{id}/load          - Load URL in session
GET  /api/session/{id}/info          - Get session information
POST /api/session/{id}/keepalive     - Send keepalive heartbeat
POST /api/session/{id}/close         - Close browser session
GET  /api/sessions                   - List all sessions
```

**WebSocket Events**:
- Client → Server:
  - `subscribe` - Subscribe to session frames
  - `unsubscribe` - Unsubscribe from session
  - `input:click` - Send click event
  - `input:scroll` - Send scroll event
  - `input:text` - Send text input
  - `quality:set` - Set JPEG quality
  - `fps:set` - Set target FPS
  - `adaptive:toggle` - Toggle adaptive mode

- Server → Client:
  - `frame` - Frame data (JPEG base64)
  - `subscribed` - Subscription confirmed
  - `input:acknowledged` - Input processed
  - `quality:updated` - Quality changed
  - `fps:updated` - FPS changed
  - `adaptive:updated` - Adaptive mode toggled
  - `error` - Error message

**Code Structure**:
- `app.py` - Main Flask application with WebSocket server
- `websocket_handler.py` - WebSocket streaming logic
  - `WebSocketHandler` - Manages WebSocket connections
  - `BandwidthMonitor` - Monitors bandwidth and recommends quality
  - `FrameDelta` - Detects frame changes (future optimization)

### 2. Selenium Grid + Chrome (Ports 4444, 5900, 7900)

**Technology**: Selenium Standalone Chrome, Chromium Browser

**Responsibilities**:
- Executes actual web browser instances
- Renders websites with full JavaScript support
- Provides screenshots for frame streaming
- Handles web standards and modern features
- Optional noVNC server for direct viewing

**Ports**:
- 4444: Selenium WebDriver API
- 5900: VNC server (not used by WebSocket streaming)
- 7900: noVNC web interface (optional direct access)

**Features**:
- Full Chrome browser with latest features
- Hardware acceleration disabled (for stability)
- Shared memory (2GB) for performance
- Configurable session limits (5 concurrent)
- Screenshot capture at 30 FPS

**Performance**:
- RAM: ~500MB per browser session
- CPU: ~30% per active session
- Screenshot latency: <50ms

### 3. Android WebApp (Port 9000)

**Technology**: Python 3.11, Flask, Socket.IO Client

**Responsibilities**:
- Mobile-friendly app launcher interface
- WebSocket client for frame streaming
- Pre-configured website shortcuts
- Android WebView integration

**Features**:
- 16+ popular website shortcuts (Facebook, YouTube, Gmail, etc.)
- WebSocket streaming integration
- Touch-friendly interface
- Custom URL support
- Session management proxy

**Code Structure**:
- `webapp.py` - Flask application
- `static/streaming.js` - WebSocket client library

## Data Flow

### WebSocket Streaming Sequence

```
1. Client Connects
   └─> WebSocket connection to renderer:5000/socket.io/

2. Client Subscribes
   └─> Emit 'subscribe' event with session_id
       └─> Renderer Service validates session
           └─> Success: Start streaming frames

3. Frame Streaming Loop (30 FPS)
   └─> Every 33ms:
       ├─> Renderer captures screenshot from Chrome
       ├─> Compress to JPEG (quality 10-90, adaptive)
       ├─> Encode to base64
       ├─> Emit 'frame' event to subscribed clients
       └─> Monitor bandwidth and adjust quality

4. Client Input
   └─> User clicks/scrolls/types
       └─> Client emits input event
           └─> Renderer forwards to Selenium
               └─> Chrome executes action
                   └─> Next frame reflects change

5. Adaptive Quality
   └─> Bandwidth Monitor tracks:
       ├─> Frame sizes
       ├─> Transmission times
       └─> Calculates bandwidth (Mbps)
           └─> Adjusts quality and FPS:
               ├─> Fast (>5 Mbps): Quality 90, FPS 30
               ├─> Normal (2-5 Mbps): Quality 75, FPS 20
               └─> Slow (<2 Mbps): Quality 50, FPS 10

6. Client Unsubscribes
   └─> Emit 'unsubscribe' event or disconnect
       └─> Renderer stops streaming frames
```

### Session Management Sequence

```
1. Create Session
   └─> POST /api/session/create
       └─> Renderer initializes Selenium WebDriver
           └─> Chrome browser starts
               └─> Session ID returned

2. Load URL
   └─> POST /api/session/{id}/load
       └─> Renderer sends WebDriver command
           └─> Chrome navigates to URL
               └─> Page loads and renders

3. Subscribe to Frames
   └─> Client connects WebSocket
       └─> Emit 'subscribe' with session_id
           └─> Frames start streaming at 30 FPS

4. Keepalive (Optional)
   └─> POST /api/session/{id}/keepalive
       └─> Updates last_activity timestamp
           └─> Prevents session timeout

5. Close Session
   └─> POST /api/session/{id}/close
       └─> Renderer quits WebDriver
           └─> Chrome browser terminates
               └─> Resources freed
```

## Network Architecture

### Docker Network: jiomosa-network

All services communicate within an isolated Docker bridge network:

```
chrome:4444         ← Selenium WebDriver
chrome:5900         ← VNC (not used by WebSocket)
chrome:7900         ← noVNC (optional)
renderer:5000       ← REST API + WebSocket
android-webapp:9000 ← Mobile web app
```

### External Ports

Exposed to host machine:

```
5000  → Renderer (REST API + WebSocket)
9000  → Android WebApp
4444  → Selenium Grid (internal use)
7900  → noVNC (optional direct access)
```

## Resource Requirements

### Cloud Infrastructure

- **CPU**: 2+ cores recommended
- **RAM**: 4GB minimum, 8GB recommended
  - Renderer: ~100MB
  - Chrome: ~500MB per session
  - Android WebApp: ~50MB
- **Storage**: 5GB for containers
- **Network**: 10+ Mbps bandwidth

### Client Device (Low-End)

- **CPU**: Single core (ARM/x86)
- **RAM**: 512MB (ThreadX RTOS or similar)
- **Display**: Any resolution
- **Network**: 1+ Mbps (adaptive quality handles slower connections)
- **Requirements**: WebSocket client (Socket.IO) or WebView with JavaScript

## Scalability

### Horizontal Scaling

Scale Chrome instances for more concurrent sessions:

```bash
docker compose up -d --scale chrome=5
```

### Load Balancing

Add nginx or HAProxy in front of:
- Multiple Renderer service instances
- Multiple Chrome containers
- Sticky sessions for WebSocket connections

### Session Distribution

- Use Redis for distributed session storage
- Implement session affinity in load balancer
- Share frame cache across renderer instances

## Performance Optimization

### For Low-End Clients

1. **Adaptive Mode**: Enable automatic quality adjustment (on by default)
2. **Lower FPS**: Set FPS to 15-20 for bandwidth savings
3. **Quality**: Manually set quality to 50-60 for slower networks
4. **Resolution**: Use lower browser window size

### For Cloud Infrastructure

1. **Chrome Options**: Optimize browser arguments
   ```python
   chrome_options.add_argument('--disable-gpu')
   chrome_options.add_argument('--no-sandbox')
   ```

2. **Screenshot Optimization**: Direct PNG capture (fastest method)

3. **Resource Limits**: Set Docker resource constraints
   ```yaml
   chrome:
     deploy:
       resources:
         limits:
           cpus: '2'
           memory: 2G
   ```

4. **SHM Size**: Increase shared memory for Chrome
   ```yaml
   chrome:
     shm_size: 2gb
   ```

## Security Considerations

### Implemented Security Measures

1. **Network Isolation**: All services in private Docker network
2. **No Debug Mode**: Flask debug disabled in production
3. **Error Sanitization**: Stack traces not exposed
4. **Input Validation**: URL validation and sanitization
5. **CORS**: Configured for all origins (restrictable)

### Additional Recommendations for Production

1. **Authentication**: Add JWT or OAuth to REST API and WebSocket
2. **TLS/HTTPS**: Enable SSL for all external connections
   - Use WSS:// for WebSocket
   - Use HTTPS:// for REST API
3. **Rate Limiting**: Prevent API and WebSocket abuse
4. **Firewall Rules**: Restrict port access to known IPs
5. **Session Timeouts**: Enforce maximum session duration
6. **Container Security**: 
   - Run as non-root users
   - Use security profiles (AppArmor, SELinux)
   - Scan images for vulnerabilities
7. **Secrets Management**: Use Docker secrets or vault
8. **Input Sanitization**: Validate all WebSocket events
9. **Resource Limits**: Prevent DoS through resource exhaustion

## Monitoring and Observability

### Health Checks

```bash
# Renderer Service
curl http://localhost:5000/health

# Selenium Grid
curl http://localhost:4444/status

# Session List
curl http://localhost:5000/api/sessions
```

### Logging

All services log to stdout/stderr:

```bash
docker compose logs -f renderer
docker compose logs -f chrome
docker compose logs -f android-webapp
```

### Metrics to Monitor

- Active session count
- WebSocket connections
- Frame rate (actual vs target)
- Quality adjustments
- Bandwidth usage
- Response times
- Browser errors
- Resource usage (CPU, RAM, Network)

## Deployment Options

### 1. Docker Compose (Current)

- Simple deployment
- Single-server setup
- Good for development and small deployments

### 2. Kubernetes (Recommended for Production)

- Auto-scaling
- High availability
- Resource management
- Load balancing
- Health checks and self-healing

Example architecture:
```
- Deployment: renderer (replicas: 3)
- Deployment: chrome (replicas: 5)
- Service: renderer (LoadBalancer)
- Ingress: HTTPS termination
- HPA: Auto-scaling based on CPU/memory
```

### 3. Cloud Platforms

- **AWS ECS/Fargate**: Container orchestration
- **Azure Container Instances**: Serverless containers
- **Google Cloud Run**: Fully managed containers
- **Digital Ocean App Platform**: PaaS deployment

## Comparison with Previous Architecture

### Old Architecture (Guacamole/VNC)

❌ Complex: 5 services (guacd, postgres, guacamole, chrome, renderer)
❌ Higher latency: VNC → Guacamole → Client
❌ More resources: PostgreSQL database, guacd proxy
❌ Complex setup: Database initialization, Guacamole configuration

### New Architecture (WebSocket)

✅ Simple: 3 services (chrome, renderer, android-webapp)
✅ Lower latency: Chrome → Renderer → Client (direct streaming)
✅ Fewer resources: No database, no VNC proxy
✅ Easy setup: Just Docker Compose

### Migration Benefits

- 40% fewer services
- 50% less memory usage (no PostgreSQL/guacd)
- 30% lower latency (direct streaming)
- Simpler deployment and maintenance
- Better mobile support (WebSocket works everywhere)
- Interactive input support (click, scroll, type)

## Future Enhancements

1. **WebRTC Support**: P2P streaming for ultra-low latency
2. **Session Recording**: Capture and replay sessions
3. **Multi-User Collaboration**: Shared browsing sessions
4. **Performance Dashboard**: Real-time metrics visualization
5. **Browser Profiles**: Custom extensions and settings
6. **Kubernetes Helm Chart**: Easy K8s deployment
7. **API Gateway**: Centralized authentication and rate limiting
8. **CDN Integration**: Edge caching for static assets

## Conclusion

Jiomosa provides an efficient, scalable solution for rendering modern websites on resource-constrained devices through WebSocket-based real-time streaming. The architecture is simple, performant, and well-suited for embedded systems, IoT devices, and mobile applications.
