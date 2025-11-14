#!/usr/bin/env python3
"""
Example Python client for Jiomosa Renderer Service
Demonstrates how to programmatically control browser sessions
"""
import requests
import time
import sys
from typing import Optional, Dict, Any


class JiomosaClient:
    """Client for interacting with Jiomosa Renderer API"""
    
    def __init__(self, base_url: str = "http://localhost:5000"):
        """
        Initialize the client
        
        Args:
            base_url: Base URL of the Jiomosa service
        """
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
    
    def health_check(self) -> Dict[str, Any]:
        """Check service health"""
        response = self.session.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()
    
    def get_info(self) -> Dict[str, Any]:
        """Get service information"""
        response = self.session.get(f"{self.base_url}/api/info")
        response.raise_for_status()
        return response.json()
    
    def create_session(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a new browser session
        
        Args:
            session_id: Optional custom session ID
            
        Returns:
            Session creation response
        """
        payload = {}
        if session_id:
            payload['session_id'] = session_id
        
        response = self.session.post(
            f"{self.base_url}/api/session/create",
            json=payload
        )
        response.raise_for_status()
        return response.json()
    
    def load_url(self, session_id: str, url: str) -> Dict[str, Any]:
        """
        Load a URL in a browser session
        
        Args:
            session_id: ID of the session
            url: URL to load
            
        Returns:
            Load operation response
        """
        response = self.session.post(
            f"{self.base_url}/api/session/{session_id}/load",
            json={'url': url}
        )
        response.raise_for_status()
        return response.json()
    
    def get_session_info(self, session_id: str) -> Dict[str, Any]:
        """
        Get information about a session
        
        Args:
            session_id: ID of the session
            
        Returns:
            Session information
        """
        response = self.session.get(
            f"{self.base_url}/api/session/{session_id}/info"
        )
        response.raise_for_status()
        return response.json()
    
    def close_session(self, session_id: str) -> Dict[str, Any]:
        """
        Close a browser session
        
        Args:
            session_id: ID of the session
            
        Returns:
            Close operation response
        """
        response = self.session.post(
            f"{self.base_url}/api/session/{session_id}/close"
        )
        response.raise_for_status()
        return response.json()
    
    def list_sessions(self) -> Dict[str, Any]:
        """List all active sessions"""
        response = self.session.get(f"{self.base_url}/api/sessions")
        response.raise_for_status()
        return response.json()
    
    def get_vnc_info(self) -> Dict[str, Any]:
        """Get VNC connection information"""
        response = self.session.get(f"{self.base_url}/api/vnc/info")
        response.raise_for_status()
        return response.json()


def demo_basic_usage():
    """Demonstrate basic usage of the Jiomosa client"""
    print("=" * 60)
    print("Jiomosa Python Client Demo")
    print("=" * 60)
    
    # Initialize client
    client = JiomosaClient()
    
    try:
        # Check health
        print("\n1. Checking service health...")
        health = client.health_check()
        print(f"   Status: {health['status']}")
        print(f"   Active sessions: {health['active_sessions']}")
        
        # Create session
        print("\n2. Creating browser session...")
        session_result = client.create_session("demo_session")
        session_id = session_result['session_id']
        print(f"   Session ID: {session_id}")
        
        # Load a website
        print("\n3. Loading website...")
        url = "https://www.wikipedia.org"
        load_result = client.load_url(session_id, url)
        print(f"   URL: {url}")
        print(f"   Status: {load_result['message']}")
        
        # Wait for page to load
        print("\n4. Waiting for page to fully load...")
        time.sleep(3)
        
        # Get session info
        print("\n5. Getting session information...")
        info = client.get_session_info(session_id)
        page_info = info.get('page_info', {})
        print(f"   Page Title: {page_info.get('title', 'N/A')}")
        print(f"   Current URL: {page_info.get('url', 'N/A')}")
        
        # Get VNC info
        print("\n6. Getting VNC connection details...")
        vnc_info = client.get_vnc_info()
        print(f"   VNC URL: {vnc_info['vnc_url']}")
        print(f"   Web VNC: {vnc_info['web_vnc_url']}")
        
        print("\n" + "=" * 60)
        print("You can now view the rendered page at:")
        print(f"  {vnc_info['web_vnc_url']}")
        print("=" * 60)
        
        # Wait for user to view
        input("\nPress Enter to close the session and exit...")
        
        # Close session
        print("\n7. Closing session...")
        close_result = client.close_session(session_id)
        print(f"   {close_result['message']}")
        
        print("\n✓ Demo completed successfully!")
        
    except requests.exceptions.ConnectionError:
        print("\n✗ Error: Cannot connect to Jiomosa service")
        print("   Make sure it's running: docker compose up -d")
        sys.exit(1)
    except requests.exceptions.HTTPError as e:
        print(f"\n✗ HTTP Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        sys.exit(1)


def demo_multiple_sessions():
    """Demonstrate managing multiple browser sessions"""
    print("\n" + "=" * 60)
    print("Multiple Sessions Demo")
    print("=" * 60)
    
    client = JiomosaClient()
    
    # Websites to load
    websites = [
        ("session_1", "https://example.com"),
        ("session_2", "https://news.ycombinator.com"),
        ("session_3", "https://github.com"),
    ]
    
    created_sessions = []
    
    try:
        # Create sessions and load websites
        for session_id, url in websites:
            print(f"\nCreating {session_id} and loading {url}...")
            client.create_session(session_id)
            client.load_url(session_id, url)
            created_sessions.append(session_id)
            time.sleep(2)
        
        # List all active sessions
        print("\nActive sessions:")
        sessions = client.list_sessions()
        for session in sessions['sessions']:
            print(f"  - {session['session_id']}: {session['current_page']}")
        
        input("\nPress Enter to close all sessions...")
        
        # Close all sessions
        for session_id in created_sessions:
            print(f"Closing {session_id}...")
            client.close_session(session_id)
        
        print("\n✓ All sessions closed!")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        # Cleanup
        for session_id in created_sessions:
            try:
                client.close_session(session_id)
            except:
                pass


if __name__ == '__main__':
    # Run basic demo
    demo_basic_usage()
    
    # Optionally run multiple sessions demo
    if len(sys.argv) > 1 and sys.argv[1] == '--multiple':
        demo_multiple_sessions()
