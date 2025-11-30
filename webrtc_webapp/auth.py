"""
Authentication and Session Management for JioCloudApps
"""
import os
import json
import aiosqlite
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Request
from models import User, UserCreate, UserResponse, Token, TokenData, BrowserSession

# Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "jiocloudapps-secret-key-change-in-production-2024")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 30  # Long-lived tokens for app-like experience

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Database path
DB_PATH = os.getenv("DB_PATH", "/app/data/jiocloudapps.db")


async def init_db():
    """Initialize SQLite database"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    async with aiosqlite.connect(DB_PATH) as db:
        # Users table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                hashed_password TEXT NOT NULL,
                created_at TEXT NOT NULL,
                is_active INTEGER DEFAULT 1
            )
        """)
        
        # Browser sessions table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS browser_sessions (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                url TEXT NOT NULL,
                renderer_session_id TEXT,
                title TEXT,
                favicon TEXT,
                created_at TEXT NOT NULL,
                last_accessed TEXT NOT NULL,
                is_active INTEGER DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        
        # Create index for faster lookups
        await db.execute("CREATE INDEX IF NOT EXISTS idx_sessions_user ON browser_sessions(user_id)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_sessions_url ON browser_sessions(user_id, url)")
        
        await db.commit()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


async def get_user_by_username(username: str) -> Optional[User]:
    """Get user by username"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return User(
                    id=row["id"],
                    username=row["username"],
                    email=row["email"],
                    hashed_password=row["hashed_password"],
                    created_at=datetime.fromisoformat(row["created_at"]),
                    is_active=bool(row["is_active"])
                )
    return None


async def get_user_by_id(user_id: str) -> Optional[User]:
    """Get user by ID"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM users WHERE id = ?", (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return User(
                    id=row["id"],
                    username=row["username"],
                    email=row["email"],
                    hashed_password=row["hashed_password"],
                    created_at=datetime.fromisoformat(row["created_at"]),
                    is_active=bool(row["is_active"])
                )
    return None


async def create_user(user_data: UserCreate) -> User:
    """Create a new user"""
    import uuid
    
    user = User(
        id=str(uuid.uuid4()),
        username=user_data.username,
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
        created_at=datetime.now()
    )
    
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT INTO users (id, username, email, hashed_password, created_at, is_active)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (user.id, user.username, user.email, user.hashed_password,
             user.created_at.isoformat(), 1)
        )
        await db.commit()
    
    return user


async def authenticate_user(username: str, password: str) -> Optional[User]:
    """Authenticate a user"""
    user = await get_user_by_username(username)
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user


def get_token_from_cookie(request: Request) -> Optional[str]:
    """Extract JWT token from cookie"""
    return request.cookies.get("access_token")


def get_token_from_header(request: Request) -> Optional[str]:
    """Extract JWT token from Authorization header"""
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header[7:]
    return None


async def get_current_user(request: Request) -> Optional[User]:
    """Get current user from JWT token (cookie or header)"""
    token = None
    
    # Try cookie first
    token = get_token_from_cookie(request)
    
    # Then try Authorization header
    if not token:
        token = get_token_from_header(request)
    
    if not token:
        return None
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
    except JWTError:
        return None
    
    user = await get_user_by_id(user_id)
    return user


async def get_current_user_required(request: Request) -> User:
    """Get current user - raises exception if not authenticated"""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


# ============ Browser Session Management ============

async def get_user_sessions(user_id: str) -> List[BrowserSession]:
    """Get all browser sessions for a user"""
    sessions = []
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """SELECT * FROM browser_sessions 
               WHERE user_id = ? AND is_active = 1 
               ORDER BY last_accessed DESC""",
            (user_id,)
        ) as cursor:
            async for row in cursor:
                sessions.append(BrowserSession(
                    id=row["id"],
                    user_id=row["user_id"],
                    url=row["url"],
                    renderer_session_id=row["renderer_session_id"],
                    title=row["title"],
                    favicon=row["favicon"],
                    created_at=datetime.fromisoformat(row["created_at"]),
                    last_accessed=datetime.fromisoformat(row["last_accessed"]),
                    is_active=bool(row["is_active"])
                ))
    return sessions


async def get_session_by_url(user_id: str, url: str) -> Optional[BrowserSession]:
    """Get existing session for a URL"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """SELECT * FROM browser_sessions 
               WHERE user_id = ? AND url = ? AND is_active = 1""",
            (user_id, url)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return BrowserSession(
                    id=row["id"],
                    user_id=row["user_id"],
                    url=row["url"],
                    renderer_session_id=row["renderer_session_id"],
                    title=row["title"],
                    favicon=row["favicon"],
                    created_at=datetime.fromisoformat(row["created_at"]),
                    last_accessed=datetime.fromisoformat(row["last_accessed"]),
                    is_active=bool(row["is_active"])
                )
    return None


async def get_session_by_id(session_id: str) -> Optional[BrowserSession]:
    """Get session by ID"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM browser_sessions WHERE id = ?", (session_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return BrowserSession(
                    id=row["id"],
                    user_id=row["user_id"],
                    url=row["url"],
                    renderer_session_id=row["renderer_session_id"],
                    title=row["title"],
                    favicon=row["favicon"],
                    created_at=datetime.fromisoformat(row["created_at"]),
                    last_accessed=datetime.fromisoformat(row["last_accessed"]),
                    is_active=bool(row["is_active"])
                )
    return None


async def create_browser_session(user_id: str, url: str, renderer_session_id: str = None) -> BrowserSession:
    """Create a new browser session"""
    import uuid
    
    session = BrowserSession(
        id=str(uuid.uuid4()),
        user_id=user_id,
        url=url,
        renderer_session_id=renderer_session_id,
        created_at=datetime.now(),
        last_accessed=datetime.now()
    )
    
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT INTO browser_sessions 
               (id, user_id, url, renderer_session_id, title, favicon, created_at, last_accessed, is_active)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (session.id, session.user_id, session.url, session.renderer_session_id,
             session.title, session.favicon, session.created_at.isoformat(),
             session.last_accessed.isoformat(), 1)
        )
        await db.commit()
    
    return session


async def update_session_renderer_id(session_id: str, renderer_session_id: str):
    """Update renderer session ID for a browser session"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """UPDATE browser_sessions 
               SET renderer_session_id = ?, last_accessed = ?
               WHERE id = ?""",
            (renderer_session_id, datetime.now().isoformat(), session_id)
        )
        await db.commit()


async def update_session_access_time(session_id: str):
    """Update last accessed time for a session"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE browser_sessions SET last_accessed = ? WHERE id = ?",
            (datetime.now().isoformat(), session_id)
        )
        await db.commit()


async def close_browser_session(session_id: str):
    """Mark a browser session as inactive (soft delete)"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE browser_sessions SET is_active = 0, renderer_session_id = NULL WHERE id = ?",
            (session_id,)
        )
        await db.commit()


async def clear_all_user_sessions(user_id: str):
    """Clear all sessions for a user"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE browser_sessions SET is_active = 0, renderer_session_id = NULL WHERE user_id = ?",
            (user_id,)
        )
        await db.commit()
