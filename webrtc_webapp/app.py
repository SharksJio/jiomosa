"""
Jiomosa WebRTC WebApp
Modern Progressive Web App for Android with Material Design
"""
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os

app = FastAPI(title="Jiomosa WebApp")

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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9000)
