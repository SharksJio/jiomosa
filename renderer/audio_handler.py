"""
Audio Handler for KaiOS Client
Captures audio from browser sessions and streams to clients via WebSocket
"""
import logging
import time
import threading
import base64
import struct
from io import BytesIO

logger = logging.getLogger(__name__)


class AudioChunk:
    """Represents an audio chunk for streaming"""
    
    def __init__(self, data, sample_rate=44100, channels=1, bits_per_sample=16):
        self.data = data
        self.sample_rate = sample_rate
        self.channels = channels
        self.bits_per_sample = bits_per_sample
        self.timestamp = time.time()


class AudioCapture:
    """
    Captures audio from Chrome browser.
    
    Note: Chrome in Selenium runs headless without audio output.
    This class provides infrastructure for audio streaming when available.
    
    Options for audio capture:
    1. Chrome with --use-fake-device-for-media-stream for test tones
    2. PulseAudio virtual sink capture (requires system audio config)
    3. CDP Audio capturing (experimental)
    """
    
    def __init__(self, session_id, driver=None):
        self.session_id = session_id
        self.driver = driver
        self.capturing = False
        self.capture_thread = None
        self.audio_buffer = []
        self.buffer_lock = threading.Lock()
        self.max_buffer_size = 100  # Keep last 100 chunks
        self.sample_rate = 44100
        self.channels = 1
        self.bits_per_sample = 16
        
    def start_capture(self):
        """Start audio capture"""
        if self.capturing:
            return
            
        self.capturing = True
        logger.info(f"[Audio] Starting capture for session {self.session_id}")
        
        # For now, we'll generate silence or test tone
        # Real implementation would use PulseAudio or CDP
        self.capture_thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.capture_thread.start()
        
    def stop_capture(self):
        """Stop audio capture"""
        self.capturing = False
        logger.info(f"[Audio] Stopping capture for session {self.session_id}")
        
    def _capture_loop(self):
        """Main capture loop"""
        chunk_duration = 0.1  # 100ms chunks
        samples_per_chunk = int(self.sample_rate * chunk_duration)
        
        while self.capturing:
            try:
                # Generate a simple test tone or silence
                # In a real implementation, this would capture from PulseAudio
                audio_data = self._generate_silence(samples_per_chunk)
                
                chunk = AudioChunk(
                    data=audio_data,
                    sample_rate=self.sample_rate,
                    channels=self.channels,
                    bits_per_sample=self.bits_per_sample
                )
                
                with self.buffer_lock:
                    self.audio_buffer.append(chunk)
                    # Trim buffer if too large
                    while len(self.audio_buffer) > self.max_buffer_size:
                        self.audio_buffer.pop(0)
                        
                time.sleep(chunk_duration)
                
            except Exception as e:
                logger.error(f"[Audio] Capture error: {e}")
                time.sleep(0.1)
                
    def _generate_silence(self, num_samples):
        """Generate silence (all zeros)"""
        return bytes(num_samples * 2)  # 16-bit samples = 2 bytes each
        
    def _generate_test_tone(self, num_samples, frequency=440):
        """Generate a test tone (sine wave)"""
        import math
        data = bytearray()
        for i in range(num_samples):
            # Generate sine wave sample
            t = i / self.sample_rate
            value = int(32767 * 0.5 * math.sin(2 * math.pi * frequency * t))
            # Pack as signed 16-bit little-endian
            data.extend(struct.pack('<h', value))
        return bytes(data)
        
    def get_chunk(self):
        """Get next audio chunk from buffer"""
        with self.buffer_lock:
            if self.audio_buffer:
                return self.audio_buffer.pop(0)
        return None
        
    def get_all_chunks(self):
        """Get all available audio chunks"""
        with self.buffer_lock:
            chunks = self.audio_buffer[:]
            self.audio_buffer.clear()
            return chunks


class AudioStreamer:
    """
    Manages audio streaming to connected clients.
    Provides WebSocket audio endpoint for KaiOS client.
    """
    
    def __init__(self, socketio, active_sessions):
        self.socketio = socketio
        self.active_sessions = active_sessions
        self.audio_captures = {}  # session_id -> AudioCapture
        self.client_audio_sessions = {}  # client_id -> session_id
        self.streaming = False
        self.stream_thread = None
        
    def start_streaming(self):
        """Start the audio streaming thread"""
        if self.streaming:
            return
            
        self.streaming = True
        self.stream_thread = threading.Thread(target=self._stream_loop, daemon=True)
        self.stream_thread.start()
        logger.info("[AudioStreamer] Streaming thread started")
        
    def stop_streaming(self):
        """Stop the audio streaming thread"""
        self.streaming = False
        logger.info("[AudioStreamer] Streaming thread stopped")
        
    def subscribe_client(self, client_id, session_id):
        """Subscribe a client to audio from a session"""
        if session_id not in self.audio_captures:
            # Create audio capture for this session
            session = self.active_sessions.get(session_id)
            driver = session.driver if session else None
            self.audio_captures[session_id] = AudioCapture(session_id, driver)
            self.audio_captures[session_id].start_capture()
            
        self.client_audio_sessions[client_id] = session_id
        logger.info(f"[AudioStreamer] Client {client_id} subscribed to audio from session {session_id}")
        
    def unsubscribe_client(self, client_id):
        """Unsubscribe a client from audio"""
        session_id = self.client_audio_sessions.pop(client_id, None)
        
        # Check if any other clients are listening to this session
        if session_id:
            other_clients = [c for c, s in self.client_audio_sessions.items() if s == session_id]
            if not other_clients:
                # No more clients, stop capture
                if session_id in self.audio_captures:
                    self.audio_captures[session_id].stop_capture()
                    del self.audio_captures[session_id]
                    
        logger.info(f"[AudioStreamer] Client {client_id} unsubscribed from audio")
        
    def _stream_loop(self):
        """Main streaming loop - sends audio chunks to subscribed clients"""
        while self.streaming:
            try:
                # For each session with audio capture
                for session_id, capture in list(self.audio_captures.items()):
                    chunks = capture.get_all_chunks()
                    if not chunks:
                        continue
                        
                    # Find clients subscribed to this session
                    clients = [c for c, s in self.client_audio_sessions.items() if s == session_id]
                    if not clients:
                        continue
                        
                    # Combine chunks into a single payload
                    combined_data = b''.join(chunk.data for chunk in chunks)
                    
                    # Encode for transmission
                    audio_payload = {
                        'session_id': session_id,
                        'data': base64.b64encode(combined_data).decode('utf-8'),
                        'sample_rate': capture.sample_rate,
                        'channels': capture.channels,
                        'format': 'pcm16',
                        'timestamp': time.time()
                    }
                    
                    # Send to each client
                    for client_id in clients:
                        try:
                            self.socketio.emit('audio', audio_payload, room=client_id)
                        except Exception as e:
                            logger.error(f"[AudioStreamer] Error sending to client {client_id}: {e}")
                            
                time.sleep(0.05)  # 50ms interval for low latency
                
            except Exception as e:
                logger.error(f"[AudioStreamer] Stream loop error: {e}")
                time.sleep(0.1)


def create_audio_streamer(socketio, active_sessions):
    """Factory function to create AudioStreamer"""
    streamer = AudioStreamer(socketio, active_sessions)
    streamer.start_streaming()
    return streamer
