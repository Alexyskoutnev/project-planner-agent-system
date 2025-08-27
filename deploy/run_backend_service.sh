#!/bin/bash

# Backend service setup script for Project Planner
set -e  # Exit on any error

APP_DIR="/home/ubuntu/project-planner-agent-system"
SERVICE_NAME="fastapi"
VENV_DIR="$APP_DIR/venv"

echo "🚀 Setting up FastAPI Backend Service..."

# Check if app directory exists
if [ ! -d "$APP_DIR" ]; then
    echo "❌ App directory not found: $APP_DIR"
    exit 1
fi

# Setup Python virtual environment if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
    echo "👉 Creating Python virtual environment..."
    cd "$APP_DIR"
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
else
    echo "✅ Virtual environment already exists"
fi

# Check if .env file exists
if [ ! -f "$APP_DIR/.env" ]; then
    echo "⚠️  .env file not found. Creating template..."
    echo "OPENAI_API_KEY=your_openai_api_key_here" > "$APP_DIR/.env"
    echo "🔧 Please edit $APP_DIR/.env and add your OpenAI API key"
fi

echo "👉 Creating systemd service for FastAPI..."

# Create systemd service file
sudo tee /etc/systemd/system/$SERVICE_NAME.service > /dev/null <<EOL
[Unit]
Description=Project Planner FastAPI Backend
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=$APP_DIR
Environment=PATH=$VENV_DIR/bin
ExecStart=$VENV_DIR/bin/uvicorn api.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOL

echo "👉 Reloading systemd..."
sudo systemctl daemon-reload

echo "👉 Enabling service..."
sudo systemctl enable $SERVICE_NAME

echo "👉 Starting service..."
sudo systemctl start $SERVICE_NAME

# Wait a moment for service to start
sleep 2

# Check service status
if systemctl is-active --quiet $SERVICE_NAME; then
    echo "✅ FastAPI service is running"
    echo "📊 Service status:"
    sudo systemctl status $SERVICE_NAME --no-pager -l
    
    # Test if backend is responding
    if curl -s http://localhost:8000/health > /dev/null; then
        echo "✅ Backend health check passed"
    else
        echo "⚠️  Backend not responding to health check"
    fi
else
    echo "❌ FastAPI service failed to start"
    echo "📋 Service logs:"
    sudo journalctl -u $SERVICE_NAME -n 20 --no-pager
    exit 1
fi

echo ""
echo "✅ Backend service setup complete!"
echo "🔧 Useful commands:"
echo "   sudo systemctl status $SERVICE_NAME"
echo "   sudo journalctl -u $SERVICE_NAME -f"
