#!/bin/bash

# Ovra AI - Install System Services Script
# This script installs Ovra AI as systemd services

set -e

PROJECT_ROOT="/home/ali/development/ovra_ai"
SCRIPTS_DIR="$PROJECT_ROOT/scripts"
LOGS_DIR="$PROJECT_ROOT/logs"

echo "🔧 Installing Ovra AI System Services..."

# Create logs directory
mkdir -p "$LOGS_DIR"

# Stop any existing manual processes
echo "🛑 Stopping any existing manual processes..."
pkill -f "manage.py runserver" 2>/dev/null || true
pkill -f "next dev" 2>/dev/null || true
pkill -f "npm run dev" 2>/dev/null || true
sleep 2

# Copy service files to systemd directory
echo "📋 Installing service files..."
sudo cp "$SCRIPTS_DIR/ovra-backend.service" /etc/systemd/system/
sudo cp "$SCRIPTS_DIR/ovra-frontend.service" /etc/systemd/system/

# Set proper permissions
sudo chmod 644 /etc/systemd/system/ovra-backend.service
sudo chmod 644 /etc/systemd/system/ovra-frontend.service

# Reload systemd daemon
echo "🔄 Reloading systemd daemon..."
sudo systemctl daemon-reload

# Enable services to start on boot
echo "⚡ Enabling services to start on boot..."
sudo systemctl enable ovra-backend.service
sudo systemctl enable ovra-frontend.service

# Start services
echo "🚀 Starting services..."
sudo systemctl start ovra-backend.service
sudo systemctl start ovra-frontend.service

# Wait a moment for services to start
sleep 5

# Check service status
echo ""
echo "📊 Service Status:"
echo "Backend:"
sudo systemctl status ovra-backend.service --no-pager -l
echo ""
echo "Frontend:"
sudo systemctl status ovra-frontend.service --no-pager -l

echo ""
echo "🎉 Ovra AI Services Installed Successfully!"
echo "📡 Backend:  http://localhost:8000"
echo "🎨 Frontend: http://localhost:3000"
echo ""
echo "🔧 Service Management Commands:"
echo "   Start:   sudo systemctl start ovra-backend ovra-frontend"
echo "   Stop:    sudo systemctl stop ovra-backend ovra-frontend"
echo "   Restart: sudo systemctl restart ovra-backend ovra-frontend"
echo "   Status:  sudo systemctl status ovra-backend ovra-frontend"
echo "   Logs:    sudo journalctl -u ovra-backend -f"
echo "            sudo journalctl -u ovra-frontend -f"
echo ""
echo "📝 Log Files:"
echo "   Backend:  tail -f $LOGS_DIR/backend.log"
echo "   Frontend: tail -f $LOGS_DIR/frontend.log"
