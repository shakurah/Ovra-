#!/bin/bash

# Ovra AI - Stop Services Script
# This script stops both backend and frontend services

set -e

PROJECT_ROOT="/home/ali/development/ovra_ai"
LOGS_DIR="$PROJECT_ROOT/logs"

echo "🛑 Stopping Ovra AI Services..."
echo "🔒 SSH Protection: This script will NOT affect SSH services (port 22)"

# Function to stop service by PID file
stop_service() {
    local service_name=$1
    local pid_file="$LOGS_DIR/${service_name}.pid"
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if ps -p $pid > /dev/null 2>&1; then
            echo "🔄 Stopping $service_name (PID: $pid)..."
            # Use TERM signal first (gentler)
            kill -TERM $pid 2>/dev/null || kill $pid

            # Wait longer for graceful shutdown
            local count=0
            while ps -p $pid > /dev/null 2>&1 && [ $count -lt 15 ]; do
                sleep 1
                count=$((count + 1))
                if [ $count -eq 5 ]; then
                    echo "⏳ Waiting for graceful shutdown..."
                fi
            done

            # Force kill only as last resort
            if ps -p $pid > /dev/null 2>&1; then
                echo "⚡ Force stopping $service_name (last resort)..."
                kill -9 $pid 2>/dev/null || true
                sleep 1
            fi
            
            echo "✅ $service_name stopped"
        else
            echo "⚠️  $service_name process not found (PID: $pid)"
        fi
        rm -f "$pid_file"
    else
        echo "⚠️  No PID file found for $service_name"
    fi
}

# Function to stop processes by port (with SSH protection)
stop_by_port() {
    local port=$1
    local service_name=$2

    # Skip SSH port for safety
    if [ "$port" = "22" ]; then
        echo "⚠️  Skipping SSH port 22 for safety"
        return 0
    fi

    local pids=$(lsof -ti:$port 2>/dev/null || true)
    if [ -n "$pids" ]; then
        echo "🔄 Stopping $service_name processes on port $port..."
        # Additional safety check - verify these are not SSH or VS Code processes
        for pid in $pids; do
            process_name=$(ps -p $pid -o comm= 2>/dev/null || echo "unknown")
            process_cmd=$(ps -p $pid -o cmd= 2>/dev/null || echo "unknown")

            # Skip SSH, VS Code, and other protected processes
            if [[ "$process_name" == *"ssh"* ]] || [[ "$process_cmd" == *"ssh"* ]] || [[ "$process_cmd" == *"code"* ]] || [[ "$process_cmd" == *"vscode"* ]]; then
                echo "⚠️  Skipping protected process (PID: $pid, Name: $process_name)"
                continue
            fi

            echo "🔄 Gently stopping process $pid ($process_name) on port $port"
            # Try TERM first, then KILL
            kill -TERM $pid 2>/dev/null || true
            sleep 1
            if ps -p $pid > /dev/null 2>&1; then
                kill -9 $pid 2>/dev/null || true
            fi
        done
        echo "✅ $service_name processes stopped"
    fi
}

# Stop backend
echo "📡 Stopping Django Backend..."
stop_service "backend"
stop_by_port 8000 "backend"

# Stop frontend
echo "🎨 Stopping Next.js Frontend..."
stop_service "frontend"
stop_by_port 3000 "frontend"

# Clean up any remaining Node.js processes related to our project (with SSH protection)
echo "🧹 Cleaning up remaining processes..."
# Use more specific patterns and check for SSH processes
if pgrep -f "next dev" >/dev/null 2>&1; then
    echo "🔄 Found Next.js dev processes, checking for safety..."
    pgrep -f "next dev" | while read pid; do
        process_cmd=$(ps -p $pid -o cmd= 2>/dev/null || echo "unknown")
        if [[ "$process_cmd" == *"ssh"* ]]; then
            echo "⚠️  Skipping SSH-related process: $process_cmd"
        else
            echo "🔄 Killing Next.js process: $pid"
            kill $pid 2>/dev/null || true
        fi
    done
fi

if pgrep -f "manage.py runserver" >/dev/null 2>&1; then
    echo "🔄 Found Django runserver processes, checking for safety..."
    pgrep -f "manage.py runserver" | while read pid; do
        process_cmd=$(ps -p $pid -o cmd= 2>/dev/null || echo "unknown")
        if [[ "$process_cmd" == *"ssh"* ]]; then
            echo "⚠️  Skipping SSH-related process: $process_cmd"
        else
            echo "🔄 Killing Django process: $pid"
            kill $pid 2>/dev/null || true
        fi
    done
fi

# Additional cleanup for stubborn processes
echo "🔍 Final cleanup check..."
stop_by_port 8000 "any remaining backend"
stop_by_port 3000 "any remaining frontend"

# Wait a moment for processes to fully terminate
sleep 1

echo ""
echo "✅ All Ovra AI Services Stopped Successfully!"
echo ""
echo "📋 Service Management:"
echo "   Start:   ./scripts/start_services.sh"
echo "   Stop:    ./scripts/stop_services.sh"
echo "   Restart: ./scripts/restart_services.sh"
echo "   Status:  ./scripts/status_services.sh"
