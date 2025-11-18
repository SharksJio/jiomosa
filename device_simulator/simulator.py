#!/usr/bin/env python3
"""
Jiomosa Device Simulator
A test application that emulates a low-end device (like ThreadX RTOS) 
to demonstrate website rendering in a WebView without showing browser UI.
"""
import os
import sys
import json
import time
import logging
import argparse
import requests
from flask import Flask, render_template_string, request, jsonify

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configuration
JIOMOSA_SERVER = os.getenv('JIOMOSA_SERVER', 'http://localhost:5000')
DEVICE_PROFILE = os.getenv('DEVICE_PROFILE', 'threadx_512mb')

# Device profiles simulating different hardware constraints
DEVICE_PROFILES = {
    'threadx_512mb': {
        'name': 'ThreadX RTOS (512MB RAM)',
        'screen_width': 1024,
        'screen_height': 600,
        'memory_mb': 512,
        'description': 'Low-end embedded device with minimal resources'
    },
    'iot_device': {
        'name': 'IoT Device (256MB RAM)',
        'screen_width': 800,
        'screen_height': 480,
        'memory_mb': 256,
        'description': 'Very constrained IoT device'
    },
    'thin_client': {
        'name': 'Thin Client (1GB RAM)',
        'screen_width': 1280,
        'screen_height': 720,
        'memory_mb': 1024,
        'description': 'Basic thin client workstation'
    },
    'legacy_system': {
        'name': 'Legacy System (2GB RAM)',
        'screen_width': 1366,
        'screen_height': 768,
        'memory_mb': 2048,
        'description': 'Older computer with limited resources'
    }
}

# Global state
current_session_id = None
current_profile = DEVICE_PROFILES.get(DEVICE_PROFILE, DEVICE_PROFILES['threadx_512mb'])


# HTML template for the device simulator UI
SIMULATOR_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Jiomosa Device Simulator - {{ profile['name'] }}</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        
        .simulator-container {
            background: #fff;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
            max-width: 1400px;
            width: 100%;
            display: flex;
            flex-direction: column;
            height: 90vh;
        }
        
        .device-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .device-info {
            display: flex;
            align-items: center;
            gap: 15px;
        }
        
        .device-icon {
            width: 40px;
            height: 40px;
            background: rgba(255,255,255,0.2);
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 20px;
        }
        
        .device-details h1 {
            font-size: 18px;
            margin-bottom: 3px;
        }
        
        .device-details p {
            font-size: 12px;
            opacity: 0.9;
        }
        
        .device-stats {
            display: flex;
            gap: 20px;
            font-size: 12px;
        }
        
        .stat-item {
            background: rgba(255,255,255,0.2);
            padding: 5px 10px;
            border-radius: 5px;
        }
        
        .control-panel {
            background: #f8f9fa;
            padding: 15px 20px;
            border-bottom: 1px solid #e0e0e0;
        }
        
        .control-row {
            display: flex;
            gap: 10px;
            align-items: center;
        }
        
        .url-input {
            flex: 1;
            padding: 10px 15px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 14px;
            transition: border-color 0.3s;
        }
        
        .url-input:focus {
            outline: none;
            border-color: #667eea;
        }
        
        .btn {
            padding: 10px 20px;
            border: none;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
            display: flex;
            align-items: center;
            gap: 5px;
        }
        
        .btn-primary {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        
        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
        }
        
        .btn-secondary {
            background: #6c757d;
            color: white;
        }
        
        .btn-secondary:hover {
            background: #5a6268;
        }
        
        .btn-success {
            background: #28a745;
            color: white;
        }
        
        .btn-success:hover {
            background: #218838;
        }
        
        .btn-danger {
            background: #dc3545;
            color: white;
        }
        
        .btn-danger:hover {
            background: #c82333;
        }
        
        .btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        
        .device-screen {
            flex: 1;
            background: #000;
            position: relative;
            overflow: hidden;
        }
        
        #webview-frame {
            width: 100%;
            height: 100%;
            border: none;
            display: none;
        }
        
        .welcome-screen {
            width: 100%;
            height: 100%;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            color: #888;
            text-align: center;
            padding: 40px;
        }
        
        .welcome-screen .icon {
            font-size: 80px;
            margin-bottom: 20px;
            opacity: 0.3;
        }
        
        .welcome-screen h2 {
            font-size: 24px;
            margin-bottom: 10px;
            color: #666;
        }
        
        .welcome-screen p {
            font-size: 14px;
            max-width: 500px;
        }
        
        .loading-screen {
            width: 100%;
            height: 100%;
            display: none;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            color: #fff;
        }
        
        .spinner {
            width: 50px;
            height: 50px;
            border: 5px solid rgba(255,255,255,0.3);
            border-top-color: #fff;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin-bottom: 20px;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        
        .status-bar {
            background: #f8f9fa;
            padding: 8px 20px;
            border-top: 1px solid #e0e0e0;
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 12px;
            color: #6c757d;
        }
        
        .status-indicator {
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .status-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #28a745;
            animation: pulse 2s infinite;
        }
        
        .status-dot.disconnected {
            background: #dc3545;
            animation: none;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        
        .quick-actions {
            display: flex;
            gap: 10px;
            margin-top: 10px;
        }
        
        .quick-action-btn {
            padding: 5px 10px;
            font-size: 12px;
            background: #e9ecef;
            color: #495057;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            transition: all 0.2s;
        }
        
        .quick-action-btn:hover {
            background: #dee2e6;
        }
        
        .profiles-dropdown {
            padding: 8px 12px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 14px;
            background: white;
            cursor: pointer;
        }
    </style>
</head>
<body>
    <div class="simulator-container">
        <!-- Device Header -->
        <div class="device-header">
            <div class="device-info">
                <div class="device-icon">📱</div>
                <div class="device-details">
                    <h1>{{ profile['name'] }}</h1>
                    <p>{{ profile['description'] }}</p>
                </div>
            </div>
            <div class="device-stats">
                <div class="stat-item">
                    🖥️ {{ profile['screen_width'] }}x{{ profile['screen_height'] }}
                </div>
                <div class="stat-item">
                    💾 {{ profile['memory_mb'] }}MB RAM
                </div>
            </div>
        </div>
        
        <!-- Control Panel -->
        <div class="control-panel">
            <div class="control-row">
                <select id="profileSelect" class="profiles-dropdown" onchange="changeProfile()">
                    {% for key, prof in profiles.items() %}
                    <option value="{{ key }}" {% if key == current_profile_key %}selected{% endif %}>
                        {{ prof['name'] }}
                    </option>
                    {% endfor %}
                </select>
                <input type="text" 
                       id="urlInput" 
                       class="url-input" 
                       placeholder="Enter URL to load (e.g., https://example.com)"
                       value="">
                <button class="btn btn-primary" onclick="loadURL()">
                    🚀 Load Website
                </button>
                <button class="btn btn-success" onclick="createSession()" id="createBtn">
                    ➕ New Session
                </button>
                <button class="btn btn-danger" onclick="closeSession()" id="closeBtn" disabled>
                    ❌ Close
                </button>
            </div>
            <div class="quick-actions">
                <button class="quick-action-btn" onclick="loadQuickURL('https://example.com')">
                    Example.com
                </button>
                <button class="quick-action-btn" onclick="loadQuickURL('https://www.wikipedia.org')">
                    Wikipedia
                </button>
                <button class="quick-action-btn" onclick="loadQuickURL('https://news.ycombinator.com')">
                    Hacker News
                </button>
                <button class="quick-action-btn" onclick="loadQuickURL('https://github.com')">
                    GitHub
                </button>
            </div>
        </div>
        
        <!-- Device Screen (WebView) -->
        <div class="device-screen">
            <div class="welcome-screen" id="welcomeScreen">
                <div class="icon">🌐</div>
                <h2>Welcome to Jiomosa Device Simulator</h2>
                <p>This simulates a low-end device viewing cloud-rendered websites. 
                   Click "New Session" to start, then enter a URL to browse.</p>
                <p style="margin-top: 10px; font-size: 12px; opacity: 0.7;">
                    No browser UI - just the website content, perfect for embedded systems.
                </p>
            </div>
            <div class="loading-screen" id="loadingScreen">
                <div class="spinner"></div>
                <p>Loading website...</p>
            </div>
            <iframe id="webview-frame"></iframe>
        </div>
        
        <!-- Status Bar -->
        <div class="status-bar">
            <div class="status-indicator">
                <div class="status-dot" id="statusDot"></div>
                <span id="statusText">Disconnected</span>
            </div>
            <div id="sessionInfo">No active session</div>
            <div id="jiomosaServer">Jiomosa: {{ jiomosa_server }}</div>
        </div>
    </div>
    
    <script>
        // Use the simulator's proxy endpoint to avoid CORS issues in Codespaces
        const JIOMOSA_SERVER = "/proxy"; // Proxy through the simulator backend
        
        let currentSessionId = null;
        let keepaliveInterval = null;
        
        // Initialize
        window.addEventListener('load', () => {
            checkServerHealth();
            setInterval(checkServerHealth, 30000); // Check every 30 seconds
        });
        
        async function checkServerHealth() {
            try {
                const response = await fetch(`${JIOMOSA_SERVER}/health`);
                if (response.ok) {
                    updateStatus('connected', 'Connected to Jiomosa Server');
                } else {
                    updateStatus('disconnected', 'Server Error');
                }
            } catch (error) {
                updateStatus('disconnected', 'Cannot connect to Jiomosa Server');
            }
        }
        
        function updateStatus(status, message) {
            const statusDot = document.getElementById('statusDot');
            const statusText = document.getElementById('statusText');
            
            if (status === 'connected') {
                statusDot.classList.remove('disconnected');
                statusText.textContent = message;
            } else {
                statusDot.classList.add('disconnected');
                statusText.textContent = message;
            }
        }
        
        async function createSession() {
            const createBtn = document.getElementById('createBtn');
            const closeBtn = document.getElementById('closeBtn');
            
            try {
                createBtn.disabled = true;
                updateStatus('connected', 'Creating session...');
                
                const sessionId = `device_sim_${Date.now()}`;
                const response = await fetch(`${JIOMOSA_SERVER}/api/session/create`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({session_id: sessionId})
                });
                
                if (!response.ok) {
                    const errorText = await response.text();
                    throw new Error(`HTTP ${response.status}: ${errorText}`);
                }
                
                const data = await response.json();
                currentSessionId = data.session_id;
                
                document.getElementById('sessionInfo').textContent = 
                    `Session: ${currentSessionId}`;
                
                createBtn.disabled = true;
                closeBtn.disabled = false;
                
                updateStatus('connected', 'Session active');
                
                // Start keepalive
                startKeepalive();
                
                console.log(`Session created successfully: ${currentSessionId}`);
                return true; // Indicate success
                
            } catch (error) {
                console.error('Error creating session:', error);
                const errorMsg = error.message || 'Unknown error';
                alert(`Failed to create session: ${errorMsg}\n\nCheck console (F12) for details.\nServer: ${JIOMOSA_SERVER}`);
                createBtn.disabled = false;
                updateStatus('disconnected', 'Session creation failed');
                return false; // Indicate failure
            }
        }
        
        async function loadURL() {
            const urlInput = document.getElementById('urlInput');
            const url = urlInput.value.trim();
            
            if (!url) {
                alert('Please enter a URL');
                return;
            }
            
            // Automatically create session if none exists
            if (!currentSessionId) {
                const success = await createSession();
                if (!success) {
                    // Session creation failed, don't continue
                    return;
                }
                // Wait a moment for session to be fully ready
                await new Promise(resolve => setTimeout(resolve, 500));
            }
            
            try {
                showLoading(true);
                updateStatus('connected', 'Loading URL...');
                
                // Load URL in the session
                const response = await fetch(
                    `${JIOMOSA_SERVER}/api/session/${currentSessionId}/load`,
                    {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({url: url})
                    }
                );
                
                if (!response.ok) {
                    const errorText = await response.text();
                    throw new Error(`HTTP ${response.status}: ${errorText}`);
                }
                
                // Wait a moment for the page to start rendering
                await new Promise(resolve => setTimeout(resolve, 2000));
                
                // Use noVNC for interactive viewing instead of static frames
                // The noVNC viewer allows full mouse/keyboard interaction
                const vncUrl = 'http://localhost:7900/?autoconnect=1&resize=scale&password=secret';
                
                // In Codespaces, we need to use the forwarded port URL
                let viewerURL;
                if (window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1') {
                    // We're in Codespaces - construct the forwarded URL
                    const currentUrl = new URL(window.location.href);
                    if (currentUrl.hostname.includes('github.dev') || currentUrl.hostname.includes('githubpreview.dev')) {
                        // GitHub Codespaces format: xxx-8000.xxx.github.dev -> xxx-7900.xxx.github.dev
                        const vncHost = currentUrl.hostname.replace(/-8000\./, '-7900.');
                        viewerURL = `${currentUrl.protocol}//${vncHost}/?autoconnect=1&resize=scale&password=secret`;
                    } else {
                        viewerURL = vncUrl;
                    }
                } else {
                    viewerURL = vncUrl;
                }
                
                document.getElementById('webview-frame').src = viewerURL;
                
                showWebView();
                updateStatus('connected', `Viewing: ${url}`);
                
            } catch (error) {
                console.error('Error loading URL:', error);
                alert(`Failed to load URL: ${error.message}\n\nCheck console (F12) for details.`);
                showLoading(false);
            }
        }
        
        async function loadQuickURL(url) {
            document.getElementById('urlInput').value = url;
            
            // Automatically create session if none exists
            if (!currentSessionId) {
                const success = await createSession();
                if (!success) {
                    // Session creation failed, don't continue
                    return;
                }
            }
            
            // Load the URL (with small delay to ensure session is ready)
            setTimeout(() => loadURL(), 500);
        }
        
        async function closeSession() {
            if (!currentSessionId) return;
            
            try {
                updateStatus('connected', 'Closing session...');
                
                const response = await fetch(
                    `${JIOMOSA_SERVER}/api/session/${currentSessionId}/close`,
                    {method: 'POST'}
                );
                
                if (!response.ok) {
                    throw new Error('Failed to close session');
                }
                
                stopKeepalive();
                currentSessionId = null;
                
                document.getElementById('sessionInfo').textContent = 'No active session';
                document.getElementById('createBtn').disabled = false;
                document.getElementById('closeBtn').disabled = true;
                document.getElementById('urlInput').value = '';
                
                showWelcome();
                updateStatus('connected', 'Session closed');
                
            } catch (error) {
                console.error('Error closing session:', error);
                alert('Failed to close session: ' + error.message);
            }
        }
        
        function startKeepalive() {
            if (keepaliveInterval) {
                clearInterval(keepaliveInterval);
            }
            
            keepaliveInterval = setInterval(async () => {
                if (currentSessionId) {
                    try {
                        await fetch(
                            `${JIOMOSA_SERVER}/api/session/${currentSessionId}/keepalive`,
                            {method: 'POST'}
                        );
                    } catch (error) {
                        console.error('Keepalive failed:', error);
                    }
                }
            }, 30000); // Every 30 seconds
        }
        
        function stopKeepalive() {
            if (keepaliveInterval) {
                clearInterval(keepaliveInterval);
                keepaliveInterval = null;
            }
        }
        
        function showWelcome() {
            document.getElementById('welcomeScreen').style.display = 'flex';
            document.getElementById('loadingScreen').style.display = 'none';
            document.getElementById('webview-frame').style.display = 'none';
        }
        
        function showLoading(show) {
            if (show) {
                document.getElementById('welcomeScreen').style.display = 'none';
                document.getElementById('loadingScreen').style.display = 'flex';
                document.getElementById('webview-frame').style.display = 'none';
            } else {
                document.getElementById('loadingScreen').style.display = 'none';
            }
        }
        
        function showWebView() {
            document.getElementById('welcomeScreen').style.display = 'none';
            document.getElementById('loadingScreen').style.display = 'none';
            document.getElementById('webview-frame').style.display = 'block';
        }
        
        function changeProfile() {
            const profile = document.getElementById('profileSelect').value;
            window.location.href = `/simulator?profile=${profile}`;
        }
        
        // Cleanup on page unload
        window.addEventListener('beforeunload', () => {
            stopKeepalive();
        });
    </script>
</body>
</html>
"""


@app.route('/')
def index():
    """Redirect to simulator page"""
    return simulator()


@app.route('/simulator')
def simulator():
    """Main device simulator interface"""
    profile_key = request.args.get('profile', DEVICE_PROFILE)
    profile = DEVICE_PROFILES.get(profile_key, DEVICE_PROFILES['threadx_512mb'])
    
    return render_template_string(
        SIMULATOR_TEMPLATE,
        profile=profile,
        profiles=DEVICE_PROFILES,
        current_profile_key=profile_key,
        jiomosa_server=JIOMOSA_SERVER
    )


@app.route('/api/profiles')
def get_profiles():
    """Get available device profiles"""
    return jsonify(DEVICE_PROFILES)


@app.route('/proxy/<path:endpoint>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def proxy_to_jiomosa(endpoint):
    """Proxy requests to Jiomosa server to avoid CORS issues"""
    try:
        url = f"{JIOMOSA_SERVER}/{endpoint}"
        
        # Forward the request
        if request.method == 'POST':
            response = requests.post(url, json=request.get_json(), timeout=30)
        elif request.method == 'GET':
            response = requests.get(url, timeout=30)
        elif request.method == 'PUT':
            response = requests.put(url, json=request.get_json(), timeout=30)
        elif request.method == 'DELETE':
            response = requests.delete(url, timeout=30)
        else:
            return jsonify({'error': 'Method not allowed'}), 405
        
        # Return the response
        return response.content, response.status_code, {'Content-Type': response.headers.get('Content-Type', 'application/json')}
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Proxy error: {e}")
        return jsonify({'error': str(e), 'jiomosa_server': JIOMOSA_SERVER}), 500


@app.route('/api/<path:endpoint>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def proxy_api_to_jiomosa(endpoint):
    """Direct proxy for /api/ paths (for viewer iframe)"""
    return proxy_to_jiomosa(f"api/{endpoint}")


@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'jiomosa-device-simulator',
        'jiomosa_server': JIOMOSA_SERVER,
        'current_profile': current_profile['name']
    })


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Jiomosa Device Simulator - Test low-end device website rendering'
    )
    parser.add_argument(
        '--server',
        default='http://localhost:5000',
        help='Jiomosa server URL (default: http://localhost:5000)'
    )
    parser.add_argument(
        '--profile',
        default='threadx_512mb',
        choices=DEVICE_PROFILES.keys(),
        help='Device profile to simulate (default: threadx_512mb)'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=8000,
        help='Port to run simulator on (default: 8000)'
    )
    parser.add_argument(
        '--host',
        default='0.0.0.0',
        help='Host to bind to (default: 0.0.0.0)'
    )
    
    args = parser.parse_args()
    
    # Update configuration
    global JIOMOSA_SERVER, DEVICE_PROFILE, current_profile
    JIOMOSA_SERVER = args.server
    DEVICE_PROFILE = args.profile
    current_profile = DEVICE_PROFILES[DEVICE_PROFILE]
    
    logger.info("="*60)
    logger.info("Jiomosa Device Simulator Starting")
    logger.info("="*60)
    logger.info(f"Jiomosa Server: {JIOMOSA_SERVER}")
    logger.info(f"Device Profile: {current_profile['name']}")
    logger.info(f"Simulator URL: http://{args.host}:{args.port}")
    logger.info("="*60)
    logger.info("Open the simulator in your browser to get started!")
    logger.info("="*60)
    
    # Check if Jiomosa server is accessible
    try:
        response = requests.get(f"{JIOMOSA_SERVER}/health", timeout=5)
        if response.ok:
            logger.info("✓ Successfully connected to Jiomosa server")
        else:
            logger.warning("⚠ Jiomosa server returned non-OK status")
    except Exception as e:
        logger.error(f"✗ Cannot connect to Jiomosa server: {e}")
        logger.error("  Make sure Jiomosa is running: docker compose up -d")
        sys.exit(1)
    
    # Run Flask app
    app.run(host=args.host, port=args.port, debug=False)


if __name__ == '__main__':
    main()
