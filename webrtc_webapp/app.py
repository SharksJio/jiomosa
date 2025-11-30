"""
JioCloudApps WebRTC WebApp
Modern Progressive Web App for Android with Material Design
User Authentication and Session Management
"""
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect, Depends, HTTPException, status, Form
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os
import httpx
import websockets
import asyncio
import json
from typing import Optional
from contextlib import asynccontextmanager

from models import UserCreate, UserLogin, UserResponse, SessionCreate, SessionResponse
from auth import (
    init_db, create_user, authenticate_user, create_access_token,
    get_current_user, get_current_user_required, get_user_by_username,
    get_user_sessions, get_session_by_url, get_session_by_id,
    create_browser_session, update_session_renderer_id, update_session_access_time,
    close_browser_session, clear_all_user_sessions
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - initialize database on startup"""
    await init_db()
    yield


app = FastAPI(title="JioCloudApps WebApp", lifespan=lifespan)

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
        'url': 'https://www.youtube.com',
        'icon': '▶️',
        'color': '#FF0000',
        'category': 'media'
    },
    {
        'id': 'facebook',
        'name': 'Facebook',
        'url': 'https://www.facebook.com',
        'icon': '📘',
        'color': '#1877F2',
        'category': 'social'
    },
    {
        'id': 'twitter',
        'name': 'X',
        'url': 'https://twitter.com',
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


# ============ Authentication Routes ============

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Login page"""
    user = await get_current_user(request)
    if user:
        return RedirectResponse(url="/", status_code=302)
    return templates.TemplateResponse("login.html", {"request": request, "error": None})


@app.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    """Handle login form submission"""
    user = await authenticate_user(username, password)
    if not user:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Invalid username or password"
        })
    
    # Create access token
    access_token = create_access_token(data={"sub": user.id})
    
    # Set cookie and redirect
    response = RedirectResponse(url="/", status_code=303)
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=30 * 24 * 60 * 60,  # 30 days
        samesite="lax",
        path="/"
    )
    return response


@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    """Registration page"""
    user = await get_current_user(request)
    if user:
        return RedirectResponse(url="/", status_code=302)
    return templates.TemplateResponse("register.html", {"request": request, "error": None})


@app.post("/register")
async def register(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...)
):
    """Handle registration form submission"""
    # Validate passwords match
    if password != confirm_password:
        return templates.TemplateResponse("register.html", {
            "request": request,
            "error": "Passwords do not match"
        })
    
    # Check if username exists
    existing_user = await get_user_by_username(username)
    if existing_user:
        return templates.TemplateResponse("register.html", {
            "request": request,
            "error": "Username already exists"
        })
    
    # Create user
    try:
        user_data = UserCreate(username=username, email=email, password=password)
        user = await create_user(user_data)
        
        # Create access token and login
        access_token = create_access_token(data={"sub": user.id})
        response = RedirectResponse(url="/", status_code=302)
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            max_age=30 * 24 * 60 * 60,
            samesite="lax",
            path="/"
        )
        return response
    except Exception as e:
        return templates.TemplateResponse("register.html", {
            "request": request,
            "error": f"Registration failed: {str(e)}"
        })


@app.get("/logout")
async def logout():
    """Logout user"""
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie("access_token")
    return response


# ============ Main Pages ============

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Home page with app launcher"""
    user = await get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    
    # Get user's active sessions
    sessions = await get_user_sessions(user.id)
    
    return templates.TemplateResponse("index.html", {
        "request": request,
        "apps": WEBSITE_APPS,
        "webrtc_server": WEBRTC_SERVER,
        "user": user,
        "sessions": sessions
    })


@app.get("/viewer", response_class=HTMLResponse)
async def viewer(request: Request, url: str):
    """WebRTC viewer page"""
    user = await get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    
    # Check for existing session for this URL
    existing_session = await get_session_by_url(user.id, url)
    
    # Convert to dict for JSON serialization in template
    existing_session_dict = None
    if existing_session:
        existing_session_dict = {
            "id": existing_session.id,
            "url": existing_session.url,
            "renderer_session_id": existing_session.renderer_session_id,
            "title": existing_session.title,
            "created_at": existing_session.created_at.isoformat(),
            "last_accessed": existing_session.last_accessed.isoformat(),
            "is_active": existing_session.is_active
        }
    
    return templates.TemplateResponse("viewer.html", {
        "request": request,
        "url": url,
        "webrtc_server": WEBRTC_SERVER,
        "user": user,
        "existing_session": existing_session_dict
    })


@app.get("/health")
async def health():
    """Health check"""
    return {"status": "healthy"}


# ============ User Session Management API ============

@app.get("/api/user/sessions")
async def get_my_sessions(request: Request):
    """Get current user's browser sessions"""
    user = await get_current_user(request)
    if not user:
        return JSONResponse(content={"success": False, "error": "Not authenticated"}, status_code=401)
    
    sessions = await get_user_sessions(user.id)
    return {
        "success": True,
        "sessions": [
            {
                "id": s.id,
                "url": s.url,
                "renderer_session_id": s.renderer_session_id,
                "title": s.title,
                "created_at": s.created_at.isoformat(),
                "last_accessed": s.last_accessed.isoformat(),
                "is_active": s.is_active
            }
            for s in sessions
        ]
    }


@app.post("/api/user/sessions")
async def create_my_session(request: Request):
    """Create or get existing session for a URL"""
    user = await get_current_user(request)
    if not user:
        return JSONResponse(content={"success": False, "error": "Not authenticated"}, status_code=401)
    
    body = await request.json()
    url = body.get("url")
    renderer_session_id = body.get("renderer_session_id")
    
    if not url:
        return JSONResponse(content={"success": False, "error": "URL required"}, status_code=400)
    
    # Check for existing session
    existing = await get_session_by_url(user.id, url)
    if existing:
        # Update renderer session ID if provided
        if renderer_session_id:
            await update_session_renderer_id(existing.id, renderer_session_id)
            existing.renderer_session_id = renderer_session_id
        else:
            await update_session_access_time(existing.id)
        
        return {
            "success": True,
            "session": {
                "id": existing.id,
                "url": existing.url,
                "renderer_session_id": existing.renderer_session_id,
                "is_new": False
            }
        }
    
    # Create new session
    session = await create_browser_session(user.id, url, renderer_session_id)
    return {
        "success": True,
        "session": {
            "id": session.id,
            "url": session.url,
            "renderer_session_id": session.renderer_session_id,
            "is_new": True
        }
    }


@app.delete("/api/user/sessions/{session_id}")
async def close_my_session(session_id: str, request: Request):
    """Close a specific browser session"""
    user = await get_current_user(request)
    if not user:
        return JSONResponse(content={"success": False, "error": "Not authenticated"}, status_code=401)
    
    session = await get_session_by_id(session_id)
    if not session or session.user_id != user.id:
        return JSONResponse(content={"success": False, "error": "Session not found"}, status_code=404)
    
    # Close renderer session if exists
    if session.renderer_session_id:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                await client.delete(f"{WEBRTC_SERVER}/api/session/{session.renderer_session_id}")
        except Exception:
            pass  # Ignore renderer errors
    
    await close_browser_session(session_id)
    return {"success": True, "message": "Session closed"}


@app.delete("/api/user/sessions")
async def clear_my_sessions(request: Request):
    """Clear all browser sessions for current user"""
    user = await get_current_user(request)
    if not user:
        return JSONResponse(content={"success": False, "error": "Not authenticated"}, status_code=401)
    
    # Get all active sessions to close renderer sessions
    sessions = await get_user_sessions(user.id)
    for session in sessions:
        if session.renderer_session_id:
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    await client.delete(f"{WEBRTC_SERVER}/api/session/{session.renderer_session_id}")
            except Exception:
                pass
    
    await clear_all_user_sessions(user.id)
    return {"success": True, "message": "All sessions cleared"}


@app.get("/api/user/me")
async def get_current_user_info(request: Request):
    """Get current user info"""
    user = await get_current_user(request)
    if not user:
        return JSONResponse(content={"success": False, "error": "Not authenticated"}, status_code=401)
    
    return {
        "success": True,
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email
        }
    }


# ============ Renderer Proxy Endpoints ============

@app.post("/api/session/create")
async def proxy_create_session(request: Request):
    """Proxy session create to webrtc-renderer"""
    user = await get_current_user(request)
    if not user:
        return JSONResponse(content={"success": False, "error": "Not authenticated"}, status_code=401)
    
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
    user = await get_current_user(request)
    if not user:
        return JSONResponse(content={"success": False, "error": "Not authenticated"}, status_code=401)
    
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
async def proxy_close_session(session_id: str, request: Request):
    """Proxy session close to webrtc-renderer"""
    user = await get_current_user(request)
    if not user:
        return JSONResponse(content={"success": False, "error": "Not authenticated"}, status_code=401)
    
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
async def proxy_list_sessions(request: Request):
    """Proxy sessions list to webrtc-renderer"""
    user = await get_current_user(request)
    if not user:
        return JSONResponse(content={"success": False, "error": "Not authenticated"}, status_code=401)
    
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


# ============ WebSocket Proxy ============

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
