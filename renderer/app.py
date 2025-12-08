"""
Jio Cloud Apps Renderer Service
A service that coordinates Selenium browser sessions with WebSocket streaming for remote rendering
"""
import os
import logging
import time
import base64
import threading
import hashlib
import shutil
import glob
import re
from flask import Flask, jsonify, request, send_file, render_template_string, Response
from flask_cors import CORS
from flask_socketio import SocketIO, emit, disconnect
from websocket_handler import WebSocketHandler
from audio_handler import create_audio_streamer
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from io import BytesIO
from PIL import Image
import subprocess
import wave
import struct

# Try to import yt-dlp (may not be available in all environments)
try:
    import yt_dlp
    YT_DLP_AVAILABLE = True
except ImportError:
    YT_DLP_AVAILABLE = False
    logging.warning("yt-dlp not available - YouTube streaming will be disabled")

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

# Initialize WebSocket support
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Initialize WebSocket handler (will be set when app starts)
ws_handler = None

# Initialize Audio streamer (will be set when app starts)
audio_streamer = None

# Environment configuration
SELENIUM_HOST = os.getenv('SELENIUM_HOST', 'chrome')
SELENIUM_PORT = os.getenv('SELENIUM_PORT', '4444')
SESSION_TIMEOUT = int(os.getenv('SESSION_TIMEOUT', '300'))  # 5 minutes default
FRAME_CAPTURE_INTERVAL = float(os.getenv('FRAME_CAPTURE_INTERVAL', '1.0'))  # 1 second default

# KaiOS client directory - check multiple locations
KAIOS_CLIENT_DIR = None
for path in ['/kaios_client', '/app/kaios_client', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'kaios_client')]:
    if os.path.exists(path):
        KAIOS_CLIENT_DIR = path
        break
if not KAIOS_CLIENT_DIR:
    KAIOS_CLIENT_DIR = '/kaios_client'  # Default fallback

# YouTube video cache directory
YOUTUBE_CACHE_DIR = os.getenv('YOUTUBE_CACHE_DIR', '/tmp/youtube_cache')
YOUTUBE_CACHE_MAX_SIZE_MB = int(os.getenv('YOUTUBE_CACHE_MAX_SIZE_MB', '500'))  # 500MB max cache
YOUTUBE_CACHE_MAX_AGE_HOURS = int(os.getenv('YOUTUBE_CACHE_MAX_AGE_HOURS', '24'))  # Keep videos for 24 hours

# Ensure cache directory exists
os.makedirs(YOUTUBE_CACHE_DIR, exist_ok=True)

# Store active sessions
active_sessions = {}

# YouTube download status tracking
youtube_downloads = {}
youtube_downloads_lock = threading.Lock()

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
            
            # Use mobile viewport size (320x480) - standard mobile size Chrome can render
            # Content will be scaled down to 240x320 for KaiOS display
            chrome_options.add_argument('--window-size=320,480')
            chrome_options.add_argument('--window-position=0,0')
            
            # Force light mode for better readability on small screens
            chrome_options.add_argument('--force-color-profile=srgb')
            chrome_options.add_argument('--disable-features=WebContentsForceDark')
            
            # Force videos to play inline, not download or open externally
            chrome_options.add_argument('--autoplay-policy=no-user-gesture-required')
            chrome_options.add_argument('--disable-features=PreloadMediaEngagementData,MediaEngagementBypassAutoplayPolicies')
            
            # Kiosk mode: hide browser UI elements for clean web content view
            chrome_options.add_argument('--kiosk')
            chrome_options.add_argument('--start-maximized')
            chrome_options.add_argument('--disable-infobars')
            chrome_options.add_argument('--disable-extensions')
            
            # KaiOS-like mobile user agent to load mobile versions of websites
            mobile_user_agent = 'Mozilla/5.0 (Mobile; rv:48.0) Gecko/48.0 Firefox/48.0 KAIOS/2.5'
            chrome_options.add_argument(f'--user-agent={mobile_user_agent}')
            
            # Mobile emulation for proper responsive rendering
            # Using 320x480 which is a standard mobile size Chrome properly supports
            mobile_emulation = {
                'deviceMetrics': {'width': 320, 'height': 480, 'pixelRatio': 1.0},
                'userAgent': mobile_user_agent
            }
            chrome_options.add_experimental_option('mobileEmulation', mobile_emulation)
            
            # Set preference to prefer light color scheme
            prefs = {
                'profile.default_content_setting_values.color_scheme': 1,  # 1 = light
            }
            chrome_options.add_experimental_option('prefs', prefs)
            
            # Hide browser chrome (address bar, tabs, etc.)
            chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # Connect to remote Selenium Grid
            selenium_url = f'http://{SELENIUM_HOST}:{SELENIUM_PORT}/wd/hub'
            logger.info(f"Connecting to Selenium at {selenium_url}")
            
            self.driver = webdriver.Remote(
                command_executor=selenium_url,
                options=chrome_options
            )
            
            # Chrome has a minimum window size (~500px), so we set a reasonable size
            # and rely on mobile emulation to render content at mobile dimensions
            self.driver.set_window_size(320, 480)
            
            logger.info(f"Browser session {self.session_id} initialized with mobile emulation")
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
            
            # For YouTube, use the light theme parameter
            if 'youtube.com' in url and '?' in url:
                url = url + '&theme=light'
            elif 'youtube.com' in url:
                url = url + '?theme=light'
            
            # For WhatsApp Web, force desktop mode
            if 'web.whatsapp.com' in url:
                # Temporarily change user agent to desktop for WhatsApp Web
                desktop_user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                self.driver.execute_cdp_cmd('Network.setUserAgentOverride', {'userAgent': desktop_user_agent})
                logger.info("Set desktop user agent for WhatsApp Web")
            
            self.driver.get(url)
            
            if wait_for_load:
                # Wait for page to be in ready state
                WebDriverWait(self.driver, timeout).until(
                    lambda d: d.execute_script('return document.readyState') == 'complete'
                )
            
            # Force light mode by overriding CSS and injecting white background
            try:
                # For Wikipedia, Google News, and WhatsApp Web, use minimal CSS to avoid layout corruption
                if 'wikipedia.org' in url or 'news.google.com' in url or 'web.whatsapp.com' in url:
                    self.driver.execute_script("""
                        // Minimal CSS for Wikipedia and Google News - just force light mode
                        document.documentElement.style.colorScheme = 'light';
                        document.documentElement.style.backgroundColor = '#ffffff';
                        document.body.style.backgroundColor = '#ffffff';
                        
                        var style = document.createElement('style');
                        style.id = 'jiomosa-light-mode';
                        style.textContent = `
                            /* Minimal overrides for Wikipedia, Google News, and WhatsApp Web */
                            body { background-color: #ffffff !important; }
                            html { background-color: #ffffff !important; }
                        `;
                        document.head.appendChild(style);
                        
                        // Disable zoom on the page - prevent browser zoom shortcuts
                        document.body.style.zoom = '1';
                        document.body.style.transform = 'none';
                        document.documentElement.style.fontSize = '16px';
                        
                        // Prevent zoom via meta tag
                        var metaViewport = document.querySelector('meta[name="viewport"]');
                        if (metaViewport) {
                            metaViewport.setAttribute('content', 'width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no');
                        } else {
                            var meta = document.createElement('meta');
                            meta.name = 'viewport';
                            meta.content = 'width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no';
                            document.head.appendChild(meta);
                        }
                        
                        // Block keyboard shortcuts that trigger zoom (Ctrl+, Ctrl-, numbers, etc.)
                        document.addEventListener('keydown', function(e) {
                            // Block Ctrl+Plus, Ctrl+Minus, Ctrl+0 (zoom shortcuts)
                            if (e.ctrlKey && (e.key === '+' || e.key === '-' || e.key === '0' || e.key === '=' || e.keyCode === 187 || e.keyCode === 189 || e.keyCode === 48)) {
                                e.preventDefault();
                                e.stopPropagation();
                                return false;
                            }
                            // Block key 3 (which Google News uses for zoom-in) - prevent default to let our scroll handler work
                            if (e.key === '3' || e.keyCode === 51) {
                                e.preventDefault();
                                e.stopPropagation();
                                return false;
                            }
                        }, true);
                        
                        // Prevent wheel zoom
                        document.addEventListener('wheel', function(e) {
                            if (e.ctrlKey) {
                                e.preventDefault();
                                return false;
                            }
                        }, { passive: false });
                    """)
                else:
                    self.driver.execute_script("""
                        // Force light color scheme
                        document.documentElement.style.colorScheme = 'light';
                        document.documentElement.style.backgroundColor = '#ffffff';
                        document.body.style.backgroundColor = '#ffffff';
                        
                        // Add comprehensive CSS overrides for dark-themed sites
                        var style = document.createElement('style');
                        style.id = 'jiomosa-light-mode';
                        style.textContent = `
                            /* === DISABLE FOCUS OUTLINES AND SELECTION === */
                            /* Remove ugly blue focus outlines and selection highlights */
                            *:focus, *:focus-visible, *:focus-within {
                                outline: none !important;
                                box-shadow: none !important;
                                -webkit-tap-highlight-color: transparent !important;
                            }
                            * {
                                -webkit-tap-highlight-color: transparent !important;
                                -webkit-touch-callout: none !important;
                                -webkit-user-select: none !important;
                                -moz-user-select: none !important;
                                -ms-user-select: none !important;
                                user-select: none !important;
                            }
                            /* Allow text selection in inputs */
                            input, textarea, [contenteditable="true"] {
                                -webkit-user-select: text !important;
                                -moz-user-select: text !important;
                                -ms-user-select: text !important;
                                user-select: text !important;
                            }
                            /* Remove selection highlight color */
                            ::selection {
                                background: transparent !important;
                            }
                            ::-moz-selection {
                                background: transparent !important;
                            }
                            /* Instagram specific - remove blue tap highlight */
                            a, button, [role="button"], [tabindex] {
                                -webkit-tap-highlight-color: transparent !important;
                                outline: none !important;
                            }
                            /* Instagram - hide focus overlays and blue screens */
                            [style*="background-color: rgb(0, 149, 246)"],
                            [style*="background: rgb(0, 149, 246)"],
                            [style*="rgba(0, 149, 246"],
                            div[style*="position: fixed"][style*="inset: 0"],
                            div[style*="position: fixed"][style*="top: 0"][style*="left: 0"][style*="right: 0"][style*="bottom: 0"] {
                                display: none !important;
                                visibility: hidden !important;
                                opacity: 0 !important;
                                pointer-events: none !important;
                            }
                            /* Hide any full-screen overlays */
                            body > div[style*="position: fixed"]:not([role="dialog"]):not([aria-modal="true"]) {
                                background-color: transparent !important;
                            }
                            /* Instagram specific blue color override */
                            [style*="#0095f6"], [style*="rgb(0, 149, 246)"] {
                                background-color: transparent !important;
                            }
                            
                            :root { 
                                color-scheme: light !important;
                                /* YouTube variables */
                                --yt-spec-base-background: #fff !important;
                                --yt-spec-brand-background-primary: #fff !important;
                                --yt-spec-brand-background-solid: #fff !important;
                                --yt-spec-general-background-a: #fff !important;
                                --yt-spec-general-background-b: #f9f9f9 !important;
                                --yt-spec-general-background-c: #f1f1f1 !important;
                            --yt-spec-text-primary: #030303 !important;
                            --yt-spec-text-secondary: #606060 !important;
                            /* Twitter/X variables */
                            --background-color-primary: #fff !important;
                            --background-color-secondary: #f7f9f9 !important;
                            --text-color-primary: #0f1419 !important;
                            --text-color-secondary: #536471 !important;
                            /* Reddit variables */
                            --background: #fff !important;
                            --background-color: #fff !important;
                            --newCommunityTheme-body: #fff !important;
                            --newCommunityTheme-bodyText: #1c1c1c !important;
                            --color-neutral-background: #fff !important;
                            --color-neutral-content: #1c1c1c !important;
                        }
                        html, body {
                            background-color: #ffffff !important;
                            color: #000000 !important;
                        }
                        
                        /* === YouTube === */
                        ytd-app, #content, #page-manager {
                            background-color: #ffffff !important;
                        }
                        
                        /* === Twitter/X === */
                        [data-testid="primaryColumn"], 
                        [data-testid="sidebarColumn"],
                        main, header, nav,
                        .css-1dbjc4n, .r-14lw9ot, .r-kemksi {
                            background-color: #ffffff !important;
                        }
                        /* Twitter login/signup popups */
                        [role="dialog"], [role="modal"],
                        [aria-modal="true"] {
                            background-color: #ffffff !important;
                        }
                        /* Twitter dark text fix */
                        [dir="ltr"] span, [dir="rtl"] span,
                        article span, a span {
                            color: inherit !important;
                        }
                        
                        /* === Facebook === */
                        ._li, ._5s61, ._2yav,
                        [role="main"], [role="banner"], [role="navigation"],
                        .__fb-dark-mode, .x1n2onr6, .x9f619,
                        [style*="background-color: rgb(36, 37, 38)"],
                        [style*="background-color: rgb(24, 25, 26)"] {
                            background-color: #ffffff !important;
                            color: #1c1e21 !important;
                        }
                        /* Facebook mobile */
                        #viewport, #page, .mobile-viewport,
                        ._52z5, ._5s61, ._li {
                            background-color: #ffffff !important;
                        }
                        /* Facebook login page */
                        ._8esj, ._9ay7, [data-visualcompletion="ignore"] {
                            background-color: #ffffff !important;
                        }
                        
                        /* === Reddit === */
                        .SubredditVars-r-popular, .SubredditVars-r-all,
                        shreddit-app, [data-redditstyle="true"],
                        .ListingLayout-backgroundContainer,
                        .Post, .Comment, .thing,
                        #AppRouter-main-content,
                        [class*="sidebar"], [class*="Sidebar"] {
                            background-color: #ffffff !important;
                            color: #1c1c1c !important;
                        }
                        /* Reddit new UI */
                        body.v2, body[style*="background"],
                        main, shreddit-app {
                            background-color: #ffffff !important;
                        }
                        /* Reddit post cards */
                        article, [data-testid="post-container"],
                        faceplate-partial, faceplate-tracker {
                            background-color: #ffffff !important;
                        }
                        
                        /* === Wikipedia === */
                        .mw-body, #content, #mw-content-text,
                        .vector-body, .mw-page-container {
                            background-color: #ffffff !important;
                            color: #202122 !important;
                        }
                        
                        /* === Google News === */
                        c-wiz, [jscontroller], [jsname],
                        .SbN5l, .bGIfxd, .Oc0wGc {
                            background-color: #ffffff !important;
                        }
                        
                        /* === Weather.com === */
                        [class*="DaybreakLargeScreen"], [class*="CurrentConditions"],
                        main, header, [data-testid] {
                            background-color: #ffffff !important;
                        }
                        
                        /* === DuckDuckGo === */
                        /* Hide blue autocomplete overlay */
                        .search--adv, .search--hero__above,
                        .is-active .search__autocomplete,
                        .search__autocomplete--open,
                        .modal, .modal--open, .modal__overlay,
                        .search--focus .search__input--adv__wrap::before,
                        .search--focus::before,
                        [class*="searchbox_overlay"],
                        [class*="searchbox_modal"],
                        [class*="Modal_overlay"],
                        .acp-wrap, .acp {
                            background-color: #ffffff !important;
                            background: #ffffff !important;
                        }
                        /* Make autocomplete dropdown readable */
                        .acp, .acp-wrap, .search__autocomplete, 
                        [class*="searchbox_dropdown"],
                        [class*="suggestion"] {
                            background-color: #ffffff !important;
                            border: 1px solid #ccc !important;
                        }
                        /* Remove blue overlay completely */
                        .search--focus .search-wrap::before,
                        .search--focus::before,
                        .search--adv .search-wrap::before {
                            display: none !important;
                            opacity: 0 !important;
                        }
                        
                        /* === General Dark Mode Override === */
                        /* Force all dark backgrounds to light */
                        [dark], [dark-theme], .dark-theme, .dark,
                        [data-theme="dark"], [data-color-mode="dark"],
                        [data-darkmode="true"], .nightmode, .night-mode,
                        [class*="dark-mode"], [class*="darkmode"] {
                            background-color: #ffffff !important;
                            color: #000000 !important;
                        }
                        
                        /* Fix common overlay/popup backgrounds */
                        [role="dialog"], [role="modal"], [aria-modal="true"],
                        .modal, .popup, .overlay, .dropdown,
                        [class*="Modal"], [class*="Popup"], [class*="Overlay"],
                        [class*="Dropdown"], [class*="Menu"] {
                            background-color: #ffffff !important;
                        }
                        
                        /* Ensure text is readable */
                        p, span, div, h1, h2, h3, h4, h5, h6, a, li, td, th {
                            color: inherit !important;
                        }
                    `;
                    if (!document.getElementById('jiomosa-light-mode')) {
                        document.head.appendChild(style);
                    }
                    
                    // Remove dark mode classes from various sites
                    document.documentElement.removeAttribute('dark');
                    document.documentElement.removeAttribute('data-theme');
                    document.documentElement.removeAttribute('data-color-mode');
                    document.body.classList.remove('dark-theme', 'dark', 'nightmode', 'night-mode');
                    document.body.removeAttribute('data-darkmode');
                    
                    // Disable zoom on the page - prevent browser zoom shortcuts
                    document.body.style.zoom = '1';
                    document.body.style.transform = 'none';
                    document.documentElement.style.fontSize = '16px';
                    
                    // Prevent zoom via meta tag
                    var metaViewport = document.querySelector('meta[name="viewport"]');
                    if (metaViewport) {
                        metaViewport.setAttribute('content', 'width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no');
                    } else {
                        var meta = document.createElement('meta');
                        meta.name = 'viewport';
                        meta.content = 'width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no';
                        document.head.appendChild(meta);
                    }
                    
                    // Block keyboard shortcuts that trigger zoom (Ctrl+, Ctrl-, numbers, etc.)
                    document.addEventListener('keydown', function(e) {
                        // Block Ctrl+Plus, Ctrl+Minus, Ctrl+0 (zoom shortcuts)
                        if (e.ctrlKey && (e.key === '+' || e.key === '-' || e.key === '0' || e.key === '=' || e.keyCode === 187 || e.keyCode === 189 || e.keyCode === 48)) {
                            e.preventDefault();
                            e.stopPropagation();
                            return false;
                        }
                        // Block key 3 (which Google News uses for zoom-in) - prevent default to let our scroll handler work
                        if (e.key === '3' || e.keyCode === 51) {
                            e.preventDefault();
                            e.stopPropagation();
                            return false;
                        }
                        // Block number keys 1-9 if they might trigger zoom or shortcuts
                        // Note: We don't block all numbers, just prevent default if Ctrl is held
                    }, true);
                    
                    // Prevent wheel zoom
                    document.addEventListener('wheel', function(e) {
                        if (e.ctrlKey) {
                            e.preventDefault();
                        }
                    }, { passive: false });
                    
                    // YouTube-specific: Force inline video playback, prevent downloads
                    if (window.location.hostname.indexOf('youtube') !== -1) {
                        // Override any download prompts
                        window.addEventListener('beforeunload', function(e) {
                            // Don't show download dialogs
                        });
                        
                        // Force videos to play inline
                        var videos = document.querySelectorAll('video');
                        videos.forEach(function(v) {
                            v.setAttribute('playsinline', '');
                            v.setAttribute('webkit-playsinline', '');
                            v.removeAttribute('download');
                        });
                        
                        // Observe for new videos added to DOM
                        var observer = new MutationObserver(function(mutations) {
                            mutations.forEach(function(mutation) {
                                mutation.addedNodes.forEach(function(node) {
                                    if (node.tagName === 'VIDEO') {
                                        node.setAttribute('playsinline', '');
                                        node.setAttribute('webkit-playsinline', '');
                                        node.removeAttribute('download');
                                    }
                                    if (node.querySelectorAll) {
                                        node.querySelectorAll('video').forEach(function(v) {
                                            v.setAttribute('playsinline', '');
                                            v.setAttribute('webkit-playsinline', '');
                                            v.removeAttribute('download');
                                        });
                                    }
                                });
                            });
                        });
                        observer.observe(document.body, { childList: true, subtree: true });
                        
                        // Block download manager prompts
                        if (window.navigator && window.navigator.registerProtocolHandler) {
                            // Already handled
                        }
                    }
                """)
            except Exception as e:
                logger.warning(f"Could not inject light mode CSS: {e}")
            
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
    
    def send_click(self, x, y):
        """Send click event at specified coordinates - improved for navigation"""
        try:
            if not self.driver:
                return False, "Driver not initialized"
            
            # Get current viewport dimensions for debugging
            viewport_size = self.driver.execute_script("return {width: window.innerWidth, height: window.innerHeight};")
            logger.info(f"Click at ({x}, {y}), viewport: {viewport_size}")
            
            # Use JavaScript-based click for better reliability and navigation support
            # Enhanced to handle video players, checkboxes, radio buttons, and label elements
            script = f"""
                var x = {x}, y = {y};
                var element = document.elementFromPoint(x, y);
                if (!element) {{
                    return {{success: false, error: 'No element found at ' + x + ',' + y}};
                }}
                
                console.log('Initial element at (' + x + ', ' + y + '):', element.tagName, element.className, element.type || '');
                
                // Function to find clickable ancestor
                function findClickable(el, maxDepth) {{
                    for (var i = 0; i < maxDepth && el; i++) {{
                        if (el.tagName === 'A' || el.tagName === 'BUTTON' || 
                            (el.tagName === 'INPUT' && (el.type === 'submit' || el.type === 'button' || el.type === 'checkbox' || el.type === 'radio')) ||
                            el.getAttribute('role') === 'button' ||
                            el.getAttribute('role') === 'checkbox' ||
                            el.getAttribute('role') === 'switch' ||
                            el.onclick || el.hasAttribute('onclick') ||
                            (el.className && typeof el.className === 'string' && 
                             (el.className.indexOf('btn') !== -1 || el.className.indexOf('button') !== -1 ||
                              el.className.indexOf('play') !== -1 || el.className.indexOf('ytp-') !== -1 ||
                              el.className.indexOf('checkbox') !== -1 || el.className.indexOf('toggle') !== -1 ||
                              el.className.indexOf('switch') !== -1))) {{
                            return el;
                        }}
                        el = el.parentElement;
                    }}
                    return null;
                }}
                
                // For SVG elements, path elements, or elements with pointer-events, find clickable parent
                if (element.tagName === 'svg' || element.tagName === 'SVG' || 
                    element.tagName === 'path' || element.tagName === 'PATH' ||
                    element.tagName === 'use' || element.tagName === 'USE' ||
                    element.tagName === 'g' || element.tagName === 'G' ||
                    element.tagName === 'circle' || element.tagName === 'rect' ||
                    element.tagName === 'line' || element.tagName === 'polyline' ||
                    element.tagName === 'polygon') {{
                    var clickable = findClickable(element, 10);
                    if (clickable) element = clickable;
                }}
                
                // Handle custom checkbox/toggle elements (Reddit, etc.)
                // Look for role="checkbox", role="switch", or checkbox-like class names
                var isCustomCheckbox = element.getAttribute('role') === 'checkbox' || 
                    element.getAttribute('role') === 'switch' ||
                    (element.className && typeof element.className === 'string' && 
                     (element.className.indexOf('checkbox') !== -1 || 
                      element.className.indexOf('toggle') !== -1 ||
                      element.className.indexOf('switch') !== -1));
                
                // Also check parent for checkbox role (sometimes the visual is inside)
                if (!isCustomCheckbox && element.parentElement) {{
                    var parent = element.parentElement;
                    isCustomCheckbox = parent.getAttribute('role') === 'checkbox' || 
                        parent.getAttribute('role') === 'switch' ||
                        (parent.className && typeof parent.className === 'string' && 
                         (parent.className.indexOf('checkbox') !== -1 || 
                          parent.className.indexOf('toggle') !== -1));
                    if (isCustomCheckbox) element = parent;
                }}
                
                // Handle label elements - find and click the associated input
                if (element.tagName === 'LABEL') {{
                    var forId = element.getAttribute('for');
                    if (forId) {{
                        var input = document.getElementById(forId);
                        if (input) element = input;
                    }} else {{
                        // Label might contain the input
                        var input = element.querySelector('input');
                        if (input) element = input;
                    }}
                }}
                
                // For checkboxes and radio buttons, toggle directly
                if (element.tagName === 'INPUT' && (element.type === 'checkbox' || element.type === 'radio')) {{
                    element.checked = !element.checked;
                    // Dispatch change event
                    var changeEvent = new Event('change', {{bubbles: true}});
                    element.dispatchEvent(changeEvent);
                    var inputEvent = new Event('input', {{bubbles: true}});
                    element.dispatchEvent(inputEvent);
                    return {{
                        success: true,
                        element: element.tagName,
                        type: element.type,
                        checked: element.checked
                    }};
                }}
                
                // Handle custom checkbox with aria-checked attribute
                if (isCustomCheckbox) {{
                    var currentState = element.getAttribute('aria-checked');
                    if (currentState !== null) {{
                        var newState = currentState === 'true' ? 'false' : 'true';
                        element.setAttribute('aria-checked', newState);
                    }}
                    // Still dispatch click events for the component to handle
                }}
                
                // Scroll element into view if needed
                element.scrollIntoView({{behavior: 'instant', block: 'nearest'}});
                
                // DON'T focus the element - it causes blue overlay on some sites like Instagram
                // Only focus input fields
                if (element.tagName === 'INPUT' || element.tagName === 'TEXTAREA' || element.isContentEditable) {{
                    if (element.focus) {{
                        element.focus();
                    }}
                }}
                
                // Special handling for consent/cookie buttons - look for common consent button patterns
                var isConsentButton = false;
                var consentKeywords = ['accept', 'agree', 'consent', 'allow', 'ok', 'got it', 'continue', 'i accept', 'i agree'];
                var elementText = (element.textContent || '').toLowerCase().trim();
                var elementId = (element.id || '').toLowerCase();
                var elementClass = (typeof element.className === 'string' ? element.className : '').toLowerCase();
                
                for (var i = 0; i < consentKeywords.length; i++) {{
                    if (elementText.indexOf(consentKeywords[i]) !== -1 || 
                        elementId.indexOf(consentKeywords[i]) !== -1 ||
                        elementClass.indexOf(consentKeywords[i]) !== -1) {{
                        isConsentButton = true;
                        break;
                    }}
                }}
                
                // If it's a consent button, try multiple click methods
                if (isConsentButton) {{
                    console.log('Detected consent button, using enhanced click');
                    // Try pointer events
                    var pointerDown = new PointerEvent('pointerdown', {{
                        view: window, bubbles: true, cancelable: true, clientX: x, clientY: y, button: 0, isPrimary: true
                    }});
                    var pointerUp = new PointerEvent('pointerup', {{
                        view: window, bubbles: true, cancelable: true, clientX: x, clientY: y, button: 0, isPrimary: true
                    }});
                    element.dispatchEvent(pointerDown);
                    element.dispatchEvent(pointerUp);
                }}
                
                // Dispatch complete mouse event sequence for maximum compatibility
                var mousedown = new MouseEvent('mousedown', {{
                    view: window,
                    bubbles: true,
                    cancelable: true,
                    clientX: x,
                    clientY: y,
                    button: 0
                }});
                var mouseup = new MouseEvent('mouseup', {{
                    view: window,
                    bubbles: true,
                    cancelable: true,
                    clientX: x,
                    clientY: y,
                    button: 0
                }});
                var click = new MouseEvent('click', {{
                    view: window,
                    bubbles: true,
                    cancelable: true,
                    clientX: x,
                    clientY: y,
                    button: 0
                }});
                
                element.dispatchEvent(mousedown);
                element.dispatchEvent(mouseup);
                element.dispatchEvent(click);
                
                // Also call native click() for links and buttons
                if (element.click) element.click();
                
                // For consent buttons, also try clicking any visible accept buttons in the DOM
                if (isConsentButton || element.tagName === 'DIV' || element.tagName === 'SPAN') {{
                    // Try to find and click common consent buttons
                    var selectors = [
                        '#onetrust-accept-btn-handler',
                        '.onetrust-accept-btn-handler',
                        '[id*="accept"]',
                        '[class*="accept"]',
                        'button[title*="Accept"]',
                        'button[aria-label*="Accept"]',
                        '.consent-accept',
                        '.cookie-accept',
                        '#accept-cookies',
                        '.accept-button',
                        '[data-testid*="accept"]'
                    ];
                    for (var s = 0; s < selectors.length; s++) {{
                        try {{
                            var btn = document.querySelector(selectors[s]);
                            if (btn && btn.offsetParent !== null) {{
                                btn.click();
                                console.log('Clicked consent button via selector: ' + selectors[s]);
                                break;
                            }}
                        }} catch(e) {{}}
                    }}
                }}
                
                return {{
                    success: true,
                    element: element.tagName,
                    id: element.id || '',
                    class: element.className || '',
                    href: element.href || '',
                    text: element.textContent ? element.textContent.substring(0, 50) : ''
                }};
            """
            
            result = self.driver.execute_script(script)
            self.last_activity = time.time()
            
            if isinstance(result, dict) and result.get('success'):
                logger.info(f"Click sent at ({x}, {y}) - element: {result.get('element')} {result.get('class', '')} {result.get('text', '')[:30]}")
                # Give page time to process the click and start navigation if needed
                time.sleep(0.1)
                # Return element info for client to know what was clicked
                return True, result
            else:
                logger.warning(f"Click at ({x}, {y}) - {result}")
                return True, {'success': True, 'element': 'UNKNOWN'}
            
        except Exception as e:
            logger.error(f"Error sending click: {e}")
            return False, {'error': str(e)}
    
    def send_scroll(self, delta_x, delta_y):
        """Send scroll event - handles both window and element scrolling"""
        try:
            if not self.driver:
                return False, "Driver not initialized"
            
            # Enhanced scroll script that works with custom scroll containers (Instagram, Facebook, etc.)
            script = f"""
                var deltaX = {delta_x};
                var deltaY = {delta_y};
                
                // Function to find the scrollable element
                function findScrollable() {{
                    // Common scroll container selectors for various sites
                    var selectors = [
                        'main[role="main"]',           // Instagram, Twitter
                        '[role="feed"]',               // Facebook feed
                        'article',                     // General articles
                        '.scroll-container',
                        '[data-pagelet="FeedUnit_0"]', // Facebook
                        'section main',                // Instagram
                        '[style*="overflow"]',         // Elements with overflow set
                        'body',
                        'html'
                    ];
                    
                    // First check if there's an element under the center of the viewport that's scrollable
                    var centerX = window.innerWidth / 2;
                    var centerY = window.innerHeight / 2;
                    var el = document.elementFromPoint(centerX, centerY);
                    
                    // Walk up the DOM to find a scrollable parent
                    while (el && el !== document.body && el !== document.documentElement) {{
                        var style = window.getComputedStyle(el);
                        var overflowY = style.overflowY;
                        var overflowX = style.overflowX;
                        
                        if ((overflowY === 'auto' || overflowY === 'scroll' || overflowY === 'overlay') && el.scrollHeight > el.clientHeight) {{
                            return el;
                        }}
                        if ((overflowX === 'auto' || overflowX === 'scroll' || overflowX === 'overlay') && el.scrollWidth > el.clientWidth) {{
                            return el;
                        }}
                        el = el.parentElement;
                    }}
                    
                    // Try specific selectors
                    for (var i = 0; i < selectors.length; i++) {{
                        var elements = document.querySelectorAll(selectors[i]);
                        for (var j = 0; j < elements.length; j++) {{
                            var elem = elements[j];
                            if (elem.scrollHeight > elem.clientHeight || elem.scrollWidth > elem.clientWidth) {{
                                return elem;
                            }}
                        }}
                    }}
                    
                    return null;
                }}
                
                var scrollTarget = findScrollable();
                var scrolled = false;
                
                if (scrollTarget && scrollTarget !== document.body && scrollTarget !== document.documentElement) {{
                    // Scroll the specific container
                    var beforeY = scrollTarget.scrollTop;
                    var beforeX = scrollTarget.scrollLeft;
                    scrollTarget.scrollBy(deltaX, deltaY);
                    scrolled = (scrollTarget.scrollTop !== beforeY || scrollTarget.scrollLeft !== beforeX);
                    console.log('Scrolled element:', scrollTarget.tagName, scrollTarget.className, 'by', deltaY);
                }}
                
                // Also try window scroll as fallback or in addition
                if (!scrolled) {{
                    var beforeWinY = window.scrollY || window.pageYOffset;
                    var beforeWinX = window.scrollX || window.pageXOffset;
                    window.scrollBy(deltaX, deltaY);
                    scrolled = (window.scrollY !== beforeWinY || window.scrollX !== beforeWinX);
                    console.log('Scrolled window by', deltaY);
                }}
                
                // Also dispatch wheel event for sites that listen for it
                var wheelEvent = new WheelEvent('wheel', {{
                    deltaX: deltaX,
                    deltaY: deltaY,
                    deltaMode: 0,
                    bubbles: true,
                    cancelable: true
                }});
                (scrollTarget || document.body).dispatchEvent(wheelEvent);
                
                return scrolled;
            """
            result = self.driver.execute_script(script)
            self.last_activity = time.time()
            logger.info(f"Scroll sent: dx={delta_x}, dy={delta_y}, scrolled={result}")
            return True, f"Scrolled by ({delta_x}, {delta_y})"
            
        except Exception as e:
            logger.error(f"Error sending scroll: {e}")
            return False, f"Error: {str(e)}"
    
    def send_text(self, text):
        """Send text input to focused element - improved with element detection"""
        try:
            if not self.driver:
                return False, "Driver not initialized"
            
            # First, try to find an active/focused input element
            # If none is focused, try to find any visible input field and focus it
            script = """
                var activeElement = document.activeElement;
                var isInputFocused = activeElement && 
                    (activeElement.tagName === 'INPUT' || 
                     activeElement.tagName === 'TEXTAREA' || 
                     activeElement.isContentEditable);
                
                if (!isInputFocused) {
                    // Try to find and focus a visible input field
                    var inputs = document.querySelectorAll('input[type="text"], input[type="search"], input:not([type]), textarea, [contenteditable="true"]');
                    for (var i = 0; i < inputs.length; i++) {
                        var input = inputs[i];
                        if (input.offsetParent !== null) { // Check if visible
                            input.focus();
                            input.scrollIntoView({behavior: 'instant', block: 'center'});
                            return {focused: true, element: input.tagName, id: input.id || '', type: input.type || ''};
                        }
                    }
                    return {focused: false, error: 'No input element found'};
                }
                return {focused: true, element: activeElement.tagName, id: activeElement.id || '', type: activeElement.type || ''};
            """
            
            focus_result = self.driver.execute_script(script)
            logger.info(f"Text input focus check: {focus_result}")
            
            # Now send the text using ActionChains for natural typing
            from selenium.webdriver.common.action_chains import ActionChains
            actions = ActionChains(self.driver)
            actions.send_keys(text)
            actions.perform()
            
            self.last_activity = time.time()
            logger.info(f"Text sent: {text[:50]}...")
            return True, "Text sent successfully"
            
        except Exception as e:
            logger.error(f"Error sending text: {e}")
            return False, f"Error: {str(e)}"
    
    def send_key(self, key):
        """Send a special key (Enter, Backspace, Tab, etc.) to the browser"""
        try:
            if not self.driver:
                return False, "Driver not initialized"
            
            from selenium.webdriver.common.keys import Keys
            from selenium.webdriver.common.action_chains import ActionChains
            
            # Map key names to Selenium Keys
            key_map = {
                'Enter': Keys.ENTER,
                'Backspace': Keys.BACKSPACE,
                'Tab': Keys.TAB,
                'Escape': Keys.ESCAPE,
                'Delete': Keys.DELETE,
                'ArrowUp': Keys.ARROW_UP,
                'ArrowDown': Keys.ARROW_DOWN,
                'ArrowLeft': Keys.ARROW_LEFT,
                'ArrowRight': Keys.ARROW_RIGHT,
                'Home': Keys.HOME,
                'End': Keys.END,
                'PageUp': Keys.PAGE_UP,
                'PageDown': Keys.PAGE_DOWN,
                'Space': Keys.SPACE,
            }
            
            selenium_key = key_map.get(key)
            if selenium_key:
                actions = ActionChains(self.driver)
                actions.send_keys(selenium_key)
                actions.perform()
                self.last_activity = time.time()
                logger.info(f"Key sent: {key}")
                return True, f"Key {key} sent successfully"
            else:
                return False, f"Unknown key: {key}"
            
        except Exception as e:
            logger.error(f"Error sending key: {e}")
            return False, f"Error: {str(e)}"
    
    def keepalive(self):
        """Update last activity timestamp to keep session alive"""
        self.last_activity = time.time()
        logger.info(f"Keepalive received for session {self.session_id}")
        return True
    
    def is_expired(self, timeout=SESSION_TIMEOUT):
        """Check if session has expired based on inactivity"""
        return (time.time() - self.last_activity) > timeout
    
    def capture_frame(self, target_width=240, target_height=296):
        """Capture current browser frame as PNG screenshot - optimized for KaiOS display (240x296 + 24px status bar)"""
        try:
            if not self.driver:
                return None
            
            # Capture screenshot from browser
            screenshot = self.driver.get_screenshot_as_png()
            
            # Resize to fit KaiOS display (240x296)
            img = Image.open(BytesIO(screenshot))
            # Use high-quality resizing to maintain readability
            img = img.resize((target_width, target_height), Image.Resampling.LANCZOS)
            
            # Convert back to PNG bytes
            output = BytesIO()
            img.save(output, format='PNG', optimize=True)
            resized_screenshot = output.getvalue()
            
            with self.frame_lock:
                self.last_frame = resized_screenshot
                self.last_activity = time.time()
            
            return resized_screenshot
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


def stream_frames_to_clients():
    """Background task to capture and stream frames to subscribed clients"""
    logger.info("Frame streaming thread started")
    
    while True:
        try:
            if not ws_handler or not ws_handler.client_sessions:
                time.sleep(0.1)  # No clients, sleep briefly
                continue
            
            # Get all unique sessions that have subscribers
            subscribed_sessions = set(ws_handler.client_sessions.values())
            
            for session_id in subscribed_sessions:
                # Get session
                session = active_sessions.get(session_id)
                if not session or not session.driver:
                    continue
                
                # Capture frame
                try:
                    frame_data = session.capture_frame()
                    if not frame_data:
                        continue
                    
                    # Find all clients subscribed to this session
                    clients_for_session = [
                        client_id for client_id, sess_id in ws_handler.client_sessions.items()
                        if sess_id == session_id
                    ]
                    
                    # Send frame to each subscribed client
                    for client_id in clients_for_session:
                        try:
                            # Get client's FPS setting
                            client_fps = ws_handler.client_fps.get(client_id, 30)
                            
                            # Encode frame with client's quality settings
                            encoded_frame, frame_size = ws_handler.encode_frame_for_websocket(frame_data, client_id)
                            
                            if encoded_frame:
                                # Get bandwidth stats
                                bandwidth_monitor = ws_handler.bandwidth_monitors.get(client_id)
                                bandwidth_mbps = bandwidth_monitor.get_bandwidth_mbps() if bandwidth_monitor else 0
                                
                                # Emit frame to specific client
                                socketio.emit('frame', {
                                    'session_id': session_id,
                                    'image': f'data:image/jpeg;base64,{encoded_frame}',
                                    'timestamp': time.time(),
                                    'stats': {
                                        'size': frame_size,
                                        'quality': ws_handler.client_quality.get(client_id, 85),
                                        'fps': client_fps,
                                        'bandwidthMbps': round(bandwidth_mbps, 2),
                                        'adaptive': ws_handler.adaptive_mode.get(client_id, True)
                                    }
                                }, room=client_id)
                                
                        except Exception as e:
                            logger.error(f"Error sending frame to client {client_id}: {e}")
                
                except Exception as e:
                    logger.error(f"Error capturing frame for session {session_id}: {e}")
            
            # Sleep based on highest FPS requirement among all clients
            if ws_handler.client_fps:
                max_fps = max(ws_handler.client_fps.values())
                sleep_time = 1.0 / max_fps if max_fps > 0 else 0.033  # Default ~30 FPS
            else:
                sleep_time = 0.033  # ~30 FPS default
            
            # Minimum sleep to prevent excessive CPU usage
            time.sleep(max(sleep_time, 0.033))
            
        except Exception as e:
            logger.error(f"Error in frame streaming thread: {e}")
            time.sleep(0.1)


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'jiomosa-renderer',
        'selenium': f'{SELENIUM_HOST}:{SELENIUM_PORT}',
        'active_sessions': len(active_sessions),
        'websocket': 'enabled'
    }), 200


@app.route('/api/info', methods=['GET'])
def info():
    """Get service information"""
    return jsonify({
        'service': 'Jiomosa Renderer',
        'version': '2.0.0',
        'description': 'Cloud-based website rendering service with WebSocket streaming for low-end devices',
        'streaming': 'WebSocket (Socket.IO)',
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
            'websocket': 'ws://<host>:5000/socket.io/'
        },
        'alternative_access': {
            'description': 'Chrome noVNC web interface for direct browser access (optional)',
            'url': 'http://localhost:7900',
            'password': 'secret'
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
            'websocket_url': f'ws://localhost:5000/socket.io/',
            'alternative_access': {
                'description': 'Chrome noVNC for direct browser viewing',
                'url': 'http://localhost:7900',
                'password': 'secret'
            }
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
                'page_info': page_info
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
            'page_info': page_info
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting session info: {e}")
        return jsonify({'error': 'Failed to get session info'}), 500


@app.route('/api/session/<session_id>/input/click', methods=['POST'])
def send_click(session_id):
    """Send click input to browser session"""
    try:
        if session_id not in active_sessions:
            return jsonify({'error': 'Session not found'}), 404
        
        data = request.get_json() or {}
        x = data.get('x', 0)
        y = data.get('y', 0)
        
        session = active_sessions[session_id]
        
        # Client sends coordinates already mapped to viewport space (320x480)
        # Just use them directly
        mapped_x, mapped_y = int(x), int(y)
        logger.info(f"Click at ({mapped_x},{mapped_y}) in viewport space")
        
        success, result = session.send_click(mapped_x, mapped_y)
        
        # result is now a dict with element info
        element = result.get('element', 'UNKNOWN') if isinstance(result, dict) else 'UNKNOWN'
        
        return jsonify({
            'success': success,
            'message': f"Click sent at ({mapped_x}, {mapped_y})",
            'element': element,
            'coordinates': {'x': x, 'y': y},
            'mapped': {'x': mapped_x, 'y': mapped_y}
        }), 200 if success else 500
        
    except Exception as e:
        logger.error(f"Error sending click: {e}")
        return jsonify({'error': 'Failed to send click'}), 500


@app.route('/api/session/<session_id>/input/scroll', methods=['POST'])
def send_scroll(session_id):
    """Send scroll input to browser session"""
    try:
        if session_id not in active_sessions:
            return jsonify({'error': 'Session not found'}), 404
        
        data = request.get_json() or {}
        delta_x = data.get('deltaX', 0)
        delta_y = data.get('deltaY', 0)
        
        session = active_sessions[session_id]
        success, message = session.send_scroll(delta_x, delta_y)
        
        return jsonify({
            'success': success,
            'message': message,
            'scroll': {'deltaX': delta_x, 'deltaY': delta_y}
        }), 200 if success else 500
        
    except Exception as e:
        logger.error(f"Error sending scroll: {e}")
        return jsonify({'error': 'Failed to send scroll'}), 500


@app.route('/api/session/<session_id>/input/key', methods=['POST'])
def send_key(session_id):
    """Send a special key (Enter, Backspace, etc.) to browser session"""
    try:
        if session_id not in active_sessions:
            return jsonify({'error': 'Session not found'}), 404
        
        data = request.get_json() or {}
        key = data.get('key', '')
        
        session = active_sessions[session_id]
        success, message = session.send_key(key)
        
        return jsonify({
            'success': success,
            'message': message
        }), 200 if success else 500
        
    except Exception as e:
        logger.error(f"Error sending key: {e}")
        return jsonify({'error': 'Failed to send key'}), 500


@app.route('/api/session/<session_id>/input/text', methods=['POST'])
def send_text(session_id):
    """Send text input to browser session"""
    try:
        if session_id not in active_sessions:
            return jsonify({'error': 'Session not found'}), 404
        
        data = request.get_json() or {}
        text = data.get('text', '')
        
        session = active_sessions[session_id]
        success, message = session.send_text(text)
        
        return jsonify({
            'success': success,
            'message': message
        }), 200 if success else 500
        
    except Exception as e:
        logger.error(f"Error sending text: {e}")
        return jsonify({'error': 'Failed to send text'}), 500


@app.route('/api/session/<session_id>/execute', methods=['POST'])
def execute_script(session_id):
    """Execute JavaScript in the browser session"""
    try:
        if session_id not in active_sessions:
            return jsonify({'error': 'Session not found'}), 404
        
        data = request.get_json() or {}
        script = data.get('script', '')
        
        if not script:
            return jsonify({'error': 'Script is required'}), 400
        
        session = active_sessions[session_id]
        if not session.driver:
            return jsonify({'error': 'Driver not initialized'}), 500
        
        try:
            # Wrap script in a function to allow return statements
            wrapped_script = f"return (function() {{ {script} }})();"
            result = session.driver.execute_script(wrapped_script)
            session.last_activity = time.time()
            return jsonify({
                'success': True,
                'result': result  # Return as-is, Flask will JSON-serialize it
            }), 200
        except Exception as e:
            logger.error(f"Script execution error: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 200  # Return 200 even on script error to differentiate from API errors
        
    except Exception as e:
        logger.error(f"Error executing script: {e}")
        return jsonify({'error': 'Failed to execute script'}), 500


# ============================================================================
# YouTube Video Streaming Endpoints (for KaiOS)
# ============================================================================

def get_video_id_from_url(url_or_id):
    """Extract YouTube video ID from URL or return ID if already an ID"""
    if not url_or_id:
        return None
    
    # If it's already a video ID (11 characters, alphanumeric with - and _)
    if re.match(r'^[a-zA-Z0-9_-]{11}$', url_or_id):
        return url_or_id
    
    # Try to extract from various YouTube URL formats
    patterns = [
        r'(?:v=|/v/|youtu\.be/|/embed/|/shorts/)([a-zA-Z0-9_-]{11})',
        r'(?:watch\?.*v=)([a-zA-Z0-9_-]{11})',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url_or_id)
        if match:
            return match.group(1)
    
    return None


def get_cached_video_path(video_id):
    """Get the path to a cached video file"""
    return os.path.join(YOUTUBE_CACHE_DIR, f"{video_id}_kaios.mp4")


def cleanup_old_cache():
    """Remove old cached videos to free up space"""
    try:
        now = time.time()
        max_age_seconds = YOUTUBE_CACHE_MAX_AGE_HOURS * 3600
        total_size = 0
        files_with_time = []
        
        for filename in os.listdir(YOUTUBE_CACHE_DIR):
            filepath = os.path.join(YOUTUBE_CACHE_DIR, filename)
            if os.path.isfile(filepath):
                stat = os.stat(filepath)
                files_with_time.append((filepath, stat.st_mtime, stat.st_size))
                total_size += stat.st_size
        
        # Remove files older than max age
        for filepath, mtime, size in files_with_time:
            if now - mtime > max_age_seconds:
                logger.info(f"Removing old cached video: {filepath}")
                os.remove(filepath)
                total_size -= size
        
        # If still over size limit, remove oldest files
        max_size_bytes = YOUTUBE_CACHE_MAX_SIZE_MB * 1024 * 1024
        if total_size > max_size_bytes:
            files_with_time.sort(key=lambda x: x[1])  # Sort by mtime, oldest first
            for filepath, mtime, size in files_with_time:
                if os.path.exists(filepath):
                    logger.info(f"Removing cached video to free space: {filepath}")
                    os.remove(filepath)
                    total_size -= size
                    if total_size <= max_size_bytes * 0.8:  # Keep 20% buffer
                        break
                        
    except Exception as e:
        logger.error(f"Error cleaning up cache: {e}")


def download_and_transcode_video(video_id, output_path):
    """Download YouTube video and transcode to H.264 Baseline for KaiOS"""
    if not YT_DLP_AVAILABLE:
        return False, "yt-dlp not available"
    
    temp_path = output_path + '.temp'
    download_path = output_path + '.download'
    
    try:
        # yt-dlp options for downloading video with audio merged
        # Use format that includes both video and audio in a single file
        ydl_opts = {
            'format': 'best[ext=mp4][height<=480]/best[height<=480]/best',  # Prefer mp4 with video+audio
            'outtmpl': download_path,
            'quiet': False,  # Enable output for debugging
            'no_warnings': False,
            'extract_flat': False,
            'merge_output_format': 'mp4',  # Force merge to mp4 if separate streams
            'postprocessors': [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4',
            }],
        }
        
        # Download the video
        logger.info(f"Downloading YouTube video: {video_id}")
        url = f"https://www.youtube.com/watch?v={video_id}"
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = info.get('title', 'Unknown')
            duration = info.get('duration', 0)
            logger.info(f"Downloaded: {title} ({duration}s)")
        
        # Find the downloaded file (yt-dlp may add extension)
        actual_download = None
        for ext in ['', '.mp4', '.webm', '.mkv', '.m4a']:
            check_path = download_path + ext if ext else download_path
            if os.path.exists(check_path):
                actual_download = check_path
                break
        
        if not actual_download:
            # Try glob pattern
            matches = glob.glob(download_path + '*')
            if matches:
                actual_download = matches[0]
        
        if not actual_download or not os.path.exists(actual_download):
            return False, "Download failed - file not found"
        
        # Transcode to H.264 Baseline profile for KaiOS compatibility
        # Using ffmpeg with settings optimized for KaiOS Gecko 48
        logger.info(f"Transcoding to H.264 Baseline: {video_id}")
        
        ffmpeg_cmd = [
            'ffmpeg', '-y',
            '-i', actual_download,
            '-c:v', 'libx264',
            '-profile:v', 'baseline',
            '-level', '3.0',
            '-preset', 'fast',
            '-crf', '28',  # Reasonable quality with smaller file size
            '-vf', 'scale=320:-2',  # Scale to 320px width for KaiOS screen
            '-c:a', 'aac',
            '-ac', '2',
            '-ar', '44100',
            '-b:a', '96k',  # Lower audio bitrate for smaller files
            '-movflags', '+faststart',  # Enable progressive download
            '-threads', '2',
            '-f', 'mp4',  # Explicitly specify mp4 format for .temp file
            temp_path
        ]
        
        result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True, timeout=600)
        
        # Clean up download file
        if os.path.exists(actual_download):
            os.remove(actual_download)
        
        if result.returncode != 0:
            logger.error(f"FFmpeg error: {result.stderr}")
            if os.path.exists(temp_path):
                os.remove(temp_path)
            return False, f"Transcoding failed: {result.stderr[:200]}"
        
        # Move temp file to final location
        shutil.move(temp_path, output_path)
        
        # Get file size
        file_size = os.path.getsize(output_path)
        logger.info(f"Video ready: {video_id} ({file_size / 1024:.1f} KB)")
        
        # Cleanup old cache files
        cleanup_old_cache()
        
        return True, {"title": title, "duration": duration, "size": file_size}
        
    except subprocess.TimeoutExpired:
        logger.error(f"Transcoding timeout for video: {video_id}")
        for path in [temp_path, download_path]:
            if os.path.exists(path):
                os.remove(path)
        return False, "Transcoding timeout"
    except Exception as e:
        logger.error(f"Error downloading/transcoding video {video_id}: {e}")
        for path in [temp_path, download_path]:
            if os.path.exists(path):
                os.remove(path)
        return False, str(e)


@app.route('/api/youtube/info/<video_id>', methods=['GET'])
def youtube_video_info(video_id):
    """Get information about a YouTube video without downloading"""
    if not YT_DLP_AVAILABLE:
        return jsonify({'error': 'YouTube streaming not available'}), 503
    
    video_id = get_video_id_from_url(video_id)
    if not video_id:
        return jsonify({'error': 'Invalid video ID'}), 400
    
    try:
        url = f"https://www.youtube.com/watch?v={video_id}"
        
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
        # Check if already cached
        cached_path = get_cached_video_path(video_id)
        is_cached = os.path.exists(cached_path)
        
        return jsonify({
            'success': True,
            'video_id': video_id,
            'title': info.get('title', 'Unknown'),
            'duration': info.get('duration', 0),
            'thumbnail': info.get('thumbnail', ''),
            'channel': info.get('uploader', 'Unknown'),
            'views': info.get('view_count', 0),
            'cached': is_cached,
            'stream_url': f'/api/youtube/stream/{video_id}'
        })
        
    except Exception as e:
        logger.error(f"Error getting video info for {video_id}: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/youtube/prepare/<video_id>', methods=['POST'])
def youtube_prepare_video(video_id):
    """Start preparing a YouTube video for streaming (download + transcode)"""
    if not YT_DLP_AVAILABLE:
        return jsonify({'error': 'YouTube streaming not available'}), 503
    
    video_id = get_video_id_from_url(video_id)
    if not video_id:
        return jsonify({'error': 'Invalid video ID'}), 400
    
    cached_path = get_cached_video_path(video_id)
    
    # If already cached, return immediately
    if os.path.exists(cached_path):
        file_size = os.path.getsize(cached_path)
        return jsonify({
            'success': True,
            'status': 'ready',
            'video_id': video_id,
            'size': file_size,
            'stream_url': f'/api/youtube/stream/{video_id}'
        })
    
    # Check if already downloading
    with youtube_downloads_lock:
        if video_id in youtube_downloads:
            status = youtube_downloads[video_id]
            return jsonify({
                'success': True,
                'status': status.get('status', 'downloading'),
                'video_id': video_id,
                'message': status.get('message', 'Download in progress')
            })
        
        # Start download in background
        youtube_downloads[video_id] = {'status': 'downloading', 'message': 'Starting download...'}
    
    def download_thread():
        try:
            with youtube_downloads_lock:
                youtube_downloads[video_id] = {'status': 'downloading', 'message': 'Downloading video...'}
            
            success, result = download_and_transcode_video(video_id, cached_path)
            
            with youtube_downloads_lock:
                if success:
                    youtube_downloads[video_id] = {
                        'status': 'ready',
                        'message': 'Video ready',
                        'title': result.get('title', ''),
                        'size': result.get('size', 0)
                    }
                else:
                    youtube_downloads[video_id] = {
                        'status': 'error',
                        'message': str(result)
                    }
        except Exception as e:
            with youtube_downloads_lock:
                youtube_downloads[video_id] = {'status': 'error', 'message': str(e)}
    
    thread = threading.Thread(target=download_thread, daemon=True)
    thread.start()
    
    return jsonify({
        'success': True,
        'status': 'downloading',
        'video_id': video_id,
        'message': 'Download started'
    })


@app.route('/api/youtube/status/<video_id>', methods=['GET'])
def youtube_video_status(video_id):
    """Check the status of a video preparation"""
    video_id = get_video_id_from_url(video_id)
    if not video_id:
        return jsonify({'error': 'Invalid video ID'}), 400
    
    cached_path = get_cached_video_path(video_id)
    
    # If file exists, it's ready
    if os.path.exists(cached_path):
        file_size = os.path.getsize(cached_path)
        return jsonify({
            'success': True,
            'status': 'ready',
            'video_id': video_id,
            'size': file_size,
            'stream_url': f'/api/youtube/stream/{video_id}'
        })
    
    # Check download status
    with youtube_downloads_lock:
        if video_id in youtube_downloads:
            status = youtube_downloads[video_id]
            return jsonify({
                'success': True,
                'status': status.get('status', 'unknown'),
                'video_id': video_id,
                'message': status.get('message', ''),
                'stream_url': f'/api/youtube/stream/{video_id}' if status.get('status') == 'ready' else None
            })
    
    return jsonify({
        'success': True,
        'status': 'not_found',
        'video_id': video_id,
        'message': 'Video not prepared. Call /api/youtube/prepare/{video_id} first.'
    })


@app.route('/api/youtube/stream/<video_id>', methods=['GET'])
def youtube_stream_video(video_id):
    """Stream a prepared YouTube video (H.264 Baseline for KaiOS)"""
    video_id = get_video_id_from_url(video_id)
    if not video_id:
        return jsonify({'error': 'Invalid video ID'}), 400
    
    cached_path = get_cached_video_path(video_id)
    
    # If not cached, start download and return status
    if not os.path.exists(cached_path):
        # Auto-prepare the video
        if YT_DLP_AVAILABLE:
            # Check if already downloading
            with youtube_downloads_lock:
                if video_id not in youtube_downloads:
                    youtube_downloads[video_id] = {'status': 'downloading', 'message': 'Starting...'}
                    
                    def auto_download():
                        try:
                            success, result = download_and_transcode_video(video_id, cached_path)
                            with youtube_downloads_lock:
                                if success:
                                    youtube_downloads[video_id] = {'status': 'ready'}
                                else:
                                    youtube_downloads[video_id] = {'status': 'error', 'message': str(result)}
                        except Exception as e:
                            with youtube_downloads_lock:
                                youtube_downloads[video_id] = {'status': 'error', 'message': str(e)}
                    
                    thread = threading.Thread(target=auto_download, daemon=True)
                    thread.start()
        
        return jsonify({
            'error': 'Video not ready',
            'status': 'preparing',
            'video_id': video_id,
            'message': 'Video is being prepared. Check /api/youtube/status/{video_id}'
        }), 202
    
    # Stream the video with proper headers for progressive download
    try:
        file_size = os.path.getsize(cached_path)
        
        # Support range requests for seeking
        range_header = request.headers.get('Range')
        
        if range_header:
            # Parse range header
            byte_start = 0
            byte_end = file_size - 1
            
            match = re.match(r'bytes=(\d+)-(\d*)', range_header)
            if match:
                byte_start = int(match.group(1))
                if match.group(2):
                    byte_end = int(match.group(2))
            
            byte_end = min(byte_end, file_size - 1)
            content_length = byte_end - byte_start + 1
            
            def generate():
                with open(cached_path, 'rb') as f:
                    f.seek(byte_start)
                    remaining = content_length
                    while remaining > 0:
                        chunk_size = min(8192, remaining)
                        chunk = f.read(chunk_size)
                        if not chunk:
                            break
                        remaining -= len(chunk)
                        yield chunk
            
            response = Response(
                generate(),
                status=206,
                mimetype='video/mp4',
                direct_passthrough=True
            )
            response.headers['Content-Range'] = f'bytes {byte_start}-{byte_end}/{file_size}'
            response.headers['Accept-Ranges'] = 'bytes'
            response.headers['Content-Length'] = content_length
            return response
        
        # Full file response
        return send_file(
            cached_path,
            mimetype='video/mp4',
            as_attachment=False,
            conditional=True
        )
        
    except Exception as e:
        logger.error(f"Error streaming video {video_id}: {e}")
        return jsonify({'error': 'Failed to stream video'}), 500


@app.route('/api/youtube/list', methods=['GET'])
def youtube_list_cached():
    """List all cached YouTube videos"""
    try:
        videos = []
        for filename in os.listdir(YOUTUBE_CACHE_DIR):
            if filename.endswith('_kaios.mp4'):
                video_id = filename.replace('_kaios.mp4', '')
                filepath = os.path.join(YOUTUBE_CACHE_DIR, filename)
                stat = os.stat(filepath)
                videos.append({
                    'video_id': video_id,
                    'size': stat.st_size,
                    'created': stat.st_mtime,
                    'stream_url': f'/api/youtube/stream/{video_id}'
                })
        
        return jsonify({
            'success': True,
            'videos': videos,
            'cache_dir': YOUTUBE_CACHE_DIR,
            'total_size': sum(v['size'] for v in videos)
        })
        
    except Exception as e:
        logger.error(f"Error listing cached videos: {e}")
        return jsonify({'error': str(e)}), 500


# ============================================================================
# KaiOS Client Serving Endpoints
# ============================================================================

@app.route('/kaios/debug', methods=['GET'])
def kaios_debug():
    """Debug endpoint to check KaiOS client directory"""
    import glob
    files = []
    if os.path.exists(KAIOS_CLIENT_DIR):
        files = os.listdir(KAIOS_CLIENT_DIR)
    return jsonify({
        'kaios_client_dir': KAIOS_CLIENT_DIR,
        'exists': os.path.exists(KAIOS_CLIENT_DIR),
        'files': files,
        'cwd': os.getcwd()
    })

@app.route('/kaios/', methods=['GET'])
def serve_kaios_index():
    """Serve KaiOS launcher page"""
    return serve_kaios_client('launcher.html')

@app.route('/kaios/<path:filename>', methods=['GET'])
def serve_kaios_client(filename):
    """Serve KaiOS client files"""
    try:
        logger.info(f"Serving KaiOS file: {filename}, from dir: {KAIOS_CLIENT_DIR}")
        
        # Security: only allow specific file extensions
        allowed_extensions = ['.html', '.css', '.js', '.png', '.jpg', '.ico', '.svg', '.webapp', '.json', '.mp4', '.webm', '.ogg', '.mp3', '.wav']
        ext = os.path.splitext(filename)[1].lower()
        if ext not in allowed_extensions:
            return jsonify({'error': 'File type not allowed'}), 403
        
        file_path = os.path.join(KAIOS_CLIENT_DIR, filename)
        
        # Security: prevent directory traversal
        if not os.path.abspath(file_path).startswith(os.path.abspath(KAIOS_CLIENT_DIR)):
            return jsonify({'error': 'Access denied'}), 403
        
        if not os.path.exists(file_path):
            logger.error(f"KaiOS file not found: {file_path}")
            return jsonify({'error': 'KaiOS client not found', 'path': file_path}), 404
        
        # Determine content type
        content_types = {
            '.html': 'text/html; charset=utf-8',
            '.css': 'text/css; charset=utf-8',
            '.js': 'application/javascript; charset=utf-8',
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.ico': 'image/x-icon',
            '.svg': 'image/svg+xml',
            '.webapp': 'application/x-web-app-manifest+json',
            '.json': 'application/json',
            '.mp4': 'video/mp4',
            '.webm': 'video/webm',
            '.ogg': 'video/ogg',
            '.mp3': 'audio/mpeg',
            '.wav': 'audio/wav'
        }
        content_type = content_types.get(ext, 'application/octet-stream')
        
        return send_file(file_path, mimetype=content_type)
        
    except Exception as e:
        logger.error(f"Error serving KaiOS file: {e}")
        return jsonify({'error': 'Failed to serve file'}), 500


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
        
        # Return image directly with cache control for high FPS streaming
        response = send_file(
            BytesIO(frame),
            mimetype='image/png',
            as_attachment=False,
            download_name=f'{session_id}_frame.png'
        )
        # Prevent caching to ensure fresh frames at 30 FPS
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response
        
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


# ============================================================================
# WebSocket Event Handlers for Real-time Framebuffer Streaming
# ============================================================================

@socketio.on('connect')
def handle_websocket_connect():
    """Handle new WebSocket connection"""
    logger.info(f"WebSocket client connected: {request.sid}")
    emit('status', {'message': 'Connected to Jiomosa renderer', 'type': 'connection'})


@socketio.on('disconnect')
def handle_websocket_disconnect():
    """Handle WebSocket disconnection"""
    logger.info(f"WebSocket client disconnected: {request.sid}")
    # Clean up any active subscriptions
    if ws_handler:
        ws_handler.handle_unsubscribe(request.sid)


@socketio.on('subscribe')
def handle_subscribe(data):
    """Subscribe to framebuffer streaming for a session
    
    Expected data: {'session_id': 'session-xyz'}
    """
    global ws_handler
    if not ws_handler:
        emit('error', {'message': 'WebSocket handler not initialized'})
        return
    
    session_id = data.get('session_id')
    if not session_id:
        emit('error', {'message': 'session_id is required'})
        return
    
    if session_id not in active_sessions:
        emit('error', {'message': f'Session {session_id} not found'})
        return
    
    logger.info(f"Client {request.sid} subscribed to session {session_id}")
    ws_handler.handle_subscribe(request.sid, session_id, emit)
    emit('subscribed', {'session_id': session_id, 'message': 'Subscribed to framebuffer stream'})


@socketio.on('unsubscribe')
def handle_unsubscribe(data):
    """Unsubscribe from framebuffer streaming"""
    global ws_handler
    if ws_handler:
        session_id = data.get('session_id', 'unknown')
        logger.info(f"Client {request.sid} unsubscribed from session {session_id}")
        ws_handler.handle_unsubscribe(request.sid)
    emit('unsubscribed', {'message': 'Unsubscribed from framebuffer stream'})


@socketio.on('input:click')
def handle_input_click(data):
    """Handle click input event
    
    Expected data: {'x': 100, 'y': 200}
    """
    global ws_handler
    if not ws_handler:
        emit('error', {'message': 'WebSocket handler not initialized'})
        return
    
    session_id = ws_handler.get_session_id_for_client(request.sid)
    if not session_id or session_id not in active_sessions:
        emit('error', {'message': 'Not subscribed to any session'})
        return
    
    x = data.get('x')
    y = data.get('y')
    if x is None or y is None:
        emit('error', {'message': 'x and y coordinates required'})
        return
    
    try:
        session = active_sessions[session_id]
        session.send_click(x, y)
        logger.debug(f"Click event sent to {session_id}: ({x}, {y})")
        emit('input:acknowledged', {'type': 'click', 'x': x, 'y': y})
    except Exception as e:
        logger.error(f"Error sending click to {session_id}: {e}")
        emit('error', {'message': f'Failed to send click: {str(e)}'})


@socketio.on('input:scroll')
def handle_input_scroll(data):
    """Handle scroll input event
    
    Expected data: {'deltaX': 0, 'deltaY': 50}
    """
    global ws_handler
    if not ws_handler:
        emit('error', {'message': 'WebSocket handler not initialized'})
        return
    
    session_id = ws_handler.get_session_id_for_client(request.sid)
    if not session_id or session_id not in active_sessions:
        emit('error', {'message': 'Not subscribed to any session'})
        return
    
    deltaX = data.get('deltaX', 0)
    deltaY = data.get('deltaY', 0)
    
    try:
        session = active_sessions[session_id]
        session.send_scroll(deltaX, deltaY)
        logger.debug(f"Scroll event sent to {session_id}: ({deltaX}, {deltaY})")
        emit('input:acknowledged', {'type': 'scroll', 'deltaX': deltaX, 'deltaY': deltaY})
    except Exception as e:
        logger.error(f"Error sending scroll to {session_id}: {e}")
        emit('error', {'message': f'Failed to send scroll: {str(e)}'})


@socketio.on('input:text')
def handle_input_text(data):
    """Handle text input event
    
    Expected data: {'text': 'hello'}
    """
    global ws_handler
    if not ws_handler:
        emit('error', {'message': 'WebSocket handler not initialized'})
        return
    
    session_id = ws_handler.get_session_id_for_client(request.sid)
    if not session_id or session_id not in active_sessions:
        emit('error', {'message': 'Not subscribed to any session'})
        return
    
    text = data.get('text', '')
    if not text:
        emit('error', {'message': 'text is required'})
        return
    
    try:
        session = active_sessions[session_id]
        session.send_text(text)
        logger.debug(f"Text event sent to {session_id}: '{text}'")
        emit('input:acknowledged', {'type': 'text', 'length': len(text)})
    except Exception as e:
        logger.error(f"Error sending text to {session_id}: {e}")
        emit('error', {'message': f'Failed to send text: {str(e)}'})


@socketio.on('quality:set')
def handle_quality_set(data):
    """Set JPEG quality for frame compression
    
    Expected data: {'quality': 75}  # 1-100
    """
    global ws_handler
    if not ws_handler:
        emit('error', {'message': 'WebSocket handler not initialized'})
        return
    
    quality = data.get('quality')
    if quality is None or not (1 <= quality <= 100):
        emit('error', {'message': 'quality must be between 1 and 100'})
        return
    
    client_id = request.sid
    ws_handler.set_quality(client_id, quality)
    logger.info(f"Quality set to {quality} for client {client_id}")
    emit('quality:updated', {'quality': quality})


@socketio.on('fps:set')
def handle_fps_set(data):
    """Set target FPS for frame streaming
    
    Expected data: {'fps': 30}  # 1-60
    """
    global ws_handler
    if not ws_handler:
        emit('error', {'message': 'WebSocket handler not initialized'})
        return
    
    fps = data.get('fps')
    if fps is None or not (1 <= fps <= 60):
        emit('error', {'message': 'fps must be between 1 and 60'})
        return
    
    client_id = request.sid
    ws_handler.set_fps(client_id, fps)
    logger.info(f"FPS set to {fps} for client {client_id}")
    emit('fps:updated', {'fps': fps})


@socketio.on('adaptive:toggle')
def handle_adaptive_toggle(data):
    """Toggle adaptive quality mode
    
    Expected data: {'enabled': True}
    """
    global ws_handler
    if not ws_handler:
        emit('error', {'message': 'WebSocket handler not initialized'})
        return
    
    enabled = data.get('enabled', True)
    client_id = request.sid
    ws_handler.toggle_adaptive_mode(client_id, enabled)
    logger.info(f"Adaptive mode set to {enabled} for client {client_id}")
    emit('adaptive:updated', {'enabled': enabled})


# ============================================================================
# Audio WebSocket Handlers for KaiOS Client
# ============================================================================

@socketio.on('audio:subscribe')
def handle_audio_subscribe(data):
    """Subscribe to audio streaming for a session
    
    Expected data: {'session_id': 'session-xyz'}
    """
    global audio_streamer
    if not audio_streamer:
        emit('error', {'message': 'Audio streamer not initialized'})
        return
    
    session_id = data.get('session_id')
    if not session_id:
        emit('error', {'message': 'session_id is required'})
        return
    
    if session_id not in active_sessions:
        emit('error', {'message': f'Session {session_id} not found'})
        return
    
    logger.info(f"Client {request.sid} subscribing to audio for session {session_id}")
    audio_streamer.subscribe_client(request.sid, session_id)
    emit('audio:subscribed', {'session_id': session_id, 'message': 'Subscribed to audio stream'})


@socketio.on('audio:unsubscribe')
def handle_audio_unsubscribe(data):
    """Unsubscribe from audio streaming"""
    global audio_streamer
    if audio_streamer:
        session_id = data.get('session_id', 'unknown')
        logger.info(f"Client {request.sid} unsubscribing from audio for session {session_id}")
        audio_streamer.unsubscribe_client(request.sid)
    emit('audio:unsubscribed', {'message': 'Unsubscribed from audio stream'})


if __name__ == '__main__':
    logger.info("Starting Jiomosa Renderer Service with WebSocket Streaming")
    logger.info(f"Selenium: {SELENIUM_HOST}:{SELENIUM_PORT}")
    logger.info(f"Session Timeout: {SESSION_TIMEOUT} seconds")
    logger.info(f"Frame Capture Interval: {FRAME_CAPTURE_INTERVAL} seconds")
    logger.info(f"KaiOS Client Dir: {KAIOS_CLIENT_DIR}")
    logger.info("WebSocket: Socket.IO enabled on ws://0.0.0.0:5000/socket.io/")
    
    # Initialize WebSocket handler
    ws_handler = WebSocketHandler(socketio, active_sessions)
    logger.info("WebSocket handler initialized")
    
    # Initialize Audio streamer
    audio_streamer = create_audio_streamer(socketio, active_sessions)
    logger.info("Audio streamer initialized")
    
    # Start cleanup thread
    cleanup_thread = threading.Thread(target=cleanup_expired_sessions, daemon=True)
    cleanup_thread.start()
    logger.info("Session cleanup thread started")
    
    # Start frame streaming thread
    streaming_thread = threading.Thread(target=stream_frames_to_clients, daemon=True)
    streaming_thread.start()
    logger.info("Frame streaming thread started")
    
    # Debug mode disabled for security - use environment variable to enable if needed
    debug_mode = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
    socketio.run(app, host='0.0.0.0', port=5000, debug=debug_mode, allow_unsafe_werkzeug=True)
