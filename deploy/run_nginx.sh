
#!/bin/bash

echo "👉 Installing and configuring Nginx..."

# Install Nginx
sudo apt update
sudo apt install nginx -y

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
if [ -d "/home/ubuntu/project-planner-naii/frontend/build" ]; then
    echo "✅ Frontend build directory found"
else
    echo "⚠️  Frontend build directory not found. Make sure to run build_frontend.sh first!"
fi

echo "👉 Nginx status:"
systemctl status nginx --no-pager