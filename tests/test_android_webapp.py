#!/usr/bin/env python3
"""
Tests for the Jiomosa Android WebApp
"""
import time
import unittest
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class TestAndroidWebApp(unittest.TestCase):
    """Test cases for the Android WebApp"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures"""
        cls.webapp_url = 'http://localhost:9000'
        cls.renderer_url = 'http://localhost:5000'
        
        # Create session with retries
        cls.session = requests.Session()
        retry = Retry(
            total=5,
            backoff_factor=1,
            status_forcelist=[500, 502, 503, 504]
        )
        adapter = HTTPAdapter(max_retries=retry)
        cls.session.mount('http://', adapter)
        cls.session.mount('https://', adapter)
        
        # Wait for services to be ready
        print("Waiting for services to be ready...")
        cls.wait_for_service(cls.webapp_url, 'Android WebApp')
        cls.wait_for_service(cls.renderer_url, 'Renderer')
    
    @classmethod
    def wait_for_service(cls, url, name, timeout=60):
        """Wait for a service to become available"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = cls.session.get(f"{url}/health", timeout=5)
                if response.ok:
                    print(f"✓ {name} is ready")
                    return True
            except Exception as e:
                time.sleep(2)
        
        raise Exception(f"{name} did not become ready within {timeout} seconds")
    
    def test_webapp_health(self):
        """Test webapp health endpoint"""
        response = self.session.get(f"{self.webapp_url}/health")
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(data['status'], 'healthy')
        self.assertEqual(data['service'], 'jiomosa-android-webapp')
        print("✓ WebApp health check passed")
    
    def test_home_page_loads(self):
        """Test that the home page loads successfully"""
        response = self.session.get(self.webapp_url)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'App Launcher', response.content)
        self.assertIn(b'apps-grid', response.content)
        print("✓ Home page loads successfully")
    
    def test_apps_api_endpoint(self):
        """Test the apps API endpoint"""
        response = self.session.get(f"{self.webapp_url}/api/apps")
        self.assertEqual(response.status_code, 200)
        
        apps = response.json()
        self.assertIsInstance(apps, list)
        self.assertGreater(len(apps), 0)
        
        # Check structure of first app
        first_app = apps[0]
        required_fields = ['id', 'name', 'url', 'icon', 'color', 'category']
        for field in required_fields:
            self.assertIn(field, first_app)
        
        print(f"✓ Apps API returns {len(apps)} apps")
    
    def test_viewer_page_loads(self):
        """Test that the viewer page loads"""
        response = self.session.get(
            f"{self.webapp_url}/viewer",
            params={'session': 'test_session', 'app': 'Test App'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Test App', response.content)
        self.assertIn(b'content-frame', response.content)
        print("✓ Viewer page loads successfully")
    
    def test_proxy_health_endpoint(self):
        """Test that proxy to renderer works"""
        response = self.session.get(f"{self.webapp_url}/proxy/health")
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(data['service'], 'jiomosa-renderer')
        print("✓ Proxy to renderer works")
    
    def test_create_session_through_proxy(self):
        """Test creating a session through the proxy"""
        session_id = f"test_android_{int(time.time())}"
        
        response = self.session.post(
            f"{self.webapp_url}/proxy/api/session/create",
            json={'session_id': session_id},
            timeout=30
        )
        
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['session_id'], session_id)
        print(f"✓ Session created through proxy: {session_id}")
        
        # Clean up: close the session
        try:
            close_response = self.session.post(
                f"{self.webapp_url}/proxy/api/session/{session_id}/close",
                timeout=10
            )
            if close_response.ok:
                print(f"✓ Session {session_id} closed")
        except Exception as e:
            print(f"Warning: Could not close session: {e}")
    
    def test_popular_websites_in_apps_list(self):
        """Test that popular websites are included in the apps list"""
        response = self.session.get(f"{self.webapp_url}/api/apps")
        apps = response.json()
        
        app_names = [app['name'].lower() for app in apps]
        
        # Check for some popular sites
        expected_sites = ['facebook', 'youtube', 'google', 'github']
        for site in expected_sites:
            found = any(site in name for name in app_names)
            self.assertTrue(found, f"{site} should be in the apps list")
        
        print(f"✓ All expected popular websites are present")
    
    def test_app_categories(self):
        """Test that apps have proper categories"""
        response = self.session.get(f"{self.webapp_url}/api/apps")
        apps = response.json()
        
        categories = set(app['category'] for app in apps)
        expected_categories = ['social', 'media', 'search', 'dev', 'reference']
        
        for category in expected_categories:
            self.assertIn(category, categories, f"Category '{category}' should exist")
        
        print(f"✓ Apps are properly categorized: {', '.join(sorted(categories))}")


def main():
    """Run the tests"""
    print("="*60)
    print("Jiomosa Android WebApp Tests")
    print("="*60)
    print()
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAndroidWebApp)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print()
    print("="*60)
    if result.wasSuccessful():
        print("✓ All tests passed!")
    else:
        print("✗ Some tests failed")
        if result.failures:
            print(f"Failures: {len(result.failures)}")
        if result.errors:
            print(f"Errors: {len(result.errors)}")
    print("="*60)
    
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    exit(main())
