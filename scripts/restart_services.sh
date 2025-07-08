#!/bin/bash

# Ovra AI - Restart Services Script
# This script restarts all three services: backend, frontend, and MCP BOE

set -e

echo "🔄 Restarting Ovra AI Services..."

# Function to restart systemctl service
restart_service() {
    local service_name=$1
    local service_desc=$2
    
    echo "🔄 Restarting $service_desc..."
    
    if sudo systemctl restart "$service_name"; then
        echo "✅ $service_desc restarted successfully"
        return 0
    else
        echo "❌ Failed to restart $service_desc"
        return 1
    fi
}

# Restart all services
restart_service "ovra-backend" "Backend Service"
restart_service "ovra-frontend" "Frontend Service"
restart_service "ovra-mcp-boe" "MCP BOE Service"

echo ""
echo "🎉 All Ovra AI Services Restarted Successfully!"
echo "📡 Backend:   http://localhost:8000"
echo "🎨 Frontend:  http://localhost:3000"
echo "🤖 MCP BOE:   Running on configured port"
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
