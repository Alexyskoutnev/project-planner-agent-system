#!/bin/bash

# Frontend build script for Project Planner
set -e  # Exit on any error

APP_DIR="/home/ubuntu/project-planner-agent-system"
FRONTEND_DIR="$APP_DIR/frontend"
BUILD_DIR="$FRONTEND_DIR/build"

echo "🚀 Building Project Planner Frontend..."

# Install Node.js & npm if not already installed
if ! command -v node &> /dev/null || ! command -v npm &> /dev/null; then
    echo "👉 Installing Node.js & npm..."
    sudo apt update
    sudo apt install -y nodejs npm
else
    echo "✅ Node.js and npm already installed"
fi

# Check if frontend directory exists
if [ ! -d "$FRONTEND_DIR" ]; then
    echo "❌ Frontend directory not found: $FRONTEND_DIR"
    exit 1
fi

echo "👉 Building React frontend..."
cd "$FRONTEND_DIR"

# Install dependencies
echo "📦 Installing npm dependencies..."
npm install

# Set production environment variables
export NODE_ENV=production
# # Copy production environment file
# cp ../.env.production .env.production

# Build the frontend with production optimizations
echo "🔨 Building production bundle..."
npm run build

# Verify build was successful
if [ -d "$BUILD_DIR" ] && [ -f "$BUILD_DIR/index.html" ]; then
    echo "✅ Frontend build complete!"
    echo "📁 Build directory: $BUILD_DIR"
    echo "📊 Build size:"
    du -sh "$BUILD_DIR"
else
    echo "❌ Build failed - build directory or index.html not found"
    exit 1
fi