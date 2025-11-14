# Jiomosa Usage Guide

This guide provides detailed examples of using the Jiomosa renderer system.

## Table of Contents
1. [Basic Usage](#basic-usage)
2. [Advanced Examples](#advanced-examples)
3. [Integration Examples](#integration-examples)
4. [Troubleshooting](#troubleshooting)

## Basic Usage

### Starting the System

```bash
# Start all services
docker compose up -d

# Check service status
docker compose ps

# View logs
docker compose logs -f
```

### Simple Website Rendering

```bash
# 1. Create a session
curl -X POST http://localhost:5000/api/session/create \
  -H "Content-Type: application/json" \
  -d '{"session_id": "demo"}'

# 2. Load a website
curl -X POST http://localhost:5000/api/session/demo/load \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'

# 3. View the rendered page
# Option A: Web browser (noVNC) - http://localhost:7900
# Option B: VNC client - vnc://localhost:5900  
# Option C: Guacamole web interface - http://localhost:8080/guacamole/

# 4. Close when done
curl -X POST http://localhost:5000/api/session/demo/close
```

## Advanced Examples

### Multiple Sessions

```bash
# Create multiple sessions for different websites
for i in {1..3}; do
  curl -X POST http://localhost:5000/api/session/create \
    -H "Content-Type: application/json" \
    -d "{\"session_id\": \"session_$i\"}"
done

# Load different websites in each session
curl -X POST http://localhost:5000/api/session/session_1/load \
  -H "Content-Type: application/json" \
  -d '{"url": "https://github.com"}'

curl -X POST http://localhost:5000/api/session/session_2/load \
  -H "Content-Type: application/json" \
  -d '{"url": "https://news.ycombinator.com"}'

# List all active sessions
curl http://localhost:5000/api/sessions
```

### Session Management Script

```bash
#!/bin/bash
# session_manager.sh

API="http://localhost:5000"

create_and_load() {
  local session_id=$1
  local url=$2
  
  echo "Creating session: $session_id"
  curl -s -X POST "$API/api/session/create" \
    -H "Content-Type: application/json" \
    -d "{\"session_id\": \"$session_id\"}" | jq
  
  echo "Loading URL: $url"
  curl -s -X POST "$API/api/session/$session_id/load" \
    -H "Content-Type: application/json" \
    -d "{\"url\": \"$url\"}" | jq
  
  echo "Session info:"
  curl -s "$API/api/session/$session_id/info" | jq
}

# Usage
create_and_load "news" "https://news.ycombinator.com"
```

### Python Client Example

```python
#!/usr/bin/env python3
"""
Jiomosa Python Client Example
"""
import requests
import time

class JiomosaClient:
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
    
    def create_session(self, session_id):
        """Create a new browser session"""
        response = requests.post(
            f"{self.base_url}/api/session/create",
            json={"session_id": session_id}
        )
        return response.json()
    
    def load_url(self, session_id, url):
        """Load a URL in a session"""
        response = requests.post(
            f"{self.base_url}/api/session/{session_id}/load",
            json={"url": url}
        )
        return response.json()
    
    def get_session_info(self, session_id):
        """Get session information"""
        response = requests.get(
            f"{self.base_url}/api/session/{session_id}/info"
        )
        return response.json()
    
    def close_session(self, session_id):
        """Close a session"""
        response = requests.post(
            f"{self.base_url}/api/session/{session_id}/close"
        )
        return response.json()

# Example usage
if __name__ == "__main__":
    client = JiomosaClient()
    
    # Create session
    print("Creating session...")
    result = client.create_session("python_demo")
    print(f"Session created: {result['session_id']}")
    
    # Load website
    print("Loading website...")
    result = client.load_url("python_demo", "https://www.wikipedia.org")
    print(f"Status: {result['message']}")
    
    # Wait for page to load
    time.sleep(3)
    
    # Get info
    print("Getting session info...")
    info = client.get_session_info("python_demo")
    print(f"Title: {info['page_info']['title']}")
    print(f"URL: {info['page_info']['url']}")
    
    # Close
    print("Closing session...")
    client.close_session("python_demo")
    print("Done!")
```

## Integration Examples

### Web Application Integration

```html
<!DOCTYPE html>
<html>
<head>
    <title>Jiomosa Web Client</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        #vnc-container { 
            width: 100%; 
            height: 600px; 
            border: 1px solid #ccc; 
        }
        button { padding: 10px; margin: 5px; }
        input { padding: 8px; width: 300px; }
    </style>
</head>
<body>
    <h1>Jiomosa Browser</h1>
    
    <div>
        <input type="text" id="url" placeholder="Enter URL" value="https://example.com">
        <button onclick="loadUrl()">Load</button>
        <button onclick="newSession()">New Session</button>
    </div>
    
    <div id="status"></div>
    
    <iframe id="vnc-container" src="http://localhost:7900/?autoconnect=1"></iframe>
    
    <script>
        let currentSession = null;
        const API = 'http://localhost:5000';
        
        async function newSession() {
            const sessionId = 'web_' + Date.now();
            const response = await fetch(`${API}/api/session/create`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({session_id: sessionId})
            });
            const data = await response.json();
            currentSession = data.session_id;
            updateStatus(`Session created: ${currentSession}`);
        }
        
        async function loadUrl() {
            if (!currentSession) {
                await newSession();
            }
            
            const url = document.getElementById('url').value;
            updateStatus(`Loading ${url}...`);
            
            const response = await fetch(`${API}/api/session/${currentSession}/load`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({url: url})
            });
            const data = await response.json();
            updateStatus(data.success ? 'Page loaded!' : 'Error loading page');
        }
        
        function updateStatus(message) {
            document.getElementById('status').textContent = message;
        }
        
        // Initialize
        newSession();
    </script>
</body>
</html>
```

### IoT Device Client (Conceptual)

```c
// Conceptual example for ThreadX RTOS
// This shows how a low-end device would connect to Jiomosa

#include "tx_api.h"
#include "vnc_client.h"
#include "http_client.h"

// Initialize Jiomosa connection
int jiomosa_init(const char* server_ip) {
    char api_url[256];
    char session_id[64];
    
    // Create session via API
    snprintf(api_url, sizeof(api_url), 
             "http://%s:5000/api/session/create", server_ip);
    
    http_post(api_url, "{\"session_id\":\"iot_device\"}", session_id);
    
    // Connect VNC client to view the browser
    vnc_connect(server_ip, 5900);
    
    return 0;
}

// Load a website
int jiomosa_load_url(const char* server_ip, const char* url) {
    char api_url[256];
    char payload[512];
    
    snprintf(api_url, sizeof(api_url),
             "http://%s:5000/api/session/iot_device/load", server_ip);
    snprintf(payload, sizeof(payload), "{\"url\":\"%s\"}", url);
    
    return http_post(api_url, payload, NULL);
}

// Main task
void iot_main_task(ULONG thread_input) {
    const char* server = "192.168.1.100";
    
    // Initialize connection
    jiomosa_init(server);
    
    // Load website
    jiomosa_load_url(server, "https://example.com");
    
    // VNC client displays the rendered page
    // Device only needs ~512MB RAM for VNC display
    while(1) {
        tx_thread_sleep(100);
    }
}
```

## Troubleshooting

### Service Not Starting

```bash
# Check if ports are in use
netstat -tulpn | grep -E '5000|8080|4444|5900'

# Check Docker status
docker compose ps
docker compose logs renderer
docker compose logs chrome

# Restart services
docker compose down
docker compose up -d
```

### Cannot Connect to VNC

```bash
# Verify VNC ports are exposed
docker port jiomosa-chrome

# Test noVNC web interface (port 7900)
curl -I http://localhost:7900/

# Test raw VNC protocol (port 5900) - should not return HTTP
curl --connect-timeout 5 localhost:5900

# Check Chrome container logs
docker logs jiomosa-chrome

# Note: Port 5900 is for VNC clients only, not web browsers
# Use port 7900 for web browser access via noVNC
```

### Guacamole Not Working (404 or Login Errors)

```bash
# Check if Guacamole is accessible at the correct path
curl -I http://localhost:8080/guacamole/

# If you get 404, the service might not be started properly
docker logs jiomosa-guacamole --tail 20

# Check if database is properly initialized
docker exec jiomosa-postgres psql -U guacamole_user -d guacamole_db -c "SELECT COUNT(*) FROM guacamole_user;"

# If the tables are missing, rebuild the volume and let the init scripts re-run
docker compose down -v
docker compose up -d postgres
sleep 10
docker compose up -d

# Schema files live under scripts/guacamole-init and include the default admin user.
# Default login: username=guacadmin, password=guacadmin
```

### Guacamole "Unexpected Internal Error" on Login

If you see "An error has occurred and this action cannot be completed" when accessing Guacamole, the web app could not log in to PostgreSQL (usually because the password was missing).

1. Confirm the Guacamole service receives the `POSTGRESQL_*` variables:
    ```bash
    docker compose config | grep -A3 POSTGRESQL_
    ```
2. Restart only the Guacamole container so it reloads the credentials:
    ```bash
    docker compose up -d guacamole
    ```
3. Verify login via API (HTTP 200 returns an auth token):
    ```bash
    curl -s -X POST http://localhost:8080/guacamole/api/tokens \
      -H "Content-Type: application/x-www-form-urlencoded" \
      -d "username=guacadmin&password=guacadmin"
    ```

If you still hit errors after resetting the credentials, the noVNC interface at `http://localhost:7900/` remains a functional fallback.

### Session Creation Fails

```bash
# Check Selenium status
curl http://localhost:4444/status

# Check renderer logs
docker logs jiomosa-renderer -f

# Verify service health
curl http://localhost:5000/health
```

### Website Not Loading

```bash
# Check if session exists
curl http://localhost:5000/api/sessions

# Get detailed session info
curl http://localhost:5000/api/session/YOUR_SESSION_ID/info

# Check Chrome console for errors
docker logs jiomosa-chrome --tail 50
```

### Performance Issues

```bash
# Scale Chrome instances
docker compose up -d --scale chrome=3

# Adjust browser window size (in renderer config)
# Smaller = better performance for low-end clients

# Check resource usage
docker stats
```

## Best Practices

1. **Session Management**: Always close sessions when done
2. **Error Handling**: Check response status codes
3. **Timeouts**: Set appropriate timeouts for page loads
4. **Resource Limits**: Monitor container resource usage
5. **Network**: Use local network for lowest latency
6. **Security**: Don't expose services publicly without authentication

## Performance Tips

1. **Lower Resolution**: Reduce browser window size for better performance
2. **Disable Images**: Configure browser to not load images when possible
3. **Connection Pooling**: Reuse sessions instead of creating new ones
4. **Load Balancing**: Scale Chrome instances horizontally
5. **Caching**: Cache frequently accessed pages

---

For more information, see the main [README.md](README.md)
