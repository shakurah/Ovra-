#!/bin/bash

# Setup Next.js frontend
echo "Setting up Next.js frontend..."

cd frontend

# Install dependencies
npm install

# Build the application
npm run build

# Create PM2 ecosystem file
cat > ecosystem.config.js << 'EOF'
module.exports = {
  apps: [{
    name: 'ovra-frontend',
    script: 'npm',
    args: 'start',
    cwd: '/home/ali/development/ovra_ai/frontend',
    instances: 1,
    autorestart: true,
    watch: false,
    max_memory_restart: '1G',
    env: {
      NODE_ENV: 'production',
      HOST: '0.0.0.0',
      PORT: 3000,
      NEXT_PUBLIC_API_URL: 'http://localhost:8000/api/v1'
    }
  }]
}
EOF

echo "Frontend setup completed!"
