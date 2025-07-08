#!/bin/bash

# Ovra AI - Status Services Script  
# This script checks the status of all three services: backend, frontend, and MCP BOE

echo "📊 Ovra AI Services Status"
echo "=========================="

# Function to check systemctl service status
check_service_status() {
    local service_name=$1
    local service_desc=$2
    local port=$3
    
    echo ""
    echo "🔍 $service_desc:"
    echo "   Service: $service_name"
    
    if systemctl is-active --quiet "$service_name"; then
        echo "   Status: ✅ RUNNING"
        echo "   Enabled: $(systemctl is-enabled $service_name 2>/dev/null || echo 'unknown')"
        
        # Get main PID if available
        local main_pid=$(systemctl show -p MainPID --value "$service_name" 2>/dev/null)
        if [ -n "$main_pid" ] && [ "$main_pid" != "0" ]; then
            echo "   PID: $main_pid"
        fi
        
        # Show port if provided
        if [ -n "$port" ]; then
            echo "   Port: $port"
            echo "   URL: http://localhost:$port"
        fi
        
        # Get uptime
        local since=$(systemctl show -p ActiveEnterTimestamp --value "$service_name" 2>/dev/null)
        if [ -n "$since" ]; then
            echo "   Started: $since"
        fi
    else
        echo "   Status: ❌ NOT RUNNING"
        echo "   Enabled: $(systemctl is-enabled $service_name 2>/dev/null || echo 'unknown')"
        
        if [ -n "$port" ]; then
            echo "   Port: $port"
            echo "   URL: http://localhost:$port (unavailable)"
        fi
        
        # Show last exit status if failed
        local exit_code=$(systemctl show -p ExecMainStatus --value "$service_name" 2>/dev/null)
        if [ -n "$exit_code" ] && [ "$exit_code" != "0" ]; then
            echo "   Exit Code: $exit_code"
        fi
    fi
}

# Check all services
check_service_status "ovra-backend" "Backend Service" "8000"
check_service_status "ovra-frontend" "Frontend Service" "3000"  
check_service_status "ovra-mcp-boe" "MCP BOE Service"

echo ""
echo "📝 Service Logs (last 3 lines):"
echo "   Backend:"
sudo journalctl -u ovra-backend -n 3 --no-pager 2>/dev/null | sed 's/^/     /' || echo "     (Unable to read logs)"

echo "   Frontend:"
sudo journalctl -u ovra-frontend -n 3 --no-pager 2>/dev/null | sed 's/^/     /' || echo "     (Unable to read logs)"

echo "   MCP BOE:"
sudo journalctl -u ovra-mcp-boe -n 3 --no-pager 2>/dev/null | sed 's/^/     /' || echo "     (Unable to read logs)"

echo ""
echo "📋 Service Management:"
echo "   Start:   ./scripts/start_services.sh"
echo "   Stop:    ./scripts/stop_services.sh"
echo "   Restart: ./scripts/restart_services.sh"
echo "   Status:  ./scripts/status_services.sh"
echo ""
echo "📝 View Full Logs:"
echo "   Backend:  sudo journalctl -u ovra-backend -f"
echo "   Frontend: sudo journalctl -u ovra-frontend -f"
echo "   MCP BOE:  sudo journalctl -u ovra-mcp-boe -f"
