#!/bin/bash

# OVRA AI Complete Ubuntu Server Deployment Script
# This script deploys OVRA AI on a fresh Ubuntu server with everything needed

set -e

PROJECT_ROOT="/home/ali/development/ovra_ai"
SCRIPTS_DIR="$PROJECT_ROOT/scripts"

echo "🚀 Starting Complete OVRA AI Deployment..."
echo "📍 Project Root: $PROJECT_ROOT"
echo ""

# Function to print colored output
print_step() {
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "🔹 $1"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

# Function to check if script exists and is executable
check_script() {
    if [ ! -f "$1" ]; then
        echo "❌ Script not found: $1"
        exit 1
    fi
    if [ ! -x "$1" ]; then
        echo "🔧 Making script executable: $1"
        chmod +x "$1"
    fi
}

# Ensure we're in the right directory
cd "$PROJECT_ROOT"

# Step 1: Install System Dependencies
print_step "Step 1: Installing System Dependencies"
check_script "$SCRIPTS_DIR/install_dependencies.sh"
bash "$SCRIPTS_DIR/install_dependencies.sh"

# Step 2: Install Project Dependencies
print_step "Step 2: Installing Project Dependencies"
check_script "$SCRIPTS_DIR/install_project.sh"
bash "$SCRIPTS_DIR/install_project.sh"

# Step 3: Configure Nginx for Direct Port Access
print_step "Step 3: Configuring Nginx"
check_script "$SCRIPTS_DIR/nginx_config.sh"
bash "$SCRIPTS_DIR/nginx_config.sh"

# Step 4: Install System Services
print_step "Step 4: Installing System Services"
check_script "$SCRIPTS_DIR/install_services.sh"
bash "$SCRIPTS_DIR/install_services.sh"

# Step 5: Create additional helper scripts
print_step "Step 5: Creating Helper Scripts"

# Create deployment status script
cat > "$SCRIPTS_DIR/deployment_status.sh" << 'EOF'
#!/bin/bash

echo "🔍 OVRA AI Deployment Status"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check system services
echo "📊 System Services:"
echo "  PostgreSQL: $(systemctl is-active postgresql)"
echo "  Nginx: $(systemctl is-active nginx)"
echo ""

# Check OVRA services
echo "🎯 OVRA Services:"
echo "  Backend: $(systemctl is-active ovra-backend)"
echo "  Frontend: $(systemctl is-active ovra-frontend)"
echo "  MCP BOE: $(systemctl is-active ovra-mcp-boe)"
echo ""

# Check ports
echo "🔌 Port Status:"
echo "  Port 80 (Frontend): $(netstat -tlnp | grep :80 | wc -l) connections"
echo "  Port 8000 (Backend): $(netstat -tlnp | grep :8000 | wc -l) connections"
echo "  Port 9000 (MCP BOE): $(netstat -tlnp | grep :9000 | wc -l) connections"
echo ""

# Check access URLs
echo "🌐 Access URLs:"
echo "  Frontend: http://localhost:80"
echo "  Backend API: http://localhost:8000"
echo "  MCP BOE Server: http://localhost:9000"
echo ""

# Check logs
echo "📄 Recent Logs:"
echo "  Backend: $(tail -n 1 /home/ali/development/ovra_ai/logs/backend.log 2>/dev/null || echo 'No logs yet')"
echo "  Frontend: $(tail -n 1 /home/ali/development/ovra_ai/logs/frontend.log 2>/dev/null || echo 'No logs yet')"
echo ""

# Database check
echo "🗄️  Database Status:"
if sudo -u postgres psql -c "SELECT 1" ovra_ai >/dev/null 2>&1; then
    echo "  Database: ✅ Connected"
else
    echo "  Database: ❌ Connection failed"
fi
EOF

# Create quick restart script
cat > "$SCRIPTS_DIR/quick_restart.sh" << 'EOF'
#!/bin/bash

echo "🔄 Restarting OVRA AI Services..."

# Stop services
sudo systemctl stop ovra-frontend ovra-backend ovra-mcp-boe

# Wait a moment
sleep 2

# Start services
sudo systemctl start ovra-backend ovra-frontend ovra-mcp-boe

# Check status
sleep 3
echo "📊 Service Status:"
sudo systemctl status ovra-backend --no-pager -l
sudo systemctl status ovra-frontend --no-pager -l
sudo systemctl status ovra-mcp-boe --no-pager -l

echo "✅ Restart complete!"
EOF

# Create update script
cat > "$SCRIPTS_DIR/update_project.sh" << 'EOF'
#!/bin/bash

echo "🔄 Updating OVRA AI Project..."

PROJECT_ROOT="/home/ali/development/ovra_ai"
cd "$PROJECT_ROOT"

# Stop services
sudo systemctl stop ovra-frontend ovra-backend ovra-mcp-boe

# Update git repo (if it's a git repo)
if [ -d ".git" ]; then
    echo "📦 Pulling latest changes..."
    git pull
fi

# Update backend
echo "🔧 Updating backend..."
cd "$PROJECT_ROOT/backend"
pnpm install
pnpm run db:generate
pnpm run db:push
if grep -q '"build"' package.json; then
    pnpm run build
fi

# Update frontend
echo "🎨 Updating frontend..."
cd "$PROJECT_ROOT/frontend"
pnpm install
pnpm run build

# Restart services
echo "🚀 Restarting services..."
sudo systemctl start ovra-backend ovra-frontend ovra-mcp-boe

echo "✅ Update complete!"
EOF

# Make helper scripts executable
chmod +x "$SCRIPTS_DIR/deployment_status.sh"
chmod +x "$SCRIPTS_DIR/quick_restart.sh"
chmod +x "$SCRIPTS_DIR/update_project.sh"

# Final deployment summary
print_step "Deployment Complete!"

echo "🎉 OVRA AI has been successfully deployed!"
echo ""
echo "📋 Deployment Summary:"
echo "  ✅ System dependencies installed"
echo "  ✅ Project dependencies installed"
echo "  ✅ Database configured"
echo "  ✅ System services installed"
echo "  ✅ Applications built and configured"
echo ""
echo "🔌 Service Configuration:"
echo "  🌐 Frontend (Next.js): Port 80 (direct)"
echo "  📡 Backend (Express.js): Port 8000 (direct)"
echo "  🔧 MCP BOE Server: Port 9000 (direct)"
echo ""
echo "🌐 Access URLs:"
echo "  Frontend: http://localhost:80"
echo "  Backend API: http://localhost:8000"
echo "  MCP BOE Server: http://localhost:9000"
echo ""
echo "🔧 Management Commands:"
echo "  Status: ./scripts/deployment_status.sh"
echo "  Restart: ./scripts/quick_restart.sh"
echo "  Update: ./scripts/update_project.sh"
echo "  Logs: sudo journalctl -u ovra-backend -f"
echo ""
echo "⚠️  Important Notes:"
echo "  - Frontend runs on port 80 (requires sudo privileges)"
echo "  - Backend runs on port 8000 (standard user)"
echo "  - MCP BOE runs on port 9000 (standard user)"
echo "  - All services are managed by systemd"
echo "  - Services auto-start on boot"
echo ""
echo "🔑 Database Details:"
echo "  Database: ovra_ai"
echo "  User: ovra_user"
echo "  Password: ovra_password"
echo "  Host: localhost:5432"
echo ""
echo "📁 Important Files:"
echo "  Backend config: $PROJECT_ROOT/backend/.env"
echo "  Frontend config: $PROJECT_ROOT/frontend/.env.local"
echo "  Service logs: $PROJECT_ROOT/logs/"
echo ""
echo "🚀 Your OVRA AI deployment is now ready!"
echo "Run './scripts/deployment_status.sh' to check the status anytime."