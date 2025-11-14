# Jiomosa Architecture

## Overview

Jiomosa is a cloud-based website rendering solution designed to enable low-end devices (like RTOS systems with 512MB RAM) to access modern, resource-intensive websites by offloading rendering to powerful cloud infrastructure.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     Low-End Client Device                        │
│                   (ThreadX RTOS, 512MB RAM)                      │
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │          Guacamole Client / VNC Viewer                    │  │
│  │     (Only displays streamed frames - minimal resources)   │  │
│  └──────────────┬────────────────────────────────────────────┘  │
└─────────────────┼───────────────────────────────────────────────┘
                  │
                  │ Guacamole Protocol (RDP/VNC)
                  │ Optimized for low bandwidth
                  │
                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Cloud Infrastructure                          │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                 Guacamole Server (guacd)                  │  │
│  │          Remote Desktop Protocol Gateway                   │  │
│  │  - Handles protocol translation                           │  │
│  │  - Compression and optimization                           │  │
│  └───────┬──────────────────────────────────────────────────┘  │
│          │                                                       │
│          │ VNC Protocol                                         │
│          │                                                       │
│  ┌───────▼──────────────────────────────────────────────────┐  │
│  │         Selenium Grid + Chrome Browser                    │  │
│  │  ┌──────────────────────────────────────────────────┐    │  │
│  │  │    Chrome Browser with Selenium WebDriver        │    │  │
│  │  │  - Renders actual websites                       │    │  │
│  │  │  - JavaScript execution                          │    │  │
│  │  │  - Full web standards support                    │    │  │
│  │  └──────────────────────────────────────────────────┘    │  │
│  │  ┌──────────────────────────────────────────────────┐    │  │
│  │  │         VNC Server (x11vnc)                      │    │  │
│  │  │  - Shares browser display                        │    │  │
│  │  │  - Streams to Guacamole                          │    │  │
│  │  └──────────────────────────────────────────────────┘    │  │
│  └───────▲──────────────────────────────────────────────────┘  │
│          │                                                       │
│          │ WebDriver Protocol                                   │
│          │                                                       │
│  ┌───────┴──────────────────────────────────────────────────┐  │
│  │           Renderer Service (Python/Flask)                 │  │
│  │  ┌──────────────────────────────────────────────────┐    │  │
│  │  │         REST API Endpoints                       │    │  │
│  │  │  - POST /api/session/create                      │    │  │
│  │  │  - POST /api/session/{id}/load                   │    │  │
│  │  │  - GET  /api/session/{id}/info                   │    │  │
│  │  │  - POST /api/session/{id}/close                  │    │  │
│  │  │  - GET  /api/sessions                            │    │  │
│  │  └──────────────────────────────────────────────────┘    │  │
│  │  ┌──────────────────────────────────────────────────┐    │  │
│  │  │       Session Management                         │    │  │
│  │  │  - Browser lifecycle control                     │    │  │
│  │  │  - URL loading and navigation                    │    │  │
│  │  │  - Multiple concurrent sessions                  │    │  │
│  │  └──────────────────────────────────────────────────┘    │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              PostgreSQL Database                          │  │
│  │  - Guacamole configuration                                │  │
│  │  - User sessions and connections                          │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              Guacamole Web Client                         │  │
│  │  - Web-based management interface                         │  │
│  │  - Connection configuration                               │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. Renderer Service (Port 5000)

**Technology**: Python 3.11, Flask, Selenium WebDriver

**Responsibilities**:
- Exposes REST API for external control
- Manages browser session lifecycle
- Controls Selenium WebDriver to navigate and interact with websites
- Coordinates between Selenium Grid and Guacamole

**Key Features**:
- Multiple concurrent session support
- Session timeout management
- Health monitoring
- Comprehensive error handling

**API Endpoints**:
```
GET  /health                          - Service health check
GET  /api/info                        - Service information
POST /api/session/create              - Create browser session
POST /api/session/{id}/load           - Load URL in session
GET  /api/session/{id}/info           - Get session information
POST /api/session/{id}/close          - Close browser session
GET  /api/sessions                    - List all sessions
GET  /api/vnc/info                    - VNC connection details
```

### 2. Selenium Grid + Chrome (Ports 4444, 5900, 7900)

**Technology**: Selenium Standalone Chrome, Chrome Browser, VNC Server

**Responsibilities**:
- Executes actual web browser instances
- Renders websites with full JavaScript support
- Provides VNC server for remote display access
- Handles web standards and modern features

**Ports**:
- 4444: Selenium WebDriver API
- 5900: VNC server (for Guacamole connection)
- 7900: noVNC web interface (for browser access)

**Features**:
- Full Chrome browser with latest features
- Hardware acceleration disabled (for stability)
- Shared memory for performance
- Configurable session limits

### 3. Guacamole Server (guacd) (Port 4822)

**Technology**: Apache Guacamole Daemon

**Responsibilities**:
- Acts as remote desktop protocol gateway
- Translates VNC to Guacamole protocol
- Optimizes streaming for low-bandwidth connections
- Handles compression and frame rate optimization

**Benefits**:
- Efficient protocol for slow networks
- Low latency streaming
- Cross-platform client support
- Secure connection handling

### 4. Guacamole Web Client (Port 8080)

**Technology**: Apache Guacamole Web Application

**Responsibilities**:
- Browser-based client interface
- Connection management UI
- User authentication (when configured)
- Session monitoring

**Access**: http://localhost:8080/guacamole/

### 5. PostgreSQL Database

**Technology**: PostgreSQL 15

**Responsibilities**:
- Stores Guacamole configuration
- Manages user sessions and permissions
- Connection history and logging

## Data Flow

### Website Loading Sequence

```
1. Client Request
   └─> POST /api/session/{id}/load
       └─> Renderer Service

2. Renderer Service
   └─> Selenium WebDriver Command
       └─> Selenium Grid (Port 4444)

3. Selenium Grid
   └─> Chrome Browser Opens URL
       └─> Website Renders in Browser

4. VNC Server
   └─> Captures Browser Display
       └─> Streams to VNC Port 5900

5. Guacamole Server (guacd)
   └─> Connects to VNC Server
       └─> Translates to Guacamole Protocol

6. Client Device
   └─> Receives Optimized Stream
       └─> Displays in VNC Client/Guacamole Client
```

## Network Architecture

### Internal Network (Docker Network: jiomosa-network)

All services communicate within an isolated Docker network:
```
guacd           <─> postgres
guacamole       <─> guacd, postgres
chrome          <─> (Selenium Grid, VNC Server)
renderer        <─> chrome, guacd
```

### External Ports

Exposed to host machine:
```
5000  → Renderer API
8080  → Guacamole Web Interface
4444  → Selenium Grid
5900  → VNC Server
7900  → noVNC Web Interface
4822  → Guacamole Daemon
```

## Resource Requirements

### Cloud Infrastructure
- **CPU**: 2+ cores recommended
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 10GB for containers and cache
- **Network**: 10+ Mbps bandwidth

### Client Device (Low-End)
- **CPU**: Single core (ARM/x86)
- **RAM**: 512MB (ThreadX RTOS or similar)
- **Display**: Any resolution supported by VNC client
- **Network**: 1+ Mbps (lower with compression)

## Scalability

### Horizontal Scaling

Scale Chrome instances:
```bash
docker compose up -d --scale chrome=5
```

### Load Balancing

Add a reverse proxy (nginx/HAProxy) in front of:
- Multiple Renderer service instances
- Multiple Chrome instances
- Guacamole servers

### Session Distribution

- Use Redis for distributed session storage
- Implement sticky sessions for VNC connections
- Add session affinity in load balancer

## Security Considerations

### Implemented Security Measures

1. **Network Isolation**: All services in private Docker network
2. **No Debug Mode**: Flask debug mode disabled in production
3. **Error Sanitization**: Stack traces not exposed to clients
4. **Least Privilege**: Minimal GITHUB_TOKEN permissions
5. **Input Validation**: URL validation and sanitization

### Additional Security Recommendations

1. **Authentication**: Add JWT or OAuth to Renderer API
2. **TLS/HTTPS**: Enable SSL for all external connections
3. **Rate Limiting**: Prevent API abuse
4. **Firewall Rules**: Restrict port access
5. **Session Timeouts**: Automatically close inactive sessions
6. **Container Security**: Run containers as non-root users
7. **Network Policies**: Implement Kubernetes network policies
8. **Secrets Management**: Use Docker secrets or Vault

## Performance Optimization

### For Low-End Clients

1. **Resolution**: Lower browser window size
   ```python
   chrome_options.add_argument('--window-size=1280,720')
   ```

2. **Frame Rate**: Limit VNC frame rate
   ```
   VNC_FRAMERATE=15
   ```

3. **Compression**: Enable Guacamole compression
   ```
   GUACAMOLE_COMPRESSION=9
   ```

4. **Image Quality**: Reduce VNC image quality
   ```
   VNC_IMAGE_QUALITY=5
   ```

### For Cloud Infrastructure

1. **Browser Caching**: Enable browser cache
2. **Connection Pooling**: Reuse browser instances
3. **Resource Limits**: Set Docker resource constraints
4. **SHM Size**: Increase shared memory for Chrome
5. **CDN**: Use CDN for static assets

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
docker compose logs -f guacamole
```

### Metrics

Monitor:
- Active session count
- Response times
- Resource usage (CPU, RAM)
- Network bandwidth
- Browser errors

## Deployment Options

### 1. Docker Compose (Current)
- Simple deployment
- Single-server setup
- Good for PoC and testing

### 2. Kubernetes
- Production-grade
- Auto-scaling
- High availability
- Resource management

### 3. Cloud Platforms
- AWS ECS/Fargate
- Azure Container Instances
- Google Cloud Run
- Digital Ocean App Platform

## Future Enhancements

1. **WebRTC Support**: Lower latency streaming
2. **Session Recording**: Capture and replay sessions
3. **Multi-User Collaboration**: Shared browsing sessions
4. **Mobile Optimization**: Touch-friendly streaming
5. **Performance Metrics**: Real-time monitoring dashboard
6. **Browser Profiles**: Custom extensions and settings
7. **Kubernetes Helm Chart**: Easy K8s deployment
8. **API Gateway**: Centralized API management

## Comparison with Alternatives

### vs Traditional Cloud Desktop (AWS WorkSpaces, Azure Virtual Desktop)
- ✅ More lightweight (browser-only vs full desktop)
- ✅ Lower cost (smaller resource footprint)
- ✅ Faster startup (browser vs full OS boot)
- ❌ Less flexible (web browsing only)

### vs Cloud Gaming Platforms (GeForce Now, Stadia)
- ✅ Lower latency (VNC vs game streaming)
- ✅ Simpler architecture
- ✅ Lower resource requirements
- ❌ Different use case (web browsing vs gaming)

### vs Browser-in-Browser (BrowserStack, Sauce Labs)
- ✅ Open source and self-hosted
- ✅ No per-session cost
- ✅ Full control over infrastructure
- ❌ Requires infrastructure management

## Conclusion

Jiomosa provides an elegant solution for rendering modern websites on resource-constrained devices by leveraging cloud computing and efficient streaming protocols. The architecture is modular, scalable, and security-conscious, making it suitable for both proof-of-concept demonstrations and production deployments with appropriate hardening.
