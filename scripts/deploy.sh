#!/bin/bash

# Deploy script for the ARTISTING project

# Set environment variables
export DJANGO_SETTINGS_MODULE=ovra_backend.settings
export PYTHONPATH=$(pwd)/backend

# Navigate to the backend directory
cd backend

# Install backend dependencies
pip install -r requirements.txt

# Run database migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput

# Navigate to the frontend directory
cd ../frontend

# Install frontend dependencies
npm install

# Build the frontend application
npm run build

# Start the backend server
cd ../backend
gunicorn ovra_backend.wsgi:application --bind 0.0.0.0:8000 --workers 3 &

# Start the frontend server
cd ../frontend
npm start &

echo "Deployment completed successfully!"