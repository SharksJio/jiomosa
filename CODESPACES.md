# GitHub Codespaces Deployment Guide for Jiomosa

This guide explains how to deploy and test Jiomosa on GitHub Codespaces, providing a cloud-based development environment with zero local setup.

## 🚀 What is GitHub Codespaces?

GitHub Codespaces provides a complete, configurable development environment in the cloud, accessible from your browser or VS Code. It's perfect for:
- Testing Jiomosa without local Docker installation
- Collaborative development
- Accessing from any device
- Testing external websites from a cloud environment

## ✨ Quick Start

### 1. Create a Codespace

**Option A: From GitHub Repository**
1. Go to https://github.com/SharksJio/jiomosa
2. Click the green **Code** button
3. Select **Codespaces** tab
4. Click **Create codespace on main** (or your branch)

**Option B: From VS Code**
1. Install the GitHub Codespaces extension
2. Open Command Palette (Ctrl+Shift+P / Cmd+Shift+P)
3. Type "Codespaces: Create New Codespace"
4. Select this repository

### 2. Wait for Setup

The Codespace will automatically:
- ✅ Install Docker and Docker Compose
- ✅ Pre-pull required Docker images
- ✅ Build the renderer service
- ✅ Install Python dependencies
- ✅ Configure port forwarding

This takes **3-5 minutes** on first creation.

### 3. Start Jiomosa Services

Once the Codespace is ready, open a terminal and run:

```bash
# Start all services
docker compose up -d

# Wait for services to initialize (30-60 seconds)
sleep 45

# Check health
curl http://localhost:5000/health
```

### 4. Access the Services

In VS Code, go to the **PORTS** tab (bottom panel) to see forwarded ports:

| Port | Service | Access |
|------|---------|--------|
| 5000 | Renderer API | Click globe icon to open |
| 7900 | noVNC Browser View | Click globe icon to open |
| 8080 | Guacamole Web | Click globe icon to open |
| 4444 | Selenium Grid | For debugging |
| 5900 | VNC Server | For VNC clients |

**Tip:** Make ports **Public** in the Ports tab to access from external devices or share with others.

## 🌐 Testing External Websites

### Using the Quick Demo

```bash
bash examples/quick_demo.sh
```

This will:
1. Create a browser session
2. Load example.com
3. Show you how to view the rendered page
4. Clean up the session

### Testing Specific Websites

```bash
# Create a session
curl -X POST http://localhost:5000/api/session/create \
  -H "Content-Type: application/json" \
  -d '{"session_id": "test1"}'

# Load any external website
curl -X POST http://localhost:5000/api/session/test1/load \
  -H "Content-Type: application/json" \
  -d '{"url": "https://news.ycombinator.com"}'

# View the rendered page
# Click on port 7900 in the PORTS tab
```

### Test Multiple Websites

Create a custom test script:

```bash
#!/bin/bash
# test_my_websites.sh

websites=(
    "https://www.google.com"
    "https://github.com"
    "https://www.wikipedia.org"
    "https://stackoverflow.com"
    "https://reddit.com"
)

for i in "${!websites[@]}"; do
    session_id="test_$i"
    url="${websites[$i]}"
    
    echo "Testing: $url"
    
    curl -s -X POST http://localhost:5000/api/session/create \
        -H "Content-Type: application/json" \
        -d "{\"session_id\": \"$session_id\"}" > /dev/null
    
    curl -s -X POST http://localhost:5000/api/session/$session_id/load \
        -H "Content-Type: application/json" \
        -d "{\"url\": \"$url\"}"
    
    echo "✓ Loaded $url - View at port 7900"
    sleep 3
    
    curl -s -X POST http://localhost:5000/api/session/$session_id/close > /dev/null
done
```

Save this as `test_my_websites.sh`, make it executable, and run:

```bash
chmod +x test_my_websites.sh
./test_my_websites.sh
```

### Using the Built-in Test Suite

```bash
# Test multiple predefined websites
bash tests/test_websites.sh

# Run integration tests
python tests/test_renderer.py
```

## 🔍 Viewing Rendered Pages

### Method 1: noVNC Web Interface (Recommended)

1. Go to **PORTS** tab in VS Code
2. Find port **7900** (noVNC Web Interface)
3. Click the **globe icon** 🌐 to open in browser
4. You'll see the Chrome browser with the loaded website

**Direct URL format:**
```
https://YOUR-CODESPACE-NAME-7900.app.github.dev/?autoconnect=1&resize=scale&password=secret
```

### Method 2: Using the API

Create and load websites programmatically:

```python
import requests
import time

# Get the Codespace URL
base_url = "http://localhost:5000"

# Create session
response = requests.post(
    f"{base_url}/api/session/create",
    json={"session_id": "demo"}
)
print(response.json())

# Load website
response = requests.post(
    f"{base_url}/api/session/demo/load",
    json={"url": "https://www.wikipedia.org"}
)
print(response.json())

# View at port 7900
print("View the page at port 7900 in VS Code Ports tab")

time.sleep(10)

# Close session
response = requests.post(f"{base_url}/api/session/demo/close")
print(response.json())
```

### Method 3: From External Devices

To test from external devices (phones, tablets, IoT devices):

1. In VS Code Ports tab, right-click port **7900**
2. Select **Port Visibility** → **Public**
3. Copy the forwarded URL
4. Open on your device: `https://YOUR-CODESPACE-NAME-7900.app.github.dev`

This simulates the actual use case of rendering websites on low-end devices!

## 📊 Advanced Testing Scenarios

### Performance Testing

```bash
# Monitor resource usage
docker stats

# Check active sessions
curl http://localhost:5000/api/sessions

# Test concurrent sessions
for i in {1..5}; do
  curl -X POST http://localhost:5000/api/session/create \
    -H "Content-Type: application/json" \
    -d "{\"session_id\": \"session_$i\"}" &
done
wait
```

### Testing Complex Websites

```bash
# Test JavaScript-heavy site
curl -X POST http://localhost:5000/api/session/create \
  -d '{"session_id": "js_test"}'
curl -X POST http://localhost:5000/api/session/js_test/load \
  -d '{"url": "https://react.dev"}'

# Test video streaming site
curl -X POST http://localhost:5000/api/session/create \
  -d '{"session_id": "video_test"}'
curl -X POST http://localhost:5000/api/session/video_test/load \
  -d '{"url": "https://www.youtube.com"}'

# Test social media
curl -X POST http://localhost:5000/api/session/create \
  -d '{"session_id": "social_test"}'
curl -X POST http://localhost:5000/api/session/social_test/load \
  -d '{"url": "https://twitter.com"}'
```

### Automated Testing Script

Create `tests/test_external_websites.sh`:

```bash
#!/bin/bash
# Comprehensive external website testing

set -e

echo "Starting External Website Tests..."

# Test categories
declare -A websites=(
    ["Search Engine"]="https://www.google.com"
    ["News Site"]="https://news.ycombinator.com"
    ["Documentation"]="https://docs.python.org"
    ["E-commerce"]="https://www.amazon.com"
    ["Social Media"]="https://reddit.com"
    ["Video Platform"]="https://vimeo.com"
    ["Developer Tools"]="https://github.com"
)

for category in "${!websites[@]}"; do
    url="${websites[$category]}"
    session_id=$(echo "$category" | tr ' ' '_' | tr '[:upper:]' '[:lower:]')
    
    echo ""
    echo "Testing $category: $url"
    
    # Create session
    curl -s -X POST http://localhost:5000/api/session/create \
        -H "Content-Type: application/json" \
        -d "{\"session_id\": \"$session_id\"}" > /dev/null
    
    # Load website
    start_time=$(date +%s)
    response=$(curl -s -X POST http://localhost:5000/api/session/$session_id/load \
        -H "Content-Type: application/json" \
        -d "{\"url\": \"$url\"}")
    end_time=$(date +%s)
    
    if echo "$response" | grep -q "success"; then
        load_time=$((end_time - start_time))
        echo "✓ Loaded in ${load_time}s"
    else
        echo "✗ Failed to load"
    fi
    
    # Get page info
    info=$(curl -s http://localhost:5000/api/session/$session_id/info)
    title=$(echo "$info" | grep -o '"title":"[^"]*"' | cut -d'"' -f4)
    echo "  Page title: $title"
    
    sleep 2
    
    # Close session
    curl -s -X POST http://localhost:5000/api/session/$session_id/close > /dev/null
done

echo ""
echo "✓ All external website tests complete!"
```

## 🛠️ Troubleshooting

### Services Not Starting

```bash
# Check Docker status
docker compose ps

# View logs
docker compose logs renderer
docker compose logs chrome

# Restart services
docker compose down
docker compose up -d
```

### Port Not Forwarding

1. Go to **PORTS** tab
2. Check if port shows "Port not available"
3. Try making it **Public**
4. Refresh the Codespace if needed

### Out of Resources

Codespaces might run out of resources with multiple sessions:

```bash
# Check resource usage
docker stats

# Scale down if needed
docker compose down
docker system prune -f

# Restart with limited sessions
docker compose up -d
```

### VNC Page Not Loading

```bash
# Verify VNC service
docker logs jiomosa-chrome

# Check VNC port
docker port jiomosa-chrome 7900

# Restart Chrome container
docker compose restart chrome
```

## 💰 Codespaces Pricing

GitHub provides free Codespaces hours:
- **Free tier**: 120 core-hours/month (60 hours on 2-core machine)
- **Pro plan**: 180 core-hours/month
- Stopped Codespaces don't consume hours

**Tips to save hours:**
- Stop Codespace when not in use (automatic after 30 min)
- Use the smallest machine type that works
- Delete unused Codespaces

## 🔐 Security Considerations

When testing external websites in Codespaces:

1. **Port Visibility**: Keep ports **Private** unless sharing is needed
2. **Session Management**: Close sessions after testing
3. **Sensitive Sites**: Avoid logging into accounts on test sessions
4. **Public Access**: Only make ports public temporarily
5. **Clean Up**: Stop Codespace when done

## 📝 Best Practices

### For Development

```bash
# Keep services running in background
docker compose up -d

# Monitor logs in real-time
docker compose logs -f renderer

# Quick restart after changes
docker compose restart renderer
```

### For Testing

```bash
# Test before committing
bash tests/test_websites.sh

# Verify API functionality
python tests/test_renderer.py

# Check service health
curl http://localhost:5000/health
```

### For Collaboration

1. **Share your Codespace URL**:
   - Make port 7900 Public
   - Share the forwarded URL
   - Others can view rendered pages

2. **Live Share**:
   - Use VS Code Live Share extension
   - Collaborate in real-time

## 🎯 Real-World Testing Scenarios

### Scenario 1: IoT Device Simulation

Test as if accessing from a low-end device:

```bash
# Start session
curl -X POST http://localhost:5000/api/session/create \
  -d '{"session_id": "iot_device"}'

# Load a complex website
curl -X POST http://localhost:5000/api/session/iot_device/load \
  -d '{"url": "https://www.cnn.com"}'

# Access from mobile device using Public port URL
# This simulates an IoT device viewing the rendered stream
```

### Scenario 2: Web Scraping Test

```python
# test_scraping.py
import requests
import time

api = "http://localhost:5000"

# Create session
requests.post(f"{api}/api/session/create", json={"session_id": "scraper"})

# Load target website
requests.post(
    f"{api}/api/session/scraper/load",
    json={"url": "https://quotes.toscrape.com"}
)

time.sleep(3)

# Get page info
info = requests.get(f"{api}/api/session/scraper/info").json()
print(f"Loaded: {info['page_info']['title']}")

# Clean up
requests.post(f"{api}/api/session/scraper/close")
```

### Scenario 3: Automated Website Monitoring

Monitor website availability and rendering:

```bash
#!/bin/bash
# monitor_websites.sh

while true; do
    session_id="monitor_$(date +%s)"
    
    curl -s -X POST http://localhost:5000/api/session/create \
        -d "{\"session_id\": \"$session_id\"}" > /dev/null
    
    response=$(curl -s -X POST http://localhost:5000/api/session/$session_id/load \
        -d '{"url": "https://example.com"}')
    
    if echo "$response" | grep -q "success"; then
        echo "$(date): Website is accessible ✓"
    else
        echo "$(date): Website check failed ✗"
    fi
    
    curl -s -X POST http://localhost:5000/api/session/$session_id/close > /dev/null
    
    sleep 300  # Check every 5 minutes
done
```

## 📚 Next Steps

1. **Read the docs**:
   - [README.md](README.md) - Full documentation
   - [QUICKSTART.md](QUICKSTART.md) - Quick start guide
   - [DEPLOYMENT.md](DEPLOYMENT.md) - Other deployment options

2. **Try examples**:
   - `examples/quick_demo.sh` - Basic demo
   - `examples/python_client.py` - Python API usage
   - `tests/test_websites.sh` - Multi-site testing

3. **Customize**:
   - Modify `docker-compose.yml` for your needs
   - Create custom test scripts
   - Add authentication (for production)

4. **Deploy to production**:
   - See [DEPLOYMENT.md](DEPLOYMENT.md) for cloud options
   - Consider AWS, DigitalOcean, or GCP
   - Implement security measures

## 🆘 Getting Help

- **Issues**: [GitHub Issues](https://github.com/SharksJio/jiomosa/issues)
- **Discussions**: [GitHub Discussions](https://github.com/SharksJio/jiomosa/discussions)
- **Documentation**: See README.md and other docs

## ✅ Checklist: Testing External Websites

- [ ] Created Codespace
- [ ] Started services with `docker compose up -d`
- [ ] Verified health endpoint
- [ ] Tested example.com
- [ ] Tested 3+ different websites
- [ ] Viewed rendered pages on port 7900
- [ ] Tested from external device (mobile/tablet)
- [ ] Ran automated test suite
- [ ] Checked performance with `docker stats`
- [ ] Cleaned up sessions and stopped Codespace

---

**Happy Testing! 🚀**

With GitHub Codespaces, you can now test Jiomosa and external websites from anywhere, without any local setup!
