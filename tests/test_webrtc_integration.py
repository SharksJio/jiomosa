"""
Integration tests for WebRTC Renderer
Tests the new WebRTC-based streaming solution
"""
import pytest
import requests
import time
import asyncio
from typing import Dict, Any

# Configuration
BASE_URL = "http://localhost:8000"
TIMEOUT = 30


def wait_for_service(url: str, timeout: int = 60) -> bool:
    """Wait for service to become available"""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get(f"{url}/health", timeout=5)
            if response.status_code == 200:
                return True
        except requests.exceptions.RequestException:
            pass
        time.sleep(2)
    return False


@pytest.fixture(scope="module")
def ensure_service():
    """Ensure the WebRTC renderer service is running"""
    assert wait_for_service(BASE_URL), f"WebRTC renderer not available at {BASE_URL}"
    yield
    # Cleanup is done per test


class TestWebRTCRenderer:
    """Test suite for WebRTC Renderer"""
    
    def test_health_endpoint(self, ensure_service):
        """Test health check endpoint"""
        response = requests.get(f"{BASE_URL}/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "timestamp" in data
        print(f"✓ Health check passed - Version: {data['version']}")
    
    def test_info_endpoint(self, ensure_service):
        """Test info endpoint"""
        response = requests.get(f"{BASE_URL}/api/info")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert "webrtc" in data
        assert "browser" in data
        assert "connections" in data
        
        # Verify WebRTC video config
        webrtc = data["webrtc"]
        assert "video" in webrtc, "Video configuration should be present"
        video_config = webrtc["video"]
        assert video_config["codec"] in ["H264", "VP8", "VP9"]
        assert "resolution" in video_config
        assert "framerate" in video_config
        
        # Verify WebRTC audio config
        assert "audio" in webrtc, "Audio configuration should be present"
        audio_config = webrtc["audio"]
        assert "enabled" in audio_config
        assert "sample_rate" in audio_config
        assert "channels" in audio_config
        
        print(f"✓ Info endpoint passed - Video: {video_config['codec']}, {video_config['resolution']}")
        print(f"  Audio: enabled={audio_config['enabled']}, {audio_config['sample_rate']}Hz, {audio_config['channels']}ch")
    
    def test_create_session(self, ensure_service):
        """Test session creation"""
        response = requests.post(
            f"{BASE_URL}/api/session/create",
            json={"session_id": "test-session-1"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert data["session_id"] == "test-session-1"
        assert "websocket_url" in data
        print(f"✓ Session created: {data['session_id']}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/session/test-session-1")
    
    def test_create_session_auto_id(self, ensure_service):
        """Test session creation with auto-generated ID"""
        response = requests.post(
            f"{BASE_URL}/api/session/create",
            json={}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert len(data["session_id"]) > 0
        print(f"✓ Session created with auto ID: {data['session_id']}")
        
        # Cleanup
        session_id = data["session_id"]
        requests.delete(f"{BASE_URL}/api/session/{session_id}")
    
    def test_load_url(self, ensure_service):
        """Test loading a URL in a session"""
        # Create session
        response = requests.post(
            f"{BASE_URL}/api/session/create",
            json={"session_id": "test-load-url"}
        )
        assert response.status_code == 200
        
        # Load URL
        response = requests.post(
            f"{BASE_URL}/api/session/test-load-url/load",
            json={"url": "https://example.com"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        # URL may have trailing slash added by pydantic
        assert data["url"].rstrip('/') == "https://example.com"
        print(f"✓ URL loaded successfully: {data['url']}")
        
        # Give it a moment to load
        time.sleep(2)
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/session/test-load-url")
    
    def test_load_url_nonexistent_session(self, ensure_service):
        """Test loading URL in non-existent session"""
        response = requests.post(
            f"{BASE_URL}/api/session/nonexistent-session/load",
            json={"url": "https://example.com"}
        )
        assert response.status_code == 404
        print("✓ Correctly rejected URL load for nonexistent session")
    
    def test_list_sessions(self, ensure_service):
        """Test listing active sessions"""
        # Create a session
        response = requests.post(
            f"{BASE_URL}/api/session/create",
            json={"session_id": "test-list-1"}
        )
        assert response.status_code == 200
        
        # List sessions
        response = requests.get(f"{BASE_URL}/api/sessions")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert "sessions" in data
        sessions = data["sessions"]
        assert "active_sessions" in sessions
        assert sessions["active_sessions"] >= 1
        assert "test-list-1" in sessions["sessions"]
        print(f"✓ Listed sessions - Active: {sessions['active_sessions']}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/session/test-list-1")
    
    def test_close_session(self, ensure_service):
        """Test closing a session"""
        # Create session
        response = requests.post(
            f"{BASE_URL}/api/session/create",
            json={"session_id": "test-close"}
        )
        assert response.status_code == 200
        
        # Close session
        response = requests.delete(f"{BASE_URL}/api/session/test-close")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        print(f"✓ Session closed successfully")
        
        # Verify it's gone
        response = requests.get(f"{BASE_URL}/api/sessions")
        data = response.json()
        assert "test-close" not in data["sessions"]["sessions"]
    
    def test_multiple_sessions(self, ensure_service):
        """Test creating multiple concurrent sessions"""
        session_ids = [f"test-multi-{i}" for i in range(3)]
        
        # Create multiple sessions
        for session_id in session_ids:
            response = requests.post(
                f"{BASE_URL}/api/session/create",
                json={"session_id": session_id}
            )
            assert response.status_code == 200
        
        # Verify all exist
        response = requests.get(f"{BASE_URL}/api/sessions")
        data = response.json()
        sessions = data["sessions"]["sessions"]
        for session_id in session_ids:
            assert session_id in sessions
        print(f"✓ Created {len(session_ids)} concurrent sessions")
        
        # Cleanup all
        for session_id in session_ids:
            requests.delete(f"{BASE_URL}/api/session/{session_id}")
    
    def test_session_lifecycle(self, ensure_service):
        """Test complete session lifecycle"""
        session_id = "test-lifecycle"
        
        # 1. Create
        response = requests.post(
            f"{BASE_URL}/api/session/create",
            json={"session_id": session_id}
        )
        assert response.status_code == 200
        print(f"✓ Step 1: Session created")
        
        # 2. Load URL
        response = requests.post(
            f"{BASE_URL}/api/session/{session_id}/load",
            json={"url": "https://example.com"}
        )
        assert response.status_code == 200
        print(f"✓ Step 2: URL loaded")
        
        # 3. Wait for page load
        time.sleep(2)
        
        # 4. Verify session exists
        response = requests.get(f"{BASE_URL}/api/sessions")
        data = response.json()
        assert session_id in data["sessions"]["sessions"]
        print(f"✓ Step 3: Session verified active")
        
        # 5. Close
        response = requests.delete(f"{BASE_URL}/api/session/{session_id}")
        assert response.status_code == 200
        print(f"✓ Step 4: Session closed")
        
        # 6. Verify closed
        response = requests.get(f"{BASE_URL}/api/sessions")
        data = response.json()
        assert session_id not in data["sessions"]["sessions"]
        print(f"✓ Step 5: Session confirmed closed")


class TestWebRTCWebApp:
    """Test suite for WebRTC WebApp"""
    
    WEBAPP_URL = "http://localhost:9000"
    
    def test_webapp_health(self):
        """Test webapp health check"""
        if not wait_for_service(self.WEBAPP_URL, timeout=30):
            pytest.skip("WebApp not available")
        
        response = requests.get(f"{self.WEBAPP_URL}/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        print("✓ WebApp health check passed")
    
    def test_webapp_home_page(self):
        """Test webapp home page loads"""
        if not wait_for_service(self.WEBAPP_URL, timeout=30):
            pytest.skip("WebApp not available")
        
        response = requests.get(self.WEBAPP_URL)
        assert response.status_code == 200
        assert b"Jiomosa" in response.content
        assert b"Cloud Browser" in response.content
        print("✓ WebApp home page loaded")
    
    def test_webapp_viewer_page(self):
        """Test webapp viewer page loads"""
        if not wait_for_service(self.WEBAPP_URL, timeout=30):
            pytest.skip("WebApp not available")
        
        response = requests.get(f"{self.WEBAPP_URL}/viewer?url=https://example.com")
        assert response.status_code == 200
        assert b"webrtc-client.js" in response.content
        print("✓ WebApp viewer page loaded")


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "-s"])
