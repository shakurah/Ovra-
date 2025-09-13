#!/bin/bash

# This script sets up the backend environment for the ARTISTING project.

# Update package list and install necessary packages
echo "Updating package list..."
sudo apt-get update

echo "Installing Python and pip..."
sudo apt-get install -y python3 python3-pip python3-venv

# Create a virtual environment
echo "Creating a virtual environment..."
python3 -m venv venv

# Activate the virtual environment
echo "Activating the virtual environment..."
source venv/bin/activate

# Install required Python packages
echo "Installing required packages from requirements.txt..."
pip install -r requirements.txt

# Run database migrations
echo "Running database migrations..."
python manage.py migrate

# Create a superuser (optional)
echo "Creating a superuser..."
python manage.py createsuperuser

# Start the Django development server
echo "Starting the Django development server..."
python manage.py runserver

echo "Backend setup completed successfully!"