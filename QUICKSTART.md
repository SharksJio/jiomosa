# Jiomosa Quick Start Guide

Get Jiomosa up and running in 5 minutes!

## Prerequisites

- Docker and Docker Compose installed
- 4GB+ RAM available
- Ports 5000, 8080, 4444, 5900, 7900 available

## Installation Steps

### 1. Clone the Repository

```bash
git clone https://github.com/SharksJio/jiomosa.git
cd jiomosa
```

### 2. Start All Services

```bash
docker compose up -d
```

This will start:
- Renderer Service (API)
- Selenium Chrome (with VNC)
- Guacamole Server
- Guacamole Web Client
- PostgreSQL Database

### 3. Wait for Services to Initialize

```bash
# Check status
docker compose ps

# Wait until all services are healthy (30-60 seconds)
curl http://localhost:5000/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "jiomosa-renderer",
  "active_sessions": 0
}
```

## First Website Rendering

### Using the API

```bash
# 1. Create a browser session
curl -X POST http://localhost:5000/api/session/create \
  -H "Content-Type: application/json" \
  -d '{"session_id": "my_first_session"}'

# 2. Load a website
curl -X POST http://localhost:5000/api/session/my_first_session/load \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'

# 3. View the rendered page
# Open in your browser: http://localhost:7900/?autoconnect=1&resize=scale&password=secret
```

### Using the Demo Script

```bash
# Run the quick demo
./examples/quick_demo.sh
```

## Viewing Rendered Pages

You have three options to view the rendered browser:

### Option 1: noVNC Web Interface (Easiest)
Open in your browser:
```
http://localhost:7900/?autoconnect=1&resize=scale&password=secret
```

### Option 2: VNC Client
Use any VNC client:
```
Server: localhost:5900
Password: secret
```

### Option 3: Guacamole Web Client
```
http://localhost:8080/guacamole/
```

## Test Multiple Websites

```bash
# Run automated tests
python tests/test_renderer.py

# Test multiple websites
bash tests/test_websites.sh
```

## Quick Reference

### API Endpoints

```bash
# Health check
curl http://localhost:5000/health

# Service info
curl http://localhost:5000/api/info

# Create session
curl -X POST http://localhost:5000/api/session/create \
  -H "Content-Type: application/json" \
  -d '{"session_id": "test"}'

# Load URL
curl -X POST http://localhost:5000/api/session/test/load \
  -H "Content-Type: application/json" \
  -d '{"url": "https://github.com"}'

# Get session info
curl http://localhost:5000/api/session/test/info

# List all sessions
curl http://localhost:5000/api/sessions

# Close session
curl -X POST http://localhost:5000/api/session/test/close
```

### Docker Commands

```bash
# Start services
docker compose up -d

# Stop services
docker compose down

# View logs
docker compose logs -f

# View specific service logs
docker compose logs -f renderer
docker compose logs -f chrome

# Restart a service
docker compose restart renderer

# Check service status
docker compose ps

# Scale Chrome instances
docker compose up -d --scale chrome=3
```

## Using from Python

```python
import requests

# Create session
response = requests.post(
    "http://localhost:5000/api/session/create",
    json={"session_id": "python_demo"}
)
print(response.json())

# Load website
response = requests.post(
    "http://localhost:5000/api/session/python_demo/load",
    json={"url": "https://www.wikipedia.org"}
)
print(response.json())

# View at: http://localhost:7900

# Close session
response = requests.post(
    "http://localhost:5000/api/session/python_demo/close"
)
print(response.json())
```

Or use the provided Python client:
```bash
python examples/python_client.py
```

## Troubleshooting

### Services Won't Start

```bash
# Check if ports are in use
netstat -tulpn | grep -E '5000|8080|4444|5900'

# Check Docker status
docker compose ps

# View error logs
docker compose logs
```

### Cannot Connect to VNC

```bash
# Verify VNC port
docker port jiomosa-chrome 5900

# Test VNC connection
nc -zv localhost 5900
```

### Session Creation Fails

```bash
# Check Selenium status
curl http://localhost:4444/status

# Check renderer logs
docker logs jiomosa-renderer --tail 50
```

### Clean Start

```bash
# Stop and remove all containers and volumes
docker compose down -v

# Remove images (optional)
docker rmi jiomosa-renderer:latest

# Start fresh
docker compose up -d
```

## Next Steps

1. **Read the Documentation**
   - [README.md](README.md) - Complete guide
   - [USAGE.md](USAGE.md) - Detailed examples
   - [ARCHITECTURE.md](ARCHITECTURE.md) - Technical details

2. **Try Examples**
   - `examples/python_client.py` - Python integration
   - `examples/stress_test.sh` - Load testing
   - `tests/test_websites.sh` - Multi-site testing

3. **Customize Configuration**
   - Edit `docker-compose.yml` for your needs
   - Adjust environment variables
   - Configure resource limits

4. **Deploy to Production**
   - Review security considerations in README
   - Add authentication
   - Enable HTTPS/TLS
   - Set up monitoring

## Common Use Cases

### IoT Device Integration

```c
// Pseudo-code for IoT device
vnc_client_connect("cloud-server.com", 5900);
// Device displays the stream with ~512MB RAM
```

### Web Scraping

```python
# Create session
session_id = "scraper"
create_session(session_id)
load_url(session_id, "https://example.com")

# Now you can view the page in your browser
# or use Selenium API to extract data
```

### Automated Testing

```bash
# Test website rendering on different devices
for site in website1 website2 website3; do
  curl -X POST http://localhost:5000/api/session/create \
    -d "{\"session_id\": \"$site\"}"
  curl -X POST http://localhost:5000/api/session/$site/load \
    -d "{\"url\": \"https://$site.com\"}"
done
```

## Performance Tips

1. **Lower Resolution**: Reduce browser window size for better performance
2. **Connection Pooling**: Reuse sessions instead of creating new ones
3. **Resource Limits**: Set Docker CPU/memory limits
4. **Network**: Use local deployment for lowest latency
5. **Scaling**: Add more Chrome instances for concurrent users

## Support

- **Issues**: Use GitHub issue tracker
- **Documentation**: See README.md and USAGE.md
- **CI/CD**: GitHub Actions runs tests automatically

---

**You're all set!** Your Jiomosa instance is ready to render websites for low-end devices.

Open http://localhost:7900 to see it in action! 🚀
