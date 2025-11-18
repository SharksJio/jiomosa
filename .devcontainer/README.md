# Jiomosa DevContainer Configuration

This directory contains the GitHub Codespaces / VS Code DevContainer configuration for Jiomosa.

## What's Inside

- **devcontainer.json**: Main configuration file that defines:
  - Base image (Ubuntu 22.04)
  - Features (Docker-in-Docker, Python 3.11)
  - VS Code extensions
  - Port forwarding setup
  - Resource requirements

- **post-create-command.sh**: Automated setup script that runs after container creation:
  - Installs Python dependencies
  - Pre-pulls Docker images
  - Builds the renderer service
  - Displays helpful getting started information

## Features Configured

### Docker Support
- Docker-in-Docker enabled for running services
- Docker Compose v2 installed

### Python Environment
- Python 3.11 pre-installed
- Test dependencies (requests, pytest)
- Linting tools configured

### VS Code Extensions
- Python language support
- Docker management
- YAML editing

### Port Forwarding
Automatically forwards these ports:
- **5000**: Renderer API (WebSocket + REST)
- **9000**: Android WebApp (Mobile UI)
- **4444**: Selenium Grid
- **7900**: noVNC Web Interface (optional, for direct browser viewing)

## Resource Requirements

- **CPUs**: 4 cores
- **Memory**: 8GB RAM
- **Storage**: 32GB

These are minimum requirements for running all Jiomosa services. Codespaces will allocate resources based on availability and your plan.

## Using the DevContainer

### In GitHub Codespaces
1. Go to the repository
2. Click Code → Codespaces → Create codespace
3. Wait for automatic setup (3-5 minutes)
4. Start using Jiomosa!

### In VS Code Locally
1. Install "Dev Containers" extension
2. Open command palette (Ctrl+Shift+P)
3. Select "Dev Containers: Open Folder in Container"
4. Choose the jiomosa directory
5. Wait for setup to complete

## After Setup

Once the container is ready, you can:

```bash
# Start services
docker compose up -d

# Check health
curl http://localhost:5000/health

# Run demo
bash examples/quick_demo.sh

# Test external websites
bash tests/test_external_websites.sh
```

## Customization

You can customize the devcontainer by editing `devcontainer.json`:

- Add more VS Code extensions
- Change Python version
- Adjust port forwarding
- Modify resource requirements
- Add additional features

## Troubleshooting

### Container Build Fails
- Check Docker daemon is running
- Ensure sufficient disk space
- Try rebuilding: Dev Containers: Rebuild Container

### Ports Not Forwarding
- Check PORTS tab in VS Code
- Verify services are running: `docker compose ps`
- Restart port forwarding in VS Code

### Out of Resources
- Close unused Codespaces
- Use smaller machine type
- Scale down services if needed

## Learn More

- [GitHub Codespaces Documentation](https://docs.github.com/en/codespaces)
- [VS Code Dev Containers](https://code.visualstudio.com/docs/devcontainers/containers)
- [Jiomosa Codespaces Guide](../CODESPACES.md)
