# Jiomosa Deployment & Testing Guide

This guide explains where and how to deploy Jiomosa for testing websites.

## Deployment Options

### 1. Local Deployment (Easiest - Start Here!)

**Best for**: Initial testing, development, and learning

**Requirements**:
- Docker and Docker Compose installed
- 4GB+ RAM
- Any OS (Windows, Mac, Linux)

**Steps**:
```bash
# Clone the repository
git clone https://github.com/SharksJio/jiomosa.git
cd jiomosa

# Start all services
docker compose up -d

# Wait for services to be ready (30-60 seconds)
docker compose ps

# Test the health endpoint
curl http://localhost:5000/health
```

**Access Points**:
- Renderer API (WebSocket + REST): http://localhost:5000
- Android WebApp: http://localhost:9000
- Selenium Grid: http://localhost:4444
- noVNC (optional, for direct browser viewing): http://localhost:7900 (password: secret)

**Test a website**:
```bash
# Create session
curl -X POST http://localhost:5000/api/session/create \
  -H "Content-Type: application/json" \
  -d '{"session_id": "test1"}'

# Load website
curl -X POST http://localhost:5000/api/session/test1/load \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.google.com"}'

# Option A: Use Android WebApp (recommended)
# Open http://localhost:9000 in browser

# Option B: View via noVNC (optional, for debugging)
# Open http://localhost:7900 in browser
```

### 2. Cloud VM Deployment (Recommended for Remote Testing)

**Best for**: Remote access, testing from multiple devices, production-like environment

#### Option A: AWS EC2

**Instance Requirements**:
- Instance type: t3.medium or larger (2 vCPU, 4GB RAM)
- OS: Ubuntu 22.04 LTS
- Storage: 20GB SSD
- Security Group: Allow ports 22, 80, 443, 5000, 7900, 8080

**Deployment Steps**:
```bash
# 1. SSH into your EC2 instance
ssh -i your-key.pem ubuntu@your-ec2-ip

# 2. Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
newgrp docker

# 3. Install Docker Compose
sudo apt update
sudo apt install docker-compose-plugin -y

# 4. Clone and start Jiomosa
git clone https://github.com/SharksJio/jiomosa.git
cd jiomosa
docker compose up -d

# 5. Configure firewall
sudo ufw allow 5000
sudo ufw allow 9000
sudo ufw allow 7900
```

**Access from anywhere**:
```bash
# Replace YOUR_EC2_IP with your instance IP
curl -X POST http://YOUR_EC2_IP:5000/api/session/create \
  -H "Content-Type: application/json" \
  -d '{"session_id": "remote_test"}'

curl -X POST http://YOUR_EC2_IP:5000/api/session/remote_test/load \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.wikipedia.org"}'

# View at: http://YOUR_EC2_IP:7900
```

**Estimated Cost**: ~$0.05/hour ($36/month for t3.medium)

#### Option B: DigitalOcean Droplet

**Droplet Requirements**:
- Size: Basic - 2 vCPU, 4GB RAM ($24/month)
- OS: Ubuntu 22.04
- Datacenter: Choose closest to your location

**One-Click Deployment**:
```bash
# 1. Create droplet via DigitalOcean dashboard

# 2. SSH into droplet
ssh root@your-droplet-ip

# 3. Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# 4. Deploy Jiomosa
git clone https://github.com/SharksJio/jiomosa.git
cd jiomosa
docker compose up -d

# 5. Configure firewall
ufw allow 5000
ufw allow 7900
ufw allow 8080
ufw allow 22
ufw enable
```

**Access**: http://your-droplet-ip:7900

**Estimated Cost**: $24/month

#### Option C: Google Cloud Platform (GCP)

**VM Requirements**:
- Machine type: e2-medium (2 vCPU, 4GB RAM)
- Boot disk: Ubuntu 22.04 LTS, 20GB
- Firewall: Allow HTTP, HTTPS, and custom ports

**Deployment**:
```bash
# 1. Create VM in GCP Console

# 2. SSH via browser or gcloud CLI
gcloud compute ssh your-vm-name

# 3. Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 4. Deploy Jiomosa
git clone https://github.com/SharksJio/jiomosa.git
cd jiomosa
sudo docker compose up -d
```

**Firewall Rules** (in GCP Console):
- Create rule: Allow TCP on ports 5000, 7900, 8080

**Estimated Cost**: ~$25/month

#### Option D: Azure Container Instances

**For containerized deployment**:
```bash
# Using Azure CLI
az group create --name jiomosa-rg --location eastus

az container create \
  --resource-group jiomosa-rg \
  --name jiomosa \
  --image selenium/standalone-chrome:latest \
  --ports 4444 5900 7900 \
  --cpu 2 \
  --memory 4
```

### 3. Free Cloud Testing Options

#### Option A: GitHub Codespaces (Recommended - Best Free Option)

**Access**: https://github.com/SharksJio/jiomosa

**Why use Codespaces?**
- ✅ Automatic setup with devcontainer
- ✅ VS Code environment in the browser
- ✅ Port forwarding built-in
- ✅ Easy external website testing
- ✅ No local Docker installation needed

**Steps**:
1. Go to https://github.com/SharksJio/jiomosa
2. Click green **"Code"** button → **"Codespaces"** tab
3. Click **"Create codespace on main"**
4. Wait 3-5 minutes for automatic setup
5. Once ready, run in the terminal:
```bash
docker compose up -d
```
6. Access services via **PORTS** tab in VS Code:
   - Click port **7900** to view rendered browsers
   - Click port **5000** to access the API

**Testing External Websites**:
```bash
# Run comprehensive external website tests
bash tests/test_external_websites.sh

# Or test specific sites
curl -X POST http://localhost:5000/api/session/create \
  -d '{"session_id": "test"}'
curl -X POST http://localhost:5000/api/session/test/load \
  -d '{"url": "https://github.com"}'
# View at port 7900
```

**Making Ports Public** (for external device testing):
1. In VS Code **PORTS** tab, right-click port **7900**
2. Select **Port Visibility** → **Public**
3. Copy the URL and access from any device (phone, tablet, IoT device)
4. This simulates the real use case of low-end devices accessing rendered content!

**Free Tier**:
- 120 core-hours/month (60 hours on 2-core, 30 hours on 4-core)
- Auto-stops after 30 minutes of inactivity
- Delete unused Codespaces to save quota

**Complete Guide**: See [CODESPACES.md](CODESPACES.md) for comprehensive instructions

#### Option B: Play with Docker (Free, No Setup)

**Access**: https://labs.play-with-docker.com/

**Steps**:
1. Click "Login" and sign in with Docker Hub account
2. Click "Add New Instance"
3. Run commands:
```bash
git clone https://github.com/SharksJio/jiomosa.git
cd jiomosa
docker compose up -d
```
4. Click on port numbers that appear (5000, 7900) to access

**Limitations**:
- 4-hour session limit
- Need to restart after timeout
- Slower performance
- Less convenient than Codespaces

### 4. Kubernetes Deployment (Production)

**Best for**: High availability, auto-scaling, production workloads

**Prerequisites**:
- Kubernetes cluster (GKE, EKS, AKS, or local k3s)
- kubectl configured
- Helm (optional)

**Quick Deployment**:
```bash
# Create namespace
kubectl create namespace jiomosa

# Deploy services
kubectl apply -f - <<EOF
apiVersion: v1
kind: Service
metadata:
  name: chrome-service
  namespace: jiomosa
spec:
  ports:
  - port: 4444
    name: selenium
  - port: 5900
    name: vnc
  - port: 7900
    name: novnc
  selector:
    app: chrome
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: chrome
  namespace: jiomosa
spec:
  replicas: 2
  selector:
    matchLabels:
      app: chrome
  template:
    metadata:
      labels:
        app: chrome
    spec:
      containers:
      - name: chrome
        image: selenium/standalone-chrome:latest
        ports:
        - containerPort: 4444
        - containerPort: 5900
        - containerPort: 7900
        resources:
          requests:
            memory: "2Gi"
            cpu: "1"
          limits:
            memory: "4Gi"
            cpu: "2"
EOF
```

## Testing Different Websites

### Quick Website Tests

```bash
# Test simple website
curl -X POST http://localhost:5000/api/session/create -H "Content-Type: application/json" -d '{"session_id": "s1"}'
curl -X POST http://localhost:5000/api/session/s1/load -H "Content-Type: application/json" -d '{"url": "https://example.com"}'

# Test news site
curl -X POST http://localhost:5000/api/session/create -H "Content-Type: application/json" -d '{"session_id": "s2"}'
curl -X POST http://localhost:5000/api/session/s2/load -H "Content-Type: application/json" -d '{"url": "https://news.ycombinator.com"}'

# Test social media
curl -X POST http://localhost:5000/api/session/create -H "Content-Type: application/json" -d '{"session_id": "s3"}'
curl -X POST http://localhost:5000/api/session/s3/load -H "Content-Type: application/json" -d '{"url": "https://reddit.com"}'

# Test video platform
curl -X POST http://localhost:5000/api/session/create -H "Content-Type: application/json" -d '{"session_id": "s4"}'
curl -X POST http://localhost:5000/api/session/s4/load -H "Content-Type: application/json" -d '{"url": "https://youtube.com"}'
```

### Automated Website Testing

Use the provided test scripts:

```bash
# Test multiple websites automatically
bash tests/test_websites.sh

# Run integration tests
python tests/test_renderer.py

# Stress test with multiple concurrent sessions
bash examples/stress_test.sh 10
```

### Custom Website List

Create a test script for your websites:

```bash
#!/bin/bash
# my_websites_test.sh

websites=(
    "https://your-site-1.com"
    "https://your-site-2.com"
    "https://your-site-3.com"
)

for i in "${!websites[@]}"; do
    session_id="test_$i"
    url="${websites[$i]}"
    
    echo "Testing: $url"
    
    # Create session
    curl -s -X POST http://localhost:5000/api/session/create \
        -H "Content-Type: application/json" \
        -d "{\"session_id\": \"$session_id\"}" > /dev/null
    
    # Load website
    curl -s -X POST http://localhost:5000/api/session/$session_id/load \
        -H "Content-Type: application/json" \
        -d "{\"url\": \"$url\"}"
    
    echo "View at: http://localhost:7900"
    sleep 5
    
    # Close session
    curl -s -X POST http://localhost:5000/api/session/$session_id/close > /dev/null
done
```

## Viewing Rendered Websites

### Option 1: Web Browser (noVNC)
- URL: `http://YOUR_SERVER_IP:7900`
- Password: `secret`
- **Best for**: Quick viewing, no client installation needed
- **Screenshot**: Shows browser interface directly in your web browser

### Option 2: VNC Client (Better Quality)
- Server: `YOUR_SERVER_IP:5900`
- Password: `secret`
- **Recommended clients**:
  - **Windows**: TightVNC, RealVNC
  - **Mac**: Built-in Screen Sharing (⌘K in Finder)
  - **Linux**: Remmina, TigerVNC
- **Best for**: Better quality, lower latency, local viewing

### Option 3: Guacamole Web Interface
- URL: `http://YOUR_SERVER_IP:8080/guacamole/`
- **Best for**: Advanced features, session management

## Testing from Low-End Devices

### Testing the RTOS Use Case

**Simulate a low-end client**:

1. **Using Raspberry Pi Zero**:
```bash
# On Raspberry Pi (512MB RAM)
sudo apt install xtightvncviewer
vncviewer YOUR_SERVER_IP:5900
```

2. **Using ESP32 with Display**:
```cpp
// Pseudo-code for ESP32
#include <VNC_Client.h>
VNC_Client vnc;
vnc.connect("YOUR_SERVER_IP", 5900);
// Display frame buffer on screen
```

3. **Using Old Android Phone**:
- Install "VNC Viewer" app
- Connect to `YOUR_SERVER_IP:5900`
- Password: `secret`

## Performance Testing

### Monitor Resource Usage

```bash
# Check service resource usage
docker stats

# Monitor active sessions
curl http://localhost:5000/api/sessions

# View logs
docker compose logs -f renderer
```

### Latency Testing

```bash
# Measure API response time
time curl -X POST http://YOUR_SERVER_IP:5000/api/session/create \
  -H "Content-Type: application/json" \
  -d '{"session_id": "perf_test"}'

# Measure page load time
time curl -X POST http://YOUR_SERVER_IP:5000/api/session/perf_test/load \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'
```

## Troubleshooting

### Services Not Starting

```bash
# Check Docker status
docker compose ps

# View all logs
docker compose logs

# Restart services
docker compose down
docker compose up -d
```

### Can't Access from Remote

```bash
# Check if ports are open
sudo ufw status
sudo netstat -tulpn | grep -E '5000|7900|8080'

# Add firewall rules
sudo ufw allow 5000
sudo ufw allow 7900
sudo ufw allow 8080
```

### Poor Performance

```bash
# Reduce browser resolution
# Edit docker-compose.yml:
environment:
  - SE_SCREEN_WIDTH=1280
  - SE_SCREEN_HEIGHT=720

# Scale Chrome instances
docker compose up -d --scale chrome=3

# Increase resources
# Edit docker-compose.yml and add:
services:
  chrome:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
```

## Cost Comparison

| Platform | Type | Cost/Month | Setup Time | Best For |
|----------|------|------------|------------|----------|
| Local | Free | $0 | 5 min | Development, testing |
| Play with Docker | Free | $0 | 1 min | Quick demo (4hr limit) |
| DigitalOcean | VPS | $24 | 10 min | Small production |
| AWS EC2 t3.medium | VPS | $36 | 15 min | Production |
| GCP e2-medium | VPS | $25 | 15 min | Production |
| Kubernetes | Cluster | $50+ | 30 min | Enterprise |

## Recommended Testing Path

1. **Start Local** (Day 1)
   - Deploy on your laptop/desktop
   - Test with 5-10 websites
   - Learn the API

2. **Move to Cloud** (Day 2)
   - Deploy on DigitalOcean or AWS
   - Test remote access
   - Try from different devices

3. **Test on Low-End Device** (Day 3)
   - Connect from Raspberry Pi or old phone
   - Measure latency and quality
   - Test real RTOS use case

4. **Scale and Optimize** (Day 4+)
   - Add more Chrome instances
   - Optimize settings
   - Deploy to production

## Quick Commands Reference

```bash
# Deploy locally
docker compose up -d

# Create session
curl -X POST http://localhost:5000/api/session/create -H "Content-Type: application/json" -d '{"session_id": "demo"}'

# Load website
curl -X POST http://localhost:5000/api/session/demo/load -H "Content-Type: application/json" -d '{"url": "https://example.com"}'

# View sessions
curl http://localhost:5000/api/sessions

# Close session
curl -X POST http://localhost:5000/api/session/demo/close

# View in browser
open http://localhost:7900

# Stop all services
docker compose down
```

## Next Steps

1. **Try it locally first**: `docker compose up -d`
2. **Access noVNC**: http://localhost:7900
3. **Load a website**: Use the API commands above
4. **Deploy to cloud**: Choose a platform from the options above
5. **Test from remote device**: Connect from your phone/tablet

For more details, see:
- [QUICKSTART.md](QUICKSTART.md) - Basic setup
- [USAGE.md](USAGE.md) - Advanced usage examples
- [ARCHITECTURE.md](ARCHITECTURE.md) - Technical details
