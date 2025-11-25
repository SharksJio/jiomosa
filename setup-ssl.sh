#!/bin/bash
# Generate self-signed SSL certificate for development
# For production, use Let's Encrypt or proper certificates

echo "Setting up SSL certificates for Jiomosa WebRTC..."

# Create SSL directory
mkdir -p ssl
cd ssl

# Generate self-signed certificate (valid for 365 days)
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout selfsigned.key \
  -out selfsigned.crt \
  -subj "/C=US/ST=State/L=City/O=Jiomosa/CN=localhost"

echo "✅ Self-signed SSL certificate generated!"
echo ""
echo "⚠️  WARNING: This is a self-signed certificate for development only."
echo "    Browsers will show a security warning."
echo ""
echo "For production, use Let's Encrypt:"
echo "  1. Get a domain name"
echo "  2. Point it to your public IP"
echo "  3. Use certbot to get free SSL certificates"
echo ""
echo "Next steps:"
echo "  1. Start nginx: docker compose -f docker-compose.nginx.yml up -d"
echo "  2. Access via: https://YOUR_IP"
echo ""
