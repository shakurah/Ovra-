#!/bin/bash

# Configure Nginx for OVRA AI - Reverse Proxy Configuration
echo "🌐 Configuring Nginx for OVRA AI..."

# Stop nginx temporarily
echo "🛑 Stopping nginx temporarily for configuration..."
sudo systemctl stop nginx

# Remove default sites
sudo rm -f /etc/nginx/sites-enabled/ovra-ai
sudo rm -f /etc/nginx/sites-enabled/default

# Create nginx configuration for OVRA AI
sudo tee /etc/nginx/sites-available/ovra-ai << 'EOF'
# OVRA AI Nginx Configuration
# Frontend: Next.js served by nginx on port 80
# Backend: Express.js proxied to port 8000

server {
    listen 80;
    server_name 167.99.143.136 localhost _;

    # Frontend - serve Next.js static files
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 86400;
    }

    # Backend API - proxy to Express.js
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 86400;
    }

    # Static files for backend
    location /static/ {
        alias /home/ovra_ai/backend/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
        try_files $uri =404;
    }

    # Uploads/media files
    location /uploads/ {
        alias /home/ovra_ai/backend/uploads/;
        expires 1y;
        add_header Cache-Control "public";
        try_files $uri =404;
    }

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;

    # Logs
    access_log /var/log/nginx/ovra-ai.access.log;
    error_log /var/log/nginx/ovra-ai.error.log;
}
EOF

# Enable the site
sudo ln -sf /etc/nginx/sites-available/ovra-ai /etc/nginx/sites-enabled/

# Create log directory
sudo mkdir -p /var/log/nginx

# Test nginx configuration
echo "🔍 Testing nginx configuration..."
sudo nginx -t

if [ $? -eq 0 ]; then
    echo "✅ Nginx configuration is valid!"

    # Enable and start nginx
    sudo systemctl enable nginx
    sudo systemctl start nginx

    echo "✅ Nginx configured and started successfully!"
    echo ""
    echo "📋 Configuration Summary:"
    echo "  🌐 Frontend: http://167.99.143.136:80 (nginx → Next.js:3000)"
    echo "  📡 Backend API: http://167.99.143.136:80/api/ (nginx → Express.js:8000)"
    echo ""
    echo "⚠️  Important Notes:"
    echo "  - Frontend runs on port 3000, proxied through nginx on port 80"
    echo "  - Backend API accessible via /api/ path on port 80"
    echo "  - Direct backend access: http://167.99.143.136:8000"
else
    echo "❌ Nginx configuration test failed!"
    exit 1
fi
