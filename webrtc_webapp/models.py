"""
User and Session Models for JioCloudApps
"""
from datetime import datetime
from typing import Optional, Dict, List
from pydantic import BaseModel, Field
import uuid


class User(BaseModel):
    """User model"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str
    email: str
    hashed_password: str
    created_at: datetime = Field(default_factory=datetime.now)
    is_active: bool = True


class UserCreate(BaseModel):
    """User registration model"""
    username: str
    email: str
    password: str


class UserLogin(BaseModel):
    """User login model"""
    username: str
    password: str


class UserResponse(BaseModel):
    """User response model (without password)"""
    id: str
    username: str
    email: str
    created_at: datetime
    is_active: bool


class Token(BaseModel):
    """JWT Token model"""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Token payload data"""
    username: Optional[str] = None
    user_id: Optional[str] = None


class BrowserSession(BaseModel):
    """Browser session for a user"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    url: str
    renderer_session_id: Optional[str] = None
    title: Optional[str] = None
    favicon: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    last_accessed: datetime = Field(default_factory=datetime.now)
    is_active: bool = True


class SessionCreate(BaseModel):
    """Create browser session request"""
    url: str


class SessionResponse(BaseModel):
    """Browser session response"""
    id: str
    url: str
    renderer_session_id: Optional[str]
    title: Optional[str]
    created_at: datetime
    last_accessed: datetime
    is_active: bool
