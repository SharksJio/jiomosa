"""
WebRTC Video Track for Browser Streaming
Captures frames from browser and streams via WebRTC
"""
import asyncio
import logging
import time
from collections import deque
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
        # Frame buffer for skip logic - keep only latest 2 frames
        self.frame_buffer: deque = deque(maxlen=2)
        self._frames_skipped = 0
        logger.info(f"Initialized BrowserVideoTrack for session {session_id} at {fps} FPS")
    
    async def recv(self):
        """
        Receive the next video frame
        Called by WebRTC to get frames for streaming
        """
        if not self._running:
            raise MediaStreamError("Track stopped")
        
        # Rate limiting to maintain target FPS
        current_time = time.time()
        elapsed = current_time - self.last_frame_time
        if elapsed < self.frame_interval:
            await asyncio.sleep(self.frame_interval - elapsed)
        
        self.last_frame_time = time.time()
        
        try:
            # Get screenshot from browser (now using fast CDP JPEG capture)
            screenshot_bytes = await browser_pool.screenshot(self.session_id)
            
            if screenshot_bytes is None:
                # If no screenshot available, return a blank frame
                logger.warning(f"No screenshot available for session {self.session_id}")
                return await self._create_blank_frame()
            
            # Add frame to buffer
            self.frame_buffer.append(screenshot_bytes)
            
            # Skip frames if behind schedule (frame buffer has more than 1 frame)
            if len(self.frame_buffer) > 1:
                frames_to_skip = len(self.frame_buffer) - 1
                self._frames_skipped += frames_to_skip
                if self._frames_skipped % 10 == 0:
                    logger.warning(f"Skipped {frames_to_skip} frames for session {self.session_id} (total skipped: {self._frames_skipped})")
                # Clear buffer and use only latest frame
                latest_frame = self.frame_buffer[-1]
                self.frame_buffer.clear()
                self.frame_buffer.append(latest_frame)
            
            # Get the latest frame from buffer
            frame_bytes = self.frame_buffer[-1]
            
            # Convert JPEG screenshot to VideoFrame (optimized for CDP)
            frame = await self._create_video_frame(frame_bytes)
            
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
