"""
Browser management with Playwright
Implements browser instance pooling for efficient resource usage
"""
import asyncio
import logging
from typing import Optional, Dict
from datetime import datetime, timedelta
from playwright.async_api import async_playwright, Browser, BrowserContext, Page, Playwright
from config import settings
import base64

logger = logging.getLogger(__name__)


class BrowserPool:
    """Manages a pool of browser instances for efficient reuse"""
    
    def __init__(self):
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.contexts: Dict[str, BrowserContext] = {}
        self.pages: Dict[str, Page] = {}
        self.session_timestamps: Dict[str, datetime] = {}
        self._lock = asyncio.Lock()
        
    async def initialize(self):
        """Initialize Playwright and browser"""
        try:
            logger.info("Initializing Playwright...")
            self.playwright = await async_playwright().start()
            
            logger.info(f"Launching {settings.browser_type} browser...")
            self.browser = await self.playwright.chromium.launch(
                headless=settings.browser_headless,
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-extensions',
                    '--remote-debugging-port=9222',  # Enable CDP
                    '--disable-background-networking',
                    '--disable-background-timer-throttling',
                    '--disable-backgrounding-occluded-windows',
                    '--disable-renderer-backgrounding',
                    '--disable-hang-monitor',
                    '--disable-ipc-flooding-protection',
                    '--disable-popup-blocking',
                    '--disable-prompt-on-repost',
                    '--metrics-recording-only',
                    '--no-first-run',
                    '--password-store=basic',
                    '--use-mock-keychain',
                    '--force-color-profile=srgb',
                    # Performance optimizations
                    '--disable-blink-features=AutomationControlled',
                    '--disable-web-security',  # For CORS during development
                ]
            )
            logger.info("Browser initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize browser: {e}")
            raise
    
    async def create_session(self, session_id: str, width: int = None, height: int = None) -> Page:
        """Create a new browser session (context + page) with optional custom viewport"""
        async with self._lock:
            if session_id in self.pages:
                logger.warning(f"Session {session_id} already exists")
                return self.pages[session_id]
            
            if len(self.pages) >= settings.browser_max_sessions:
                raise RuntimeError(f"Maximum sessions reached ({settings.browser_max_sessions})")
            
            # Use provided dimensions or defaults
            viewport_width = width or settings.webrtc_video_width
            viewport_height = height or settings.webrtc_video_height
            
            logger.info(f"Creating session {session_id} with viewport {viewport_width}x{viewport_height}")
            
            try:
                # Create a new browser context (isolated session)
                context = await self.browser.new_context(
                    viewport={'width': viewport_width, 'height': viewport_height},
                    device_scale_factor=1.0,
                    has_touch=True,
                    is_mobile=True,
                    user_agent='Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
                    locale='en-US',
                    timezone_id='America/New_York',
                    geolocation={'latitude': 40.7128, 'longitude': -74.0060},
                    permissions=['geolocation'],
                    color_scheme='light',
                    reduced_motion='no-preference',
                )
                
                # Create a new page in the context
                page = await context.new_page()
                
                # Set default timeouts
                page.set_default_timeout(30000)  # 30 seconds
                page.set_default_navigation_timeout(30000)
                
                # Enable CDP session for fast screenshots
                cdp_session = await context.new_cdp_session(page)
                
                # Store references including CDP session
                self.contexts[session_id] = context
                self.pages[session_id] = page
                self.session_timestamps[session_id] = datetime.now()
                # Store CDP session for fast frame capture
                if not hasattr(self, 'cdp_sessions'):
                    self.cdp_sessions = {}
                self.cdp_sessions[session_id] = cdp_session
                
                logger.info(f"Created session {session_id} ({len(self.pages)} active)")
                return page
                
            except Exception as e:
                logger.error(f"Failed to create session {session_id}: {e}")
                raise
    
    async def get_page(self, session_id: str) -> Optional[Page]:
        """Get an existing page for a session"""
        return self.pages.get(session_id)
    
    async def navigate(self, session_id: str, url: str) -> bool:
        """Navigate a session to a URL"""
        page = await self.get_page(session_id)
        if not page:
            raise ValueError(f"Session {session_id} not found")
        
        try:
            logger.info(f"Navigating session {session_id} to {url}")
            await page.goto(url, wait_until='domcontentloaded', timeout=30000)
            
            # Update activity timestamp
            self.session_timestamps[session_id] = datetime.now()
            return True
        except Exception as e:
            logger.error(f"Failed to navigate session {session_id} to {url}: {e}")
            return False
    
    async def click(self, session_id: str, x: int, y: int):
        """Perform a click at coordinates"""
        page = await self.get_page(session_id)
        if not page:
            raise ValueError(f"Session {session_id} not found")
        
        try:
            await page.mouse.click(x, y)
            self.session_timestamps[session_id] = datetime.now()
        except Exception as e:
            logger.error(f"Failed to click in session {session_id}: {e}")
            raise
    
    async def scroll(self, session_id: str, delta_y: int):
        """Scroll the page"""
        page = await self.get_page(session_id)
        if not page:
            raise ValueError(f"Session {session_id} not found")
        
        try:
            await page.mouse.wheel(0, delta_y)
            self.session_timestamps[session_id] = datetime.now()
        except Exception as e:
            logger.error(f"Failed to scroll in session {session_id}: {e}")
            raise
    
    async def type_text(self, session_id: str, text: str):
        """Type text into the focused element"""
        page = await self.get_page(session_id)
        if not page:
            raise ValueError(f"Session {session_id} not found")
        
        try:
            await page.keyboard.type(text)
            self.session_timestamps[session_id] = datetime.now()
        except Exception as e:
            logger.error(f"Failed to type text in session {session_id}: {e}")
            raise
    
    async def press_key(self, session_id: str, key: str):
        """Press a specific key (supports special keys like Enter, Backspace, etc.)"""
        page = await self.get_page(session_id)
        if not page:
            raise ValueError(f"Session {session_id} not found")
        
        try:
            await page.keyboard.press(key)
            self.session_timestamps[session_id] = datetime.now()
        except Exception as e:
            logger.error(f"Failed to press key '{key}' in session {session_id}: {e}")
            raise
    
    async def resize_viewport(self, session_id: str, width: int, height: int):
        """Resize the viewport of an existing session"""
        page = await self.get_page(session_id)
        if not page:
            raise ValueError(f"Session {session_id} not found")
        
        try:
            await page.set_viewport_size({'width': width, 'height': height})
            self.session_timestamps[session_id] = datetime.now()
            logger.info(f"Resized session {session_id} viewport to {width}x{height}")
        except Exception as e:
            logger.error(f"Failed to resize viewport for session {session_id}: {e}")
            raise
    
    async def screenshot(self, session_id: str) -> Optional[bytes]:
        """Take a screenshot using CDP for maximum performance (3-5ms vs 20-50ms)"""
        if not hasattr(self, 'cdp_sessions') or session_id not in self.cdp_sessions:
            logger.warning(f"CDP session not found for {session_id}, falling back to Playwright screenshot")
            return await self._screenshot_fallback(session_id)
        
        try:
            cdp_session = self.cdp_sessions[session_id]
            
            # Use CDP Page.captureScreenshot - MUCH faster than Playwright's screenshot()
            # Returns base64-encoded JPEG directly from browser rendering engine
            result = await cdp_session.send('Page.captureScreenshot', {
                'format': 'jpeg',
                'quality': 85,  # Good balance between quality and size
                'captureBeyondViewport': False,
                'fromSurface': True  # Capture from compositing surface (faster)
            })
            
            # Decode base64 to bytes
            screenshot_bytes = base64.b64decode(result['data'])
            return screenshot_bytes
            
        except Exception as e:
            logger.error(f"CDP screenshot failed for session {session_id}: {e}, falling back")
            return await self._screenshot_fallback(session_id)
    
    async def _screenshot_fallback(self, session_id: str) -> Optional[bytes]:
        """Fallback to Playwright screenshot if CDP fails"""
        page = await self.get_page(session_id)
        if not page:
            return None
        
        try:
            screenshot = await page.screenshot(type='jpeg', quality=85, full_page=False)
            return screenshot
        except Exception as e:
            logger.error(f"Failed to take screenshot of session {session_id}: {e}")
            return None
    
    async def close_session(self, session_id: str):
        """Close a browser session"""
        async with self._lock:
            if session_id not in self.pages:
                logger.warning(f"Session {session_id} not found")
                return
            
            try:
                # Close page and context
                page = self.pages[session_id]
                context = self.contexts[session_id]
                
                await page.close()
                await context.close()
                
                # Remove from dictionaries
                del self.pages[session_id]
                del self.contexts[session_id]
                del self.session_timestamps[session_id]
                
                # Remove CDP session if exists
                if hasattr(self, 'cdp_sessions') and session_id in self.cdp_sessions:
                    del self.cdp_sessions[session_id]
                
                logger.info(f"Closed session {session_id} ({len(self.pages)} active)")
            except Exception as e:
                logger.error(f"Failed to close session {session_id}: {e}")
    
    async def cleanup_stale_sessions(self):
        """Remove sessions that have been inactive for too long"""
        now = datetime.now()
        timeout_delta = timedelta(seconds=settings.browser_session_timeout)
        
        # Find stale sessions without holding the lock
        stale_sessions = []
        async with self._lock:
            stale_sessions = [
                session_id for session_id, timestamp in self.session_timestamps.items()
                if now - timestamp > timeout_delta
            ]
        
        # Close sessions one by one (close_session acquires its own lock)
        for session_id in stale_sessions:
            logger.info(f"Cleaning up stale session {session_id}")
            await self.close_session(session_id)
    
    async def get_stats(self) -> Dict:
        """Get pool statistics"""
        return {
            'active_sessions': len(self.pages),
            'max_sessions': settings.browser_max_sessions,
            'sessions': list(self.pages.keys())
        }
    
    async def shutdown(self):
        """Shutdown the browser pool"""
        logger.info("Shutting down browser pool...")
        
        # Close all sessions
        session_ids = list(self.pages.keys())
        for session_id in session_ids:
            await self.close_session(session_id)
        
        # Close browser
        if self.browser:
            await self.browser.close()
        
        # Stop playwright
        if self.playwright:
            await self.playwright.stop()
        
        logger.info("Browser pool shutdown complete")


# Global browser pool instance
browser_pool = BrowserPool()
