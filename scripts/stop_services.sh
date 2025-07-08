#!/bin/bash

# Ovra AI - Stop Services Script
# This script stops all three services: backend, frontend, and MCP BOE

set -e

echo "🛑 Stopping Ovra AI Services..."

# Function to stop systemctl service
stop_service() {
    local service_name=$1
    local service_desc=$2
    
    echo "🔄 Stopping $service_desc..."
    
    if ! systemctl is-active --quiet "$service_name"; then
        echo "⚠️  $service_desc already stopped"
        return 0
    fi
    
    if sudo systemctl stop "$service_name"; then
        echo "✅ $service_desc stopped successfully"
        return 0
    else
        echo "❌ Failed to stop $service_desc"
        return 1
    fi
}

# Stop all services
stop_service "ovra-backend" "Backend Service"
stop_service "ovra-frontend" "Frontend Service"
stop_service "ovra-mcp-boe" "MCP BOE Service"

echo ""
echo "✅ All Ovra AI Services Stopped Successfully!"
echo ""
echo "📋 Service Management:"
echo "   Start:   ./scripts/start_services.sh"
echo "   Stop:    ./scripts/stop_services.sh"
echo "   Restart: ./scripts/restart_services.sh"
echo "   Status:  ./scripts/status_services.sh"
echo ""
echo "📝 View Logs:"
echo "   Backend:  sudo journalctl -u ovra-backend -f"
echo "   Frontend: sudo journalctl -u ovra-frontend -f"
echo "   MCP BOE:  sudo journalctl -u ovra-mcp-boe -f"
