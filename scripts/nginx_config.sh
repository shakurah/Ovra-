#!/bin/bash

# Configure Nginx for OVRA AI - Direct Port Configuration
echo "🌐 Configuring Nginx for OVRA AI (Direct Port Access)..."

# Since frontend runs on port 80 and backend on port 8000, we'll disable nginx proxy
# and just use nginx for serving static files and optional SSL termination

# Disable nginx service to avoid port conflicts
echo "🛑 Disabling nginx service to avoid port conflicts..."
sudo systemctl stop nginx
sudo systemctl disable nginx

# Remove nginx sites
sudo rm -f /etc/nginx/sites-enabled/ovra-ai
sudo rm -f /etc/nginx/sites-enabled/default

# Create a simple nginx configuration for port 8080 (as backup/admin interface)
sudo tee /etc/nginx/sites-available/ovra-ai-admin << 'EOF'
# OVRA AI Admin Interface on port 8080
# Frontend: Next.js on port 80 (direct)
# Backend: Express.js on port 8000 (direct)
# MCP BOE: SSE Server on port 9000 (direct)

server {
    listen 8080;
    server_name localhost ovra.local _;
    
    # Simple status page
    location / {
        return 200 "OVRA AI Services Status\n\nFrontend: http://localhost:80\nBackend: http://localhost:8000\nMCP BOE: http://localhost:9000\n\nAll services are running directly on their respective ports.\n";
        add_header Content-Type text/plain;
    }
    
    # Static files for backend (if any)
    location /static/ {
        alias /home/ali/development/ovra_ai/backend/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
        try_files $uri =404;
    }
    
    # Uploads/media files (if any)
    location /uploads/ {
        alias /home/ali/development/ovra_ai/backend/uploads/;
        expires 1y;
        add_header Cache-Control "public";
        try_files $uri =404;
    }
    
    # Logs
    access_log /var/log/nginx/ovra-ai-admin.access.log;
    error_log /var/log/nginx/ovra-ai-admin.error.log;
}
EOF

# Create log directory
sudo mkdir -p /var/log/nginx

echo "✅ Nginx configuration updated for direct port access!"
echo ""
echo "📋 Configuration Summary:"
echo "  🌐 Frontend (Next.js): http://localhost:80 (direct)"
echo "  📡 Backend API: http://localhost:8000 (direct)"  
echo "  🔧 MCP BOE Server: http://localhost:9000 (direct)"
echo "  🛠️  Admin Interface: http://localhost:8080 (nginx, optional)"
echo ""
echo "⚠️  Important Notes:"
echo "  - Services run directly on their ports (no proxy)"
echo "  - Frontend requires sudo/root to bind to port 80"
echo "  - Nginx is disabled to avoid port conflicts"
echo "  - Admin interface on port 8080 can be enabled if needed"
echo ""
echo "🔧 To enable admin interface on port 8080:"
echo "  sudo ln -sf /etc/nginx/sites-available/ovra-ai-admin /etc/nginx/sites-enabled/"
echo "  sudo systemctl enable nginx"
echo "  sudo systemctl start nginx"
