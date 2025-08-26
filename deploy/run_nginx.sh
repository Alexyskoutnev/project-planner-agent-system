
#!/bin/bash

# Nginx setup script for Project Planner
set -e  # Exit on any error

APP_DIR="/home/ubuntu/project-planner-agent-system"
BUILD_DIR="$APP_DIR/frontend/build"

echo "🚀 Setting up Nginx for Project Planner..."

# Install Nginx if not already installed
if ! command -v nginx &> /dev/null; then
    echo "👉 Installing Nginx..."
    sudo apt update
    sudo apt install nginx -y
else
    echo "✅ Nginx already installed"
fi

# Enable and start nginx
sudo systemctl enable nginx
sudo systemctl start nginx

echo "👉 Configuring Nginx for Project Planner..."

# Remove default site
sudo rm -f /etc/nginx/sites-enabled/default

# Copy our config
sudo cp deploy/nginx_config /etc/nginx/sites-available/project

# Enable our site
sudo ln -sf /etc/nginx/sites-available/project /etc/nginx/sites-enabled/

# Set correct permissions for the app directory
sudo chmod 755 "$APP_DIR"
sudo chmod 755 "$APP_DIR/frontend"

# Test nginx configuration
echo "👉 Testing Nginx configuration..."
if sudo nginx -t; then
    echo "✅ Nginx configuration is valid"
    sudo systemctl reload nginx
    echo "✅ Nginx reloaded successfully"
else
    echo "❌ Nginx configuration failed - please check the config"
    exit 1
fi

# Check if frontend build exists
if [ -d "$BUILD_DIR" ] && [ -f "$BUILD_DIR/index.html" ]; then
    echo "✅ Frontend build directory found"
    echo "📁 Serving from: $BUILD_DIR"
else
    echo "⚠️  Frontend build not found at: $BUILD_DIR"
    echo "🔧 Run './deploy/build_frontend.sh' first to build the frontend"
fi

echo "👉 Nginx status:"
systemctl status nginx --no-pager

echo ""
echo "✅ Nginx setup complete!"
echo "🌐 Your app should be available at: http://$(curl -s ifconfig.me)/"