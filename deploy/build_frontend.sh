#!/bin/bash

APP_DIR="/home/ubuntu/project-planner-naii"
FRONTEND_DIR="$APP_DIR/frontend"
NGINX_ROOT="$APP_DIR/frontend/build"
NGINX_SITE="/etc/nginx/sites-available/project"

echo "👉 Installing Node.js & npm (if not already installed)..."
sudo apt update
sudo apt install -y nodejs npm

echo "👉 Building React frontend..."
cd $FRONTEND_DIR
npm install

# Build the frontend
npm run build

echo "✅ Frontend build complete!"
echo "Build directory: $FRONTEND_DIR/build"