#!/bin/bash

# Ovra AI - Test Services Script
# This script tests both backend and frontend services

PROJECT_ROOT="/home/ali/development/ovra_ai"

echo "🧪 Testing Ovra AI Services..."

# Function to test HTTP endpoint
test_endpoint() {
    local url=$1
    local name=$2
    local expected_status=${3:-200}
    
    echo "🔍 Testing $name: $url"
    
    local response=$(curl -s -w "%{http_code}" -o /dev/null "$url" 2>/dev/null)
    
    if [ "$response" = "$expected_status" ]; then
        echo "✅ $name: OK (HTTP $response)"
        return 0
    else
        echo "❌ $name: FAILED (HTTP $response, expected $expected_status)"
        return 1
    fi
}

# Function to test JSON API endpoint
test_api_endpoint() {
    local url=$1
    local name=$2
    
    echo "🔍 Testing $name API: $url"
    
    local response=$(curl -s -H "Content-Type: application/json" "$url" 2>/dev/null)
    local status=$?
    
    if [ $status -eq 0 ] && [ -n "$response" ]; then
        echo "✅ $name API: OK"
        echo "   Response: $(echo "$response" | head -c 100)..."
        return 0
    else
        echo "❌ $name API: FAILED"
        return 1
    fi
}

echo ""
echo "📡 Testing Backend Services..."

# Test Django backend - local and external access
test_endpoint "http://localhost:8000" "Django Backend (localhost)" 404  # 404 is expected for root
test_endpoint "http://0.0.0.0:8000" "Django Backend (external)" 404  # 404 is expected for root
test_api_endpoint "http://localhost:8000/api/v1/" "Django API Root (localhost)"
test_api_endpoint "http://0.0.0.0:8000/api/v1/" "Django API Root (external)"

echo ""
echo "🎨 Testing Frontend Services..."

# Test Next.js frontend - local and external access
test_endpoint "http://localhost:3000" "Next.js Frontend (localhost)" 200
test_endpoint "http://0.0.0.0:3000" "Next.js Frontend (external)" 200
test_endpoint "http://localhost:3000/login" "Login Page (localhost)" 200
test_endpoint "http://localhost:3000/signup" "Signup Page (localhost)" 200

echo ""
echo "🔗 Testing Service Integration..."

# Test if frontend can reach backend
echo "🔍 Testing frontend-backend connectivity..."
if curl -s http://localhost:3000 | grep -q "localhost:8000\|api"; then
    echo "✅ Frontend-Backend Integration: OK"
else
    echo "⚠️  Frontend-Backend Integration: Cannot verify"
fi

echo ""
echo "🌐 Testing External Accessibility..."

# Get the server's IP address
SERVER_IP=$(hostname -I | awk '{print $1}')
echo "📡 Server IP: $SERVER_IP"

if [ -n "$SERVER_IP" ]; then
    echo "🔍 Testing external access via IP..."
    test_endpoint "http://$SERVER_IP:3000" "Frontend via IP" 200
    test_endpoint "http://$SERVER_IP:8000" "Backend via IP" 404
else
    echo "⚠️  Could not determine server IP for external testing"
fi

echo ""
echo "📊 Service Health Summary:"
echo "=========================="

# Check service status
if curl -s http://localhost:8000 >/dev/null 2>&1; then
    echo "📡 Backend:  ✅ HEALTHY"
else
    echo "📡 Backend:  ❌ UNHEALTHY"
fi

if curl -s http://localhost:3000 >/dev/null 2>&1; then
    echo "🎨 Frontend: ✅ HEALTHY"
else
    echo "🎨 Frontend: ❌ UNHEALTHY"
fi

echo ""
echo "🌐 Service URLs:"
echo "   Local Frontend:    http://localhost:3000"
echo "   External Frontend: http://0.0.0.0:3000"
echo "   Local Backend:     http://localhost:8000"
echo "   External Backend:  http://0.0.0.0:8000"
echo "   API:               http://localhost:8000/api/v1/"
if [ -n "$SERVER_IP" ]; then
    echo ""
    echo "🌍 External Access (via IP):"
    echo "   Frontend: http://$SERVER_IP:3000"
    echo "   Backend:  http://$SERVER_IP:8000"
    echo "   API:      http://$SERVER_IP:8000/api/v1/"
fi
echo ""
echo "📋 Next Steps:"
echo "   1. Open http://localhost:3000 in your browser"
echo "   2. Test user registration and login"
echo "   3. Try the chat functionality"
echo "   4. Check language switching (EN/ES)"
echo "   5. Test external access from another machine using server IP"
