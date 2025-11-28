"""
Audio Pipeline Integration Tests for WebRTC Renderer
Tests the audio streaming functionality
"""
import pytest
import requests
import time
import json
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


class TestAudioPipeline:
    """Test suite for Audio Pipeline"""
    
    def test_audio_config_in_info(self, ensure_service):
        """Test that audio configuration is exposed in /api/info"""
        response = requests.get(f"{BASE_URL}/api/info")
        assert response.status_code == 200
        data = response.json()
        
        # Check that audio configuration is present
        assert "webrtc" in data
        webrtc_config = data["webrtc"]
        
        # Verify audio section exists
        assert "audio" in webrtc_config, "Audio configuration should be in webrtc section"
        audio_config = webrtc_config["audio"]
        
        # Verify audio settings
        assert "enabled" in audio_config, "Audio should have 'enabled' flag"
        assert "sample_rate" in audio_config, "Audio should have 'sample_rate'"
        assert "channels" in audio_config, "Audio should have 'channels'"
        assert "codec" in audio_config, "Audio should have 'codec'"
        
        # Check expected values
        assert audio_config["sample_rate"] == 48000, "Sample rate should be 48000 Hz"
        assert audio_config["channels"] in [1, 2], "Channels should be 1 or 2"
        assert audio_config["codec"] == "opus", "Codec should be opus"
        
        print(f"✓ Audio configuration verified:")
        print(f"  - Enabled: {audio_config['enabled']}")
        print(f"  - Sample Rate: {audio_config['sample_rate']} Hz")
        print(f"  - Channels: {audio_config['channels']}")
        print(f"  - Codec: {audio_config['codec']}")
    
    def test_session_with_audio_support(self, ensure_service):
        """Test creating a session that supports audio"""
        # Create session
        response = requests.post(
            f"{BASE_URL}/api/session/create",
            json={"session_id": "test-audio-session"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert data["session_id"] == "test-audio-session"
        
        print(f"✓ Session with audio support created: {data['session_id']}")
        
        # Load a page with audio capability (YouTube as example)
        response = requests.post(
            f"{BASE_URL}/api/session/test-audio-session/load",
            json={"url": "https://www.example.com"}
        )
        assert response.status_code == 200
        
        print("✓ URL loaded in audio-enabled session")
        
        # Allow time for page load
        time.sleep(2)
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/session/test-audio-session")
        print("✓ Session closed successfully")
    
    def test_video_config_separate_from_audio(self, ensure_service):
        """Test that video and audio configs are separate in info endpoint"""
        response = requests.get(f"{BASE_URL}/api/info")
        assert response.status_code == 200
        data = response.json()
        
        webrtc_config = data["webrtc"]
        
        # Check video configuration
        assert "video" in webrtc_config, "Video configuration should be separate"
        video_config = webrtc_config["video"]
        
        assert "codec" in video_config
        assert "resolution" in video_config
        assert "framerate" in video_config
        assert "bitrate_range" in video_config
        
        # Ensure video and audio are separate
        assert "audio" in webrtc_config
        audio_config = webrtc_config["audio"]
        
        # Video-specific fields should not be in audio
        assert "resolution" not in audio_config
        assert "framerate" not in audio_config
        
        # Audio-specific fields should not be in video
        assert "sample_rate" not in video_config
        assert "channels" not in video_config
        
        print("✓ Video and audio configurations are properly separated")
        print(f"  Video: {video_config['codec']}, {video_config['resolution']}, {video_config['framerate']} FPS")
        print(f"  Audio: {audio_config['codec']}, {audio_config['sample_rate']} Hz, {audio_config['channels']} channels")


class TestAudioSessionLifecycle:
    """Test audio session lifecycle"""
    
    def test_full_audio_session_lifecycle(self, ensure_service):
        """Test complete session lifecycle with audio capability"""
        session_id = "test-audio-lifecycle"
        
        # 1. Create session
        response = requests.post(
            f"{BASE_URL}/api/session/create",
            json={"session_id": session_id}
        )
        assert response.status_code == 200
        print(f"✓ Step 1: Session created")
        
        # 2. Load a URL that could have audio
        response = requests.post(
            f"{BASE_URL}/api/session/{session_id}/load",
            json={"url": "https://www.example.com"}
        )
        assert response.status_code == 200
        print(f"✓ Step 2: URL loaded")
        
        # 3. Wait for page to initialize
        time.sleep(2)
        
        # 4. Verify session exists and is active
        response = requests.get(f"{BASE_URL}/api/sessions")
        data = response.json()
        assert session_id in data["sessions"]["sessions"]
        print(f"✓ Step 3: Session verified active")
        
        # 5. Close session
        response = requests.delete(f"{BASE_URL}/api/session/{session_id}")
        assert response.status_code == 200
        print(f"✓ Step 4: Session closed")
        
        # 6. Verify session is closed
        response = requests.get(f"{BASE_URL}/api/sessions")
        data = response.json()
        assert session_id not in data["sessions"]["sessions"]
        print(f"✓ Step 5: Session confirmed closed")
    
    def test_multiple_audio_sessions(self, ensure_service):
        """Test multiple concurrent sessions with audio"""
        session_ids = [f"test-audio-multi-{i}" for i in range(3)]
        
        # Create multiple sessions
        for session_id in session_ids:
            response = requests.post(
                f"{BASE_URL}/api/session/create",
                json={"session_id": session_id}
            )
            assert response.status_code == 200
        
        print(f"✓ Created {len(session_ids)} concurrent audio sessions")
        
        # Verify all exist
        response = requests.get(f"{BASE_URL}/api/sessions")
        data = response.json()
        sessions = data["sessions"]["sessions"]
        for session_id in session_ids:
            assert session_id in sessions
        
        print("✓ All audio sessions are active")
        
        # Cleanup all
        for session_id in session_ids:
            requests.delete(f"{BASE_URL}/api/session/{session_id}")
        
        print("✓ All audio sessions closed")


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "-s"])
