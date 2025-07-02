# Ovra AI Service Management Scripts

This directory contains scripts for managing the Ovra AI Tax Assistant services (Django backend and Next.js frontend).

## Available Scripts

### 🚀 `start_services.sh`
Starts both backend and frontend services.

**Features:**
- Checks if services are already running
- Activates Python virtual environment for backend
- Runs database migrations if needed
- Starts Django on port 8000
- Starts Next.js on port 3000
- Creates PID files for process tracking
- Comprehensive startup validation

**Usage:**
```bash
./scripts/start_services.sh
```

### 🛑 `stop_services.sh`
Stops both backend and frontend services.

**Features:**
- Graceful shutdown using PID files
- Force kill if processes don't respond
- Cleanup of remaining processes by port
- Removes stale PID files

**Usage:**
```bash
./scripts/stop_services.sh
```

### 🔄 `restart_services.sh`
Restarts both services (stop + start).

**Usage:**
```bash
./scripts/restart_services.sh
```

### 📊 `status_services.sh`
Shows detailed status of both services.

**Features:**
- Port availability check
- Process information (PID, name)
- PID file validation
- Log file information
- Service URLs

**Usage:**
```bash
./scripts/status_services.sh
```

### 🧪 `test_services.sh`
Tests service functionality and connectivity.

**Features:**
- HTTP endpoint testing
- API connectivity validation
- Frontend-backend integration check
- Health summary report

**Usage:**
```bash
./scripts/test_services.sh
```

## Service Information

### Backend (Django)
- **Port:** 8000
- **URL:** http://localhost:8000
- **API:** http://localhost:8000/api/v1/
- **Log:** `logs/backend.log`
- **PID:** `logs/backend.pid`

### Frontend (Next.js)
- **Port:** 3000
- **URL:** http://localhost:3000
- **Log:** `logs/frontend.log`
- **PID:** `logs/frontend.pid`

## Log Management

View real-time logs:
```bash
# Backend logs
tail -f logs/backend.log

# Frontend logs
tail -f logs/frontend.log

# Both logs simultaneously
tail -f logs/*.log
```

## Troubleshooting

### Services Won't Start
1. Check if ports are already in use:
   ```bash
   lsof -i :8000  # Backend
   lsof -i :3000  # Frontend
   ```

2. Check logs for errors:
   ```bash
   cat logs/backend.log
   cat logs/frontend.log
   ```

3. Ensure virtual environment exists:
   ```bash
   ls backend/venv/
   ```

### Services Won't Stop
1. Force stop all processes:
   ```bash
   pkill -f "manage.py runserver"
   pkill -f "next dev"
   ```

2. Kill by port:
   ```bash
   lsof -ti:8000 | xargs kill -9
   lsof -ti:3000 | xargs kill -9
   ```

### Database Issues
1. Run migrations manually:
   ```bash
   cd backend
   source venv/bin/activate
   python manage.py migrate
   ```

2. Reset database (if needed):
   ```bash
   cd backend
   rm db.sqlite3
   python manage.py migrate
   ```

## Development Workflow

### After Code Changes
Always restart services after making code changes:
```bash
./scripts/restart_services.sh
```

### Quick Status Check
```bash
./scripts/status_services.sh
```

### Full Service Test
```bash
./scripts/test_services.sh
```

## Script Maintenance

All scripts are located in the `scripts/` directory and are executable. To make scripts executable after cloning:

```bash
chmod +x scripts/*.sh
```

## Integration with Development

These scripts are designed to be called automatically after code changes. The AI assistant will use these scripts to manage services during development.

## Requirements

- **Backend:** Python 3.12+, Django 5.0+, Virtual environment
- **Frontend:** Node.js 18+, npm, Next.js 15+
- **System:** Linux/Unix environment with bash
- **Tools:** curl, lsof, ss (for port checking)
