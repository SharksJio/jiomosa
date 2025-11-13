#!/usr/bin/env python3
"""
Integration tests for Jiomosa Renderer Service
"""
import requests
import time
import sys

BASE_URL = "http://localhost:5000"

def test_health():
    """Test health endpoint"""
    print("Testing health endpoint...")
    response = requests.get(f"{BASE_URL}/health")
    assert response.status_code == 200, f"Health check failed: {response.status_code}"
    data = response.json()
    assert data['status'] == 'healthy', "Service not healthy"
    print("✓ Health check passed")

def test_info():
    """Test info endpoint"""
    print("Testing info endpoint...")
    response = requests.get(f"{BASE_URL}/api/info")
    assert response.status_code == 200, f"Info check failed: {response.status_code}"
    data = response.json()
    assert 'service' in data, "Service info missing"
    assert data['service'] == 'Jiomosa Renderer', "Service name incorrect"
    print("✓ Info endpoint passed")

def test_session_lifecycle():
    """Test complete session lifecycle"""
    print("Testing session lifecycle...")
    
    # Create session
    print("  Creating session...")
    response = requests.post(
        f"{BASE_URL}/api/session/create",
        json={"session_id": "pytest_session"}
    )
    assert response.status_code == 201, f"Session creation failed: {response.status_code}"
    data = response.json()
    assert data['success'] == True, "Session creation not successful"
    session_id = data['session_id']
    print(f"  ✓ Session created: {session_id}")
    
    # Load URL
    print("  Loading URL...")
    response = requests.post(
        f"{BASE_URL}/api/session/{session_id}/load",
        json={"url": "https://example.com"}
    )
    assert response.status_code == 200, f"URL loading failed: {response.status_code}"
    data = response.json()
    assert data['success'] == True, "URL loading not successful"
    print("  ✓ URL loaded successfully")
    
    # Wait for page to fully load
    time.sleep(2)
    
    # Get session info
    print("  Getting session info...")
    response = requests.get(f"{BASE_URL}/api/session/{session_id}/info")
    assert response.status_code == 200, f"Session info failed: {response.status_code}"
    data = response.json()
    assert 'page_info' in data, "Page info missing"
    # Verify the URL is from the expected domain (exact match or with path)
    url = data['page_info']['url']
    from urllib.parse import urlparse
    parsed = urlparse(url)
    assert parsed.scheme == 'https', "URL scheme should be https"
    assert parsed.netloc == 'example.com', "URL domain should be example.com"
    print("  ✓ Session info retrieved")
    
    # Close session
    print("  Closing session...")
    response = requests.post(f"{BASE_URL}/api/session/{session_id}/close")
    assert response.status_code == 200, f"Session close failed: {response.status_code}"
    data = response.json()
    assert data['success'] == True, "Session close not successful"
    print("  ✓ Session closed")

def test_list_sessions():
    """Test listing sessions"""
    print("Testing session listing...")
    response = requests.get(f"{BASE_URL}/api/sessions")
    assert response.status_code == 200, f"Session listing failed: {response.status_code}"
    data = response.json()
    assert 'active_sessions' in data, "Active sessions count missing"
    assert 'sessions' in data, "Sessions list missing"
    print(f"✓ Session listing passed (active: {data['active_sessions']})")

def test_vnc_info():
    """Test VNC info endpoint"""
    print("Testing VNC info endpoint...")
    response = requests.get(f"{BASE_URL}/api/vnc/info")
    assert response.status_code == 200, f"VNC info failed: {response.status_code}"
    data = response.json()
    assert 'vnc_url' in data, "VNC URL missing"
    assert 'web_vnc_url' in data, "Web VNC URL missing"
    print("✓ VNC info endpoint passed")

def main():
    """Run all tests"""
    print("=" * 60)
    print("Jiomosa Renderer Integration Tests")
    print("=" * 60)
    
    try:
        test_health()
        test_info()
        test_vnc_info()
        test_list_sessions()
        test_session_lifecycle()
        
        print("\n" + "=" * 60)
        print("All tests passed! ✓")
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
        return 1

if __name__ == '__main__':
    sys.exit(main())
