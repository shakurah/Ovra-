#!/bin/bash

# Ovra AI - Restart Services Script
# This script restarts both backend and frontend services

set -e

PROJECT_ROOT="/home/ali/development/ovra_ai"
SCRIPTS_DIR="$PROJECT_ROOT/scripts"

echo "🔄 Restarting Ovra AI Services..."

# Stop services first
echo "1️⃣ Stopping existing services..."
bash "$SCRIPTS_DIR/stop_services.sh"

# Wait a moment for cleanup
echo "⏳ Waiting for cleanup..."
sleep 2

# Start services
echo "2️⃣ Starting services..."
bash "$SCRIPTS_DIR/start_services.sh"

echo ""
echo "🎉 Ovra AI Services Restarted Successfully!"
