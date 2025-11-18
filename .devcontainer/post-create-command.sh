#!/bin/bash
# Post-create command script for GitHub Codespaces
# This script sets up the development environment after the container is created

set -e

echo "========================================"
echo "Setting up Jiomosa Development Environment"
echo "========================================"
echo ""

# Install Python dependencies for testing
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install requests pytest

# Fix Docker socket permissions
echo "Fixing Docker socket permissions..."
sudo chmod 666 /var/run/docker.sock || echo "Warning: Could not change Docker socket permissions"

# Verify Docker is available
echo "Verifying Docker installation..."
docker --version
docker compose version

# Pull required images to speed up first run
echo "Pre-pulling Docker images (this may take a few minutes)..."
docker pull selenium/standalone-chrome:latest &
wait

# Build the renderer service
echo "Building renderer service..."
cd renderer
docker build -t jiomosa-renderer:latest . || echo "Warning: Renderer build might need retry"
cd ..

echo ""
echo "========================================"
echo "Setup Complete!"
echo "========================================"
echo ""
echo "Quick Start:"
echo "  1. Start services:  docker compose up -d"
echo "  2. Check health:    curl http://localhost:5000/health"
echo "  3. Open WebApp:     Access port 9000 in VS Code Ports tab"
echo "  4. Run demo:        bash examples/quick_demo.sh"
echo "  5. View browser:    Access port 7900 in VS Code Ports tab (optional)"
echo ""
echo "Documentation:"
echo "  - CODESPACES.md    - GitHub Codespaces guide"
echo "  - QUICKSTART.md    - Quick start guide"
echo "  - README.md        - Full documentation"
echo ""
echo "Happy coding! 🚀"
echo "========================================"
