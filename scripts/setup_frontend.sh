#!/bin/bash

# This script sets up the frontend environment for the ARTISTING project.

# Navigate to the frontend directory
cd ../frontend || exit

# Install dependencies
echo "Installing frontend dependencies..."
pnpm install

# Build the frontend application
echo "Building the frontend application..."
pnpm build

# Start the frontend application
echo "Starting the frontend application..."
pnpm start

echo "Frontend setup completed successfully."