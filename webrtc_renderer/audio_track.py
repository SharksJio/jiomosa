"""
WebRTC Audio Track for Browser Audio Streaming
Captures audio from browser and streams via WebRTC
"""
import asyncio
import logging
import time
from typing import Optional
from fractions import Fraction
from av import AudioFrame
from aiortc import AudioStreamTrack
from aiortc.mediastreams import MediaStreamError
import numpy as np

logger = logging.getLogger(__name__)


class BrowserAudioTrack(AudioStreamTrack):
    """
    An audio track that generates audio frames for WebRTC streaming.
    
    This implementation creates silent audio frames as a placeholder.
    For actual browser audio capture, you would need to:
    1. Use PulseAudio/ALSA to capture system audio
    2. Or use Chrome DevTools Protocol (CDP) audio capture
    3. Or use a virtual audio device to capture browser output
    
    Note: Browser audio capture in headless mode is complex and requires
    specific system audio configuration.
    """
    kind = "audio"
    
    def __init__(self, session_id: str, sample_rate: int = 48000, channels: int = 2):
        super().__init__()
        self.session_id = session_id
        self.sample_rate = sample_rate
        self.channels = channels
        self._running = True
        self._frame_count = 0
        self._start_time = time.time()
        
        # Audio frame settings
        # Each frame is 20ms of audio (standard for WebRTC)
        self.samples_per_frame = int(sample_rate * 0.02)  # 960 samples at 48kHz
        
        logger.info(f"Initialized BrowserAudioTrack for session {session_id}: "
                   f"{sample_rate}Hz, {channels} channels, {self.samples_per_frame} samples/frame")
    
    async def recv(self) -> AudioFrame:
        """
        Receive the next audio frame.
        Called by WebRTC to get frames for streaming.
        
        Currently generates silent frames. For actual audio:
        - Implement PulseAudio capture
        - Or use CDP audio stream interception
        """
        if not self._running:
            raise MediaStreamError("Track stopped")
        
        # Calculate expected timestamp based on frame count
        # Each frame is 20ms
        pts = self._frame_count * self.samples_per_frame
        
        # Generate silent audio frame (placeholder for actual audio capture)
        # In production, this would be replaced with captured browser audio
        samples = np.zeros((self.channels, self.samples_per_frame), dtype=np.int16)
        
        # Create AudioFrame
        frame = AudioFrame.from_ndarray(samples, format='s16', layout='stereo' if self.channels == 2 else 'mono')
        frame.sample_rate = self.sample_rate
        frame.pts = pts
        frame.time_base = Fraction(1, self.sample_rate)
        
        self._frame_count += 1
        
        # Rate limiting - maintain 20ms frame intervals
        elapsed = time.time() - self._start_time
        expected_time = self._frame_count * 0.02  # 20ms per frame
        
        if elapsed < expected_time:
            await asyncio.sleep(expected_time - elapsed)
        
        # Log periodically
        if self._frame_count % 500 == 0:  # Every 10 seconds
            logger.debug(f"Audio track {self.session_id}: {self._frame_count} frames streamed")
        
        return frame
    
    def stop(self):
        """Stop the audio track"""
        logger.info(f"Stopping BrowserAudioTrack for session {self.session_id}")
        self._running = False
        super().stop()


class PulseAudioTrack(AudioStreamTrack):
    """
    Audio track that captures audio from PulseAudio.
    
    This requires PulseAudio to be properly configured with a monitor source
    that captures the browser's audio output.
    
    Prerequisites:
    1. PulseAudio running in the container
    2. A virtual sink for browser audio output
    3. A monitor source to capture that audio
    """
    kind = "audio"
    
    def __init__(self, session_id: str, sample_rate: int = 48000, channels: int = 2):
        super().__init__()
        self.session_id = session_id
        self.sample_rate = sample_rate
        self.channels = channels
        self._running = True
        self._frame_count = 0
        self._start_time = time.time()
        self._audio_queue: asyncio.Queue = asyncio.Queue(maxsize=50)
        self._capture_task: Optional[asyncio.Task] = None
        
        # Audio frame settings
        self.samples_per_frame = int(sample_rate * 0.02)  # 20ms frames
        self.frame_duration = 0.02  # 20ms
        
        logger.info(f"Initialized PulseAudioTrack for session {session_id}")
    
    async def start_capture(self):
        """Start the audio capture task"""
        self._capture_task = asyncio.create_task(self._capture_loop())
        logger.info(f"Started PulseAudio capture for session {self.session_id}")
    
    async def _capture_loop(self):
        """
        Capture audio from PulseAudio.
        
        This would use PyAudio or direct PulseAudio bindings to capture
        audio from the configured monitor source.
        """
        try:
            while self._running:
                # Placeholder: Generate silent audio
                # In production, capture from PulseAudio here
                samples = np.zeros((self.channels, self.samples_per_frame), dtype=np.int16)
                
                try:
                    self._audio_queue.put_nowait(samples)
                except asyncio.QueueFull:
                    # Drop frame if queue is full
                    pass
                
                await asyncio.sleep(self.frame_duration)
                
        except Exception as e:
            logger.error(f"Audio capture error for session {self.session_id}: {e}")
    
    async def recv(self) -> AudioFrame:
        """Receive the next audio frame"""
        if not self._running:
            raise MediaStreamError("Track stopped")
        
        try:
            # Get audio samples from capture queue
            samples = await asyncio.wait_for(
                self._audio_queue.get(),
                timeout=0.1  # 100ms timeout
            )
        except asyncio.TimeoutError:
            # Generate silent frame if no audio available
            samples = np.zeros((self.channels, self.samples_per_frame), dtype=np.int16)
        
        pts = self._frame_count * self.samples_per_frame
        
        # Create AudioFrame
        frame = AudioFrame.from_ndarray(samples, format='s16', layout='stereo' if self.channels == 2 else 'mono')
        frame.sample_rate = self.sample_rate
        frame.pts = pts
        frame.time_base = Fraction(1, self.sample_rate)
        
        self._frame_count += 1
        
        return frame
    
    def stop(self):
        """Stop the audio track and cleanup"""
        logger.info(f"Stopping PulseAudioTrack for session {self.session_id}")
        self._running = False
        
        if self._capture_task:
            self._capture_task.cancel()
        
        super().stop()
