"""
Jiomosa Renderer Service
A service that coordinates Selenium browser sessions with Guacamole for remote rendering
"""
import os
import logging
import time
from flask import Flask, jsonify, request
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Environment configuration
SELENIUM_HOST = os.getenv('SELENIUM_HOST', 'chrome')
SELENIUM_PORT = os.getenv('SELENIUM_PORT', '4444')
GUACD_HOST = os.getenv('GUACD_HOST', 'guacd')
GUACD_PORT = os.getenv('GUACD_PORT', '4822')
VNC_HOST = os.getenv('VNC_HOST', 'chrome')
VNC_PORT = os.getenv('VNC_PORT', '5900')

# Store active sessions
active_sessions = {}


class BrowserSession:
    """Manages a browser session for rendering websites"""
    
    def __init__(self, session_id):
        self.session_id = session_id
        self.driver = None
        self.created_at = time.time()
        self.last_activity = time.time()
        
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
    
    def close(self):
        """Close the browser session"""
        try:
            if self.driver:
                self.driver.quit()
                logger.info(f"Browser session {self.session_id} closed")
        except Exception as e:
            logger.error(f"Error closing browser session: {e}")


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
            'session_close': '/api/session/<session_id>/close',
            'sessions_list': '/api/sessions',
            'vnc_info': '/api/vnc/info'
        },
        'vnc_connection': {
            'host': VNC_HOST,
            'port': VNC_PORT,
            'web_interface': f'http://chrome:7900'
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
    
    # Debug mode disabled for security - use environment variable to enable if needed
    debug_mode = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
    app.run(host='0.0.0.0', port=5000, debug=debug_mode)
