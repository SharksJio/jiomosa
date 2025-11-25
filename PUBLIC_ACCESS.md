# Public Access Setup for Jiomosa WebRTC

This guide explains how to make your Jiomosa WebRTC server accessible from the public internet.

## Current Local Setup

- **WebRTC Renderer**: http://localhost:8000 (API)
- **WebRTC WebApp**: http://localhost:9000 (Web interface)
- **Local IP**: Check with `ip addr show`

## Option 1: Direct Port Forwarding (Simple)

### Step 1: Configure Your Router

1. **Access your router's admin panel** (usually http://192.168.1.1 or http://192.168.0.1)
2. **Find Port Forwarding settings** (may be under Advanced, NAT, or Virtual Servers)
3. **Add these port forwarding rules:**

   | Service Name | External Port | Internal Port | Internal IP | Protocol |
   |--------------|---------------|---------------|-------------|----------|
   | Jiomosa Web  | 9000         | 9000          | 10.170.176.93 | TCP    |
   | Jiomosa API  | 8000         | 8000          | 10.170.176.93 | TCP    |

### Step 2: Configure Firewall

```bash
# Allow incoming connections on Ubuntu/Debian
sudo ufw allow 9000/tcp
sudo ufw allow 8000/tcp
sudo ufw reload

# Or for CentOS/RHEL
sudo firewall-cmd --permanent --add-port=9000/tcp
sudo firewall-cmd --permanent --add-port=8000/tcp
sudo firewall-cmd --reload
```

### Step 3: Find Your Public IP

```bash
curl ifconfig.me
# or
curl icanhazip.com
```

### Step 4: Access Your Server

- **Web Interface**: `http://YOUR_PUBLIC_IP:9000`
- **API**: `http://YOUR_PUBLIC_IP:8000`

⚠️ **Note**: This exposes your services without HTTPS encryption!

---

## Option 2: Nginx Reverse Proxy with SSL (Recommended)

### Benefits
- ✅ HTTPS encryption
- ✅ Single port (443) to forward
- ✅ Better security
- ✅ Professional setup

### Step 1: Generate SSL Certificate

```bash
# For development (self-signed)
chmod +x setup-ssl.sh
./setup-ssl.sh

# For production with Let's Encrypt (requires domain name)
# Install certbot first:
sudo apt install certbot python3-certbot-nginx
sudo certbot certonly --standalone -d yourdomain.com
# Then update nginx.conf to use Let's Encrypt certificates
```

### Step 2: Start Nginx

```bash
# Start just nginx (if other services are already running)
docker compose -f docker-compose.nginx.yml up -d

# Or start everything together
docker compose -f docker-compose.webrtc.yml -f docker-compose.nginx.yml up -d
```

### Step 3: Configure Router

Only forward **port 443** (HTTPS):

| Service Name | External Port | Internal Port | Internal IP | Protocol |
|--------------|---------------|---------------|-------------|----------|
| Jiomosa HTTPS| 443          | 443           | 10.170.176.93 | TCP    |

Optional: Forward port 80 for HTTP→HTTPS redirect

### Step 4: Access Your Server

- **Secure Access**: `https://YOUR_PUBLIC_IP`
- Or with domain: `https://yourdomain.com`

---

## Option 3: Cloudflare Tunnel (No Port Forwarding Required!)

### Benefits
- ✅ No port forwarding needed
- ✅ Free SSL from Cloudflare
- ✅ DDoS protection
- ✅ Works behind CGNAT

### Setup

1. **Create Cloudflare account** at https://dash.cloudflare.com
2. **Install cloudflared**:
   ```bash
   wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
   sudo dpkg -i cloudflared-linux-amd64.deb
   ```

3. **Authenticate**:
   ```bash
   cloudflared tunnel login
   ```

4. **Create tunnel**:
   ```bash
   cloudflared tunnel create jiomosa
   ```

5. **Configure tunnel** (create `~/.cloudflared/config.yml`):
   ```yaml
   tunnel: <TUNNEL_ID>
   credentials-file: /home/jio/.cloudflared/<TUNNEL_ID>.json
   
   ingress:
     - hostname: jiomosa.yourdomain.com
       service: http://localhost:9000
     - service: http_status:404
   ```

6. **Start tunnel**:
   ```bash
   cloudflared tunnel run jiomosa
   ```

7. **Access**: `https://jiomosa.yourdomain.com`

---

## Option 4: Ngrok (Quick Testing)

### For temporary public access (development only)

```bash
# Install ngrok
snap install ngrok

# Authenticate (get token from ngrok.com)
ngrok authtoken YOUR_TOKEN

# Expose web interface
ngrok http 9000

# You'll get a public URL like: https://abc123.ngrok.io
```

⚠️ **Note**: Free tier has limitations and random URLs

---

## Security Best Practices

### 1. Always Use HTTPS in Production
- Never expose HTTP endpoints publicly
- Use proper SSL certificates (Let's Encrypt is free)

### 2. Add Authentication
Consider adding basic auth to nginx:

```bash
# Install apache2-utils
sudo apt install apache2-utils

# Create password file
sudo htpasswd -c /etc/nginx/.htpasswd jiomosa

# Add to nginx.conf location blocks:
# auth_basic "Restricted Access";
# auth_basic_user_file /etc/nginx/.htpasswd;
```

### 3. Rate Limiting
Add to nginx.conf:

```nginx
limit_req_zone $binary_remote_addr zone=mylimit:10m rate=10r/s;

location / {
    limit_req zone=mylimit burst=20;
    # ... other config
}
```

### 4. Monitor Your Server
```bash
# Check nginx logs
docker logs jiomosa-nginx -f

# Check WebRTC logs
docker logs jiomosa-webrtc-renderer -f
```

---

## Troubleshooting

### Can't Access from Public IP

1. **Check if services are running**:
   ```bash
   docker ps
   curl http://localhost:9000
   ```

2. **Test port forwarding**:
   ```bash
   # From another device/network
   telnet YOUR_PUBLIC_IP 9000
   ```

3. **Check firewall**:
   ```bash
   sudo ufw status
   sudo iptables -L -n
   ```

4. **Check router settings**: Ensure port forwarding is enabled and saved

### WebRTC Connection Issues

- **STUN/TURN**: For connections behind NAT, you may need a TURN server
- Uncomment the turn-server section in docker-compose.webrtc.yml
- Configure with your public IP

### Browser Shows Security Warning (Self-Signed Cert)

This is normal for development. Users must:
1. Click "Advanced"
2. Click "Proceed to site (unsafe)"

For production, use Let's Encrypt certificates.

---

## Quick Start Commands

### Start with Nginx + SSL
```bash
./setup-ssl.sh
docker compose -f docker-compose.webrtc.yml -f docker-compose.nginx.yml up -d
```

### Stop All Services
```bash
docker compose -f docker-compose.webrtc.yml -f docker-compose.nginx.yml down
```

### View Logs
```bash
docker compose -f docker-compose.webrtc.yml logs -f
```

### Check Status
```bash
docker compose -f docker-compose.webrtc.yml ps
curl https://localhost/health -k  # -k to ignore self-signed cert
```
