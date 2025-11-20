#!/bin/bash
# Quick start script for Jiomosa WebRTC

set -e

echo "🚀 Jiomosa WebRTC - Quick Start"
echo "================================"
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    echo "Visit: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    echo "Visit: https://docs.docker.com/compose/install/"
    exit 1
fi

echo "✅ Docker and Docker Compose are installed"
echo ""

# Stop any existing services
echo "🛑 Stopping any existing services..."
docker compose -f docker-compose.webrtc.yml down 2>/dev/null || true
echo ""

# Pull/build images
echo "📦 Building Docker images (this may take a few minutes)..."
docker compose -f docker-compose.webrtc.yml build
echo ""

# Start services
echo "🎬 Starting services..."
docker compose -f docker-compose.webrtc.yml up -d
echo ""

# Wait for services to be ready
echo "⏳ Waiting for services to initialize (30 seconds)..."
sleep 30

# Check service health
echo ""
echo "🔍 Checking service health..."

if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ WebRTC Renderer is healthy"
else
    echo "⚠️  WebRTC Renderer is not responding yet (may need more time)"
fi

if curl -s http://localhost:9000/health > /dev/null 2>&1; then
    echo "✅ WebRTC WebApp is healthy"
else
    echo "⚠️  WebRTC WebApp is not responding yet (may need more time)"
fi

echo ""
echo "================================"
echo "🎉 Jiomosa WebRTC is running!"
echo "================================"
echo ""
echo "📱 WebApp (User Interface):"
echo "   http://localhost:9000"
echo ""
echo "🔧 API Server:"
echo "   http://localhost:8000"
echo "   http://localhost:8000/docs (API Documentation)"
echo ""
echo "📊 View logs:"
echo "   docker compose -f docker-compose.webrtc.yml logs -f"
echo ""
echo "🛑 Stop services:"
echo "   docker compose -f docker-compose.webrtc.yml down"
echo ""
echo "📚 Documentation:"
echo "   - README: WEBRTC_README.md"
echo "   - Deployment: WEBRTC_DEPLOYMENT.md"
echo ""
echo "🌐 Open WebApp in your browser:"
echo "   http://localhost:9000"
echo ""
