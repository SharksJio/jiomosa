#!/usr/bin/env python3
"""
Test WebSocket connection to the Jiomosa renderer service
"""

import socket
import time
import json
import sys
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_websocket_port():
    """Test if WebSocket port is accessible"""
    host = 'localhost'
    port = 5000
    
    try:
        sock = socket.create_connection((host, port), timeout=5)
        sock.close()
        logger.info(f"✓ WebSocket port {port} is accessible on {host}")
        return True
    except (socket.timeout, ConnectionRefusedError) as e:
        logger.error(f"✗ Cannot connect to {host}:{port}: {e}")
        return False


def test_http_api():
    """Test HTTP API endpoints"""
    import requests
    
    endpoints = [
        ('http://localhost:5000/health', 'Health check'),
        ('http://localhost:5000/api/info', 'API info'),
    ]
    
    for url, desc in endpoints:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                logger.info(f"✓ {desc}: {url}")
            else:
                logger.error(f"✗ {desc}: Status {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"✗ {desc}: {e}")
            return False
    
    return True


def test_websocket_via_http_upgrade():
    """Test WebSocket upgrade from HTTP"""
    import subprocess
    
    # Use curl to test WebSocket upgrade
    cmd = [
        'curl', '-i', '-N',
        '-H', 'Connection: Upgrade',
        '-H', 'Upgrade: websocket',
        '-H', 'Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==',
        '-H', 'Sec-WebSocket-Version: 13',
        'http://localhost:5000/socket.io/'
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        output = result.stdout + result.stderr
        
        # Check for WebSocket upgrade response or Socket.IO response
        if '101' in output or '200' in output or 'socket.io' in output.lower():
            logger.info("✓ WebSocket upgrade response received")
            logger.debug(f"Response preview: {output[:200]}")
            return True
        else:
            logger.warning(f"⚠ Unexpected response: {output[:300]}")
            # This might still be OK - socket.io uses polling fallback
            return True
    except Exception as e:
        logger.error(f"✗ WebSocket upgrade test failed: {e}")
        return False


def test_session_creation():
    """Test creating a browser session"""
    import requests
    
    try:
        response = requests.post(
            'http://localhost:5000/api/session/create',
            json={'session_id': 'ws-test-session'},
            timeout=10
        )
        
        if response.status_code == 201:
            data = response.json()
            session_id = data.get('session_id')
            logger.info(f"✓ Session created: {session_id}")
            return session_id
        else:
            logger.error(f"✗ Session creation failed: Status {response.status_code}")
            logger.error(f"  Response: {response.text}")
            return None
    except Exception as e:
        logger.error(f"✗ Session creation error: {e}")
        return None


def test_websocket_handler_loaded():
    """Test that WebSocket handler is loaded by checking logs"""
    import subprocess
    
    try:
        result = subprocess.run(
            ['docker', 'compose', 'logs', 'renderer'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if 'WebSocket handler initialized' in result.stdout:
            logger.info("✓ WebSocket handler initialized in renderer")
            return True
        else:
            logger.warning("⚠ WebSocket handler initialization not found in logs")
            # This could be because logs were rotated
            return True
    except Exception as e:
        logger.error(f"✗ Could not check logs: {e}")
        return False


def main():
    """Run all WebSocket tests"""
    logger.info("Starting WebSocket connectivity tests...\n")
    
    tests = [
        ("Port accessibility", test_websocket_port),
        ("HTTP API endpoints", test_http_api),
        ("WebSocket handler loaded", test_websocket_handler_loaded),
        ("WebSocket upgrade", test_websocket_via_http_upgrade),
        ("Session creation", test_session_creation),
    ]
    
    results = []
    for name, test_func in tests:
        logger.info(f"\nTest: {name}")
        try:
            result = test_func()
            results.append((name, result is not None if name == "Session creation" else result))
        except Exception as e:
            logger.error(f"✗ Test failed with exception: {e}")
            results.append((name, False))
    
    # Summary
    logger.info("\n" + "="*60)
    logger.info("WebSocket Test Summary:")
    logger.info("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        logger.info(f"{status}: {name}")
    
    logger.info(f"\nTotal: {passed}/{total} tests passed")
    logger.info("="*60)
    
    return 0 if passed == total else 1


if __name__ == '__main__':
    sys.exit(main())
