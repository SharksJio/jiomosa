#!/usr/bin/env python3
"""
Integration tests for Jiomosa Device Simulator
"""
import unittest
import requests
import time
import subprocess
import sys
import os

JIOMOSA_SERVER = os.getenv('JIOMOSA_SERVER', 'http://localhost:5000')
SIMULATOR_URL = os.getenv('SIMULATOR_URL', 'http://localhost:8000')


class TestDeviceSimulator(unittest.TestCase):
    """Test cases for device simulator"""
    
    @classmethod
    def setUpClass(cls):
        """Check if services are running"""
        try:
            # Check Jiomosa server
            response = requests.get(f"{JIOMOSA_SERVER}/health", timeout=5)
            if not response.ok:
                raise Exception("Jiomosa server not healthy")
            
            # Check simulator
            response = requests.get(f"{SIMULATOR_URL}/health", timeout=5)
            if not response.ok:
                raise Exception("Simulator not healthy")
                
        except Exception as e:
            print(f"Error: Services not running - {e}")
            print("Please start services first:")
            print("  1. docker compose up -d")
            print("  2. cd device_simulator && python3 simulator.py")
            sys.exit(1)
    
    def test_simulator_health(self):
        """Test simulator health endpoint"""
        response = requests.get(f"{SIMULATOR_URL}/health")
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(data['status'], 'healthy')
        self.assertEqual(data['service'], 'jiomosa-device-simulator')
        self.assertIn('jiomosa_server', data)
        self.assertIn('current_profile', data)
    
    def test_simulator_profiles_endpoint(self):
        """Test device profiles endpoint"""
        response = requests.get(f"{SIMULATOR_URL}/api/profiles")
        self.assertEqual(response.status_code, 200)
        
        profiles = response.json()
        self.assertIn('threadx_512mb', profiles)
        self.assertIn('iot_device', profiles)
        self.assertIn('thin_client', profiles)
        self.assertIn('legacy_system', profiles)
        
        # Check profile structure
        threadx = profiles['threadx_512mb']
        self.assertIn('name', threadx)
        self.assertIn('screen_width', threadx)
        self.assertIn('screen_height', threadx)
        self.assertIn('memory_mb', threadx)
        self.assertIn('description', threadx)
    
    def test_simulator_main_page(self):
        """Test simulator main page loads"""
        response = requests.get(f"{SIMULATOR_URL}/")
        self.assertEqual(response.status_code, 200)
        self.assertIn('text/html', response.headers.get('Content-Type', ''))
        
        # Check for key elements in HTML
        html = response.text
        self.assertIn('Jiomosa Device Simulator', html)
        self.assertIn('webview-frame', html)
        self.assertIn('createSession', html)
        self.assertIn('loadURL', html)
    
    def test_complete_workflow(self):
        """Test complete workflow: create session, load URL, view, close"""
        session_id = f"test_sim_{int(time.time())}"
        
        try:
            # 1. Create session via Jiomosa API
            response = requests.post(
                f"{JIOMOSA_SERVER}/api/session/create",
                json={"session_id": session_id},
                timeout=30
            )
            self.assertEqual(response.status_code, 201)
            data = response.json()
            self.assertEqual(data['session_id'], session_id)
            
            # 2. Load a simple URL
            response = requests.post(
                f"{JIOMOSA_SERVER}/api/session/{session_id}/load",
                json={"url": "https://example.com"},
                timeout=30
            )
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.json()['success'])
            
            # 3. Wait for page to load
            time.sleep(3)
            
            # 4. Get session info
            response = requests.get(
                f"{JIOMOSA_SERVER}/api/session/{session_id}/info",
                timeout=10
            )
            self.assertEqual(response.status_code, 200)
            info = response.json()
            self.assertIn('page_info', info)
            self.assertIn('title', info['page_info'])
            
            # 5. Test frame capture
            response = requests.get(
                f"{JIOMOSA_SERVER}/api/session/{session_id}/frame",
                timeout=15
            )
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.headers.get('Content-Type'), 'image/png')
            self.assertGreater(len(response.content), 1000)  # Should be a decent-sized image
            
            # 6. Test viewer endpoint
            response = requests.get(
                f"{JIOMOSA_SERVER}/api/session/{session_id}/viewer",
                timeout=10
            )
            self.assertEqual(response.status_code, 200)
            self.assertIn('text/html', response.headers.get('Content-Type', ''))
            
        finally:
            # Cleanup: Close session
            try:
                requests.post(
                    f"{JIOMOSA_SERVER}/api/session/{session_id}/close",
                    timeout=10
                )
            except:
                pass
    
    def test_multiple_device_profiles(self):
        """Test simulator with different device profiles"""
        profiles = ['threadx_512mb', 'iot_device', 'thin_client', 'legacy_system']
        
        for profile in profiles:
            with self.subTest(profile=profile):
                response = requests.get(
                    f"{SIMULATOR_URL}/simulator?profile={profile}",
                    timeout=10
                )
                self.assertEqual(response.status_code, 200)
                self.assertIn('text/html', response.headers.get('Content-Type', ''))
                
                # Check that profile is reflected in page
                html = response.text
                # Profile info should be in the page somewhere
                self.assertTrue(len(html) > 1000)


class TestSimulatorIntegration(unittest.TestCase):
    """Integration tests for simulator with various websites"""
    
    def setUp(self):
        """Create a session before each test"""
        self.session_id = f"test_integration_{int(time.time())}"
        response = requests.post(
            f"{JIOMOSA_SERVER}/api/session/create",
            json={"session_id": self.session_id},
            timeout=30
        )
        self.assertEqual(response.status_code, 201)
    
    def tearDown(self):
        """Close session after each test"""
        try:
            requests.post(
                f"{JIOMOSA_SERVER}/api/session/{self.session_id}/close",
                timeout=10
            )
        except:
            pass
    
    def test_load_simple_website(self):
        """Test loading a simple static website"""
        response = requests.post(
            f"{JIOMOSA_SERVER}/api/session/{self.session_id}/load",
            json={"url": "https://example.com"},
            timeout=30
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])
        
        # Wait and verify
        time.sleep(2)
        response = requests.get(
            f"{JIOMOSA_SERVER}/api/session/{self.session_id}/info",
            timeout=10
        )
        self.assertEqual(response.status_code, 200)
        page_info = response.json()['page_info']
        self.assertIn('example.com', page_info['url'].lower())
    
    def test_keepalive_functionality(self):
        """Test keepalive keeps session active"""
        # Send keepalive
        response = requests.post(
            f"{JIOMOSA_SERVER}/api/session/{self.session_id}/keepalive",
            timeout=10
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('last_activity', data)
        
        # Verify session still active
        response = requests.get(
            f"{JIOMOSA_SERVER}/api/sessions",
            timeout=10
        )
        self.assertEqual(response.status_code, 200)
        sessions = response.json()['sessions']
        session_ids = [s['session_id'] for s in sessions]
        self.assertIn(self.session_id, session_ids)


def run_tests():
    """Run all tests"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(TestDeviceSimulator))
    suite.addTests(loader.loadTestsFromTestCase(TestSimulatorIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Return exit code
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(run_tests())
