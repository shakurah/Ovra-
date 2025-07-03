#!/bin/bash

# Ovra AI - Start Services Script
# This script starts both backend and frontend services

set -e

PROJECT_ROOT="/home/ali/development/ovra_ai"
BACKEND_DIR="$PROJECT_ROOT/backend"
FRONTEND_DIR="$PROJECT_ROOT/frontend"

echo "🚀 Starting Ovra AI Services..."

# Function to check if port is in use
check_port() {
    local port=$1
    # Try multiple methods to check if port is in use
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0  # Port is in use
    elif netstat -ln 2>/dev/null | grep -q ":$port "; then
        return 0  # Port is in use
    elif ss -ln 2>/dev/null | grep -q ":$port "; then
        return 0  # Port is in use
    else
        return 1  # Port is free
    fi
}

# Function to start backend
start_backend() {
    echo "📡 Starting Django Backend..."
    
    if check_port 8000; then
        echo "⚠️  Backend already running on port 8000"
        return 0
    fi
    
    cd "$BACKEND_DIR"
    
    # Activate virtual environment and start Django
    source venv/bin/activate
    
    # Run migrations if needed
    echo "🔄 Checking for database migrations..."
    python manage.py migrate --check >/dev/null 2>&1 || {
        echo "📊 Running database migrations..."
        python manage.py migrate
    }
    
    # Start Django server in background on localhost
    echo "🌐 Starting Django server on localhost:8000..."
    nohup python manage.py runserver localhost:8000 > ../logs/backend.log 2>&1 &
    local backend_pid=$!
    echo $backend_pid > ../logs/backend.pid
    
    # Wait a moment and check if it started
    sleep 3
    if check_port 8000; then
        echo "✅ Backend started successfully"
    else
        echo "❌ Failed to start backend"
        return 1
    fi
}

# Function to start frontend
start_frontend() {
    echo "🎨 Starting Next.js Frontend..."
    
    if check_port 3000; then
        echo "⚠️  Frontend already running on port 3000"
        return 0
    fi
    
    cd "$FRONTEND_DIR"
    
    # Install dependencies if node_modules doesn't exist
    if [ ! -d "node_modules" ]; then
        echo "📦 Installing frontend dependencies..."
        npm install
    fi
    
    # Start Next.js in development mode on localhost
    echo "🌐 Starting Next.js server on localhost:3000..."
    nohup bash -c "HOST=localhost PORT=3000 npm run dev" > ../logs/frontend.log 2>&1 &
    local frontend_pid=$!
    echo $frontend_pid > ../logs/frontend.pid
    
    # Wait longer for Next.js to start and check multiple times
    local attempts=0
    local max_attempts=15
    while [ $attempts -lt $max_attempts ]; do
        sleep 2
        if check_port 3000; then
            echo "✅ Frontend started successfully"
            return 0
        fi
        # Also try HTTP check
        if curl -s http://localhost:3000 >/dev/null 2>&1; then
            echo "✅ Frontend started successfully (HTTP check)"
            return 0
        fi
        attempts=$((attempts + 1))
        echo "⏳ Waiting for frontend to start... ($attempts/$max_attempts)"
    done

    echo "❌ Failed to start frontend after $max_attempts attempts"
    echo "📝 Check logs: tail -f logs/frontend.log"
    echo "🔍 Debug info:"
    echo "   Port check: $(check_port 3000 && echo 'PASS' || echo 'FAIL')"
    echo "   HTTP check: $(curl -s http://localhost:3000 >/dev/null 2>&1 && echo 'PASS' || echo 'FAIL')"
    return 1
}

# Create logs directory if it doesn't exist
mkdir -p "$PROJECT_ROOT/logs"

# Start services
start_backend
start_frontend

echo ""
echo "🎉 Ovra AI Services Started Successfully!"
echo "📡 Backend:  http://localhost:8000"
echo "🎨 Frontend: http://localhost:3000"
echo ""
echo "📋 Service Management:"
echo "   Start:   ./scripts/start_services.sh"
echo "   Stop:    ./scripts/stop_services.sh"
echo "   Restart: ./scripts/restart_services.sh"
echo "   Status:  ./scripts/status_services.sh"
echo ""
echo "📝 Logs:"
echo "   Backend:  tail -f logs/backend.log"
echo "   Frontend: tail -f logs/frontend.log"
