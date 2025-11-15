# Jiomosa - Cloud Website Renderer

A proof-of-concept (PoC) solution that combines **Apache Guacamole** and **Selenium** to render rich websites with minimal latency, designed for low-end devices like RTOS systems (e.g., ThreadX) with limited resources (512MB RAM).

## 🎯 Overview

Jiomosa enables rendering of complex, resource-intensive websites on powerful cloud infrastructure and streams the visual output to low-end devices. This approach is similar to cloud gaming services but optimized for web browsing.

### Key Features

- **Cloud-Based Rendering**: Websites run on powerful servers, not on the client device
- **Low Latency**: Optimized streaming through Guacamole remote desktop protocol
- **Resource Efficient**: Client devices only need to display the stream, not render web pages
- **Scalable**: Docker-based architecture that can be deployed anywhere
- **Easy Testing**: Built-in CI/CD pipeline for automated testing
- **Multiple Sessions**: Support for concurrent browser sessions
- **Session Keepalive**: Maintain browser sessions with heartbeat signals
- **HTML5 Framebuffer Viewer**: Stream browser frames through HTML5 interface for WebView embedding
- **ThreadX Integration**: Perfect for embedded systems with WebView support
- **Device Simulator**: Test device emulator for demonstrating website rendering in apps

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Client Device                         │
│                    (Low-end hardware)                        │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Guacamole Client / VNC Viewer                       │  │
│  │  (Displays rendered stream)                          │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────┬────────────────────────────────────────┘
                     │ Remote Desktop Protocol (RDP/VNC)
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                      Cloud Infrastructure                    │
│                                                              │
│  ┌─────────────────┐  ┌──────────────────┐                 │
│  │   Guacamole     │  │   Guacamole      │                 │
│  │   Server        │◄─┤   Web Client     │                 │
│  │   (guacd)       │  │                  │                 │
│  └────────┬────────┘  └──────────────────┘                 │
│           │                                                  │
│           ▼                                                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         Selenium Grid + Chrome Browser               │  │
│  │         (Renders actual websites)                    │  │
│  │                                                       │  │
│  │  ┌────────────────────────────────────────────────┐ │  │
│  │  │  VNC Server (provides display to Guacamole)    │ │  │
│  │  └────────────────────────────────────────────────┘ │  │
│  └──────────────────────────────────────────────────────┘  │
│           ▲                                                  │
│           │                                                  │
│  ┌────────┴────────┐                                        │
│  │   Renderer      │                                        │
│  │   Service       │                                        │
│  │   (API/Control) │                                        │
│  └─────────────────┘                                        │
└─────────────────────────────────────────────────────────────┘
```

### Components

1. **Renderer Service** (Python/Flask)
   - REST API for managing browser sessions
   - Selenium WebDriver integration
   - Session management and coordination

2. **Selenium Grid + Chrome**
   - Runs actual web browsers in containers
   - Built-in VNC server for remote display
   - Handles website rendering

3. **Apache Guacamole**
   - Remote desktop gateway (guacd)
   - Web-based client interface
   - Efficient streaming protocol

4. **PostgreSQL**
   - Database for Guacamole configuration
   - User session management

## 🚀 Quick Start

### Option 1: GitHub Codespaces (Fastest - No Setup Required!)

Perfect for testing without any local installation:

1. Click the green **Code** button at the top of this repository
2. Select **Codespaces** tab
3. Click **Create codespace on main**
4. Wait 3-5 minutes for automatic setup
5. In the terminal, run:
```bash
docker compose up -d
```
6. Access port 7900 in the **PORTS** tab to view rendered websites

📖 **Detailed guide**: See [CODESPACES.md](CODESPACES.md) for complete instructions and external website testing

### Option 2: Local Installation

**Prerequisites:**
- Docker and Docker Compose
- 4GB+ RAM recommended for running all services
- Ports 5000, 8080, 4444, 5900, 7900 available

**Installation:**

1. Clone the repository:
```bash
git clone https://github.com/SharksJio/jiomosa.git
cd jiomosa
```

2. Start all services:
```bash
docker compose up -d
```

3. Wait for services to initialize (30-60 seconds):
```bash
# Check service health
curl http://localhost:5000/health
```

### Using the Renderer API

#### 1. Create a browser session:
```bash
curl -X POST http://localhost:5000/api/session/create \
  -H "Content-Type: application/json" \
  -d '{"session_id": "my_session"}'
```

#### 2. Load a website:
```bash
curl -X POST http://localhost:5000/api/session/my_session/load \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'
```

#### 3. View the rendered page:
- **VNC Web Interface**: http://localhost:7900 (password: secret)
- **Guacamole**: http://localhost:8080/guacamole/

#### 4. Get session information:
```bash
curl http://localhost:5000/api/session/my_session/info
```

#### 5. Close the session:
```bash
curl -X POST http://localhost:5000/api/session/my_session/close
```

### Using the HTML5 Framebuffer Viewer (ThreadX Integration)

For embedded systems and ThreadX apps with WebView support:

```bash
# 1. Create session and load URL (same as above)
curl -X POST http://localhost:5000/api/session/create \
  -H "Content-Type: application/json" \
  -d '{"session_id": "threadx_session"}'

curl -X POST http://localhost:5000/api/session/threadx_session/load \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'

# 2. Access the HTML5 viewer in your WebView
# URL: http://localhost:5000/api/session/threadx_session/viewer
# This displays a framebuffer stream that auto-refreshes

# 3. Send keepalive to maintain the session
curl -X POST http://localhost:5000/api/session/threadx_session/keepalive
```

📖 **Detailed guide**: See [KEEPALIVE_FRAMEBUFFER.md](KEEPALIVE_FRAMEBUFFER.md) for ThreadX integration examples

## 🖥️ Device Simulator (Test App)

The Device Simulator is a standalone test application that emulates low-end devices to demonstrate how websites can be rendered inside an app **without showing any browser UI**. Perfect for testing and demonstrating ThreadX, IoT, and embedded system integrations.

### Key Features
- **Multiple Device Profiles**: Simulate ThreadX RTOS (512MB), IoT devices (256MB), thin clients, and legacy systems
- **WebView-Only Display**: Shows only website content, no browser chrome or UI
- **Interactive Testing**: Easy controls to load URLs and test different scenarios
- **Real-time Streaming**: Uses HTML5 framebuffer streaming
- **Session Management**: Built-in session creation and management

### Quick Start with Device Simulator

```bash
# 1. Ensure Jiomosa is running
docker compose up -d

# 2. Start the device simulator
cd device_simulator
./run_simulator.sh

# 3. Open your browser to:
http://localhost:8000

# 4. In the simulator UI:
#    - Click "New Session"
#    - Enter a URL (or use quick actions)
#    - Click "Load Website"
#    - Watch the website render in the device screen!
```

### Available Device Profiles

| Profile | Screen Size | RAM | Use Case |
|---------|-------------|-----|----------|
| ThreadX RTOS | 1024x600 | 512MB | Embedded devices, industrial controllers |
| IoT Device | 800x480 | 256MB | Smart home, constrained IoT |
| Thin Client | 1280x720 | 1GB | Kiosks, workstations |
| Legacy System | 1366x768 | 2GB | Older computers |

### Why Use the Device Simulator?

1. **No Browser UI**: Unlike VNC, shows only the website content
2. **Easy Testing**: Visual way to test how websites look on different devices
3. **Integration Demo**: Perfect for demonstrating embedded system integrations
4. **Development**: Test your app integration before deploying to real hardware
5. **Presentation**: Show stakeholders how the solution works

📖 **Detailed guide**: See [device_simulator/README.md](device_simulator/README.md) for complete documentation

## 📡 API Endpoints

### Service Information
- `GET /health` - Health check
- `GET /api/info` - Service information and available endpoints
- `GET /api/vnc/info` - VNC connection details

### Session Management
- `POST /api/session/create` - Create a new browser session
- `POST /api/session/{id}/load` - Load a URL in a session
- `GET /api/session/{id}/info` - Get session information
- `POST /api/session/{id}/keepalive` - Send keepalive signal to maintain session
- `POST /api/session/{id}/close` - Close a session
- `GET /api/sessions` - List all active sessions

### Framebuffer & Viewer (New)
- `GET /api/session/{id}/frame` - Get current browser frame as PNG image
- `GET /api/session/{id}/frame/data` - Get current browser frame as base64 JSON
- `GET /api/session/{id}/viewer` - HTML5 viewer page for framebuffer streaming

## 🧪 Testing

### Run all tests:
```bash
# Start services
docker compose up -d

# Run integration tests
python tests/test_renderer.py

# Run basic website rendering tests
bash tests/test_websites.sh

# Run comprehensive external website tests (20+ websites)
bash tests/test_external_websites.sh

# Test device simulator (requires simulator to be running)
cd device_simulator && ./run_simulator.sh &
sleep 10
python ../tests/test_device_simulator.py

# Stop services
docker compose down
```

### Testing External Websites

Test Jiomosa with real-world websites:

```bash
# Quick test with a single website
curl -X POST http://localhost:5000/api/session/create \
  -H "Content-Type: application/json" \
  -d '{"session_id": "test1"}'

curl -X POST http://localhost:5000/api/session/test1/load \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.wikipedia.org"}'

# View at: http://localhost:7900
```

The comprehensive test suite (`tests/test_external_websites.sh`) tests various website categories:
- Simple/Static sites
- Search engines
- News sites
- Documentation
- Developer platforms
- Social media
- Educational sites
- Media sites
- E-commerce
- Blogs/Content sites

**For GitHub Codespaces users**: See [CODESPACES.md](CODESPACES.md) for detailed testing guide

### Manual Testing:
```bash
# Test health
curl http://localhost:5000/health

# Create session and load Google
curl -X POST http://localhost:5000/api/session/create \
  -H "Content-Type: application/json" \
  -d '{"session_id": "test1"}' && \
curl -X POST http://localhost:5000/api/session/test1/load \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.google.com"}'

# View in browser: http://localhost:7900
```

## 🔧 Configuration

### Environment Variables

You can customize the configuration by modifying `docker-compose.yml` or setting environment variables:

**Renderer Service:**
- `SELENIUM_HOST` - Selenium Grid hostname (default: chrome)
- `SELENIUM_PORT` - Selenium Grid port (default: 4444)
- `GUACD_HOST` - Guacamole daemon hostname (default: guacd)
- `GUACD_PORT` - Guacamole daemon port (default: 4822)
- `VNC_HOST` - VNC server hostname (default: chrome)
- `VNC_PORT` - VNC server port (default: 5900)
- `SESSION_TIMEOUT` - Session timeout in seconds (default: 300)
- `FRAME_CAPTURE_INTERVAL` - Frame capture interval in seconds (default: 1.0)

**Guacamole:**
- `POSTGRES_DATABASE` - Database name
- `POSTGRES_USER` - Database user
- `POSTGRES_PASSWORD` - Database password

### Scaling

To handle more concurrent sessions, scale the Chrome service:
```bash
docker compose up -d --scale chrome=3
```

## 🔒 Security Considerations

This is a **Proof of Concept** and should not be deployed in production without additional security measures:

1. **Authentication**: Add proper authentication to the Renderer API
2. **Network Security**: Use firewall rules and secure networks
3. **HTTPS/TLS**: Enable encrypted connections
4. **Resource Limits**: Configure container resource limits
5. **Session Timeouts**: Implement session timeout mechanisms
6. **Input Validation**: Enhance URL validation and sanitization

## 🎯 Use Cases

1. **IoT Devices**: Browse modern websites on resource-constrained devices
2. **Legacy Systems**: Access modern web applications from old hardware
3. **Thin Clients**: Deploy in environments with minimal client resources
4. **Testing**: Automated website testing and screenshot capture
5. **Remote Access**: Provide web browsing in restricted environments

## 🛠️ Development

### Project Structure
```
jiomosa/
├── docker-compose.yml       # Multi-service orchestration
├── renderer/                # Renderer service
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app.py              # Flask API application
├── device_simulator/        # Device simulator for testing
│   ├── simulator.py        # Main simulator app
│   ├── requirements.txt
│   ├── run_simulator.sh    # Launcher script
│   └── README.md           # Simulator documentation
├── scripts/                # Database and setup scripts
│   └── initdb.sql
├── tests/                  # Integration tests
│   ├── test_renderer.py
│   ├── test_device_simulator.py
│   └── test_websites.sh
├── examples/               # Example usage scripts
│   └── python_client.py
├── .github/
│   └── workflows/
│       └── ci.yml          # CI/CD pipeline
└── README.md
```

### Building Locally
```bash
# Build renderer service
cd renderer
docker build -t jiomosa-renderer .

# Run with docker-compose
cd ..
docker compose up
```

### Debugging
```bash
# View logs
docker compose logs -f renderer
docker compose logs -f chrome

# Access container shell
docker exec -it jiomosa-renderer bash
docker exec -it jiomosa-chrome bash

# Check Selenium status
curl http://localhost:4444/status
```

## 🚀 CI/CD Pipeline

The GitHub Actions workflow automatically:
1. Builds all Docker images
2. Starts the services
3. Runs health checks
4. Executes integration tests
5. Tests rendering multiple websites
6. Reports results

Workflow triggers:
- Push to main/develop branches
- Pull requests
- Manual workflow dispatch

## 📊 Performance Optimization

For optimal performance on low-end clients:

1. **Reduce Resolution**: Lower the browser window size for smaller frames
2. **Compression**: Enable Guacamole's compression settings
3. **Frame Rate**: Adjust frame capture interval (FRAME_CAPTURE_INTERVAL env var)
4. **Network**: Use local network deployment for minimal latency
5. **Browser Settings**: Disable unnecessary browser features
6. **Session Management**: Use keepalive to maintain sessions without recreating
7. **Framebuffer Streaming**: Use HTML5 viewer for lower overhead than VNC

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📝 License

This project is provided as-is for educational and demonstration purposes.

## 🔗 References

- [Apache Guacamole](https://guacamole.apache.org/)
- [Selenium WebDriver](https://www.selenium.dev/)
- [Docker Selenium](https://github.com/SeleniumHQ/docker-selenium)
- [ThreadX RTOS](https://azure.microsoft.com/en-us/services/rtos/)

## 💡 Future Enhancements

- [ ] WebRTC support for lower latency
- [ ] WebSocket-based frame streaming
- [ ] Mobile-optimized streaming
- [ ] Multi-user collaboration
- [ ] Recording and playback
- [ ] Performance metrics dashboard
- [ ] Load balancing across multiple browser nodes
- [ ] Kubernetes deployment manifests
- [ ] Custom browser profiles and extensions
- [ ] JPEG frame format for smaller sizes
- [ ] Adaptive frame rate based on content changes

## 📞 Support

For issues and questions, please use the GitHub issue tracker.

---

**Built with ❤️ for low-end devices everywhere**
