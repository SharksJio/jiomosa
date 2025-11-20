# Deployment Guide for Jiomosa WebRTC

## Quick Deployment

### Docker Compose (Recommended for Getting Started)

1. **Clone the repository:**
```bash
git clone https://github.com/SharksJio/jiomosa.git
cd jiomosa
```

2. **Start WebRTC services:**
```bash
docker compose -f docker-compose.webrtc.yml up -d
```

3. **Wait for initialization:**
```bash
# Services take 30-60 seconds to fully initialize
docker compose -f docker-compose.webrtc.yml ps
docker compose -f docker-compose.webrtc.yml logs -f
```

4. **Access the application:**
- WebApp: http://localhost:9000
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Local Development

```bash
# Terminal 1: WebRTC Renderer
cd webrtc_renderer
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
playwright install chromium
playwright install-deps chromium
uvicorn main:app --reload --port 8000

# Terminal 2: WebApp
cd webrtc_webapp
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --reload --port 9000
```

## Production Deployment

### Prerequisites

- Linux server (Ubuntu 20.04+ or Debian 11+ recommended)
- 4GB+ RAM (8GB recommended for production)
- 2+ CPU cores
- Docker and Docker Compose
- Domain name (for HTTPS)
- Open ports: 80, 443, 8000, 9000

### Step 1: Server Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Logout and login to apply group changes
```

### Step 2: Clone and Configure

```bash
# Clone repository
git clone https://github.com/SharksJio/jiomosa.git
cd jiomosa

# Create environment file
cp webrtc_renderer/.env.example webrtc_renderer/.env

# Edit configuration
nano webrtc_renderer/.env
```

Configuration options:
```bash
# Video settings
WEBRTC_VIDEO_WIDTH=720
WEBRTC_VIDEO_HEIGHT=1280
WEBRTC_FRAMERATE=30

# Bitrate (bps)
WEBRTC_MIN_BITRATE=500000
WEBRTC_DEFAULT_BITRATE=1500000
WEBRTC_MAX_BITRATE=3000000

# Performance
BROWSER_MAX_SESSIONS=10
BROWSER_POOL_SIZE=3
SESSION_CLEANUP_INTERVAL=60

# STUN/TURN servers (optional TURN for NAT traversal)
STUN_SERVER=stun:stun.l.google.com:19302
# TURN_SERVER=turn:your-turn-server:3478
# TURN_USERNAME=username
# TURN_PASSWORD=password
```

### Step 3: SSL/TLS Setup with Nginx

Create `nginx.conf`:
```nginx
upstream webrtc_renderer {
    server localhost:8000;
}

upstream webrtc_webapp {
    server localhost:9000;
}

server {
    listen 80;
    server_name your-domain.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    # SSL certificates (use certbot)
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    
    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    
    # API endpoint
    location /api/ {
        proxy_pass http://webrtc_renderer;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # WebSocket endpoint
    location /ws/ {
        proxy_pass http://webrtc_renderer;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_read_timeout 86400;
    }
    
    # WebApp
    location / {
        proxy_pass http://webrtc_webapp;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Install and configure SSL:
```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal
sudo certbot renew --dry-run
```

### Step 4: Start Services

```bash
# Start services
docker compose -f docker-compose.webrtc.yml up -d

# Check status
docker compose -f docker-compose.webrtc.yml ps
docker compose -f docker-compose.webrtc.yml logs -f

# Enable auto-start on boot
docker update --restart unless-stopped $(docker ps -q)
```

### Step 5: Monitoring

Create `docker-compose.monitoring.yml`:
```yaml
services:
  prometheus:
    image: prom/prometheus:latest
    container_name: prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
    networks:
      - jiomosa-webrtc-network

  grafana:
    image: grafana/grafana:latest
    container_name: grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=changeme
    volumes:
      - grafana-data:/var/lib/grafana
    networks:
      - jiomosa-webrtc-network

volumes:
  prometheus-data:
  grafana-data:

networks:
  jiomosa-webrtc-network:
    external: true
```

## Cloud Platform Deployments

### AWS ECS/Fargate

1. Create ECR repositories
2. Build and push images
3. Create ECS task definitions
4. Deploy services with Application Load Balancer
5. Configure Route 53 for DNS

### Google Cloud Run

```bash
# Build and push
gcloud builds submit --tag gcr.io/PROJECT_ID/jiomosa-webrtc-renderer
gcloud builds submit --tag gcr.io/PROJECT_ID/jiomosa-webrtc-webapp

# Deploy
gcloud run deploy jiomosa-renderer \
  --image gcr.io/PROJECT_ID/jiomosa-webrtc-renderer \
  --platform managed \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2

gcloud run deploy jiomosa-webapp \
  --image gcr.io/PROJECT_ID/jiomosa-webrtc-webapp \
  --platform managed \
  --allow-unauthenticated
```

### Digital Ocean App Platform

1. Connect GitHub repository
2. Configure build settings
3. Set environment variables
4. Deploy

## Kubernetes Deployment

### Prerequisites
- Kubernetes cluster (1.20+)
- kubectl configured
- Helm 3.x

### Deploy with Helm (coming soon)

```bash
# Add Helm repository
helm repo add jiomosa https://sharksjio.github.io/jiomosa-helm

# Install
helm install jiomosa jiomosa/jiomosa-webrtc \
  --set renderer.replicas=3 \
  --set ingress.enabled=true \
  --set ingress.hostname=your-domain.com
```

### Manual Kubernetes Deployment

Create `k8s/deployment.yaml`:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: jiomosa-webrtc-renderer
spec:
  replicas: 3
  selector:
    matchLabels:
      app: jiomosa-webrtc-renderer
  template:
    metadata:
      labels:
        app: jiomosa-webrtc-renderer
    spec:
      containers:
      - name: renderer
        image: ghcr.io/sharksjio/jiomosa-webrtc-renderer:latest
        ports:
        - containerPort: 8000
        env:
        - name: WEBRTC_VIDEO_WIDTH
          value: "720"
        - name: WEBRTC_VIDEO_HEIGHT
          value: "1280"
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: jiomosa-webrtc-renderer
spec:
  selector:
    app: jiomosa-webrtc-renderer
  ports:
  - port: 8000
    targetPort: 8000
  type: ClusterIP
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: jiomosa-webrtc-webapp
spec:
  replicas: 2
  selector:
    matchLabels:
      app: jiomosa-webrtc-webapp
  template:
    metadata:
      labels:
        app: jiomosa-webrtc-webapp
    spec:
      containers:
      - name: webapp
        image: ghcr.io/sharksjio/jiomosa-webrtc-webapp:latest
        ports:
        - containerPort: 9000
        env:
        - name: WEBRTC_SERVER
          value: "http://jiomosa-webrtc-renderer:8000"
        resources:
          requests:
            memory: "256Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "500m"
---
apiVersion: v1
kind: Service
metadata:
  name: jiomosa-webrtc-webapp
spec:
  selector:
    app: jiomosa-webrtc-webapp
  ports:
  - port: 9000
    targetPort: 9000
  type: ClusterIP
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: jiomosa-ingress
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  tls:
  - hosts:
    - your-domain.com
    secretName: jiomosa-tls
  rules:
  - host: your-domain.com
    http:
      paths:
      - path: /api
        pathType: Prefix
        backend:
          service:
            name: jiomosa-webrtc-renderer
            port:
              number: 8000
      - path: /ws
        pathType: Prefix
        backend:
          service:
            name: jiomosa-webrtc-renderer
            port:
              number: 8000
      - path: /
        pathType: Prefix
        backend:
          service:
            name: jiomosa-webrtc-webapp
            port:
              number: 9000
```

Deploy:
```bash
kubectl apply -f k8s/deployment.yaml
```

## Scaling

### Horizontal Scaling

```bash
# Scale renderer
docker compose -f docker-compose.webrtc.yml up -d --scale webrtc-renderer=3

# Kubernetes
kubectl scale deployment jiomosa-webrtc-renderer --replicas=5
```

### Vertical Scaling

Edit `docker-compose.webrtc.yml`:
```yaml
webrtc-renderer:
  deploy:
    resources:
      limits:
        cpus: '4'
        memory: 8G
      reservations:
        cpus: '2'
        memory: 4G
```

## Troubleshooting

### Check logs
```bash
docker compose -f docker-compose.webrtc.yml logs -f webrtc-renderer
docker compose -f docker-compose.webrtc.yml logs -f webrtc-webapp
```

### Check health
```bash
curl http://localhost:8000/health
curl http://localhost:9000/health
```

### Common issues

1. **Playwright installation fails**: Run `playwright install-deps` manually
2. **Port conflicts**: Change ports in docker-compose.webrtc.yml
3. **Out of memory**: Increase Docker memory limit or reduce BROWSER_MAX_SESSIONS
4. **WebRTC connection fails**: Check STUN server accessibility, consider adding TURN server

## Security Checklist

- [ ] Enable HTTPS/WSS
- [ ] Configure firewall rules
- [ ] Set strong JWT secret key
- [ ] Enable authentication
- [ ] Set up rate limiting
- [ ] Configure CORS properly
- [ ] Regular security updates
- [ ] Monitor logs for suspicious activity
- [ ] Use secrets management (Docker secrets, Kubernetes secrets)
- [ ] Scan images for vulnerabilities

## Maintenance

### Updates
```bash
# Pull latest code
git pull origin main

# Rebuild images
docker compose -f docker-compose.webrtc.yml build

# Restart services
docker compose -f docker-compose.webrtc.yml up -d
```

### Backups
- No database required
- Configuration files in git
- Optional: Redis data if using distributed sessions

### Monitoring
- CPU usage per container
- Memory usage per container
- Active WebRTC connections
- Session count
- Error rates
- Response times

---

For more information, see [WEBRTC_README.md](WEBRTC_README.md)
