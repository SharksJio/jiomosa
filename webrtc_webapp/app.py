"""
Jiomosa WebRTC WebApp
Modern Progressive Web App for Android with Material Design
"""
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os
import httpx
import websockets
import asyncio
import json

app = FastAPI(title="Jiomosa WebApp")

# Timeout for proxying requests to renderer (browser initialization can be slow)
PROXY_TIMEOUT = 90.0

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

# Configuration
WEBRTC_SERVER = os.getenv('WEBRTC_SERVER', 'http://localhost:8000')

# Popular websites
WEBSITE_APPS = [
    {
        'id': 'youtube',
        'name': 'YouTube',
        'url': 'https://m.youtube.com',
        'icon': '▶️',
        'color': '#FF0000',
        'category': 'media'
    },
    {
        'id': 'facebook',
        'name': 'Facebook',
        'url': 'https://m.facebook.com',
        'icon': '📘',
        'color': '#1877F2',
        'category': 'social'
    },
    {
        'id': 'twitter',
        'name': 'X',
        'url': 'https://mobile.twitter.com',
        'icon': '𝕏',
        'color': '#000000',
        'category': 'social'
    },
    {
        'id': 'instagram',
        'name': 'Instagram',
        'url': 'https://www.instagram.com',
        'icon': '📷',
        'color': '#E4405F',
        'category': 'social'
    },
    {
        'id': 'reddit',
        'name': 'Reddit',
        'url': 'https://www.reddit.com',
        'icon': '🤖',
        'color': '#FF4500',
        'category': 'social'
    },
    {
        'id': 'linkedin',
        'name': 'LinkedIn',
        'url': 'https://www.linkedin.com',
        'icon': '💼',
        'color': '#0A66C2',
        'category': 'professional'
    },
    {
        'id': 'gmail',
        'name': 'Gmail',
        'url': 'https://mail.google.com',
        'icon': '📧',
        'color': '#EA4335',
        'category': 'productivity'
    },
    {
        'id': 'whatsapp',
        'name': 'WhatsApp',
        'url': 'https://web.whatsapp.com',
        'icon': '💬',
        'color': '#25D366',
        'category': 'social'
    },
    {
        'id': 'github',
        'name': 'GitHub',
        'url': 'https://github.com',
        'icon': '🐙',
        'color': '#181717',
        'category': 'developer'
    },
    {
        'id': 'amazon',
        'name': 'Amazon',
        'url': 'https://www.amazon.com',
        'icon': '🛒',
        'color': '#FF9900',
        'category': 'shopping'
    },
    {
        'id': 'netflix',
        'name': 'Netflix',
        'url': 'https://www.netflix.com',
        'icon': '🎬',
        'color': '#E50914',
        'category': 'media'
    },
    {
        'id': 'spotify',
        'name': 'Spotify',
        'url': 'https://open.spotify.com',
        'icon': '🎵',
        'color': '#1DB954',
        'category': 'media'
    },
]


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Home page with app launcher"""
    return templates.TemplateResponse("index.html", {
        "request": request,
        "apps": WEBSITE_APPS,
        "webrtc_server": WEBRTC_SERVER
    })


@app.get("/viewer", response_class=HTMLResponse)
async def viewer(request: Request, url: str):
    """WebRTC viewer page"""
    return templates.TemplateResponse("viewer.html", {
        "request": request,
        "url": url,
        "webrtc_server": WEBRTC_SERVER
    })


@app.get("/health")
async def health():
    """Health check"""
    return {"status": "healthy"}


# API Proxy endpoints - Forward requests from browser to webrtc-renderer
@app.post("/api/session/create")
async def proxy_create_session(request: Request):
    """Proxy session create to webrtc-renderer"""
    try:
        async with httpx.AsyncClient(timeout=PROXY_TIMEOUT) as client:
            body = await request.body()
            resp = await client.post(
                f"{WEBRTC_SERVER}/api/session/create",
                content=body,
                headers={"Content-Type": "application/json"}
            )
            return JSONResponse(content=resp.json(), status_code=resp.status_code)
    except httpx.ConnectError:
        return JSONResponse(
            content={"success": False, "error": "Cannot connect to webrtc-renderer service"},
            status_code=503
        )
    except httpx.TimeoutException:
        return JSONResponse(
            content={"success": False, "error": "Request to webrtc-renderer timed out"},
            status_code=504
        )
    except httpx.HTTPError as e:
        return JSONResponse(
            content={"success": False, "error": f"HTTP error: {str(e)}"},
            status_code=502
        )


@app.post("/api/session/{session_id}/load")
async def proxy_load_url(session_id: str, request: Request):
    """Proxy URL load to webrtc-renderer"""
    try:
        async with httpx.AsyncClient(timeout=PROXY_TIMEOUT) as client:
            body = await request.body()
            resp = await client.post(
                f"{WEBRTC_SERVER}/api/session/{session_id}/load",
                content=body,
                headers={"Content-Type": "application/json"}
            )
            return JSONResponse(content=resp.json(), status_code=resp.status_code)
    except httpx.ConnectError:
        return JSONResponse(
            content={"success": False, "error": "Cannot connect to webrtc-renderer service"},
            status_code=503
        )
    except httpx.TimeoutException:
        return JSONResponse(
            content={"success": False, "error": "Request to webrtc-renderer timed out"},
            status_code=504
        )
    except httpx.HTTPError as e:
        return JSONResponse(
            content={"success": False, "error": f"HTTP error: {str(e)}"},
            status_code=502
        )


@app.delete("/api/session/{session_id}")
async def proxy_close_session(session_id: str):
    """Proxy session close to webrtc-renderer"""
    try:
        async with httpx.AsyncClient(timeout=PROXY_TIMEOUT) as client:
            resp = await client.delete(f"{WEBRTC_SERVER}/api/session/{session_id}")
            return JSONResponse(content=resp.json(), status_code=resp.status_code)
    except httpx.ConnectError:
        return JSONResponse(
            content={"success": False, "error": "Cannot connect to webrtc-renderer service"},
            status_code=503
        )
    except httpx.TimeoutException:
        return JSONResponse(
            content={"success": False, "error": "Request to webrtc-renderer timed out"},
            status_code=504
        )
    except httpx.HTTPError as e:
        return JSONResponse(
            content={"success": False, "error": f"HTTP error: {str(e)}"},
            status_code=502
        )


@app.get("/api/sessions")
async def proxy_list_sessions():
    """Proxy sessions list to webrtc-renderer"""
    try:
        async with httpx.AsyncClient(timeout=PROXY_TIMEOUT) as client:
            resp = await client.get(f"{WEBRTC_SERVER}/api/sessions")
            return JSONResponse(content=resp.json(), status_code=resp.status_code)
    except httpx.ConnectError:
        return JSONResponse(
            content={"success": False, "error": "Cannot connect to webrtc-renderer service"},
            status_code=503
        )
    except httpx.TimeoutException:
        return JSONResponse(
            content={"success": False, "error": "Request to webrtc-renderer timed out"},
            status_code=504
        )
    except httpx.HTTPError as e:
        return JSONResponse(
            content={"success": False, "error": f"HTTP error: {str(e)}"},
            status_code=502
        )


# WebSocket proxy for signaling
@app.websocket("/ws/signaling")
async def websocket_signaling_proxy(websocket: WebSocket):
    """Proxy WebSocket signaling to webrtc-renderer"""
    await websocket.accept()
    
    # Convert http to ws for the backend URL
    ws_url = WEBRTC_SERVER.replace("http://", "ws://").replace("https://", "wss://") + "/ws/signaling"
    
    try:
        async with websockets.connect(ws_url) as backend_ws:
            async def forward_to_backend():
                try:
                    while True:
                        data = await websocket.receive_text()
                        await backend_ws.send(data)
                except WebSocketDisconnect:
                    pass
            
            async def forward_to_client():
                try:
                    async for message in backend_ws:
                        await websocket.send_text(message)
                except websockets.exceptions.ConnectionClosed:
                    pass
            
            # Run both directions concurrently
            await asyncio.gather(
                forward_to_backend(),
                forward_to_client(),
                return_exceptions=True
            )
    except websockets.exceptions.InvalidURI as e:
        try:
            await websocket.send_text(json.dumps({"type": "error", "message": f"Invalid backend URL: {str(e)}"}))
        except Exception:
            pass
    except websockets.exceptions.WebSocketException as e:
        try:
            await websocket.send_text(json.dumps({"type": "error", "message": f"WebSocket error: {str(e)}"}))
        except Exception:
            pass
    except OSError as e:
        try:
            await websocket.send_text(json.dumps({"type": "error", "message": f"Connection error: {str(e)}"}))
        except Exception:
            pass
    finally:
        try:
            await websocket.close()
        except Exception:
            pass


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9000)
