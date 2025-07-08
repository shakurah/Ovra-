#!/bin/bash

# Ovra AI - Start Services Script
# This script starts all three services: backend, frontend, and MCP BOE

set -e

echo "🚀 Starting Ovra AI Services..."

# Function to start systemctl service
start_service() {
    local service_name=$1
    local service_desc=$2
    
    echo "🔄 Starting $service_desc..."
    
    if systemctl is-active --quiet "$service_name"; then
        echo "⚠️  $service_desc already running"
        return 0
    fi
    
    if sudo systemctl start "$service_name"; then
        echo "✅ $service_desc started successfully"
        return 0
    else
        echo "❌ Failed to start $service_desc"
        return 1
    fi
}

# Start all services
start_service "ovra-backend" "Backend Service"
start_service "ovra-frontend" "Frontend Service"
start_service "ovra-mcp-boe" "MCP BOE Service"

echo ""
echo "🎉 All Ovra AI Services Started Successfully!"
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
