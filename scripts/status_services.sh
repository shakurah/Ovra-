#!/bin/bash

# Ovra AI - Status Services Script
# This script checks the status of both backend and frontend services

PROJECT_ROOT="/home/ali/development/ovra_ai"
LOGS_DIR="$PROJECT_ROOT/logs"

echo "📊 Ovra AI Services Status"
echo "=========================="

# Function to check if port is in use
check_port() {
    local port=$1
    # Try multiple methods to check if port is in use
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0  # Port is in use
    elif ss -ln 2>/dev/null | grep -q ":$port "; then
        return 0  # Port is in use
    else
        return 1  # Port is free
    fi
}

# Function to get process info by port
get_process_info() {
    local port=$1
    # Try lsof first
    local info=$(lsof -Pi :$port -sTCP:LISTEN 2>/dev/null | tail -n +2 | awk '{print $2, $1}' | head -1)
    if [ -n "$info" ]; then
        echo "$info"
        return
    fi

    # Try ss as fallback
    local ss_info=$(ss -tlnp 2>/dev/null | grep ":$port " | head -1)
    if [ -n "$ss_info" ]; then
        # Extract PID from ss output (format: users:(("process",pid=12345,fd=1)))
        local pid=$(echo "$ss_info" | sed -n 's/.*pid=\([0-9]*\).*/\1/p')
        local process=$(echo "$ss_info" | sed -n 's/.*users:(("\([^"]*\)".*/\1/p')
        echo "$pid $process"
    fi
}

# Function to check service status
check_service_status() {
    local service_name=$1
    local port=$2
    local pid_file="$LOGS_DIR/${service_name}.pid"
    
    echo ""
    echo "🔍 $service_name Service:"
    echo "   Port: $port"
    
    if check_port $port; then
        local process_info=$(get_process_info $port)
        local pid=$(echo $process_info | awk '{print $1}')
        local process_name=$(echo $process_info | awk '{print $2}')
        
        echo "   Status: ✅ RUNNING"
        echo "   PID: $pid"
        echo "   Process: $process_name"
        echo "   URL: http://localhost:$port"
        
        # Check if PID file exists and matches
        if [ -f "$pid_file" ]; then
            local stored_pid=$(cat "$pid_file")
            if [ "$pid" = "$stored_pid" ]; then
                echo "   PID File: ✅ MATCH"
            else
                echo "   PID File: ⚠️  MISMATCH (stored: $stored_pid, actual: $pid)"
            fi
        else
            echo "   PID File: ⚠️  MISSING"
        fi
    else
        echo "   Status: ❌ NOT RUNNING"
        echo "   URL: http://localhost:$port (unavailable)"
        
        if [ -f "$pid_file" ]; then
            local stored_pid=$(cat "$pid_file")
            echo "   PID File: ⚠️  STALE (PID: $stored_pid)"
        else
            echo "   PID File: ✅ CLEAN"
        fi
    fi
}

# Check backend status
check_service_status "Backend" 8000

# Check frontend status  
check_service_status "Frontend" 3000

echo ""
echo "📝 Log Files:"
if [ -f "$LOGS_DIR/backend.log" ]; then
    echo "   Backend:  logs/backend.log ($(wc -l < "$LOGS_DIR/backend.log") lines)"
else
    echo "   Backend:  logs/backend.log (not found)"
fi

if [ -f "$LOGS_DIR/frontend.log" ]; then
    echo "   Frontend: logs/frontend.log ($(wc -l < "$LOGS_DIR/frontend.log") lines)"
else
    echo "   Frontend: logs/frontend.log (not found)"
fi

echo ""
echo "📋 Service Management:"
echo "   Start:   ./scripts/start_services.sh"
echo "   Stop:    ./scripts/stop_services.sh"
echo "   Restart: ./scripts/restart_services.sh"
echo "   Status:  ./scripts/status_services.sh"
echo ""
echo "📝 View Logs:"
echo "   Backend:  tail -f logs/backend.log"
echo "   Frontend: tail -f logs/frontend.log"
