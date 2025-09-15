#!/bin/bash

# Complete restart script for Project Planner
set -e  # Exit on any error

echo "🔄 Restarting all Project Planner services..."

# Stop all services first
echo "👉 Stopping services..."
sudo systemctl stop fastapi || echo "⚠️  FastAPI service was not running"
sudo systemctl stop nginx || echo "⚠️  Nginx was not running"

# Kill any frontend dev processes
echo "👉 Stopping frontend dev server..."
pkill -f "npm start" || echo "⚠️  No npm start processes found"

# Wait a moment
sleep 2

# Reload systemd to pick up any config changes
echo "👉 Reloading systemd daemon..."
sudo systemctl daemon-reload

# Start backend service
echo "👉 Starting FastAPI backend..."
sudo systemctl start fastapi

# Wait for backend to be ready
echo "👉 Waiting for backend to start..."
sleep 3

# Start nginx
echo "👉 Starting nginx..."
sudo systemctl start nginx

# Check service status
echo ""
echo "📊 Service Status:"
echo "=================="

if systemctl is-active --quiet fastapi; then
    echo "✅ FastAPI: Running"
else
    echo "❌ FastAPI: Failed"
fi

if systemctl is-active --quiet nginx; then
    echo "✅ Nginx: Running"
else
    echo "❌ Nginx: Failed"
fi

# Test endpoints
echo ""
echo "🧪 Testing endpoints..."
echo "======================"

if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ Backend health check: OK"
else
    echo "❌ Backend health check: Failed"
fi

# Get server IP for frontend test
SERVER_IP=$(curl -s ifconfig.me || echo "localhost")
if curl -s http://localhost/ > /dev/null; then
    echo "✅ Frontend via nginx: OK"
    echo "🌐 Access your app at: http://$SERVER_IP/"
else
    echo "❌ Frontend via nginx: Failed"
fi

echo ""
echo "✅ Restart complete!"
echo ""
echo "🔧 Useful commands for monitoring:"
echo "   sudo systemctl status fastapi nginx"
echo "   sudo journalctl -u fastapi -f"
echo "   sudo journalctl -u nginx -f"