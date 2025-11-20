"""
WebSocket Handler for Real-time Frame Streaming
Handles bidirectional communication between client and browser session
"""
import logging
import time
from io import BytesIO
from PIL import Image
import base64

logger = logging.getLogger(__name__)


class BandwidthMonitor:
    """Monitor bandwidth and adapt quality accordingly"""
    
    def __init__(self, client_id):
        self.client_id = client_id
        self.frame_times = []  # (timestamp, frame_size) tuples
        self.max_history = 30  # Keep last 30 frames
        self.last_adjustment = time.time()
        self.adjustment_interval = 5  # Adjust every 5 seconds
        
        # Quality tiers (Mbps thresholds)
        self.fast_threshold = 5.0  # >5 Mbps
        self.normal_threshold = 2.0  # 2-5 Mbps
        self.slow_threshold = 1.0  # <2 Mbps
    
    def record_frame(self, frame_size_bytes):
        """Record frame transmission"""
        self.frame_times.append((time.time(), frame_size_bytes))
        
        # Keep only recent history
        if len(self.frame_times) > self.max_history:
            self.frame_times.pop(0)
    
    def get_bandwidth_mbps(self):
        """Calculate current bandwidth in Mbps"""
        if len(self.frame_times) < 2:
            return 5.0  # Default to fast
        
        try:
            oldest_time, _ = self.frame_times[0]
            newest_time, _ = self.frame_times[-1]
            time_delta = newest_time - oldest_time
            
            if time_delta < 0.1:  # Need at least 100ms of data
                return 5.0
            
            # Calculate total bytes transferred
            total_bytes = sum(size for _, size in self.frame_times)
            
            # Convert to bits and divide by time in seconds
            total_bits = total_bytes * 8
            bandwidth_bps = total_bits / time_delta
            bandwidth_mbps = bandwidth_bps / 1_000_000
            
            return max(0.5, min(50.0, bandwidth_mbps))  # Clamp 0.5-50 Mbps
        except Exception as e:
            logger.error(f"Error calculating bandwidth: {e}")
            return 5.0
    
    def get_recommended_quality(self):
        """Get recommended JPEG quality based on bandwidth"""
        bandwidth = self.get_bandwidth_mbps()
        
        if bandwidth > self.fast_threshold:
            return 90  # High quality for fast connections
        elif bandwidth > self.normal_threshold:
            return 75  # Medium quality for normal connections
        else:
            return 50  # Lower quality for slow connections
    
    def get_recommended_fps(self):
        """Get recommended FPS based on bandwidth"""
        bandwidth = self.get_bandwidth_mbps()
        
        # Default to higher FPS for local/fast connections
        if bandwidth > self.fast_threshold:
            return 30  # Full FPS for fast connections
        elif bandwidth > self.normal_threshold:
            return 30  # Keep 30 FPS for normal connections
        else:
            return 20  # Still decent FPS for slower connections
    
    def should_adjust(self):
        """Check if it's time to adjust quality"""
        now = time.time()
        if now - self.last_adjustment >= self.adjustment_interval:
            self.last_adjustment = now
            return True
        return False


class FrameDelta:
    """Detect and encode only changed pixels between frames"""
    
    def __init__(self, width=1920, height=1080):
        self.last_frame = None
        self.width = width
        self.height = height
        self.threshold = 20  # Pixel difference threshold
    
    def has_changed(self, new_frame_data):
        """Check if frame has significant changes"""
        if self.last_frame is None:
            return True
        
        try:
            # Quick comparison - sample every 10th pixel
            if len(new_frame_data) != len(self.last_frame):
                return True
            
            sample_rate = 10
            for i in range(0, len(new_frame_data), sample_rate):
                if abs(new_frame_data[i] - self.last_frame[i]) > self.threshold:
                    return True
            
            return False
        except Exception as e:
            logger.error(f"Error comparing frames: {e}")
            return True
    
    def get_delta(self, new_frame_data):
        """Get compressed delta of changed pixels"""
        self.last_frame = new_frame_data
        return new_frame_data  # For now, return full frame (can optimize later)


class WebSocketHandler:
    """Manages WebSocket communication for frame streaming"""
    
    def __init__(self, socketio, active_sessions):
        self.socketio = socketio
        self.active_sessions = active_sessions
        self.frame_deltas = {}  # Per-session frame delta trackers
        self.client_quality = {}  # Per-client quality settings
        self.client_fps = {}  # Per-client FPS settings
        self.client_sessions = {}  # Track which session each client is subscribed to
        self.bandwidth_monitors = {}  # Per-client bandwidth monitor
        self.adaptive_mode = {}  # Per-client adaptive mode enabled
    
    def handle_subscribe(self, client_id, session_id, emit_func):
        """Handle client subscription to a session"""
        try:
            # Initialize frame delta tracker
            if session_id not in self.frame_deltas:
                self.frame_deltas[session_id] = FrameDelta()
            
            self.client_quality[client_id] = 75  # Start with moderate quality for better FPS
            self.client_fps[client_id] = 30  # Start with 30 FPS for responsive streaming
            self.client_sessions[client_id] = session_id
            self.bandwidth_monitors[client_id] = BandwidthMonitor(client_id)
            self.adaptive_mode[client_id] = True  # Enable by default
            
            logger.info(f"Client {client_id} subscribed to session {session_id} (adaptive mode: ON)")
            emit_func('subscribe:response', {
                'session_id': session_id,
                'fps': self.client_fps[client_id],
                'quality': self.client_quality[client_id],
                'adaptive_mode': True
            })
            
        except Exception as e:
            logger.error(f"Error subscribing: {e}")
            emit_func('error', {'message': str(e)})
    
    def handle_unsubscribe(self, client_id):
        """Handle client unsubscription"""
        try:
            session_id = self.client_sessions.get(client_id)
            
            if client_id in self.client_quality:
                del self.client_quality[client_id]
            
            if client_id in self.client_fps:
                del self.client_fps[client_id]
            
            if client_id in self.client_sessions:
                del self.client_sessions[client_id]
            
            if client_id in self.bandwidth_monitors:
                del self.bandwidth_monitors[client_id]
            
            if client_id in self.adaptive_mode:
                del self.adaptive_mode[client_id]
            
            logger.info(f"Client {client_id} unsubscribed from session {session_id}")
            
        except Exception as e:
            logger.error(f"Error unsubscribing: {e}")
    
    def get_session_id_for_client(self, client_id):
        """Get the session ID for a client"""
        return self.client_sessions.get(client_id)
    
    def record_frame_sent(self, client_id, frame_size_bytes):
        """Record frame transmission for bandwidth calculation"""
        if client_id in self.bandwidth_monitors:
            monitor = self.bandwidth_monitors[client_id]
            monitor.record_frame(frame_size_bytes)
            
            # Check if we should adapt quality
            if self.adaptive_mode.get(client_id, False) and monitor.should_adjust():
                new_quality = monitor.get_recommended_quality()
                new_fps = monitor.get_recommended_fps()
                
                old_quality = self.client_quality.get(client_id, 85)
                old_fps = self.client_fps.get(client_id, 30)
                
                # Only log if changed
                if new_quality != old_quality or new_fps != old_fps:
                    bandwidth = monitor.get_bandwidth_mbps()
                    logger.info(
                        f"Client {client_id} bandwidth: {bandwidth:.2f} Mbps | "
                        f"Quality: {old_quality}→{new_quality}, FPS: {old_fps}→{new_fps}"
                    )
                    self.client_quality[client_id] = new_quality
                    self.client_fps[client_id] = new_fps
    
    def set_quality(self, client_id, quality):
        """Set JPEG quality for a client (disables adaptive mode for this setting)"""
        quality = max(1, min(100, quality))
        self.client_quality[client_id] = quality
        self.adaptive_mode[client_id] = False  # Disable adaptive when manually set
        logger.info(f"Client {client_id} quality set to {quality} (adaptive mode: OFF)")
    
    def set_fps(self, client_id, fps):
        """Set FPS for a client (disables adaptive mode for this setting)"""
        fps = max(1, min(60, fps))
        self.client_fps[client_id] = fps
        self.adaptive_mode[client_id] = False  # Disable adaptive when manually set
        logger.info(f"Client {client_id} FPS set to {fps} (adaptive mode: OFF)")
    
    def toggle_adaptive_mode(self, client_id, enabled):
        """Toggle adaptive quality mode"""
        self.adaptive_mode[client_id] = enabled
        logger.info(f"Client {client_id} adaptive mode: {'ON' if enabled else 'OFF'}")
    
    def encode_frame_for_websocket(self, frame_data, client_id):
        """Encode frame as base64 for WebSocket transmission - optimized for speed"""
        try:
            quality = self.client_quality.get(client_id, 75)
            
            # Convert PNG to JPEG with adjustable quality
            # Use fastest PIL settings for better FPS
            img = Image.open(BytesIO(frame_data))
            
            # Convert to RGB if necessary (some screenshots might be RGBA)
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Optimize size with quality - disable optimize flag for speed
            buffer = BytesIO()
            img.save(buffer, format='JPEG', quality=quality, optimize=False)
            buffer.seek(0)
            
            # Encode as base64 for WebSocket
            encoded = base64.b64encode(buffer.getvalue()).decode('utf-8')
            
            # Record transmission for bandwidth monitoring
            self.record_frame_sent(client_id, len(encoded))
            
            return encoded, len(encoded)
            
        except Exception as e:
            logger.error(f"Error encoding frame: {e}")
            return None, 0


def create_websocket_handler(socketio, active_sessions):
    """Factory function to create WebSocket handler"""
    return WebSocketHandler(socketio, active_sessions)
