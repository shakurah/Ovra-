#!/bin/bash

# Ovra AI - Service Control Script
# This script provides easy control over Ovra AI system services

set -e

# Function to show usage
show_usage() {
    echo "🔧 Ovra AI Service Control"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  start     - Start both services"
    echo "  stop      - Stop both services"
    echo "  restart   - Restart both services"
    echo "  status    - Show service status"
    echo "  logs      - Show recent logs"
    echo "  follow    - Follow logs in real-time"
    echo "  install   - Install services (first time setup)"
    echo "  uninstall - Remove services"
    echo ""
    echo "Examples:"
    echo "  $0 start"
    echo "  $0 status"
    echo "  $0 logs"
}

# Function to check if services are installed
check_services_installed() {
    if ! systemctl list-unit-files | grep -q "ovra-backend.service"; then
        echo "❌ Services not installed. Run: $0 install"
        exit 1
    fi
}

case "${1:-}" in
    "start")
        echo "🚀 Starting Ovra AI Services..."
        check_services_installed
        sudo systemctl start ovra-backend ovra-frontend
        echo "✅ Services started"
        ;;
    
    "stop")
        echo "🛑 Stopping Ovra AI Services..."
        check_services_installed
        sudo systemctl stop ovra-backend ovra-frontend
        echo "✅ Services stopped"
        ;;
    
    "restart")
        echo "🔄 Restarting Ovra AI Services..."
        check_services_installed
        sudo systemctl restart ovra-backend ovra-frontend
        echo "✅ Services restarted"
        ;;
    
    "status")
        echo "📊 Ovra AI Service Status:"
        echo ""
        echo "Backend:"
        sudo systemctl status ovra-backend --no-pager -l
        echo ""
        echo "Frontend:"
        sudo systemctl status ovra-frontend --no-pager -l
        ;;
    
    "logs")
        echo "📝 Recent Service Logs:"
        echo ""
        echo "=== Backend Logs ==="
        sudo journalctl -u ovra-backend --no-pager -n 20
        echo ""
        echo "=== Frontend Logs ==="
        sudo journalctl -u ovra-frontend --no-pager -n 20
        ;;
    
    "follow")
        echo "📝 Following Service Logs (Ctrl+C to exit)..."
        echo "Backend: ovra-backend | Frontend: ovra-frontend"
        sudo journalctl -u ovra-backend -u ovra-frontend -f
        ;;
    
    "install")
        echo "🔧 Installing Ovra AI Services..."
        bash "$(dirname "$0")/install_services.sh"
        ;;
    
    "uninstall")
        echo "🗑️  Uninstalling Ovra AI Services..."
        sudo systemctl stop ovra-backend ovra-frontend 2>/dev/null || true
        sudo systemctl disable ovra-backend ovra-frontend 2>/dev/null || true
        sudo rm -f /etc/systemd/system/ovra-backend.service
        sudo rm -f /etc/systemd/system/ovra-frontend.service
        sudo systemctl daemon-reload
        echo "✅ Services uninstalled"
        ;;
    
    *)
        show_usage
        exit 1
        ;;
esac
