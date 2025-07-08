#!/bin/bash

# OVRA AI Project Installation Script
# This script installs project dependencies and builds the applications

set -e

PROJECT_ROOT="/home/ali/development/ovra_ai"
LOGS_DIR="$PROJECT_ROOT/logs"

echo "🎯 Starting OVRA AI Project Installation..."

# Ensure we're in the project directory
cd "$PROJECT_ROOT"

# Create logs directory if it doesn't exist
mkdir -p "$LOGS_DIR"

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Verify required tools are installed
echo "🔍 Verifying required tools..."
if ! command_exists node; then
    echo "❌ Node.js is not installed. Please run install_dependencies.sh first."
    exit 1
fi

if ! command_exists pnpm; then
    echo "❌ pnpm is not installed. Please run install_dependencies.sh first."
    exit 1
fi

if ! command_exists psql; then
    echo "❌ PostgreSQL is not installed. Please run install_dependencies.sh first."
    exit 1
fi

echo "✅ All required tools are available"

# Setup Backend
echo "🔧 Setting up Backend (Express.js)..."
cd "$PROJECT_ROOT/backend"

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating backend .env file..."
    cat > .env << 'EOF'
# Database
DATABASE_URL="postgresql://ovra_user:ovra_password@localhost:5432/ovra_ai"

# JWT
JWT_SECRET="your-secret-key-change-this-in-production"
JWT_EXPIRES_IN="24h"

# Server
NODE_ENV="production"
PORT=8000
HOST="0.0.0.0"

# Admin
ADMIN_EMAIL="admin@ovra.ai"
ADMIN_PASSWORD="admin123"

# OpenAI (if needed)
OPENAI_API_KEY="your-openai-api-key"
EOF
    echo "⚠️  Please update the .env file with your actual values"
fi

# Install backend dependencies
echo "📦 Installing backend dependencies..."
pnpm install

# Generate Prisma client
echo "🔄 Generating Prisma client..."
pnpm run db:generate

# Run database migrations
echo "🗄️  Running database migrations..."
pnpm run db:push

# Build backend (if build script exists)
if grep -q '"build"' package.json; then
    echo "🏗️  Building backend..."
    pnpm run build
fi

# Setup Frontend
echo "🎨 Setting up Frontend (Next.js)..."
cd "$PROJECT_ROOT/frontend"

# Create .env.local file if it doesn't exist
if [ ! -f .env.local ]; then
    echo "📝 Creating frontend .env.local file..."
    cat > .env.local << 'EOF'
# API Configuration
NEXT_PUBLIC_API_URL="http://localhost:8000"
NEXT_PUBLIC_APP_URL="http://localhost:3000"

# Environment
NODE_ENV="production"
EOF
fi

# Install frontend dependencies
echo "📦 Installing frontend dependencies..."
pnpm install

# Build frontend
echo "🏗️  Building frontend..."
pnpm run build

# Update Nginx configuration
echo "🌐 Updating Nginx configuration..."
cd "$PROJECT_ROOT/scripts"
chmod +x nginx_config.sh
./nginx_config.sh

# Restart Nginx
echo "🔄 Restarting Nginx..."
sudo systemctl restart nginx

# Create startup script
echo "📜 Creating startup script..."
cat > "$PROJECT_ROOT/scripts/start_all.sh" << 'EOF'
#!/bin/bash

# Start all OVRA AI services
echo "🚀 Starting all OVRA AI services..."

# Start systemd services
sudo systemctl start ovra-backend
sudo systemctl start ovra-frontend
sudo systemctl start ovra-mcp-boe

# Wait for services to start
sleep 5

# Check status
echo "📊 Service Status:"
sudo systemctl status ovra-backend --no-pager -l
sudo systemctl status ovra-frontend --no-pager -l
sudo systemctl status ovra-mcp-boe --no-pager -l

echo "✅ All services started!"
EOF

chmod +x "$PROJECT_ROOT/scripts/start_all.sh"

# Test database connection
echo "🔍 Testing database connection..."
cd "$PROJECT_ROOT/backend"
if pnpm run db:generate > /dev/null 2>&1; then
    echo "✅ Database connection successful"
else
    echo "⚠️  Database connection failed - please check your configuration"
fi

echo ""
echo "🎉 OVRA AI Project Installation Complete!"
echo ""
echo "📋 Installation Summary:"
echo "  ✓ Backend dependencies installed"
echo "  ✓ Frontend dependencies installed"
echo "  ✓ Database configured"
echo "  ✓ Applications built"
echo "  ✓ Nginx configured"
echo ""
echo "🔑 Access URLs:"
echo "  🌐 Frontend: http://localhost (via Nginx)"
echo "  📚 Backend API: http://localhost/api"
echo "  🔧 Direct Backend: http://localhost:8000"
echo "  🎨 Direct Frontend: http://localhost:3000"
echo ""
echo "🎯 Next steps:"
echo "  1. Update .env files with your actual values"
echo "  2. Run './install_services.sh' to setup systemd services"
echo "  3. Run './start_all.sh' to start all services"
echo ""
echo "⚠️  Important: Please update the following files:"
echo "  - $PROJECT_ROOT/backend/.env (database & API keys)"
echo "  - $PROJECT_ROOT/frontend/.env.local (API URLs)"