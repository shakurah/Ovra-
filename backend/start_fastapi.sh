#!/bin/bash

# Ovra AI FastAPI Backend Startup Script

set -e

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "🚀 Starting Ovra AI FastAPI Backend..."
echo "📁 Working Directory: $SCRIPT_DIR"

# Activate virtual environment
source "$SCRIPT_DIR/venv/bin/activate"

# Run database migrations
echo "📦 Running database migrations..."
alembic upgrade head

# Start FastAPI server
echo "🌟 Starting FastAPI server..."
exec uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4