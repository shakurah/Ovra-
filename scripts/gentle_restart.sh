#!/bin/bash

# Ovra AI - Gentle Restart Services Script
# This script restarts services more gently to avoid VS Code connection issues

set -e

PROJECT_ROOT="/home/ali/development/ovra_ai"
BACKEND_DIR="$PROJECT_ROOT/backend"
FRONTEND_DIR="$PROJECT_ROOT/frontend"
LOGS_DIR="$PROJECT_ROOT/logs"

echo "🔄 Gently Restarting Ovra AI Services..."
echo "🔒 VS Code Safe: This script avoids aggressive process killing"

# Create logs directory if it doesn't exist
mkdir -p "$LOGS_DIR"

# Function to check if port is in use
check_port() {
    local port=$1
    lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1
}

# Function to gently stop service by PID file
gentle_stop_service() {
    local service_name=$1
    local pid_file="$LOGS_DIR/${service_name}.pid"
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if ps -p $pid > /dev/null 2>&1; then
            echo "🔄 Gently stopping $service_name (PID: $pid)..."
            # Use TERM signal first (gentler than KILL)
            kill -TERM $pid 2>/dev/null || true
            
            # Wait longer for graceful shutdown
            local count=0
            while ps -p $pid > /dev/null 2>&1 && [ $count -lt 15 ]; do
                sleep 1
                count=$((count + 1))
                echo "⏳ Waiting for $service_name to stop gracefully... ($count/15)"
            done
            
            # Only force kill if absolutely necessary
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

# Function to gently stop by port (more selective)
gentle_stop_by_port() {
    local port=$1
    local service_name=$2

    # Skip SSH port for safety
    if [ "$port" = "22" ]; then
        echo "⚠️  Skipping SSH port 22 for safety"
        return 0
    fi

    # Only target specific processes, not all processes on the port
    local pids=$(lsof -ti:$port 2>/dev/null || true)
    if [ -n "$pids" ]; then
        echo "🔄 Gently stopping $service_name processes on port $port..."
        for pid in $pids; do
            process_name=$(ps -p $pid -o comm= 2>/dev/null || echo "unknown")
            process_cmd=$(ps -p $pid -o cmd= 2>/dev/null || echo "unknown")
            
            # Skip SSH and VS Code related processes
            if [[ "$process_name" == *"ssh"* ]] || [[ "$process_cmd" == *"ssh"* ]] || [[ "$process_cmd" == *"code"* ]] || [[ "$process_cmd" == *"vscode"* ]]; then
                echo "⚠️  Skipping protected process (PID: $pid, Name: $process_name)"
                continue
            fi
            
            # Only target our specific services
            if [[ "$process_cmd" == *"manage.py runserver"* ]] || [[ "$process_cmd" == *"next dev"* ]] || [[ "$process_cmd" == *"npm run dev"* ]]; then
                echo "🔄 Gently stopping process $pid ($process_name) on port $port"
                kill -TERM $pid 2>/dev/null || true
                sleep 2  # Give time for graceful shutdown
            else
                echo "⚠️  Skipping unrelated process: $process_cmd"
            fi
        done
        echo "✅ $service_name processes stopped"
    fi
}

# Gentle restart backend
echo "📡 Gently restarting Django Backend..."
gentle_stop_service "backend"
gentle_stop_by_port 8000 "backend"

# Wait a moment before starting
echo "⏳ Waiting for backend cleanup..."
sleep 3

# Start backend
if ! check_port 8000; then
    cd "$BACKEND_DIR"
    source venv/bin/activate
    
    echo "🌐 Starting Django server on localhost:8000..."
    nohup python manage.py runserver localhost:8000 > ../logs/backend.log 2>&1 &
    backend_pid=$!
    echo $backend_pid > ../logs/backend.pid
    
    # Wait and verify
    sleep 3
    if check_port 8000; then
        echo "✅ Backend restarted successfully"
    else
        echo "❌ Failed to restart backend"
    fi
else
    echo "⚠️  Backend port still in use, skipping restart"
fi

# Gentle restart frontend
echo "🎨 Gently restarting Next.js Frontend..."
gentle_stop_service "frontend"
gentle_stop_by_port 3000 "frontend"

# Wait a moment before starting
echo "⏳ Waiting for frontend cleanup..."
sleep 3

# Start frontend
if ! check_port 3000; then
    cd "$FRONTEND_DIR"
    
    echo "🌐 Starting Next.js server on localhost:3000..."
    nohup bash -c "HOST=localhost PORT=3000 npm run dev" > ../logs/frontend.log 2>&1 &
    frontend_pid=$!
    echo $frontend_pid > ../logs/frontend.pid

    # Wait longer for Next.js
    attempts=0
    max_attempts=10
    while [ $attempts -lt $max_attempts ]; do
        sleep 3
        if check_port 3000; then
            echo "✅ Frontend restarted successfully"
            break
        fi
        attempts=$((attempts + 1))
        echo "⏳ Waiting for frontend to start... ($attempts/$max_attempts)"
    done
    
    if [ $attempts -eq $max_attempts ]; then
        echo "❌ Frontend restart may have failed, check logs"
    fi
else
    echo "⚠️  Frontend port still in use, skipping restart"
fi

echo ""
echo "🎉 Ovra AI Services Gently Restarted!"
echo "📡 Backend:  http://localhost:8000"
echo "🎨 Frontend: http://localhost:3000"
echo ""
echo "💡 This gentle restart should not affect VS Code connections"
echo "📝 Check logs if services don't start properly:"
echo "   Backend:  tail -f logs/backend.log"
echo "   Frontend: tail -f logs/frontend.log"
