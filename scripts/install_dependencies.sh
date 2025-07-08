#!/bin/bash

# Comprehensive Ubuntu Server Setup for OVRA AI
# This script installs everything needed for a fresh Ubuntu server deployment

set -e

echo "🚀 Starting OVRA AI Ubuntu Server Setup..."

# Update system packages
echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install essential system packages
echo "🔧 Installing essential system packages..."
sudo apt install -y \
    curl \
    wget \
    git \
    build-essential \
    software-properties-common \
    apt-transport-https \
    ca-certificates \
    gnupg \
    lsb-release \
    unzip \
    vim \
    htop \
    ufw

# Install PostgreSQL
echo "🐘 Installing PostgreSQL..."
sudo apt install -y postgresql postgresql-contrib libpq-dev
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create database and user
echo "🔐 Setting up PostgreSQL database..."
sudo -u postgres psql -c "CREATE DATABASE ovra_ai;"
sudo -u postgres psql -c "CREATE USER ovra_user WITH PASSWORD 'ovra_password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE ovra_ai TO ovra_user;"
sudo -u postgres psql -c "ALTER USER ovra_user CREATEDB;"

# Install Node.js 18.x (LTS)
echo "🟢 Installing Node.js 18.x LTS..."
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Install pnpm globally
echo "📦 Installing pnpm package manager..."
sudo npm install -g pnpm

# Install PM2 for process management
echo "⚡ Installing PM2 process manager..."
sudo npm install -g pm2

# Install Nginx
echo "🌐 Installing Nginx..."
sudo apt install -y nginx

# Configure firewall
echo "🔒 Configuring firewall..."
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 3000/tcp
sudo ufw allow 8000/tcp
sudo ufw allow 9000/tcp
sudo ufw --force enable

# Create project directories
echo "📁 Creating project directories..."
sudo mkdir -p /home/ali/development/ovra_ai/logs
sudo chown -R ali:ali /home/ali/development/ovra_ai

# Install Python dependencies (for any Python scripts)
echo "🐍 Installing Python dependencies..."
sudo apt install -y python3 python3-pip python3-venv

# Enable and start required services
echo "🔄 Enabling system services..."
sudo systemctl enable nginx
sudo systemctl enable postgresql
sudo systemctl start nginx
sudo systemctl start postgresql

# Set up log rotation
echo "📄 Setting up log rotation..."
sudo tee /etc/logrotate.d/ovra-ai << 'EOF'
/home/ali/development/ovra_ai/logs/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 ali ali
    postrotate
        systemctl reload ovra-backend ovra-frontend ovra-mcp-boe 2>/dev/null || true
    endscript
}
EOF

echo "✅ System dependencies installed successfully!"
echo ""
echo "📋 Installation Summary:"
echo "  ✓ PostgreSQL Database: ovra_ai"
echo "  ✓ Database User: ovra_user"
echo "  ✓ Node.js: $(node --version)"
echo "  ✓ pnpm: $(pnpm --version)"
echo "  ✓ PM2: $(pm2 --version)"
echo "  ✓ Nginx: $(nginx -v 2>&1)"
echo "  ✓ Firewall configured for ports: 22, 80, 443, 3000, 8000, 9000"
echo ""
echo "🔑 Database Connection Details:"
echo "  Host: localhost"
echo "  Database: ovra_ai"
echo "  User: ovra_user"
echo "  Password: ovra_password"
echo ""
echo "🎯 Next steps:"
echo "  1. Run './install_project.sh' to setup the application"
echo "  2. Run './install_services.sh' to setup systemd services"
