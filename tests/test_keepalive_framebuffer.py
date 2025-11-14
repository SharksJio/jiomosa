#!/usr/bin/env python3
"""
Integration tests for Jiomosa Keepalive and Framebuffer features
"""
import requests
import time
import sys
import base64
from io import BytesIO

BASE_URL = "http://localhost:5000"

def test_keepalive():
    """Test session keepalive functionality"""
    print("Testing keepalive functionality...")
    
    # Create session
    response = requests.post(
        f"{BASE_URL}/api/session/create",
        json={"session_id": "keepalive_test"}
    )
    assert response.status_code == 201, f"Session creation failed: {response.status_code}"
    data = response.json()
    session_id = data['session_id']
    print(f"  ✓ Session created: {session_id}")
    
    # Load URL
    response = requests.post(
        f"{BASE_URL}/api/session/{session_id}/load",
        json={"url": "https://example.com"}
    )
    assert response.status_code == 200, f"URL loading failed: {response.status_code}"
    print("  ✓ URL loaded")
    
    # Get initial session info
    response = requests.get(f"{BASE_URL}/api/session/{session_id}/info")
    assert response.status_code == 200, f"Session info failed: {response.status_code}"
    data = response.json()
    initial_activity = data['last_activity']
    print(f"  ✓ Initial last_activity: {initial_activity}")
    
    # Wait a bit
    time.sleep(2)
    
    # Send keepalive
    response = requests.post(f"{BASE_URL}/api/session/{session_id}/keepalive")
    assert response.status_code == 200, f"Keepalive failed: {response.status_code}"
    data = response.json()
    assert data['success'] == True, "Keepalive not successful"
    assert data['session_id'] == session_id, "Session ID mismatch"
    new_activity = data['last_activity']
    print(f"  ✓ Keepalive sent, new last_activity: {new_activity}")
    
    # Verify last_activity was updated
    assert new_activity > initial_activity, "Last activity timestamp not updated"
    print("  ✓ Last activity timestamp updated correctly")
    
    # Clean up
    response = requests.post(f"{BASE_URL}/api/session/{session_id}/close")
    assert response.status_code == 200, f"Session close failed: {response.status_code}"
    print("  ✓ Session closed")

def test_frame_capture():
    """Test framebuffer/screenshot capture functionality"""
    print("\nTesting frame capture functionality...")
    
    # Create session
    response = requests.post(
        f"{BASE_URL}/api/session/create",
        json={"session_id": "frame_test"}
    )
    assert response.status_code == 201, f"Session creation failed: {response.status_code}"
    session_id = response.json()['session_id']
    print(f"  ✓ Session created: {session_id}")
    
    # Load URL
    response = requests.post(
        f"{BASE_URL}/api/session/{session_id}/load",
        json={"url": "https://example.com"}
    )
    assert response.status_code == 200, f"URL loading failed: {response.status_code}"
    print("  ✓ URL loaded")
    
    # Wait for page to fully render
    time.sleep(2)
    
    # Test frame endpoint (PNG image)
    response = requests.get(f"{BASE_URL}/api/session/{session_id}/frame")
    assert response.status_code == 200, f"Frame capture failed: {response.status_code}"
    assert response.headers['Content-Type'] == 'image/png', "Response is not a PNG image"
    
    # Verify it's a valid PNG
    image_data = response.content
    assert len(image_data) > 0, "Frame data is empty"
    assert image_data[:8] == b'\x89PNG\r\n\x1a\n', "Not a valid PNG file"
    print(f"  ✓ Frame captured as PNG ({len(image_data)} bytes)")
    
    # Test frame/data endpoint (base64 JSON)
    response = requests.get(f"{BASE_URL}/api/session/{session_id}/frame/data")
    assert response.status_code == 200, f"Frame data failed: {response.status_code}"
    data = response.json()
    assert data['success'] == True, "Frame data not successful"
    assert 'frame' in data, "Frame data missing"
    assert data['format'] == 'png', "Frame format should be PNG"
    
    # Verify base64 encoded data can be decoded
    frame_b64 = data['frame']
    decoded = base64.b64decode(frame_b64)
    assert decoded[:8] == b'\x89PNG\r\n\x1a\n', "Decoded frame is not a valid PNG"
    print(f"  ✓ Frame data as base64 JSON ({len(frame_b64)} chars)")
    
    # Clean up
    response = requests.post(f"{BASE_URL}/api/session/{session_id}/close")
    assert response.status_code == 200, f"Session close failed: {response.status_code}"
    print("  ✓ Session closed")

def test_html5_viewer():
    """Test HTML5 viewer endpoint"""
    print("\nTesting HTML5 viewer endpoint...")
    
    # Create session
    response = requests.post(
        f"{BASE_URL}/api/session/create",
        json={"session_id": "viewer_test"}
    )
    assert response.status_code == 201, f"Session creation failed: {response.status_code}"
    session_id = response.json()['session_id']
    print(f"  ✓ Session created: {session_id}")
    
    # Load URL
    response = requests.post(
        f"{BASE_URL}/api/session/{session_id}/load",
        json={"url": "https://example.com"}
    )
    assert response.status_code == 200, f"URL loading failed: {response.status_code}"
    print("  ✓ URL loaded")
    
    # Test viewer endpoint
    response = requests.get(f"{BASE_URL}/api/session/{session_id}/viewer")
    assert response.status_code == 200, f"Viewer endpoint failed: {response.status_code}"
    assert 'text/html' in response.headers['Content-Type'], "Response is not HTML"
    
    html_content = response.text
    assert 'Jiomosa HTML5 Viewer' in html_content, "HTML content missing title"
    assert session_id in html_content, "Session ID not in HTML"
    assert 'captureFrame' in html_content, "JavaScript functions missing"
    assert 'startStreaming' in html_content, "Streaming functions missing"
    print(f"  ✓ HTML5 viewer page generated ({len(html_content)} chars)")
    print(f"  ✓ Viewer available at: {BASE_URL}/api/session/{session_id}/viewer")
    
    # Clean up
    response = requests.post(f"{BASE_URL}/api/session/{session_id}/close")
    assert response.status_code == 200, f"Session close failed: {response.status_code}"
    print("  ✓ Session closed")

def test_api_info_updated():
    """Test that API info includes new endpoints"""
    print("\nTesting API info for new endpoints...")
    
    response = requests.get(f"{BASE_URL}/api/info")
    assert response.status_code == 200, f"Info endpoint failed: {response.status_code}"
    data = response.json()
    
    endpoints = data.get('endpoints', {})
    assert 'session_keepalive' in endpoints, "Keepalive endpoint not in API info"
    assert 'session_frame' in endpoints, "Frame endpoint not in API info"
    assert 'session_frame_data' in endpoints, "Frame data endpoint not in API info"
    assert 'session_viewer' in endpoints, "Viewer endpoint not in API info"
    print("  ✓ All new endpoints in API info")
    
    session_config = data.get('session_config', {})
    assert 'timeout' in session_config, "Session timeout not in config"
    assert 'frame_capture_interval' in session_config, "Frame capture interval not in config"
    print(f"  ✓ Session timeout: {session_config['timeout']} seconds")
    print(f"  ✓ Frame capture interval: {session_config['frame_capture_interval']} seconds")

def main():
    """Run all tests"""
    print("=" * 60)
    print("Jiomosa Keepalive and Framebuffer Integration Tests")
    print("=" * 60)
    
    try:
        test_api_info_updated()
        test_keepalive()
        test_frame_capture()
        test_html5_viewer()
        
        print("\n" + "=" * 60)
        print("All keepalive and framebuffer tests passed! ✓")
        print("=" * 60)
        return 0
        
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        return 1
    except requests.exceptions.ConnectionError:
        print("\n✗ Cannot connect to service. Is it running?")
        return 1
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())
