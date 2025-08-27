#!/bin/bash

# Fix 502 Bad Gateway Error - Deployment Troubleshooting Script
echo "🔧 Fixing 502 Bad Gateway Error..."

APP_DIR="/home/ubuntu/project-planner-agent-system"
SERVICE_NAME="fastapi"

echo "📋 Diagnostic Information:"
echo "=========================="

# Check if backend service is running
echo "1. Checking FastAPI service status..."
if systemctl is-active --quiet $SERVICE_NAME; then
    echo "✅ FastAPI service is running"
else
    echo "❌ FastAPI service is NOT running"
    echo "📋 Service logs:"
    sudo journalctl -u $SERVICE_NAME -n 20 --no-pager
fi

# Check if backend is responding
echo ""
echo "2. Testing backend connectivity..."
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ Backend is responding on localhost:8000"
else
    echo "❌ Backend is NOT responding on localhost:8000"
fi

# Check nginx status
echo ""
echo "3. Checking nginx status..."
if systemctl is-active --quiet nginx; then
    echo "✅ Nginx is running"
else
    echo "❌ Nginx is NOT running"
fi

# Check nginx configuration
echo ""
echo "4. Testing nginx configuration..."
sudo nginx -t
if [ $? -eq 0 ]; then
    echo "✅ Nginx configuration is valid"
else
    echo "❌ Nginx configuration has errors"
fi

# Check if port 8000 is being used
echo ""
echo "5. Checking port 8000 usage..."
if sudo netstat -tlnp | grep :8000 > /dev/null; then
    echo "✅ Port 8000 is in use:"
    sudo netstat -tlnp | grep :8000
else
    echo "❌ Port 8000 is NOT in use"
fi

# Check nginx error logs
echo ""
echo "6. Recent nginx error logs:"
echo "=========================="
sudo tail -20 /var/log/nginx/error.log

echo ""
echo "🔧 Attempting to fix common issues..."
echo "===================================="

# Restart backend service
echo "1. Restarting FastAPI service..."
sudo systemctl restart $SERVICE_NAME
sleep 3

# Check if it started successfully
if systemctl is-active --quiet $SERVICE_NAME; then
    echo "✅ FastAPI service restarted successfully"
else
    echo "❌ FastAPI service failed to restart"
    echo "📋 Recent logs:"
    sudo journalctl -u $SERVICE_NAME -n 10 --no-pager
fi

# Restart nginx
echo ""
echo "2. Restarting nginx..."
sudo systemctl restart nginx

if systemctl is-active --quiet nginx; then
    echo "✅ Nginx restarted successfully"
else
    echo "❌ Nginx failed to restart"
fi

# Final test
echo ""
echo "🧪 Final connectivity test..."
echo "============================"
sleep 2

if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ Backend health check: PASSED"
else
    echo "❌ Backend health check: FAILED"
fi

# Test through nginx proxy
if curl -s http://localhost/api/health > /dev/null; then
    echo "✅ Nginx proxy test: PASSED"
else
    echo "❌ Nginx proxy test: FAILED"
fi

echo ""
echo "🎉 Troubleshooting complete!"
echo ""
echo "💡 If the issue persists, check:"
echo "   - Frontend build has correct API_BASE_URL ('/api')"
echo "   - .env file exists with proper configuration"
echo "   - Firewall allows traffic on ports 80 and 8000"
echo "   - Application directory path matches nginx config"
echo ""
echo "📋 Useful debugging commands:"
echo "   sudo journalctl -u $SERVICE_NAME -f    # Follow backend logs"
echo "   sudo tail -f /var/log/nginx/error.log  # Follow nginx logs"
echo "   curl -v http://localhost:8000/health   # Test backend directly"
echo "   curl -v http://localhost/api/health    # Test through nginx proxy"
