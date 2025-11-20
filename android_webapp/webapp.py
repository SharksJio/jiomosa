#!/usr/bin/env python3
"""
Jiomosa Android WebApp
A mobile-friendly web application that displays websites as app icons.
Designed to be loaded in an Android WebView.
"""
import os
import logging
import requests
from flask import Flask, render_template_string, request, jsonify, redirect
from flask_cors import CORS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Configuration
JIOMOSA_SERVER = os.getenv('JIOMOSA_SERVER', 'http://renderer:5000')

# Load WebSocket streaming client code
try:
    with open(os.path.join(os.path.dirname(__file__), 'static', 'streaming.js'), 'r') as f:
        STREAMING_CLIENT_JS = f.read()
except Exception as e:
    logger.warning(f"Could not load streaming.js: {e}")
    STREAMING_CLIENT_JS = "// Streaming client not available"

# Detect Codespaces environment and construct public URLs
CODESPACE_NAME = os.getenv('CODESPACE_NAME', '')
if CODESPACE_NAME:
    # Running in GitHub Codespaces - use public URLs
    GITHUB_DOMAIN = os.getenv('GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN', 'app.github.dev')
    VNC_URL = f'https://{CODESPACE_NAME}-7900.{GITHUB_DOMAIN}'
    PUBLIC_RENDERER_URL = f'https://{CODESPACE_NAME}-5000.{GITHUB_DOMAIN}'
    logger.info(f"Codespaces detected: VNC at {VNC_URL}")
else:
    # Running locally or in Docker
    VNC_URL = 'http://localhost:7900'
    PUBLIC_RENDERER_URL = None  # Use JIOMOSA_SERVER
    logger.info("Local environment detected")

# Popular website shortcuts with icons
WEBSITE_APPS = [
    {
        'id': 'facebook',
        'name': 'Facebook',
        'url': 'https://www.facebook.com',
        'icon': '📘',
        'color': '#1877f2',
        'category': 'social'
    },
    {
        'id': 'twitter',
        'name': 'X (Twitter)',
        'url': 'https://twitter.com',
        'icon': '🐦',
        'color': '#1da1f2',
        'category': 'social'
    },
    {
        'id': 'youtube',
        'name': 'YouTube',
        'url': 'https://www.youtube.com',
        'icon': '▶️',
        'color': '#ff0000',
        'category': 'media'
    },
    {
        'id': 'instagram',
        'name': 'Instagram',
        'url': 'https://www.instagram.com',
        'icon': '📷',
        'color': '#e4405f',
        'category': 'social'
    },
    {
        'id': 'whatsapp',
        'name': 'WhatsApp',
        'url': 'https://web.whatsapp.com',
        'icon': '💬',
        'color': '#25d366',
        'category': 'social'
    },
    {
        'id': 'linkedin',
        'name': 'LinkedIn',
        'url': 'https://www.linkedin.com',
        'icon': '💼',
        'color': '#0077b5',
        'category': 'professional'
    },
    {
        'id': 'reddit',
        'name': 'Reddit',
        'url': 'https://www.reddit.com',
        'icon': '🤖',
        'color': '#ff4500',
        'category': 'social'
    },
    {
        'id': 'github',
        'name': 'GitHub',
        'url': 'https://github.com',
        'icon': '🐙',
        'color': '#333333',
        'category': 'dev'
    },
    {
        'id': 'wikipedia',
        'name': 'Wikipedia',
        'url': 'https://www.wikipedia.org',
        'icon': '📚',
        'color': '#000000',
        'category': 'reference'
    },
    {
        'id': 'google',
        'name': 'Google',
        'url': 'https://www.google.com',
        'icon': '🔍',
        'color': '#4285f4',
        'category': 'search'
    },
    {
        'id': 'gmail',
        'name': 'Gmail',
        'url': 'https://mail.google.com',
        'icon': '📧',
        'color': '#ea4335',
        'category': 'productivity'
    },
    {
        'id': 'amazon',
        'name': 'Amazon',
        'url': 'https://www.amazon.com',
        'icon': '📦',
        'color': '#ff9900',
        'category': 'shopping'
    },
    {
        'id': 'netflix',
        'name': 'Netflix',
        'url': 'https://www.netflix.com',
        'icon': '🎬',
        'color': '#e50914',
        'category': 'media'
    },
    {
        'id': 'spotify',
        'name': 'Spotify',
        'url': 'https://open.spotify.com',
        'icon': '🎵',
        'color': '#1db954',
        'category': 'media'
    },
    {
        'id': 'news',
        'name': 'BBC News',
        'url': 'https://www.bbc.com/news',
        'icon': '📰',
        'color': '#bb1919',
        'category': 'news'
    },
    {
        'id': 'maps',
        'name': 'Google Maps',
        'url': 'https://maps.google.com',
        'icon': '🗺️',
        'color': '#34a853',
        'category': 'travel'
    },
]

# Main launcher page template
LAUNCHER_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Jiomosa App Launcher</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            -webkit-tap-highlight-color: transparent;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: env(safe-area-inset-top) env(safe-area-inset-right) env(safe-area-inset-bottom) env(safe-area-inset-left);
            overflow-x: hidden;
        }
        
        .status-bar {
            background: rgba(0, 0, 0, 0.2);
            backdrop-filter: blur(10px);
            color: white;
            padding: 12px 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            position: sticky;
            top: 0;
            z-index: 100;
        }
        
        .status-indicator {
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 12px;
        }
        
        .status-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #4ade80;
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        
        .header {
            padding: 30px 20px 20px;
            text-align: center;
            color: white;
        }
        
        .header h1 {
            font-size: 28px;
            font-weight: 700;
            margin-bottom: 8px;
            text-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
        }
        
        .header p {
            font-size: 14px;
            opacity: 0.9;
        }
        
        .search-bar {
            margin: 20px;
            position: relative;
        }
        
        .search-input {
            width: 100%;
            padding: 15px 20px 15px 50px;
            border: none;
            border-radius: 50px;
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            font-size: 16px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
            transition: all 0.3s;
        }
        
        .search-input:focus {
            outline: none;
            background: white;
            box-shadow: 0 6px 20px rgba(0, 0, 0, 0.3);
        }
        
        .search-icon {
            position: absolute;
            left: 20px;
            top: 50%;
            transform: translateY(-50%);
            font-size: 20px;
        }
        
        .apps-container {
            padding: 10px 10px 40px;
        }
        
        .apps-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(85px, 1fr));
            gap: 20px;
            max-width: 600px;
            margin: 0 auto;
        }
        
        .app-item {
            text-align: center;
            cursor: pointer;
            transition: all 0.2s;
            -webkit-user-select: none;
            user-select: none;
        }
        
        .app-item:active {
            transform: scale(0.95);
        }
        
        .app-icon {
            width: 70px;
            height: 70px;
            border-radius: 18px;
            background: white;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 36px;
            margin: 0 auto 10px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
            transition: all 0.3s;
            position: relative;
            overflow: hidden;
        }
        
        .app-icon::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: linear-gradient(135deg, rgba(255,255,255,0.3) 0%, rgba(255,255,255,0) 100%);
            z-index: 1;
        }
        
        .app-icon-emoji {
            position: relative;
            z-index: 2;
        }
        
        .app-item:hover .app-icon {
            transform: scale(1.05);
            box-shadow: 0 6px 20px rgba(0, 0, 0, 0.3);
        }
        
        .app-name {
            font-size: 12px;
            color: white;
            font-weight: 500;
            text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            padding: 0 5px;
        }
        
        .custom-url-item .app-icon {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            font-size: 32px;
            font-weight: bold;
        }
        
        .loading-overlay {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0, 0, 0, 0.8);
            backdrop-filter: blur(5px);
            z-index: 1000;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            color: white;
        }
        
        .loading-overlay.active {
            display: flex;
        }
        
        .spinner {
            width: 60px;
            height: 60px;
            border: 4px solid rgba(255, 255, 255, 0.3);
            border-top-color: white;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin-bottom: 20px;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        
        .loading-text {
            font-size: 18px;
            margin-bottom: 10px;
        }
        
        .loading-subtext {
            font-size: 14px;
            opacity: 0.7;
        }
        
        .custom-url-modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0, 0, 0, 0.5);
            backdrop-filter: blur(5px);
            z-index: 2000;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        
        .custom-url-modal.active {
            display: flex;
        }
        
        .modal-content {
            background: white;
            border-radius: 20px;
            padding: 30px;
            max-width: 400px;
            width: 100%;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
        }
        
        .modal-title {
            font-size: 20px;
            font-weight: 700;
            margin-bottom: 20px;
            color: #333;
        }
        
        .modal-input {
            width: 100%;
            padding: 15px;
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            font-size: 16px;
            margin-bottom: 20px;
            transition: border-color 0.3s;
        }
        
        .modal-input:focus {
            outline: none;
            border-color: #667eea;
        }
        
        .modal-buttons {
            display: flex;
            gap: 10px;
        }
        
        .modal-button {
            flex: 1;
            padding: 15px;
            border: none;
            border-radius: 10px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
        }
        
        .modal-button-primary {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        
        .modal-button-primary:active {
            transform: scale(0.98);
        }
        
        .modal-button-secondary {
            background: #f0f0f0;
            color: #666;
        }
        
        .modal-button-secondary:active {
            transform: scale(0.98);
        }
        
        .section-title {
            color: white;
            font-size: 14px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin: 30px 20px 15px;
            opacity: 0.9;
        }
        
        @media (min-width: 768px) {
            .apps-grid {
                grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
                gap: 25px;
            }
            
            .app-icon {
                width: 85px;
                height: 85px;
                font-size: 42px;
            }
            
            .app-name {
                font-size: 13px;
            }
        }
    </style>
</head>
<body>
    <!-- Status Bar -->
    <div class="status-bar">
        <div class="status-indicator">
            <div class="status-dot" id="statusDot"></div>
            <span id="statusText">Connected</span>
        </div>
        <div style="font-size: 12px;">Jiomosa</div>
    </div>
    
    <!-- Header -->
    <div class="header">
        <h1>🚀 App Launcher</h1>
        <p>Tap any app to browse on the cloud</p>
    </div>
    
    <!-- Search Bar -->
    <div class="search-bar">
        <div class="search-icon">🔍</div>
        <input type="text" 
               class="search-input" 
               id="searchInput"
               placeholder="Search apps or enter URL..."
               autocomplete="off">
    </div>
    
    <!-- Apps Grid -->
    <div class="apps-container">
        <div class="apps-grid" id="appsGrid">
            {% for app in apps %}
            <div class="app-item" data-url="{{ app.url }}" data-name="{{ app.name }}">
                <div class="app-icon" style="background: {{ app.color }};">
                    <span class="app-icon-emoji">{{ app.icon }}</span>
                </div>
                <div class="app-name">{{ app.name }}</div>
            </div>
            {% endfor %}
            
            <!-- Custom URL -->
            <div class="app-item custom-url-item" id="customUrlApp">
                <div class="app-icon">
                    <span class="app-icon-emoji">+</span>
                </div>
                <div class="app-name">Custom URL</div>
            </div>
        </div>
    </div>
    
    <!-- Loading Overlay -->
    <div class="loading-overlay" id="loadingOverlay">
        <div class="spinner"></div>
        <div class="loading-text" id="loadingText">Loading...</div>
        <div class="loading-subtext" id="loadingSubtext">Please wait</div>
    </div>
    
    <!-- Custom URL Modal -->
    <div class="custom-url-modal" id="customUrlModal">
        <div class="modal-content">
            <div class="modal-title">Enter Custom URL</div>
            <input type="text" 
                   class="modal-input" 
                   id="customUrlInput"
                   placeholder="https://example.com"
                   autocomplete="off">
            <div class="modal-buttons">
                <button class="modal-button modal-button-secondary" onclick="closeCustomUrlModal()">
                    Cancel
                </button>
                <button class="modal-button modal-button-primary" onclick="loadCustomUrl()">
                    Open
                </button>
            </div>
        </div>
    </div>
    
    <script>
        const JIOMOSA_SERVER = '/proxy';
        let currentSessionId = null;
        
        // Initialize
        document.addEventListener('DOMContentLoaded', () => {
            setupEventListeners();
            checkServerHealth();
            setInterval(checkServerHealth, 30000);
        });
        
        function setupEventListeners() {
            // App click handlers
            document.querySelectorAll('.app-item:not(.custom-url-item)').forEach(item => {
                item.addEventListener('click', () => {
                    const url = item.dataset.url;
                    const name = item.dataset.name;
                    launchApp(url, name);
                });
            });
            
            // Custom URL app
            document.getElementById('customUrlApp').addEventListener('click', () => {
                showCustomUrlModal();
            });
            
            // Search functionality
            const searchInput = document.getElementById('searchInput');
            searchInput.addEventListener('input', handleSearch);
            searchInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    const value = searchInput.value.trim();
                    if (value.includes('.') || value.startsWith('http')) {
                        launchApp(value, 'Custom');
                    }
                }
            });
        }
        
        function handleSearch() {
            const searchTerm = document.getElementById('searchInput').value.toLowerCase();
            const appItems = document.querySelectorAll('.app-item:not(.custom-url-item)');
            
            appItems.forEach(item => {
                const name = item.dataset.name.toLowerCase();
                if (name.includes(searchTerm)) {
                    item.style.display = 'block';
                } else {
                    item.style.display = searchTerm ? 'none' : 'block';
                }
            });
        }
        
        async function checkServerHealth() {
            try {
                const response = await fetch(`${JIOMOSA_SERVER}/health`);
                if (response.ok) {
                    updateStatus(true, 'Connected');
                } else {
                    updateStatus(false, 'Server Error');
                }
            } catch (error) {
                updateStatus(false, 'Offline');
            }
        }
        
        function updateStatus(connected, message) {
            const statusDot = document.getElementById('statusDot');
            const statusText = document.getElementById('statusText');
            
            if (connected) {
                statusDot.style.background = '#4ade80';
                statusDot.style.animation = 'pulse 2s infinite';
            } else {
                statusDot.style.background = '#ef4444';
                statusDot.style.animation = 'none';
            }
            
            statusText.textContent = message;
        }
        
        async function launchApp(url, appName) {
            try {
                showLoading(`Launching ${appName}`, 'Setting up cloud browser...');
                
                // Create or reuse session
                if (!currentSessionId) {
                    currentSessionId = `android_app_${Date.now()}`;
                    
                    const createResponse = await fetch(`${JIOMOSA_SERVER}/api/session/create`, {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({session_id: currentSessionId})
                    });
                    
                    if (!createResponse.ok) {
                        throw new Error('Failed to create session');
                    }
                    
                    await new Promise(resolve => setTimeout(resolve, 1000));
                }
                
                // Load URL
                showLoading(`Loading ${appName}`, 'Rendering website on cloud...');
                
                const loadResponse = await fetch(
                    `${JIOMOSA_SERVER}/api/session/${currentSessionId}/load`,
                    {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({url: url})
                    }
                );
                
                if (!loadResponse.ok) {
                    throw new Error('Failed to load URL');
                }
                
                // Wait for rendering
                await new Promise(resolve => setTimeout(resolve, 2000));
                
                // Verify session exists before redirecting
                const verifyResponse = await fetch(`${JIOMOSA_SERVER}/api/session/${currentSessionId}/info`);
                if (!verifyResponse.ok) {
                    throw new Error('Session verification failed - session may have timed out');
                }
                
                // Redirect to viewer
                window.location.href = `/viewer?session=${currentSessionId}&app=${encodeURIComponent(appName)}`;
                
            } catch (error) {
                console.error('Error launching app:', error);
                hideLoading();
                alert(`Failed to launch ${appName}: ${error.message}`);
            }
        }
        
        function showCustomUrlModal() {
            document.getElementById('customUrlModal').classList.add('active');
            document.getElementById('customUrlInput').focus();
        }
        
        function closeCustomUrlModal() {
            document.getElementById('customUrlModal').classList.remove('active');
            document.getElementById('customUrlInput').value = '';
        }
        
        function loadCustomUrl() {
            const url = document.getElementById('customUrlInput').value.trim();
            if (url) {
                closeCustomUrlModal();
                launchApp(url, 'Custom Site');
            }
        }
        
        function showLoading(text, subtext) {
            document.getElementById('loadingText').textContent = text;
            document.getElementById('loadingSubtext').textContent = subtext;
            document.getElementById('loadingOverlay').classList.add('active');
        }
        
        function hideLoading() {
            document.getElementById('loadingOverlay').classList.remove('active');
        }
    </script>
</body>
</html>
"""

# Website viewer template - FRAMEBUFFER STREAMING VERSION
VIEWER_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0, user-scalable=yes">
    <title>{{ app_name }} - Jiomosa</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            -webkit-tap-highlight-color: transparent;
        }
        
        html, body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #000;
            overflow: hidden;
            height: 100%;
            width: 100%;
            position: fixed;
        }
        
        .app-bar {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 12px 16px;
            display: flex;
            align-items: center;
            gap: 12px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            z-index: 9999;
            height: 60px;
        }
        
        .back-button {
            width: 36px;
            height: 36px;
            border-radius: 50%;
            background: rgba(255, 255, 255, 0.2);
            border: none;
            color: white;
            font-size: 20px;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.2s;
            flex-shrink: 0;
        }
        
        .back-button:active {
            transform: scale(0.9);
            background: rgba(255, 255, 255, 0.3);
        }
        
        .app-title {
            flex: 1;
            font-size: 16px;
            font-weight: 600;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        
        .refresh-button {
            width: 36px;
            height: 36px;
            border-radius: 50%;
            background: rgba(255, 255, 255, 0.2);
            border: none;
            color: white;
            font-size: 18px;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.2s;
            flex-shrink: 0;
        }
        
        .refresh-button:active {
            transform: scale(0.9) rotate(180deg);
            background: rgba(255, 255, 255, 0.3);
        }
        
        .viewer-container {
            position: fixed;
            top: 60px;
            left: 0;
            right: 0;
            bottom: 0;
            background: #000;
            display: flex;
            align-items: center;
            justify-content: center;
            overflow: hidden;
        }
        
        #browser-frame {
            max-width: 100%;
            max-height: 100%;
            width: auto;
            height: auto;
            object-fit: contain;
            display: none;
            cursor: pointer;
            touch-action: none; /* Prevent default touch behaviors */
        }
        
        #browser-frame.loaded {
            display: block;
        }
        
        /* Touch overlay for capturing interactions */
        .touch-overlay {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: 10;
            cursor: pointer;
            touch-action: none;
        }
        
        .loading-indicator {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            color: white;
            text-align: center;
            background: rgba(0, 0, 0, 0.8);
            padding: 30px;
            border-radius: 15px;
            z-index: 100;
        }
        
        .loading-indicator.hidden {
            display: none;
        }
        
        .spinner {
            width: 50px;
            height: 50px;
            border: 4px solid rgba(255, 255, 255, 0.3);
            border-top-color: white;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin: 0 auto 20px;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        
        .fps-counter {
            position: fixed;
            bottom: 10px;
            right: 10px;
            background: rgba(0, 0, 0, 0.7);
            color: #4ade80;
            padding: 8px 12px;
            border-radius: 8px;
            font-size: 11px;
            font-family: monospace;
            z-index: 9998;
            display: none;
        }
        
        .fps-counter.visible {
            display: block;
        }
    </style>
</head>
<body>
    <!-- App Bar -->
    <div class="app-bar">
        <button class="back-button" onclick="goBack()" aria-label="Go back">←</button>
        <div class="app-title">{{ app_name }}</div>
        <button class="refresh-button" onclick="toggleKeyboard()" aria-label="Toggle keyboard" id="keyboardBtn">⌨️</button>
        <button class="refresh-button" onclick="refresh()" aria-label="Refresh">↻</button>
    </div>
    
    <!-- Hidden input for mobile keyboard -->
    <input type="text" id="hiddenInput" style="position: absolute; left: -9999px; top: -9999px;" />
    
    <!-- Viewer Container - Direct Framebuffer Display -->
    <div class="viewer-container">
        <div class="loading-indicator" id="loadingIndicator">
            <div class="spinner"></div>
            <div>Loading {{ app_name }}...</div>
        </div>
        
        <!-- Touch overlay for capturing interactions -->
        <div class="touch-overlay" id="touchOverlay"></div>
        
        <!-- Direct browser screenshot display (no VNC, no noVNC controls) -->
        <img id="browser-frame" alt="{{ app_name }}" />
    </div>
    
    <!-- FPS Counter (debug) -->
    <div class="fps-counter" id="fpsCounter">
        FPS: <span id="fpsValue">0</span> | 
        Bandwidth: <span id="bandwidthValue">-</span> Mbps |
        <span id="adaptiveLabel" style="color: #fbbf24">📡 Adaptive</span>
    </div>
    
    <!-- Socket.IO for WebSocket support -->
    <script src="https://cdn.socket.io/4.5.4/socket.io.min.js"></script>
    
    <!-- WebSocket streaming client -->
    <script>
        // Streaming client loaded inline
        {{ STREAMING_CLIENT_JS | safe }}
        
        const sessionId = "{{ session_id }}";
        let streamingClient = null;
        let frameCount = 0;
        let lastFpsUpdate = Date.now();
        let consecutiveErrors = 0;
        const MAX_ERRORS = 5;
        let isSubscribed = false;
        let isInitialized = false;
        
        const browserFrame = document.getElementById('browser-frame');
        const loadingIndicator = document.getElementById('loadingIndicator');
        const fpsCounter = document.getElementById('fpsCounter');
        const fpsValue = document.getElementById('fpsValue');
        const bandwidthValue = document.getElementById('bandwidthValue');
        const adaptiveLabel = document.getElementById('adaptiveLabel');
        const touchOverlay = document.getElementById('touchOverlay');
        
        // Touch/click handling variables
        let lastTouchTime = 0;
        let touchStartY = 0;
        let isScrolling = false;
        
        // Initialize streaming client
        function initStreamingClient() {
            const rendererServerUrl = "{{ PUBLIC_RENDERER_URL or '' }}";
            
            console.log('[Viewer] Initializing streaming client');
            console.log('[Viewer] Session ID:', sessionId);
            console.log('[Viewer] Public Renderer URL:', rendererServerUrl || 'not set');
            console.log('[Viewer] Window origin:', window.location.origin);

            // If a PUBLIC_RENDERER_URL is not available (e.g. Codespaces vars not set),
            // fall back to using the webapp origin and proxy Socket.IO polling through
            // `/proxy/socket.io`. This avoids websocket upgrade failures through the
            // Codespaces port-forwarding layer by using HTTP polling proxied to the
            // renderer service.
            const clientOptions = { sessionId: sessionId };

            if (rendererServerUrl) {
                clientOptions.serverUrl = rendererServerUrl;
                clientOptions.transports = ['websocket', 'polling'];
                console.log('[Viewer] Using direct connection to renderer');
            } else {
                clientOptions.serverUrl = window.location.origin;
                clientOptions.path = '/proxy/socket.io';
                clientOptions.transports = ['polling'];
                console.log('[Viewer] Using proxied connection via webapp');
            }
            
            console.log('[Viewer] Client options:', JSON.stringify(clientOptions, null, 2));

            streamingClient = new FrameStreamingClient(Object.assign({
                    onFrame: (frameData) => {
                        // Update image source
                        browserFrame.src = frameData.image;
                        browserFrame.classList.add('loaded');

                        // Hide loading indicator on first frame
                        if (loadingIndicator.classList.contains('hidden') === false) {
                            loadingIndicator.classList.add('hidden');
                        }

                        // Update stats
                        const stats = frameData.stats;
                        updateFPS(stats);

                        // Reset error counter on success
                        consecutiveErrors = 0;
                    },

                    onError: (error) => {
                        console.error('Streaming error:', error);
                        consecutiveErrors++;

                        if (consecutiveErrors >= MAX_ERRORS) {
                            console.error('Too many errors, stopping stream');
                            alert('Connection lost. Please go back and try again.');
                            goBack();
                        }
                    },

                    onConnect: () => {
                        console.log('[Viewer] Streaming client connected');
                        fpsCounter.classList.add('visible');
                        // Auto-subscribe to session on connection (but only once)
                        if (!isSubscribed) {
                            console.log('[Viewer] Auto-subscribing to session:', sessionId);
                            streamingClient.subscribe(sessionId);
                            isSubscribed = true;
                        } else {
                            console.log('[Viewer] Already subscribed, skipping duplicate subscription');
                        }
                    },

                    onDisconnect: (reason) => {
                        console.log('[Viewer] Streaming client disconnected:', reason);
                        fpsCounter.classList.remove('visible');
                        isSubscribed = false; // Reset flag so we can resubscribe on reconnection
                    }
        }, clientOptions));

            setupInputHandlers();
        }
        
        // Update FPS counter
        function updateFPS(stats) {
            frameCount++;
            const now = Date.now();
            const elapsed = now - lastFpsUpdate;
            
            if (elapsed >= 1000) {
                const fps = Math.round(frameCount / (elapsed / 1000));
                fpsValue.textContent = fps;
                bandwidthValue.textContent = stats.bandwidthMbps || '-';
                
                // Update adaptive label color
                if (stats.adaptive) {
                    adaptiveLabel.textContent = '📡 Adaptive';
                    adaptiveLabel.style.color = '#4ade80';
                } else {
                    adaptiveLabel.textContent = '📌 Manual';
                    adaptiveLabel.style.color = '#f87171';
                }
                
                frameCount = 0;
                lastFpsUpdate = now;
            }
        }
        
        // Refresh - reload URL in browser
        async function refresh() {
            if (!streamingClient) return;
            
            loadingIndicator.classList.remove('hidden');
            
            try {
                const response = await fetch(`/proxy/api/session/${sessionId}/info`);
                const info = await response.json();
                
                if (info.page_info && info.page_info.url) {
                    await fetch(`/proxy/api/session/${sessionId}/load`, {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({url: info.page_info.url})
                    });
                    
                    await new Promise(resolve => setTimeout(resolve, 2000));
                }
            } catch (error) {
                console.error('Refresh failed:', error);
            }
            
            loadingIndicator.classList.add('hidden');
        }
        
        // Toggle keyboard (for mobile)
        function toggleKeyboard() {
            const hiddenInput = document.getElementById('hiddenInput');
            const keyboardBtn = document.getElementById('keyboardBtn');
            
            if (document.activeElement === hiddenInput) {
                hiddenInput.blur();
                keyboardBtn.style.opacity = '1.0';
            } else {
                hiddenInput.focus();
                keyboardBtn.style.opacity = '0.5';
                
                // Handle input from hidden field
                hiddenInput.addEventListener('input', (e) => {
                    const text = e.target.value;
                    if (text && streamingClient) {
                        // Send each character
                        for (let char of text) {
                            streamingClient.sendText(char);
                        }
                        // Clear input
                        e.target.value = '';
                    }
                });
            }
        }
        
        // Go back to launcher
        function goBack() {
            if (streamingClient) {
                streamingClient.disconnect();
            }
            
            // Close session
            fetch(`/proxy/api/session/${sessionId}/close`, {
                method: 'POST'
            }).catch(e => console.error('Error closing session:', e));
            
            window.location.href = '/';
        }
        
        // Setup input handlers
        function setupInputHandlers() {
            touchOverlay.addEventListener('click', handleClick);
            touchOverlay.addEventListener('touchstart', handleTouchStart, { passive: false });
            touchOverlay.addEventListener('touchmove', handleTouchMove, { passive: false });
            touchOverlay.addEventListener('touchend', handleTouchEnd, { passive: false });
            touchOverlay.addEventListener('wheel', handleWheel, { passive: false });
            
            // Add keyboard listeners
            document.addEventListener('keydown', handleKeyDown);
            document.addEventListener('keypress', handleKeyPress);
        }
        
        // Calculate coordinates relative to image
        function getImageCoordinates(clientX, clientY) {
            const rect = browserFrame.getBoundingClientRect();
            const imgNaturalWidth = browserFrame.naturalWidth;
            const imgNaturalHeight = browserFrame.naturalHeight;
            
            if (!imgNaturalWidth || !imgNaturalHeight) {
                return null;
            }
            
            const scaleX = imgNaturalWidth / rect.width;
            const scaleY = imgNaturalHeight / rect.height;
            
            const x = Math.round((clientX - rect.left) * scaleX);
            const y = Math.round((clientY - rect.top) * scaleY);
            
            return { x, y };
        }
        
        // Make functions globally accessible for inline onclick handlers
        window.goBack = goBack;
        window.toggleKeyboard = toggleKeyboard;
        window.refresh = refresh;
        
        // Handle click/tap
        function handleClick(event) {
            event.preventDefault();
            
            const coords = getImageCoordinates(event.clientX, event.clientY);
            if (!coords || !streamingClient) return;
            
            streamingClient.sendClick(coords.x, coords.y);
            showClickFeedback(event.clientX, event.clientY);
        }
        
        // Handle touch start
        function handleTouchStart(event) {
            event.preventDefault();
            
            if (event.touches.length === 1) {
                touchStartY = event.touches[0].clientY;
                isScrolling = false;
                lastTouchTime = Date.now();
            }
        }
        
        // Handle touch move (scrolling)
        function handleTouchMove(event) {
            event.preventDefault();
            
            if (event.touches.length === 1 && !isScrolling) {
                const deltaY = touchStartY - event.touches[0].clientY;
                
                if (Math.abs(deltaY) > 10) {
                    isScrolling = true;
                    if (streamingClient) {
                        streamingClient.sendScroll(0, deltaY);
                    }
                    touchStartY = event.touches[0].clientY;
                }
            }
        }
        
        // Handle touch end
        function handleTouchEnd(event) {
            event.preventDefault();
            
            const touchDuration = Date.now() - lastTouchTime;
            
            if (!isScrolling && touchDuration < 300) {
                const touch = event.changedTouches[0];
                const coords = getImageCoordinates(touch.clientX, touch.clientY);
                
                if (coords && streamingClient) {
                    streamingClient.sendClick(coords.x, coords.y);
                    showClickFeedback(touch.clientX, touch.clientY);
                }
            }
            
            isScrolling = false;
        }
        
        // Handle mouse wheel (desktop testing)
        function handleWheel(event) {
            event.preventDefault();
            if (streamingClient) {
                streamingClient.sendScroll(event.deltaX, event.deltaY);
            }
        }
        
        // Handle keyboard input
        function handleKeyDown(event) {
            // Don't capture if user is typing in input fields
            if (event.target.tagName === 'INPUT' || event.target.tagName === 'TEXTAREA') {
                return;
            }
            
            // Handle special keys (Enter, Tab, Backspace, etc.)
            if (streamingClient && (event.key.length === 1 || 
                ['Enter', 'Tab', 'Backspace', 'Delete', 'ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'].includes(event.key))) {
                event.preventDefault();
                // For special keys, send them as text
                let textToSend = event.key;
                if (event.key === 'Enter') textToSend = '\\n';
                if (event.key === 'Tab') textToSend = '\\t';
                if (event.key === 'Backspace') textToSend = '\\b';
                
                if (textToSend.length === 1 || textToSend === '\\n' || textToSend === '\\t' || textToSend === '\\b') {
                    streamingClient.sendText(textToSend);
                }
            }
        }
        
        function handleKeyPress(event) {
            // Don't capture if user is typing in input fields
            if (event.target.tagName === 'INPUT' || event.target.tagName === 'TEXTAREA') {
                return;
            }
            
            // Prevent default to avoid browser shortcuts
            event.preventDefault();
        }
        
        // Visual feedback for clicks
        function showClickFeedback(x, y) {
            const ripple = document.createElement('div');
            ripple.style.position = 'fixed';
            ripple.style.left = x + 'px';
            ripple.style.top = y + 'px';
            ripple.style.width = '40px';
            ripple.style.height = '40px';
            ripple.style.borderRadius = '50%';
            ripple.style.background = 'rgba(255, 255, 255, 0.5)';
            ripple.style.transform = 'translate(-50%, -50%) scale(0)';
            ripple.style.animation = 'ripple 0.6s ease-out';
            ripple.style.pointerEvents = 'none';
            ripple.style.zIndex = '10000';
            
            document.body.appendChild(ripple);
            
            setTimeout(() => {
                document.body.removeChild(ripple);
            }, 600);
        }
        
        // Add ripple animation
        const style = document.createElement('style');
        style.textContent = `
            @keyframes ripple {
                to {
                    transform: translate(-50%, -50%) scale(1);
                    opacity: 0;
                }
            }
        `;
        document.head.appendChild(style);
        
        // Auto-start streaming on page load
        window.addEventListener('load', async () => {
            // First verify the session exists
            try {
                const response = await fetch(`/proxy/api/session/${sessionId}/info`);
                if (!response.ok) {
                    alert('Session not found. Returning to launcher...');
                    window.location.href = '/';
                    return;
                }
            } catch (error) {
                console.error('Failed to verify session:', error);
                alert('Failed to connect. Returning to launcher...');
                window.location.href = '/';
                return;
            }
            
            // Session exists, start streaming
            if (!isInitialized) {
                console.log('[Viewer] Starting streaming client initialization');
                isInitialized = true;
                setTimeout(() => {
                    initStreamingClient();
                    // Don't subscribe immediately - wait for connection
                    // The client will auto-subscribe on connect event
                }, 500);
            } else {
                console.log('[Viewer] Already initialized, skipping duplicate initialization');
            }
        });
        
        // Cleanup on page unload
        window.addEventListener('beforeunload', () => {
            if (streamingClient) {
                streamingClient.disconnect();
            }
        });
        
        // Handle visibility changes
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                console.log('Page hidden');
            } else {
                console.log('Page visible');
            }
        });
    </script>
</body>
</html>
"""


@app.route('/')
def home():
    """Main launcher page"""
    return render_template_string(LAUNCHER_TEMPLATE, apps=WEBSITE_APPS)


@app.route('/viewer')
def viewer():
    """Website viewer page - WebSocket streaming (real-time bidirectional)"""
    session_id = request.args.get('session', '')
    app_name = request.args.get('app', 'Website')
    
    return render_template_string(
        VIEWER_TEMPLATE,
        session_id=session_id,
        app_name=app_name,
        STREAMING_CLIENT_JS=STREAMING_CLIENT_JS,
        PUBLIC_RENDERER_URL=PUBLIC_RENDERER_URL
    )


@app.route('/api/apps')
def get_apps():
    """Get list of available apps"""
    return jsonify(WEBSITE_APPS)


@app.route('/proxy/<path:endpoint>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def proxy_to_jiomosa(endpoint):
    """Proxy requests to Jiomosa renderer to avoid CORS issues"""
    try:
        # Preserve query string when proxying (important for Socket.IO/Engine.IO)
        query = request.query_string.decode('utf-8')
        url = f"{JIOMOSA_SERVER}/{endpoint}"
        if query:
            url = f"{url}?{query}"
        
        # Log problematic requests for debugging
        if 'ERR' in query or len(url) > 500:
            logger.warning(f"Potentially problematic proxy URL: {url[:200]}...")

        # Forward headers (preserve Content-Type for Socket.IO)
        headers = {
            'Content-Type': request.headers.get('Content-Type', 'application/octet-stream')
        }

        if request.method == 'POST':
            # Forward raw body data (Socket.IO sends text/plain, not JSON)
            response = requests.post(url, data=request.get_data(), headers=headers, timeout=120)
        elif request.method == 'GET':
            response = requests.get(url, timeout=120)
        elif request.method == 'PUT':
            response = requests.put(url, data=request.get_data(), headers=headers, timeout=120)
        elif request.method == 'DELETE':
            response = requests.delete(url, timeout=120)
        else:
            return jsonify({'error': 'Method not allowed'}), 405
        
        return response.content, response.status_code, {
            'Content-Type': response.headers.get('Content-Type', 'application/json')
        }
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Proxy error for {endpoint}: {e}")
        logger.error(f"Full URL attempted: {url if 'url' in locals() else 'URL not constructed'}")
        return jsonify({'error': str(e), 'endpoint': endpoint}), 500
    except Exception as e:
        logger.error(f"Unexpected proxy error for {endpoint}: {e}")
        return jsonify({'error': 'Internal proxy error'}), 500


@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'jiomosa-android-webapp',
        'jiomosa_server': JIOMOSA_SERVER
    })


if __name__ == '__main__':
    logger.info("="*60)
    logger.info("Jiomosa Android WebApp Starting")
    logger.info("="*60)
    logger.info(f"Jiomosa Server: {JIOMOSA_SERVER}")
    logger.info("WebApp URL: http://0.0.0.0:9000")
    logger.info("="*60)
    
    app.run(host='0.0.0.0', port=9000, debug=False)
