"""
WebRTC Audio Track for Browser Audio Streaming
Captures audio from browser via PulseAudio and streams via WebRTC
"""
import asyncio
import logging
import time
import subprocess
import os
import threading
from typing import Optional
from fractions import Fraction
from av import AudioFrame
from aiortc import AudioStreamTrack
from aiortc.mediastreams import MediaStreamError
import numpy as np

logger = logging.getLogger(__name__)


class BrowserAudioTrack(AudioStreamTrack):
    """
    An audio track that captures browser audio via PulseAudio monitor
    and streams it via WebRTC.
    
    Uses PulseAudio's monitor source to capture all system audio output,
    which includes audio from the headless Chrome browser.
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
        self._audio_process: Optional[subprocess.Popen] = None
        self._audio_thread: Optional[threading.Thread] = None
        self._audio_buffer = b''
        self._buffer_lock = threading.Lock()
        
        # Audio frame settings
        # Each frame is 20ms of audio (standard for WebRTC)
        self.samples_per_frame = int(sample_rate * 0.02)  # 960 samples at 48kHz
        self.bytes_per_frame = self.samples_per_frame * channels * 2  # 16-bit audio
        
        # Try to start audio capture
        self._start_audio_capture()
        
        logger.info(f"Initialized BrowserAudioTrack for session {session_id}: "
                   f"{sample_rate}Hz, {channels} channels, {self.samples_per_frame} samples/frame")
    
    def _start_audio_capture(self):
        """Start capturing audio from PulseAudio monitor source"""
        try:
            # Check if PulseAudio is available
            result = subprocess.run(['pactl', 'info'], capture_output=True, timeout=5)
            if result.returncode != 0:
                logger.warning("PulseAudio not available, using silent audio")
                return
            
            logger.info("PulseAudio is available, setting up audio capture")
            
            # Get the default sink monitor - use browser_audio directly
            monitor_source = "browser_audio.monitor"
            
            logger.info(f"Using PulseAudio monitor source: {monitor_source}")
            
            # Start parec to capture audio
            # Format: signed 16-bit little-endian, stereo
            # Use native sample rate and let it resample if needed
            cmd = [
                'parec',
                '--format=s16le',
                f'--rate={self.sample_rate}',
                f'--channels={self.channels}',
                '--latency-msec=50',
                f'--device={monitor_source}'
            ]
            
            logger.info(f"Starting parec with command: {' '.join(cmd)}")
            
            self._audio_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=self.bytes_per_frame
            )
            
            # Check if process started successfully
            import time
            time.sleep(0.1)
            if self._audio_process.poll() is not None:
                stderr = self._audio_process.stderr.read().decode()
                logger.error(f"parec failed to start: {stderr}")
                self._audio_process = None
                return
            
            # Start background thread to read audio data
            import threading
            self._audio_thread = threading.Thread(target=self._read_audio_loop, daemon=True)
            self._audio_thread.start()
            
            logger.info("PulseAudio capture started successfully")
            
        except FileNotFoundError:
            logger.warning("parec not found, PulseAudio tools not installed")
        except subprocess.TimeoutExpired:
            logger.warning("PulseAudio timeout, audio capture disabled")
        except Exception as e:
            logger.error(f"Failed to start audio capture: {e}", exc_info=True)
    
    def _read_audio_loop(self):
        """Background loop to read audio from parec"""
        if not self._audio_process:
            logger.warning("No audio process to read from")
            return
        
        logger.info(f"Audio read loop started for session {self.session_id}")
        bytes_read = 0
            
        try:
            while self._running and self._audio_process.poll() is None:
                data = self._audio_process.stdout.read(self.bytes_per_frame)
                if data:
                    with self._buffer_lock:
                        self._audio_buffer = data
                    bytes_read += len(data)
                    if bytes_read % (self.bytes_per_frame * 50) == 0:  # Log every ~1 second
                        logger.debug(f"Audio: read {bytes_read} bytes total")
        except Exception as e:
            logger.error(f"Audio read loop error: {e}")
        
        logger.info(f"Audio read loop ended for session {self.session_id}, total bytes: {bytes_read}")
    
    async def recv(self) -> AudioFrame:
        """
        Receive the next audio frame.
        Called by WebRTC to get frames for streaming.
        """
        if not self._running:
            raise MediaStreamError("Track stopped")
        
        # Calculate expected timestamp based on frame count
        pts = self._frame_count * self.samples_per_frame
        
        # Get audio data from buffer or generate silence
        with self._buffer_lock:
            audio_data = self._audio_buffer if self._audio_buffer else None
        
        if audio_data and len(audio_data) >= self.bytes_per_frame:
            # Convert bytes to numpy array - keep as 1D interleaved for PyAV
            samples = np.frombuffer(audio_data[:self.bytes_per_frame], dtype=np.int16)
            # Reshape to (1, total_samples) for PyAV - interleaved stereo
            samples = samples.reshape((1, -1))
        else:
            # Generate silent audio frame as fallback - interleaved format
            total_samples = self.samples_per_frame * self.channels
            samples = np.zeros((1, total_samples), dtype=np.int16)
        
        # Create AudioFrame with proper channel layout
        if self.channels == 1:
            layout = 'mono'
        else:
            layout = 'stereo'
        
        frame = AudioFrame.from_ndarray(samples, format='s16', layout=layout)
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
            has_audio = self._audio_process is not None and self._audio_process.poll() is None
            logger.debug(f"Audio track {self.session_id}: {self._frame_count} frames, capture active: {has_audio}")
        
        return frame
    
    def stop(self):
        """Stop the audio track and cleanup"""
        logger.info(f"Stopping BrowserAudioTrack for session {self.session_id}")
        self._running = False
        
        # Stop the audio capture process
        if self._audio_process:
            try:
                self._audio_process.terminate()
                self._audio_process.wait(timeout=2)
            except Exception as e:
                logger.debug(f"Error stopping audio process: {e}")
                try:
                    self._audio_process.kill()
                except:
                    pass
            self._audio_process = None
        
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
        
        # Create AudioFrame with proper channel layout
        if self.channels == 1:
            layout = 'mono'
        elif self.channels == 2:
            layout = 'stereo'
        else:
            # For unsupported channel counts, default to stereo
            layout = 'stereo'
        
        frame = AudioFrame.from_ndarray(samples, format='s16', layout=layout)
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
