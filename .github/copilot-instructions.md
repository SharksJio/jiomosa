# Jio Cloud Apps - Cloud Website Renderer

This is a proof-of-concept (PoC) solution combining Apache Guacamole and Selenium to render rich websites with minimal latency, designed for low-end devices like RTOS systems (e.g., ThreadX) with limited resources (512MB RAM).

## Project Overview

Jio Cloud Apps enables rendering of complex, resource-intensive websites on powerful cloud infrastructure and streams the visual output to low-end devices. The architecture uses Docker containers orchestrating Selenium Grid, Chrome browser, Apache Guacamole, and a Python Flask renderer service.

## Development Workflow

### Building and Running

```bash
# Start all services
docker compose up -d

# Wait for services to initialize (30-60 seconds)
docker compose ps

# Check service health
curl http://localhost:5000/health
curl http://localhost:4444/status
```

### Testing

**Always run tests before committing changes:**

```bash
# 1. Ensure services are running
docker compose up -d

# 2. Run integration tests (Python-based)
pip install requests pytest
python tests/test_renderer.py

# 3. Run website rendering tests
bash tests/test_websites.sh

# 4. Run comprehensive external website tests (optional - 20+ websites)
bash tests/test_external_websites.sh

# 5. Stop services when done
docker compose down
```

### Debugging

```bash
# View service logs
docker compose logs -f renderer
docker compose logs -f chrome
docker compose logs -f guacamole

# Access container shells
docker exec -it jiomosa-renderer bash
docker exec -it jiomosa-chrome bash

# Check Selenium Grid status
curl http://localhost:4444/status
```

### CI/CD Pipeline

The GitHub Actions workflow (`.github/workflows/ci.yml`) automatically:
1. Builds Docker images
2. Starts all services
3. Runs health checks
4. Executes integration tests
5. Tests multiple website rendering scenarios
6. Reports results and uploads artifacts

Pipeline triggers on:
- Push to `main`, `develop`, or `copilot/**` branches
- Pull requests to `main` or `develop`
- Manual workflow dispatch

## Repository Structure

```
jiomosa/
├── .github/
│   └── workflows/
│       └── ci.yml              # CI/CD pipeline configuration
├── renderer/                   # Renderer service (Python/Flask)
│   ├── Dockerfile
│   ├── requirements.txt        # Python dependencies
│   └── app.py                  # Main Flask application with API endpoints
├── scripts/                    # Database and setup scripts
│   └── initdb.sql             # PostgreSQL initialization for Guacamole
├── tests/                      # Integration tests
│   ├── test_renderer.py       # Python integration tests
│   ├── test_websites.sh       # Basic website rendering tests
│   └── test_external_websites.sh  # Comprehensive external website tests
├── examples/                   # Example configurations and usage
├── docker-compose.yml          # Multi-service orchestration
├── README.md                   # Main documentation
├── ARCHITECTURE.md             # Detailed architecture documentation
├── CODESPACES.md              # GitHub Codespaces setup guide
├── DEPLOYMENT.md              # Deployment instructions
├── QUICKSTART.md              # Quick start guide
└── USAGE.md                   # Usage documentation
```

## Key Components

### 1. Renderer Service (Python/Flask)
- **Location**: `renderer/app.py`
- **Purpose**: REST API for managing browser sessions
- **Key Classes**:
  - `BrowserSession`: Manages individual Selenium WebDriver sessions
- **Dependencies**: Flask, Selenium, Werkzeug, Requests (see `renderer/requirements.txt`)
- **Environment Variables**:
  - `SELENIUM_HOST` (default: chrome)
  - `SELENIUM_PORT` (default: 4444)
  - `GUACD_HOST` (default: guacd)
  - `GUACD_PORT` (default: 4822)
  - `VNC_HOST` (default: chrome)
  - `VNC_PORT` (default: 5900)

### 2. Selenium Grid + Chrome
- Runs in Docker container: `selenium/standalone-chrome:latest`
- Built-in VNC server for remote display
- Handles actual website rendering

### 3. Apache Guacamole
- Remote desktop gateway (guacd) and web client
- Efficient streaming protocol for low-bandwidth connections
- PostgreSQL database for configuration

### 4. PostgreSQL
- Database for Guacamole configuration
- Initialized with `scripts/initdb.sql`

## API Endpoints

### Service Information
- `GET /health` - Health check endpoint
- `GET /api/info` - Service information and available endpoints
- `GET /api/vnc/info` - VNC connection details

### Session Management
- `POST /api/session/create` - Create a new browser session
  - Body: `{"session_id": "unique_id"}`
- `POST /api/session/{id}/load` - Load a URL in a session
  - Body: `{"url": "https://example.com"}`
- `GET /api/session/{id}/info` - Get session information
- `POST /api/session/{id}/close` - Close a session
- `GET /api/sessions` - List all active sessions

### Service Access Points
- **Renderer API**: http://localhost:5000
- **VNC Web Interface**: http://localhost:7900 (password: secret)
- **Guacamole Web**: http://localhost:8080/guacamole/
- **Selenium Grid**: http://localhost:4444

## Coding Standards

### Python Code (Renderer Service)
1. **Logging**: Use the configured logger (Python's logging module)
   - Log important operations at INFO level
   - Log errors at ERROR level
   - Log warnings at WARNING level
2. **Error Handling**: Always handle WebDriver exceptions gracefully
   - Catch `TimeoutException`, `WebDriverException`
   - Return appropriate error messages to API clients
3. **Code Style**: Follow PEP 8 Python style guidelines
4. **Session Management**: Always properly close Selenium WebDriver sessions
5. **Configuration**: Use environment variables for service endpoints
6. **API Responses**: Return JSON with `success` boolean and descriptive messages

### Docker and Compose
1. **Container Names**: Use `jiomosa-` prefix (e.g., `jiomosa-renderer`)
2. **Networks**: All services use the `jiomosa-network` bridge network
3. **Restart Policy**: Use `unless-stopped` for production-like behavior
4. **Resource Limits**: Chrome container needs `shm_size: 2gb` for stability

### Testing
1. **Integration Tests**: Use Python's requests library and pytest
2. **Test Isolation**: Each test should create and clean up its own sessions
3. **Assertions**: Include descriptive failure messages
4. **Test URLs**: Use lightweight sites like example.com for basic tests
5. **CI Compatibility**: Tests must work in GitHub Actions environment

## Important Considerations

### When Making Changes

1. **Minimal Modifications**: Make the smallest possible changes to achieve the goal
2. **Docker Images**: Rebuild images after changing Dockerfiles or dependencies
   ```bash
   docker compose build renderer
   docker compose up -d --force-recreate renderer
   ```
3. **Service Dependencies**: Renderer depends on Chrome and Guacd being available
4. **Session Cleanup**: Always ensure browser sessions are properly closed
5. **Port Conflicts**: Ensure ports 5000, 8080, 4444, 5900, 7900 are available
6. **Resource Requirements**: System needs 4GB+ RAM for all services

### Security Notes

This is a **Proof of Concept** - additional security measures needed for production:
- Add authentication to the Renderer API
- Implement session timeouts
- Enhance URL validation and sanitization
- Use HTTPS/TLS for encrypted connections
- Configure container resource limits
- Apply network security rules

### Testing Changes

Before committing:
1. Start services: `docker compose up -d`
2. Wait 30-60 seconds for initialization
3. Run health checks
4. Run integration tests: `python tests/test_renderer.py`
5. Run website tests: `bash tests/test_websites.sh`
6. Check logs for errors: `docker compose logs`
7. Stop services: `docker compose down`

### Common Issues

1. **Services not starting**: Check `docker compose logs` for errors
2. **Connection refused**: Services may need more time to initialize (wait 30-60s)
3. **Selenium timeout**: Chrome container may need more memory (increase shm_size)
4. **VNC not accessible**: Ensure port 7900 is not blocked by firewall
5. **Database errors**: PostgreSQL may need clean volume: `docker compose down -v`

## Use Cases

1. **IoT Devices**: Browse modern websites on resource-constrained devices
2. **Legacy Systems**: Access modern web applications from old hardware
3. **Thin Clients**: Deploy in environments with minimal client resources
4. **Automated Testing**: Website testing and screenshot capture
5. **Remote Access**: Provide web browsing in restricted environments

## Additional Resources

- Main Documentation: `README.md`
- Architecture Details: `ARCHITECTURE.md`
- Codespaces Setup: `CODESPACES.md`
- Deployment Guide: `DEPLOYMENT.md`
- Quick Start: `QUICKSTART.md`
- Usage Examples: `USAGE.md`
