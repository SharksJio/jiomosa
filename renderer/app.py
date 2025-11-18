"""
Jiomosa Renderer Service
A service that coordinates Selenium browser sessions with Guacamole for remote rendering
"""
import os
import logging
import time
import base64
import threading
from flask import Flask, jsonify, request, send_file, render_template_string
from flask_cors import CORS
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from io import BytesIO

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
# Enable CORS with support for all origins, methods, and headers
CORS(app, resources={
    r"/*": {
        "origins": "*",
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "expose_headers": ["Content-Type"],
        "supports_credentials": False,
        "max_age": 3600
    }
})

# Environment configuration
SELENIUM_HOST = os.getenv('SELENIUM_HOST', 'chrome')
SELENIUM_PORT = os.getenv('SELENIUM_PORT', '4444')
GUACD_HOST = os.getenv('GUACD_HOST', 'guacd')
GUACD_PORT = os.getenv('GUACD_PORT', '4822')
VNC_HOST = os.getenv('VNC_HOST', 'chrome')
VNC_PORT = os.getenv('VNC_PORT', '5900')
SESSION_TIMEOUT = int(os.getenv('SESSION_TIMEOUT', '300'))  # 5 minutes default
FRAME_CAPTURE_INTERVAL = float(os.getenv('FRAME_CAPTURE_INTERVAL', '1.0'))  # 1 second default

# Store active sessions
active_sessions = {}

# Session cleanup thread
cleanup_thread = None


class BrowserSession:
    """Manages a browser session for rendering websites"""
    
    def __init__(self, session_id):
        self.session_id = session_id
        self.driver = None
        self.created_at = time.time()
        self.last_activity = time.time()
        self.last_frame = None
        self.frame_capture_active = False
        self.frame_lock = threading.Lock()
        
    def initialize(self):
        """Initialize the Selenium WebDriver"""
        try:
            chrome_options = Options()
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            
            # Connect to remote Selenium Grid
            selenium_url = f'http://{SELENIUM_HOST}:{SELENIUM_PORT}/wd/hub'
            logger.info(f"Connecting to Selenium at {selenium_url}")
            
            self.driver = webdriver.Remote(
                command_executor=selenium_url,
                options=chrome_options
            )
            logger.info(f"Browser session {self.session_id} initialized")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize browser session: {e}")
            return False
    
    def load_url(self, url, wait_for_load=True, timeout=30):
        """Load a URL in the browser"""
        try:
            if not self.driver:
                if not self.initialize():
                    return False, "Failed to initialize browser"
            
            logger.info(f"Loading URL: {url}")
            self.driver.get(url)
            
            if wait_for_load:
                # Wait for page to be in ready state
                WebDriverWait(self.driver, timeout).until(
                    lambda d: d.execute_script('return document.readyState') == 'complete'
                )
            
            self.last_activity = time.time()
            logger.info(f"Successfully loaded: {url}")
            return True, "Page loaded successfully"
            
        except TimeoutException:
            logger.warning(f"Timeout loading URL: {url}")
            return True, "Page loaded with timeout (may be partially loaded)"
        except WebDriverException as e:
            logger.error(f"WebDriver error loading URL: {e}")
            return False, f"WebDriver error: {str(e)}"
        except Exception as e:
            logger.error(f"Unexpected error loading URL: {e}")
            return False, f"Error: {str(e)}"
    
    def get_page_info(self):
        """Get information about the current page"""
        try:
            if not self.driver:
                return None
            
            return {
                'title': self.driver.title,
                'url': self.driver.current_url,
                'session_id': self.session_id,
                'window_size': self.driver.get_window_size()
            }
        except Exception as e:
            logger.error(f"Error getting page info: {e}")
            return None
    
    def keepalive(self):
        """Update last activity timestamp to keep session alive"""
        self.last_activity = time.time()
        logger.info(f"Keepalive received for session {self.session_id}")
        return True
    
    def is_expired(self, timeout=SESSION_TIMEOUT):
        """Check if session has expired based on inactivity"""
        return (time.time() - self.last_activity) > timeout
    
    def capture_frame(self):
        """Capture current browser frame as PNG screenshot"""
        try:
            if not self.driver:
                return None
            
            # Capture screenshot as PNG
            screenshot = self.driver.get_screenshot_as_png()
            
            with self.frame_lock:
                self.last_frame = screenshot
                self.last_activity = time.time()
            
            return screenshot
        except Exception as e:
            logger.error(f"Error capturing frame: {e}")
            return None
    
    def get_last_frame(self):
        """Get the last captured frame"""
        with self.frame_lock:
            return self.last_frame
    
    def close(self):
        """Close the browser session"""
        try:
            if self.driver:
                self.driver.quit()
                logger.info(f"Browser session {self.session_id} closed")
        except Exception as e:
            logger.error(f"Error closing browser session: {e}")


def cleanup_expired_sessions():
    """Background task to clean up expired sessions"""
    while True:
        try:
            time.sleep(60)  # Check every minute
            expired_sessions = []
            
            for session_id, session in active_sessions.items():
                if session.is_expired():
                    expired_sessions.append(session_id)
            
            for session_id in expired_sessions:
                logger.info(f"Cleaning up expired session: {session_id}")
                try:
                    session = active_sessions[session_id]
                    session.close()
                    del active_sessions[session_id]
                except Exception as e:
                    logger.error(f"Error cleaning up session {session_id}: {e}")
        except Exception as e:
            logger.error(f"Error in cleanup thread: {e}")


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'jiomosa-renderer',
        'selenium': f'{SELENIUM_HOST}:{SELENIUM_PORT}',
        'guacd': f'{GUACD_HOST}:{GUACD_PORT}',
        'active_sessions': len(active_sessions)
    }), 200


@app.route('/api/info', methods=['GET'])
def info():
    """Get service information"""
    return jsonify({
        'service': 'Jiomosa Renderer',
        'version': '1.0.0',
        'description': 'Cloud-based website rendering service for low-end devices',
        'endpoints': {
            'health': '/health',
            'info': '/api/info',
            'session_create': '/api/session/create',
            'session_load': '/api/session/<session_id>/load',
            'session_info': '/api/session/<session_id>/info',
            'session_keepalive': '/api/session/<session_id>/keepalive',
            'session_close': '/api/session/<session_id>/close',
            'sessions_list': '/api/sessions',
            'session_frame': '/api/session/<session_id>/frame',
            'session_frame_data': '/api/session/<session_id>/frame/data',
            'session_viewer': '/api/session/<session_id>/viewer',
            'vnc_info': '/api/vnc/info'
        },
        'vnc_connection': {
            'host': VNC_HOST,
            'port': VNC_PORT,
            'web_interface': f'http://chrome:7900'
        },
        'session_config': {
            'timeout': SESSION_TIMEOUT,
            'frame_capture_interval': FRAME_CAPTURE_INTERVAL
        }
    }), 200


@app.route('/api/session/create', methods=['POST'])
def create_session():
    """Create a new browser session"""
    try:
        data = request.get_json() or {}
        session_id = data.get('session_id', f'session_{int(time.time())}')
        
        if session_id in active_sessions:
            return jsonify({
                'error': 'Session already exists',
                'session_id': session_id
            }), 400
        
        session = BrowserSession(session_id)
        if not session.initialize():
            return jsonify({
                'error': 'Failed to initialize browser session'
            }), 500
        
        active_sessions[session_id] = session
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'created_at': session.created_at,
            'vnc_url': f'vnc://{VNC_HOST}:{VNC_PORT}',
            'web_vnc_url': f'http://localhost:7900/?autoconnect=1&resize=scale&password=secret'
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating session: {e}")
        return jsonify({'error': 'Failed to create session'}), 500


@app.route('/api/session/<session_id>/load', methods=['POST'])
def load_url(session_id):
    """Load a URL in an existing session"""
    try:
        if session_id not in active_sessions:
            return jsonify({
                'error': 'Session not found',
                'session_id': session_id
            }), 404
        
        data = request.get_json() or {}
        url = data.get('url')
        
        if not url:
            return jsonify({'error': 'URL is required'}), 400
        
        # Add protocol if missing
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        session = active_sessions[session_id]
        success, message = session.load_url(url)
        
        if success:
            page_info = session.get_page_info()
            return jsonify({
                'success': True,
                'message': message,
                'page_info': page_info,
                'vnc_url': f'vnc://{VNC_HOST}:{VNC_PORT}',
                'web_vnc_url': f'http://localhost:7900/?autoconnect=1&resize=scale&password=secret'
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': message
            }), 500
            
    except Exception as e:
        logger.error(f"Error loading URL: {e}")
        return jsonify({'error': 'Failed to load URL'}), 500


@app.route('/api/session/<session_id>/info', methods=['GET'])
def session_info(session_id):
    """Get information about a session"""
    try:
        if session_id not in active_sessions:
            return jsonify({
                'error': 'Session not found',
                'session_id': session_id
            }), 404
        
        session = active_sessions[session_id]
        page_info = session.get_page_info()
        
        return jsonify({
            'session_id': session_id,
            'created_at': session.created_at,
            'last_activity': session.last_activity,
            'page_info': page_info,
            'vnc_url': f'vnc://{VNC_HOST}:{VNC_PORT}',
            'web_vnc_url': f'http://localhost:7900/?autoconnect=1&resize=scale&password=secret'
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting session info: {e}")
        return jsonify({'error': 'Failed to get session info'}), 500


@app.route('/api/session/<session_id>/close', methods=['POST', 'DELETE'])
def close_session(session_id):
    """Close a browser session"""
    try:
        if session_id not in active_sessions:
            return jsonify({
                'error': 'Session not found',
                'session_id': session_id
            }), 404
        
        session = active_sessions[session_id]
        session.close()
        del active_sessions[session_id]
        
        return jsonify({
            'success': True,
            'message': f'Session {session_id} closed'
        }), 200
        
    except Exception as e:
        logger.error(f"Error closing session: {e}")
        return jsonify({'error': 'Failed to close session'}), 500


@app.route('/api/sessions', methods=['GET'])
def list_sessions():
    """List all active sessions"""
    try:
        sessions_list = []
        for session_id, session in active_sessions.items():
            page_info = session.get_page_info()
            sessions_list.append({
                'session_id': session_id,
                'created_at': session.created_at,
                'last_activity': session.last_activity,
                'current_page': page_info.get('url') if page_info else None
            })
        
        return jsonify({
            'active_sessions': len(active_sessions),
            'sessions': sessions_list
        }), 200
        
    except Exception as e:
        logger.error(f"Error listing sessions: {e}")
        return jsonify({'error': 'Failed to list sessions'}), 500


@app.route('/api/session/<session_id>/keepalive', methods=['POST'])
def keepalive_session(session_id):
    """Send keepalive signal to maintain session"""
    try:
        if session_id not in active_sessions:
            return jsonify({
                'error': 'Session not found',
                'session_id': session_id
            }), 404
        
        session = active_sessions[session_id]
        session.keepalive()
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'last_activity': session.last_activity,
            'message': 'Keepalive successful'
        }), 200
        
    except Exception as e:
        logger.error(f"Error sending keepalive: {e}")
        return jsonify({'error': 'Failed to send keepalive'}), 500


@app.route('/api/session/<session_id>/frame', methods=['GET'])
def get_frame(session_id):
    """Get current frame/screenshot from browser session"""
    try:
        if session_id not in active_sessions:
            return jsonify({
                'error': 'Session not found',
                'session_id': session_id
            }), 404
        
        session = active_sessions[session_id]
        frame = session.capture_frame()
        
        if frame is None:
            return jsonify({'error': 'Failed to capture frame'}), 500
        
        # Return image directly
        return send_file(
            BytesIO(frame),
            mimetype='image/png',
            as_attachment=False,
            download_name=f'{session_id}_frame.png'
        )
        
    except Exception as e:
        logger.error(f"Error getting frame: {e}")
        return jsonify({'error': 'Failed to get frame'}), 500


@app.route('/api/session/<session_id>/frame/data', methods=['GET'])
def get_frame_data(session_id):
    """Get current frame as base64 encoded data"""
    try:
        if session_id not in active_sessions:
            return jsonify({
                'error': 'Session not found',
                'session_id': session_id
            }), 404
        
        session = active_sessions[session_id]
        frame = session.capture_frame()
        
        if frame is None:
            return jsonify({'error': 'Failed to capture frame'}), 500
        
        # Return as JSON with base64 encoded image
        frame_b64 = base64.b64encode(frame).decode('utf-8')
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'timestamp': time.time(),
            'frame': frame_b64,
            'format': 'png'
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting frame data: {e}")
        return jsonify({'error': 'Failed to get frame data'}), 500


@app.route('/api/session/<session_id>/viewer', methods=['GET'])
def viewer(session_id):
    """HTML5 viewer page for framebuffer streaming"""
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Jiomosa HTML5 Viewer - {{ session_id }}</title>
        <style>
            body {
                margin: 0;
                padding: 0;
                background-color: #1a1a1a;
                font-family: Arial, sans-serif;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                min-height: 100vh;
            }
            .container {
                max-width: 100%;
                padding: 20px;
            }
            .header {
                color: #fff;
                text-align: center;
                margin-bottom: 20px;
            }
            .viewer {
                border: 2px solid #333;
                box-shadow: 0 4px 6px rgba(0,0,0,0.3);
                background-color: #000;
                display: flex;
                align-items: center;
                justify-content: center;
                min-height: 400px;
            }
            #frame {
                max-width: 100%;
                height: auto;
                display: block;
            }
            .status {
                color: #888;
                text-align: center;
                margin-top: 10px;
                font-size: 14px;
            }
            .controls {
                text-align: center;
                margin-top: 20px;
            }
            button {
                background-color: #4CAF50;
                border: none;
                color: white;
                padding: 10px 20px;
                text-align: center;
                text-decoration: none;
                display: inline-block;
                font-size: 16px;
                margin: 4px 2px;
                cursor: pointer;
                border-radius: 4px;
            }
            button:hover {
                background-color: #45a049;
            }
            button.stop {
                background-color: #f44336;
            }
            button.stop:hover {
                background-color: #da190b;
            }
            .info {
                color: #ccc;
                text-align: center;
                margin-top: 10px;
                font-size: 12px;
            }
            .loading {
                color: #fff;
                font-size: 18px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Jiomosa HTML5 Viewer</h1>
                <p>Session: <strong>{{ session_id }}</strong></p>
            </div>
            <div class="viewer">
                <img id="frame" src="" alt="Loading browser frame..." />
                <div id="loading" class="loading">Loading...</div>
            </div>
            <div class="status">
                <span id="status">Initializing...</span>
            </div>
            <div class="controls">
                <button id="startBtn" onclick="startStreaming()">Start</button>
                <button id="stopBtn" class="stop" onclick="stopStreaming()">Stop</button>
                <button onclick="captureFrame()">Capture Frame</button>
            </div>
            <div class="info">
                <p>FPS: <span id="fps">0</span> | Last Update: <span id="lastUpdate">-</span></p>
                <p>This viewer streams browser frames from the cloud to your ThreadX app WebView</p>
            </div>
        </div>
        
        <script>
            const sessionId = "{{ session_id }}";
            let streamingInterval = null;
            let frameCount = 0;
            let lastFpsUpdate = Date.now();
            let isStreaming = false;
            
            const frameImg = document.getElementById('frame');
            const loadingDiv = document.getElementById('loading');
            const statusSpan = document.getElementById('status');
            const fpsSpan = document.getElementById('fps');
            const lastUpdateSpan = document.getElementById('lastUpdate');
            
            async function captureFrame() {
                try {
                    const response = await fetch(`/api/session/${sessionId}/frame?t=${Date.now()}`);
                    if (!response.ok) {
                        throw new Error('Failed to fetch frame');
                    }
                    
                    const blob = await response.blob();
                    const imageUrl = URL.createObjectURL(blob);
                    
                    frameImg.src = imageUrl;
                    frameImg.style.display = 'block';
                    loadingDiv.style.display = 'none';
                    
                    updateStatus('Frame captured');
                    updateLastUpdate();
                    updateFPS();
                    
                    // Send keepalive
                    await fetch(`/api/session/${sessionId}/keepalive`, {
                        method: 'POST'
                    });
                    
                } catch (error) {
                    console.error('Error capturing frame:', error);
                    updateStatus('Error: ' + error.message);
                }
            }
            
            function startStreaming() {
                if (isStreaming) return;
                
                isStreaming = true;
                updateStatus('Streaming...');
                
                // Capture immediately
                captureFrame();
                
                // Then capture every second
                streamingInterval = setInterval(captureFrame, 1000);
            }
            
            function stopStreaming() {
                if (!isStreaming) return;
                
                isStreaming = false;
                if (streamingInterval) {
                    clearInterval(streamingInterval);
                    streamingInterval = null;
                }
                updateStatus('Streaming stopped');
            }
            
            function updateStatus(message) {
                statusSpan.textContent = message;
            }
            
            function updateLastUpdate() {
                const now = new Date();
                lastUpdateSpan.textContent = now.toLocaleTimeString();
            }
            
            function updateFPS() {
                frameCount++;
                const now = Date.now();
                const elapsed = now - lastFpsUpdate;
                
                if (elapsed >= 1000) {
                    const fps = Math.round(frameCount / (elapsed / 1000));
                    fpsSpan.textContent = fps;
                    frameCount = 0;
                    lastFpsUpdate = now;
                }
            }
            
            // Auto-start streaming on page load
            window.addEventListener('load', () => {
                setTimeout(startStreaming, 500);
            });
            
            // Cleanup on page unload
            window.addEventListener('beforeunload', () => {
                stopStreaming();
            });
        </script>
    </body>
    </html>
    """
    
    return render_template_string(html_template, session_id=session_id)


@app.route('/api/vnc/info', methods=['GET'])
def vnc_info():
    """Get VNC connection information"""
    return jsonify({
        'vnc_host': VNC_HOST,
        'vnc_port': VNC_PORT,
        'vnc_url': f'vnc://{VNC_HOST}:{VNC_PORT}',
        'web_vnc_url': f'http://localhost:7900/?autoconnect=1&resize=scale&password=secret',
        'guacamole_url': f'http://localhost:8080/guacamole/',
        'info': 'Use VNC client or web interface to view the rendered browser'
    }), 200


if __name__ == '__main__':
    logger.info("Starting Jiomosa Renderer Service")
    logger.info(f"Selenium: {SELENIUM_HOST}:{SELENIUM_PORT}")
    logger.info(f"Guacamole: {GUACD_HOST}:{GUACD_PORT}")
    logger.info(f"VNC: {VNC_HOST}:{VNC_PORT}")
    logger.info(f"Session Timeout: {SESSION_TIMEOUT} seconds")
    logger.info(f"Frame Capture Interval: {FRAME_CAPTURE_INTERVAL} seconds")
    
    # Start cleanup thread
    cleanup_thread = threading.Thread(target=cleanup_expired_sessions, daemon=True)
    cleanup_thread.start()
    logger.info("Session cleanup thread started")
    
    # Debug mode disabled for security - use environment variable to enable if needed
    debug_mode = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
    app.run(host='0.0.0.0', port=5000, debug=debug_mode)
