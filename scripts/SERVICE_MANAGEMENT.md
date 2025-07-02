# Ovra AI Service Management Guide

## Overview
Ovra AI is now running as system services that will automatically start on boot and restart if they crash.

## Quick Commands

### Using the Service Control Script (Recommended)
```bash
# Check status
./scripts/service_control.sh status

# Start services
./scripts/service_control.sh start

# Stop services
./scripts/service_control.sh stop

# Restart services
./scripts/service_control.sh restart

# View recent logs
./scripts/service_control.sh logs

# Follow logs in real-time
./scripts/service_control.sh follow
```

### Direct systemctl Commands
```bash
# Start services
sudo systemctl start ovra-backend ovra-frontend

# Stop services
sudo systemctl stop ovra-backend ovra-frontend

# Restart services
sudo systemctl restart ovra-backend ovra-frontend

# Check status
sudo systemctl status ovra-backend ovra-frontend

# View logs
sudo journalctl -u ovra-backend -f
sudo journalctl -u ovra-frontend -f
```

## Service Details

### Backend Service (ovra-backend)
- **Service File**: `/etc/systemd/system/ovra-backend.service`
- **URL**: http://localhost:8000
- **Working Directory**: `/home/ali/development/ovra_ai/backend`
- **Log File**: `/home/ali/development/ovra_ai/logs/backend.log`

### Frontend Service (ovra-frontend)
- **Service File**: `/etc/systemd/system/ovra-frontend.service`
- **URL**: http://localhost:3000
- **Working Directory**: `/home/ali/development/ovra_ai/frontend`
- **Log File**: `/home/ali/development/ovra_ai/logs/frontend.log`

## Features

### Auto-Start on Boot
Both services are enabled to start automatically when the system boots.

### Auto-Restart on Failure
If either service crashes, systemd will automatically restart it after 3 seconds.

### Persistent Logging
All output is logged to both:
- System journal (accessible via `journalctl`)
- Local log files in the `logs/` directory

## Troubleshooting

### Check Service Status
```bash
./scripts/service_control.sh status
```

### View Recent Errors
```bash
./scripts/service_control.sh logs
```

### Follow Live Logs
```bash
./scripts/service_control.sh follow
```

### Restart Services
```bash
./scripts/service_control.sh restart
```

### Manual Service Management
If you need to temporarily stop the services to run them manually:
```bash
# Stop services
./scripts/service_control.sh stop

# Run manually (for development)
cd backend && source venv/bin/activate && python manage.py runserver localhost:8000
cd frontend && npm run dev

# Start services again
./scripts/service_control.sh start
```

## Uninstalling Services
If you need to remove the services:
```bash
./scripts/service_control.sh uninstall
```

This will:
- Stop the services
- Disable auto-start on boot
- Remove service files
- Clean up systemd configuration
