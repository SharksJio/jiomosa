"""
WebRTC Video Track for Browser Streaming
Captures frames from browser and streams via WebRTC
"""
import asyncio
import logging
import time
from typing import Optional
from av import VideoFrame
from aiortc import VideoStreamTrack
from aiortc.mediastreams import MediaStreamError
from browser_pool import browser_pool
from PIL import Image
import io
import numpy as np

logger = logging.getLogger(__name__)


class BrowserVideoTrack(VideoStreamTrack):
    """
    A video track that captures frames from a browser session
    """
    kind = "video"
    
    def __init__(self, session_id: str, fps: int = 30):
        super().__init__()
        self.session_id = session_id
        self.fps = fps
        self.frame_interval = 1.0 / fps
        self.last_frame_time = 0
        self._running = True
        self._frame_count = 0
        # Track frame timing for skip logic
        self._last_screenshot_bytes: Optional[bytes] = None
        self._frames_skipped = 0
        self._frame_deadline = 0
        logger.info(f"Initialized BrowserVideoTrack for session {session_id} at {fps} FPS")
    
    async def recv(self):
        """
        Receive the next video frame
        Called by WebRTC to get frames for streaming
        """
        if not self._running:
            raise MediaStreamError("Track stopped")
        
        current_time = time.time()
        
        # Calculate frame deadline for skip logic
        if self._frame_deadline == 0:
            self._frame_deadline = current_time + self.frame_interval
        
        # Rate limiting to maintain target FPS
        elapsed = current_time - self.last_frame_time
        if elapsed < self.frame_interval:
            await asyncio.sleep(self.frame_interval - elapsed)
        
        self.last_frame_time = time.time()
        
        # Check if we're behind schedule and should skip frame capture
        if current_time > self._frame_deadline + self.frame_interval and self._last_screenshot_bytes is not None:
            # We're more than 1 frame behind schedule - reuse last frame
            frames_behind = int((current_time - self._frame_deadline) / self.frame_interval)
            self._frames_skipped += 1
            if self._frames_skipped % 10 == 0:
                logger.warning(f"Skipped frame capture for session {self.session_id}, {frames_behind} frames behind (total skipped: {self._frames_skipped})")
            # Reuse last frame to catch up
            self._frame_deadline = current_time + self.frame_interval
            frame = await self._create_video_frame(self._last_screenshot_bytes)
            self._frame_count += 1
            return frame
        
        # Update deadline for next frame
        self._frame_deadline = current_time + self.frame_interval
        
        try:
            # Get screenshot from browser (now using fast CDP JPEG capture)
            screenshot_bytes = await browser_pool.screenshot(self.session_id)
            
            if screenshot_bytes is None:
                # If no screenshot available, return a blank frame
                logger.warning(f"No screenshot available for session {self.session_id}")
                return await self._create_blank_frame()
            
            # Cache the screenshot for potential reuse
            self._last_screenshot_bytes = screenshot_bytes
            
            # Convert JPEG screenshot to VideoFrame (optimized for CDP)
            frame = await self._create_video_frame(screenshot_bytes)
            
            self._frame_count += 1
            if self._frame_count % 100 == 0:
                logger.info(f"Streamed {self._frame_count} frames for session {self.session_id}")
            
            return frame
            
        except Exception as e:
            logger.error(f"Error capturing frame for session {self.session_id}: {e}")
            return await self._create_blank_frame()
    
    async def _create_video_frame(self, screenshot_bytes: bytes) -> VideoFrame:
        """Convert screenshot bytes to VideoFrame (optimized for JPEG from CDP)"""
        try:
            # Open JPEG image with PIL (much faster than PNG)
            # CDP returns JPEG which decodes 2-3x faster than PNG
            img = Image.open(io.BytesIO(screenshot_bytes))
            
            # Convert to RGB if necessary (JPEG is usually already RGB)
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Convert PIL Image to numpy array for faster VideoFrame creation
            img_array = np.array(img, dtype=np.uint8)
            
            # Create VideoFrame from numpy array (faster than from_image)
            frame = VideoFrame.from_ndarray(img_array, format="rgb24")
            
            # Set presentation timestamp
            frame.pts = self._frame_count
            frame.time_base = "1/" + str(self.fps)
            
            return frame
            
        except Exception as e:
            logger.error(f"Error creating video frame: {e}")
            return await self._create_blank_frame()
    
    async def _create_blank_frame(self) -> VideoFrame:
        """Create a blank black frame"""
        from config import settings
        
        # Create a black image using numpy (faster than PIL)
        img_array = np.zeros((settings.webrtc_video_height, settings.webrtc_video_width, 3), dtype=np.uint8)
        
        # Create VideoFrame from numpy array
        frame = VideoFrame.from_ndarray(img_array, format="rgb24")
        frame.pts = self._frame_count
        frame.time_base = "1/" + str(self.fps)
        
        return frame
    
    def stop(self):
        """Stop the video track"""
        logger.info(f"Stopping BrowserVideoTrack for session {self.session_id}")
        self._running = False
        super().stop()
