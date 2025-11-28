"""
Jiomosa WebRTC Renderer - Main Application
Production-quality WebRTC streaming server for desktop browsers
"""
import asyncio
import logging
import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, HttpUrl
from typing import Optional, Dict, Any
import json

from config import settings
from browser_pool import browser_pool
from webrtc_manager import webrtc_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.debug else logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Lifespan context manager for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    # Startup
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    
    # Initialize browser pool
    await browser_pool.initialize()
    
    # Start cleanup task
    async def cleanup_task():
        while True:
            await asyncio.sleep(settings.session_cleanup_interval)
            await browser_pool.cleanup_stale_sessions()
    
    cleanup_task_handle = asyncio.create_task(cleanup_task())
    
    logger.info("Application startup complete")
    
    yield
    
    # Shutdown
    logger.info("Shutting down application...")
    cleanup_task_handle.cancel()
    await webrtc_manager.shutdown()
    await browser_pool.shutdown()
    logger.info("Application shutdown complete")


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Production-quality WebRTC streaming server for rendering desktop websites",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic models
class SessionCreate(BaseModel):
    session_id: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None


class URLLoad(BaseModel):
    url: HttpUrl


class WebRTCOffer(BaseModel):
    sdp: str
    type: str


class WebRTCAnswer(BaseModel):
    sdp: str
    type: str


class ICECandidate(BaseModel):
    candidate: str
    sdpMid: Optional[str] = None
    sdpMLineIndex: Optional[int] = None


# REST API Endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": settings.app_version,
        "timestamp": asyncio.get_event_loop().time()
    }


@app.get("/api/info")
async def get_info():
    """Get service information"""
    browser_stats = await browser_pool.get_stats()
    webrtc_stats = await webrtc_manager.get_stats()
    
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "webrtc": {
            "video": {
                "codec": settings.webrtc_video_codec,
                "resolution": f"{settings.webrtc_video_width}x{settings.webrtc_video_height}",
                "framerate": settings.webrtc_framerate,
                "bitrate_range": f"{settings.webrtc_min_bitrate}-{settings.webrtc_max_bitrate} bps"
            },
            "audio": {
                "enabled": settings.audio_enabled,
                "sample_rate": settings.audio_sample_rate,
                "channels": settings.audio_channels,
                "codec": "opus"  # WebRTC uses Opus codec for audio
            }
        },
        "browser": browser_stats,
        "connections": webrtc_stats,
        "endpoints": {
            "rest": {
                "create_session": "POST /api/session/create",
                "load_url": "POST /api/session/{session_id}/load",
                "close_session": "DELETE /api/session/{session_id}",
                "list_sessions": "GET /api/sessions"
            },
            "websocket": "WS /ws/signaling"
        }
    }


@app.post("/api/session/create")
async def create_session(data: SessionCreate):
    """Create a new browser session with optional custom viewport"""
    try:
        session_id = data.session_id or str(uuid.uuid4())
        
        # Create browser session with optional custom dimensions
        page = await browser_pool.create_session(
            session_id,
            width=data.width,
            height=data.height
        )
        
        viewport = page.viewport_size
        logger.info(f"Created session {session_id} with viewport {viewport}")
        
        return {
            "success": True,
            "session_id": session_id,
            "viewport": viewport,
            "websocket_url": f"/ws/signaling",
            "message": "Session created. Connect via WebSocket to start WebRTC streaming."
        }
        
    except Exception as e:
        logger.error(f"Failed to create session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/session/{session_id}/load")
async def load_url(session_id: str, data: URLLoad):
    """Load a URL in the session"""
    try:
        success = await browser_pool.navigate(session_id, str(data.url))
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to load URL")
        
        logger.info(f"Loaded {data.url} in session {session_id}")
        
        return {
            "success": True,
            "session_id": session_id,
            "url": str(data.url),
            "message": "URL loaded successfully"
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to load URL: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/session/{session_id}")
async def close_session(session_id: str):
    """Close a browser session"""
    try:
        # Close all WebRTC peers for this session
        await webrtc_manager.close_all_peers_for_session(session_id)
        
        # Close browser session
        await browser_pool.close_session(session_id)
        
        logger.info(f"Closed session {session_id}")
        
        return {
            "success": True,
            "session_id": session_id,
            "message": "Session closed successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to close session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/sessions")
async def list_sessions():
    """List all active sessions"""
    stats = await browser_pool.get_stats()
    return {
        "success": True,
        "sessions": stats
    }


# WebSocket endpoint for WebRTC signaling
@app.websocket("/ws/signaling")
async def websocket_signaling(websocket: WebSocket):
    """
    WebSocket endpoint for WebRTC signaling
    Handles offer/answer exchange and ICE candidate exchange
    """
    await websocket.accept()
    peer_id = str(uuid.uuid4())
    session_id = None
    
    logger.info(f"WebSocket connection established: {peer_id}")
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            msg_type = message.get("type")
            logger.debug(f"Received message type: {msg_type}")
            
            if msg_type == "join":
                # Client wants to join a session
                session_id = message.get("session_id")
                
                if not session_id:
                    await websocket.send_json({
                        "type": "error",
                        "message": "session_id is required"
                    })
                    continue
                
                # Verify session exists
                page = await browser_pool.get_page(session_id)
                if not page:
                    await websocket.send_json({
                        "type": "error",
                        "message": f"Session {session_id} not found"
                    })
                    continue
                
                # Create WebRTC peer
                peer = await webrtc_manager.create_peer(session_id, peer_id)
                
                # Create and send offer
                offer = await peer.create_offer()
                
                await websocket.send_json({
                    "type": "offer",
                    "offer": offer
                })
                
                logger.info(f"Sent offer to client {peer_id} for session {session_id}")
            
            elif msg_type == "answer":
                # Client sent answer to our offer
                answer = message.get("answer")
                
                if not answer:
                    await websocket.send_json({
                        "type": "error",
                        "message": "answer is required"
                    })
                    continue
                
                peer = await webrtc_manager.get_peer(peer_id)
                if not peer:
                    await websocket.send_json({
                        "type": "error",
                        "message": "Peer not found"
                    })
                    continue
                
                await peer.set_answer(answer)
                
                await websocket.send_json({
                    "type": "ready",
                    "message": "WebRTC connection established"
                })
                
                logger.info(f"WebRTC connection established for peer {peer_id}")
            
            elif msg_type == "ice-candidate":
                # Client sent ICE candidate
                candidate = message.get("candidate")
                
                if not candidate:
                    continue
                
                peer = await webrtc_manager.get_peer(peer_id)
                if peer:
                    await peer.add_ice_candidate(candidate)
            
            elif msg_type == "ping":
                # Keep-alive ping
                await websocket.send_json({"type": "pong"})
            
            else:
                logger.warning(f"Unknown message type: {msg_type}")
                await websocket.send_json({
                    "type": "error",
                    "message": f"Unknown message type: {msg_type}"
                })
    
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {peer_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        # Cleanup
        await webrtc_manager.close_peer(peer_id)
        logger.info(f"Cleaned up peer {peer_id}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="debug" if settings.debug else "info"
    )
