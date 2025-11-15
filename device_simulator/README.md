# Jiomosa Device Simulator

A standalone test application that emulates low-end devices (like ThreadX RTOS, IoT devices, thin clients) to demonstrate how cloud-rendered websites can be displayed in a WebView without showing any browser UI.

## Overview

The Device Simulator provides a realistic testing environment for understanding how Jiomosa works on resource-constrained devices. It simulates different hardware profiles and displays only website content through a WebView-like interface, hiding all browser chrome and UI elements.

## Key Features

- **🖥️ Multiple Device Profiles**: Simulate different hardware constraints (ThreadX, IoT devices, thin clients, legacy systems)
- **🌐 WebView-Only Display**: Shows rendered websites without any browser UI
- **⚡ Real-time Streaming**: Uses HTML5 framebuffer streaming for low overhead
- **🎮 Interactive Controls**: Easy-to-use interface for testing different URLs
- **📊 Device Metrics**: Displays screen resolution and memory constraints
- **🔄 Session Management**: Create, manage, and close browser sessions
- **💓 Automatic Keepalive**: Maintains sessions without manual intervention

## Device Profiles

The simulator includes several pre-configured device profiles:

### ThreadX RTOS (512MB RAM)
- **Screen**: 1024x600
- **Memory**: 512MB
- **Use Case**: Low-end embedded devices like industrial controllers, medical devices

### IoT Device (256MB RAM)
- **Screen**: 800x480
- **Memory**: 256MB
- **Use Case**: Very constrained IoT devices, smart home controllers

### Thin Client (1GB RAM)
- **Screen**: 1280x720
- **Memory**: 1GB
- **Use Case**: Basic workstations, kiosks, point-of-sale systems

### Legacy System (2GB RAM)
- **Screen**: 1366x768
- **Memory**: 2GB
- **Use Case**: Older computers, legacy industrial systems

## Installation

### Prerequisites

- Python 3.8 or higher
- Jiomosa server running (see main README.md)

### Quick Start

1. **Ensure Jiomosa is running**:
   ```bash
   cd /path/to/jiomosa
   docker compose up -d
   ```

2. **Run the simulator**:
   ```bash
   cd device_simulator
   ./run_simulator.sh
   ```

3. **Open your browser**:
   ```
   http://localhost:8000
   ```

### Manual Installation

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run simulator
python3 simulator.py
```

## Usage

### Basic Usage

1. **Start the simulator**:
   ```bash
   ./run_simulator.sh
   ```

2. **Open in browser**: Navigate to `http://localhost:8000`

3. **Create a session**: Click the "New Session" button

4. **Load a website**: 
   - Enter a URL in the input field
   - Click "Load Website"
   - Or use one of the quick action buttons

5. **View the website**: The website will be displayed in the device screen area, showing only the content without any browser UI

6. **Close session**: Click "Close" when done

### Command Line Options

```bash
python3 simulator.py --help
```

**Options**:
- `--server URL`: Jiomosa server URL (default: http://localhost:5000)
- `--profile PROFILE`: Device profile to use (default: threadx_512mb)
- `--port PORT`: Port to run simulator on (default: 8000)
- `--host HOST`: Host to bind to (default: 0.0.0.0)

**Examples**:

```bash
# Use different device profile
python3 simulator.py --profile iot_device

# Connect to remote Jiomosa server
python3 simulator.py --server http://192.168.1.100:5000

# Run on different port
python3 simulator.py --port 9000

# Combine options
python3 simulator.py --server http://remote:5000 --profile thin_client --port 8080
```

### Using Environment Variables

```bash
# Set Jiomosa server
export JIOMOSA_SERVER=http://192.168.1.100:5000

# Set device profile
export DEVICE_PROFILE=iot_device

# Set port
export PORT=8080

# Run simulator
./run_simulator.sh
```

## Architecture

```
┌─────────────────────────────────────────────┐
│       Device Simulator (Python/Flask)        │
│                                              │
│  ┌────────────────────────────────────────┐ │
│  │         Web-based UI                   │ │
│  │  - Device profile selection            │ │
│  │  - URL input and controls              │ │
│  │  - WebView-like display area           │ │
│  └────────────────────────────────────────┘ │
│                    │                         │
│                    │ REST API calls          │
│                    ▼                         │
│  ┌────────────────────────────────────────┐ │
│  │    Session Management                  │ │
│  │  - Create/close sessions               │ │
│  │  - Load URLs                           │ │
│  │  - Automatic keepalive                 │ │
│  └────────────────────────────────────────┘ │
└────────────────┬────────────────────────────┘
                 │
                 │ HTTP/REST
                 ▼
┌─────────────────────────────────────────────┐
│      Jiomosa Renderer Service (Flask)       │
│  - Create browser sessions                  │
│  - Load URLs in Selenium                    │
│  - Provide framebuffer viewer               │
└────────────────┬────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────┐
│       Selenium Grid + Chrome Browser        │
│  - Render actual websites                   │
│  - Provide display via VNC                  │
└─────────────────────────────────────────────┘
```

## How It Works

1. **Session Creation**: 
   - User clicks "New Session" in the simulator
   - Simulator calls Jiomosa API to create a browser session
   - A unique session ID is assigned

2. **URL Loading**:
   - User enters a URL and clicks "Load Website"
   - Simulator sends the URL to Jiomosa
   - Jiomosa instructs Selenium to load the page in Chrome
   - Chrome renders the website

3. **Display**:
   - Simulator embeds the Jiomosa HTML5 viewer in an iframe
   - The viewer captures browser screenshots every second
   - Screenshots are displayed in the device screen area
   - Only website content is shown, no browser UI

4. **Keepalive**:
   - Simulator automatically sends keepalive signals every 30 seconds
   - This prevents the session from timing out
   - Sessions remain active as long as the simulator is open

## Testing Scenarios

### Scenario 1: Simple Static Website
```
1. Create session
2. Load: https://example.com
3. Observe: Clean rendering without browser UI
```

### Scenario 2: Complex Dynamic Website
```
1. Create session
2. Load: https://www.wikipedia.org
3. Observe: Full Wikipedia site rendered and streamed
```

### Scenario 3: Mobile-Responsive Site
```
1. Select "IoT Device" profile (800x480)
2. Create session
3. Load: https://news.ycombinator.com
4. Observe: Site adapts to smaller screen size
```

### Scenario 4: Multiple Sessions
```
1. Open simulator in two browser tabs
2. Create session in each tab
3. Load different URLs
4. Observe: Independent sessions running concurrently
```

## Integration Examples

### Embedding in Native Applications

#### Electron App
```javascript
const { BrowserWindow } = require('electron');

// Create window for device simulator
const simWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    webPreferences: {
        nodeIntegration: false
    }
});

// Load simulator
simWindow.loadURL('http://localhost:8000/simulator?profile=threadx_512mb');
```

#### WebView in Android
```java
WebView webView = findViewById(R.id.webview);
webView.getSettings().setJavaScriptEnabled(true);
webView.loadUrl("http://192.168.1.100:8000/simulator?profile=iot_device");
```

#### WebView in iOS
```swift
import WebKit

let webView = WKWebView(frame: view.bounds)
if let url = URL(string: "http://192.168.1.100:8000/simulator?profile=iot_device") {
    webView.load(URLRequest(url: url))
}
view.addSubview(webView)
```

### Programmatic Control

The simulator can be controlled programmatically via the Jiomosa API:

```python
import requests

JIOMOSA_SERVER = "http://localhost:5000"

# Create session
response = requests.post(
    f"{JIOMOSA_SERVER}/api/session/create",
    json={"session_id": "my_test_session"}
)
session_id = response.json()["session_id"]

# Load URL
requests.post(
    f"{JIOMOSA_SERVER}/api/session/{session_id}/load",
    json={"url": "https://example.com"}
)

# Access viewer directly
viewer_url = f"{JIOMOSA_SERVER}/api/session/{session_id}/viewer"
print(f"Viewer URL: {viewer_url}")

# Send keepalive
requests.post(f"{JIOMOSA_SERVER}/api/session/{session_id}/keepalive")

# Close session
requests.post(f"{JIOMOSA_SERVER}/api/session/{session_id}/close")
```

## Performance Considerations

### Network Bandwidth

With default settings:
- Frame rate: 1 FPS
- Frame size: ~20-50KB (PNG compressed)
- Bandwidth: ~240 Kbps average

For lower bandwidth:
- Use smaller device profiles (IoT Device: 800x480)
- Increase frame capture interval in viewer

### Resource Usage

Simulator itself is lightweight:
- CPU: < 1% (mostly idle)
- Memory: ~50MB
- Network: Minimal (HTTP requests only)

Heavy lifting done by Jiomosa server:
- Chrome browser: ~200-500MB RAM
- Selenium: ~100MB RAM
- Guacamole/VNC: ~50MB RAM

### Latency

Typical latency (LAN):
- Frame capture: 100-200ms
- Network transfer: 10-50ms
- Display update: 50-100ms
- **Total**: 200-400ms per frame

For lower latency:
- Deploy Jiomosa on local network
- Reduce frame capture interval
- Use wired connection instead of WiFi

## Troubleshooting

### Cannot Connect to Jiomosa Server

**Problem**: Simulator shows "Cannot connect to Jiomosa Server"

**Solutions**:
1. Ensure Jiomosa is running: `docker compose up -d`
2. Check if port 5000 is accessible: `curl http://localhost:5000/health`
3. If using remote server, check firewall rules
4. Verify correct server URL in simulator settings

### Session Creation Fails

**Problem**: Error when clicking "New Session"

**Solutions**:
1. Check Jiomosa logs: `docker compose logs renderer`
2. Verify Selenium is running: `docker compose logs chrome`
3. Check if session limit reached: `curl http://localhost:5000/api/sessions`
4. Restart services: `docker compose restart`

### Website Not Loading

**Problem**: URL loads but no display in device screen

**Solutions**:
1. Wait 10-15 seconds after loading URL (initial render time)
2. Check browser logs: `docker compose logs chrome`
3. Try a simpler URL first (e.g., example.com)
4. Verify URL is accessible from the server
5. Check if website blocks automated browsers

### Frames Not Updating

**Problem**: Website displayed but frozen/not updating

**Solutions**:
1. Check browser console for JavaScript errors
2. Verify keepalive is working (status should show "Connected")
3. Refresh the simulator page
4. Close and recreate the session

### High CPU/Memory Usage

**Problem**: System resources exhausted

**Solutions**:
1. Use smaller device profiles
2. Limit number of concurrent sessions
3. Close unused sessions
4. Increase frame capture interval
5. Add resource limits in docker-compose.yml

## Advanced Usage

### Custom Device Profiles

You can add custom device profiles by editing `simulator.py`:

```python
DEVICE_PROFILES = {
    'custom_device': {
        'name': 'Custom Device',
        'screen_width': 1280,
        'screen_height': 800,
        'memory_mb': 768,
        'description': 'Custom embedded device'
    },
    # ... other profiles
}
```

### Automated Testing

Use the simulator for automated testing:

```python
import time
import requests
from selenium import webdriver

# Start simulator in background
# Then use Selenium to control it

driver = webdriver.Chrome()
driver.get('http://localhost:8000')

# Wait for page load
time.sleep(2)

# Click "New Session" button
create_btn = driver.find_element(By.ID, 'createBtn')
create_btn.click()

# Wait for session creation
time.sleep(2)

# Load URL
url_input = driver.find_element(By.ID, 'urlInput')
url_input.send_keys('https://example.com')

load_btn = driver.find_element(By.XPATH, '//button[contains(text(), "Load Website")]')
load_btn.click()

# Wait and verify
time.sleep(5)

# Take screenshot
driver.save_screenshot('simulator_test.png')

driver.quit()
```

### Integration with CI/CD

Add to your CI pipeline:

```yaml
# .github/workflows/test-simulator.yml
name: Test Device Simulator

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v2
      
      - name: Start Jiomosa services
        run: docker compose up -d
      
      - name: Wait for services
        run: sleep 30
      
      - name: Install simulator dependencies
        run: |
          cd device_simulator
          pip install -r requirements.txt
      
      - name: Start simulator
        run: |
          cd device_simulator
          python3 simulator.py &
          sleep 10
      
      - name: Test simulator health
        run: curl http://localhost:8000/health
      
      - name: Run automated tests
        run: python tests/test_device_simulator.py
```

## Security Considerations

- The simulator is intended for **testing and development only**
- No authentication is implemented
- Not recommended for production use without additional security
- Ensure Jiomosa server is secured if exposed to network
- Use HTTPS in production environments
- Implement access controls for multi-user scenarios

## Comparison with Direct VNC Access

| Feature | Device Simulator | Direct VNC |
|---------|-----------------|------------|
| Browser UI visible | No ❌ | Yes ✅ |
| Setup complexity | Simple ✅ | Complex ❌ |
| Client requirements | Web browser only | VNC client needed |
| Device emulation | Yes ✅ | No ❌ |
| Testing scenarios | Multiple profiles | Single view |
| Integration | Easy (HTTP/iframe) | Harder (VNC protocol) |
| Bandwidth | Lower | Higher |
| User experience | Cleaner | Raw desktop |

## Future Enhancements

- [ ] Touch event simulation for mobile testing
- [ ] Network throttling simulation
- [ ] CPU/memory usage indicators
- [ ] Screenshot/recording capabilities
- [ ] Session history and bookmarks
- [ ] Multi-device side-by-side comparison
- [ ] Custom screen orientations (portrait/landscape)
- [ ] Performance metrics dashboard
- [ ] Automation scripting interface

## See Also

- [README.md](../README.md) - Main documentation
- [USAGE.md](../USAGE.md) - Jiomosa usage guide
- [KEEPALIVE_FRAMEBUFFER.md](../KEEPALIVE_FRAMEBUFFER.md) - Framebuffer streaming details
- [ARCHITECTURE.md](../ARCHITECTURE.md) - System architecture

## Support

For issues and questions:
- GitHub Issues: https://github.com/SharksJio/jiomosa/issues
- Documentation: See main repository README.md

---

**Built for testing cloud-rendered websites on low-end devices** 🚀
