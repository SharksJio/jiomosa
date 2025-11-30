"""
Configuration management for WebRTC Renderer
"""
from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    app_name: str = "Jiomosa WebRTC Renderer"
    app_version: str = "2.0.0"
    debug: bool = False
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 4  # Increased from 2 to match CPU cores
    
    # WebRTC
    webrtc_max_bitrate: int = 5000000  # 5 Mbps (increased for higher quality)
    webrtc_min_bitrate: int = 500000   # 500 Kbps
    webrtc_default_bitrate: int = 2000000  # 2 Mbps (increased default)
    webrtc_video_codec: str = "H264"  # H264, VP8, VP9
    webrtc_video_width: int = 720   # Default width (can be overridden per session)
    webrtc_video_height: int = 1280  # Default height (can be overridden per session)
    webrtc_framerate: int = 30  # Default FPS (can be up to 60)
    webrtc_max_framerate: int = 60  # Maximum supported FPS
    
    # Audio settings
    audio_enabled: bool = True  # Enable audio streaming
    audio_sample_rate: int = 48000  # 48kHz sample rate (standard for WebRTC)
    audio_channels: int = 2  # Stereo audio
    
    # STUN/TURN servers (multiple for reliability)
    stun_server: str = "stun:stun.l.google.com:19302"
    stun_servers: list[str] = [
        "stun:stun.l.google.com:19302",
        "stun:stun1.l.google.com:19302"
    ]
    # Local TURN server for Docker development (host.docker.internal resolves to host from container)
    turn_server: Optional[str] = "turn:host.docker.internal:3478"
    turn_username: Optional[str] = "jiomosa"
    turn_password: Optional[str] = "jiomosapass"
    
    # Browser settings
    browser_type: str = "chromium"  # chromium, firefox, webkit
    browser_headless: bool = True
    browser_max_sessions: int = 10
    browser_session_timeout: int = 120  # 2 minutes (faster cleanup for orphaned sessions)
    browser_pool_size: int = 3  # Pre-initialized browser instances
    
    # Performance
    max_concurrent_sessions: int = 10
    session_cleanup_interval: int = 60  # seconds
    
    # Redis (optional, for distributed sessions)
    redis_enabled: bool = False
    redis_host: str = "redis"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: Optional[str] = None
    
    # Authentication
    auth_enabled: bool = False
    jwt_secret_key: str = "CHANGE_THIS_SECRET_KEY_IN_PRODUCTION"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    
    # Monitoring
    metrics_enabled: bool = True
    
    # CORS
    cors_origins: list[str] = ["*"]
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
