"""
WebRTC Peer Connection Management
Handles WebRTC signaling and peer connections
"""
import asyncio
import json
import logging
from typing import Dict, Optional
from datetime import datetime
from aiortc import RTCPeerConnection, RTCSessionDescription, RTCIceCandidate, RTCConfiguration, RTCIceServer
from aiortc.contrib.media import MediaBlackhole
from aiortc.sdp import candidate_from_sdp
from video_track import BrowserVideoTrack
from audio_track import BrowserAudioTrack
from browser_pool import browser_pool
from config import settings

logger = logging.getLogger(__name__)


class WebRTCPeer:
    """Manages a WebRTC peer connection for a session"""
    
    def __init__(self, session_id: str, peer_id: str):
        self.session_id = session_id
        self.peer_id = peer_id
        self.pc: Optional[RTCPeerConnection] = None
        self.video_track: Optional[BrowserVideoTrack] = None
        self.audio_track: Optional[BrowserAudioTrack] = None
        self.created_at = datetime.now()
        self.data_channel = None
        self._setup_peer_connection()
        
    def _setup_peer_connection(self):
        """Initialize RTCPeerConnection with STUN/TURN servers"""
        # Configure ICE servers
        ice_servers = [RTCIceServer(urls=[settings.stun_server])]
        
        if settings.turn_server:
            ice_servers.append(RTCIceServer(
                urls=[settings.turn_server],
                username=settings.turn_username,
                credential=settings.turn_password
            ))
        
        config = RTCConfiguration(iceServers=ice_servers)
        self.pc = RTCPeerConnection(configuration=config)
        
        # Set up event handlers
        @self.pc.on("connectionstatechange")
        async def on_connectionstatechange():
            logger.info(f"Connection state for {self.peer_id}: {self.pc.connectionState}")
            
            if self.pc.connectionState == "failed":
                await self.close()
        
        @self.pc.on("iceconnectionstatechange")
        async def on_iceconnectionstatechange():
            logger.info(f"ICE connection state for {self.peer_id}: {self.pc.iceConnectionState}")
        
        @self.pc.on("datachannel")
        def on_datachannel(channel):
            logger.info(f"Data channel established: {channel.label}, readyState: {channel.readyState}")
            self.data_channel = channel
            
            @channel.on("message")
            def on_message(message):
                logger.info(f"Received data channel message: {message}")
                asyncio.create_task(self._handle_data_channel_message(message))
            
            @channel.on("open")
            def on_open():
                logger.info(f"Data channel opened: {channel.label}")
            
            @channel.on("close")
            def on_close():
                logger.info(f"Data channel closed: {channel.label}")
        
        logger.info(f"WebRTC peer connection created for {self.peer_id}")
    
    async def _handle_data_channel_message(self, message: str):
        """Handle messages from the data channel (input events)"""
        try:
            data = json.loads(message)
            event_type = data.get('type')
            
            if event_type == 'click':
                x, y = data.get('x', 0), data.get('y', 0)
                await browser_pool.click(self.session_id, x, y)
                logger.info(f"Click at ({x}, {y}) in session {self.session_id}")
                
            elif event_type == 'scroll':
                delta_y = data.get('deltaY', 0)
                await browser_pool.scroll(self.session_id, delta_y)
                logger.info(f"Scroll by {delta_y} in session {self.session_id}")
                
            elif event_type == 'text':
                text = data.get('text', '')
                await browser_pool.type_text(self.session_id, text)
                logger.info(f"Typed text '{text}' in session {self.session_id}")
                
            elif event_type == 'key':
                key = data.get('key', '')
                await browser_pool.press_key(self.session_id, key)
                logger.info(f"Pressed key '{key}' in session {self.session_id}")
                
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in data channel message: {e}")
        except Exception as e:
            logger.error(f"Error handling data channel message: {e}")
    
    async def create_offer(self) -> dict:
        """Create WebRTC offer with video and audio tracks"""
        try:
            # Create video track
            self.video_track = BrowserVideoTrack(
                session_id=self.session_id,
                fps=settings.webrtc_framerate
            )
            
            # Create audio track
            self.audio_track = BrowserAudioTrack(
                session_id=self.session_id,
                sample_rate=settings.audio_sample_rate,
                channels=settings.audio_channels
            )
            
            # Add video track to peer connection
            self.pc.addTrack(self.video_track)
            
            # Add audio track to peer connection
            if settings.audio_enabled:
                self.pc.addTrack(self.audio_track)
                logger.info(f"Added audio track for peer {self.peer_id}")
            
            # Create data channel for input events
            self.data_channel = self.pc.createDataChannel("input")
            logger.info(f"Created data channel for input events, id: {id(self.data_channel)}, readyState: {self.data_channel.readyState}")
            
            # Set up handlers for the data channel we created
            @self.data_channel.on("open")
            def on_open():
                logger.info(f"Data channel opened (server-created)")
            
            @self.data_channel.on("close") 
            def on_close():
                logger.info(f"Data channel closed (server-created)")
            
            @self.data_channel.on("message")
            def on_message(message):
                logger.info(f"Received message on server-created channel: {message}")
                asyncio.create_task(self._handle_data_channel_message(message))
            
            # Create offer
            offer = await self.pc.createOffer()
            await self.pc.setLocalDescription(offer)
            
            logger.info(f"Created offer for peer {self.peer_id}")
            
            return {
                "sdp": self.pc.localDescription.sdp,
                "type": self.pc.localDescription.type
            }
            
        except Exception as e:
            logger.error(f"Error creating offer: {e}")
            raise
    
    async def set_answer(self, answer: dict):
        """Set remote description from answer"""
        try:
            rtc_answer = RTCSessionDescription(sdp=answer["sdp"], type=answer["type"])
            await self.pc.setRemoteDescription(rtc_answer)
            logger.info(f"Set answer for peer {self.peer_id}")
        except Exception as e:
            logger.error(f"Error setting answer: {e}")
            raise
    
    async def add_ice_candidate(self, candidate: dict):
        """Add ICE candidate"""
        try:
            # Parse the candidate SDP string into an RTCIceCandidate object
            candidate_sdp = candidate.get("candidate")
            if not candidate_sdp:
                logger.warning(f"Empty candidate received for peer {self.peer_id}")
                return
                
            ice_candidate = candidate_from_sdp(candidate_sdp)
            ice_candidate.sdpMid = candidate.get("sdpMid")
            ice_candidate.sdpMLineIndex = candidate.get("sdpMLineIndex")
            
            await self.pc.addIceCandidate(ice_candidate)
            logger.info(f"Added ICE candidate for peer {self.peer_id}")
        except Exception as e:
            logger.error(f"Error adding ICE candidate: {e}")
            raise
    
    async def close(self):
        """Close the peer connection"""
        logger.info(f"Closing peer connection {self.peer_id}")
        
        if self.video_track:
            self.video_track.stop()
        
        if self.audio_track:
            self.audio_track.stop()
        
        if self.pc:
            await self.pc.close()


class WebRTCManager:
    """Manages all WebRTC peer connections"""
    
    def __init__(self):
        self.peers: Dict[str, WebRTCPeer] = {}
        self._lock = asyncio.Lock()
    
    async def create_peer(self, session_id: str, peer_id: str) -> WebRTCPeer:
        """Create a new peer connection"""
        async with self._lock:
            if peer_id in self.peers:
                logger.warning(f"Peer {peer_id} already exists, closing old connection")
                await self.close_peer(peer_id)
            
            peer = WebRTCPeer(session_id, peer_id)
            self.peers[peer_id] = peer
            logger.info(f"Created WebRTC peer {peer_id} for session {session_id}")
            return peer
    
    async def get_peer(self, peer_id: str) -> Optional[WebRTCPeer]:
        """Get an existing peer connection"""
        return self.peers.get(peer_id)
    
    async def close_peer(self, peer_id: str):
        """Close a peer connection and cleanup associated browser session"""
        async with self._lock:
            if peer_id not in self.peers:
                logger.warning(f"Peer {peer_id} not found")
                return
            
            peer = self.peers[peer_id]
            session_id = peer.session_id
            
            await peer.close()
            del self.peers[peer_id]
            logger.info(f"Closed peer {peer_id}")
        
        # Cleanup browser session after releasing the lock
        if session_id:
            from browser_pool import browser_pool
            logger.info(f"Cleaning up browser session {session_id} for closed peer {peer_id}")
            await browser_pool.close_session(session_id)
    
    async def close_all_peers_for_session(self, session_id: str):
        """Close all peer connections for a session"""
        peers_to_close = [
            peer_id for peer_id, peer in self.peers.items()
            if peer.session_id == session_id
        ]
        
        for peer_id in peers_to_close:
            await self.close_peer(peer_id)
    
    async def get_stats(self) -> dict:
        """Get statistics about active peers"""
        return {
            'active_peers': len(self.peers),
            'peers': {
                peer_id: {
                    'session_id': peer.session_id,
                    'connection_state': peer.pc.connectionState if peer.pc else 'unknown',
                    'created_at': peer.created_at.isoformat()
                }
                for peer_id, peer in self.peers.items()
            }
        }
    
    async def shutdown(self):
        """Close all peer connections"""
        logger.info("Shutting down WebRTC manager...")
        peer_ids = list(self.peers.keys())
        for peer_id in peer_ids:
            await self.close_peer(peer_id)
        logger.info("WebRTC manager shutdown complete")


# Global WebRTC manager instance
webrtc_manager = WebRTCManager()
