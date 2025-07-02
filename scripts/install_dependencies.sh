#!/bin/bash

# Install system dependencies for Ovra AI deployment
echo "Installing system dependencies..."

# Update package list
sudo apt update

# Install Node.js and npm
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Install Python and pip
sudo apt-get install -y python3 python3-pip python3-venv

# Install Nginx
sudo apt-get install -y nginx

# Install PM2 for Node.js process management
sudo npm install -g pm2

# Install system packages for Python dependencies
sudo apt-get install -y build-essential libpq-dev python3-dev

echo "System dependencies installed successfully!"
