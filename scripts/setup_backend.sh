#!/bin/bash

# Setup Django backend with Gunicorn
echo "Setting up Django backend..."

cd backend

# Activate virtual environment
source venv/bin/activate

# Install additional production dependencies
pip install gunicorn

# Collect static files
python manage.py collectstatic --noinput

# Create Gunicorn configuration
cat > gunicorn.conf.py << 'EOF'
# Gunicorn configuration file
bind = "0.0.0.0:8000"
workers = 3
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100
timeout = 30
keepalive = 2
preload_app = True
daemon = False
user = "www-data"
group = "www-data"
tmp_upload_dir = None
errorlog = "/var/log/gunicorn/error.log"
accesslog = "/var/log/gunicorn/access.log"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'
loglevel = "info"
EOF

# Create log directories
sudo mkdir -p /var/log/gunicorn
sudo chown -R www-data:www-data /var/log/gunicorn

echo "Backend setup completed!"
