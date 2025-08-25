#!/bin/bash

# Run backend service

APP_DIR="/home/ubuntu/project-planner-naii"
SERVICE_NAME="fastapi"

echo "👉 Creating systemd service for FastAPI..."

sudo tee /etc/systemd/system/$SERVICE_NAME.service > /dev/null <<EOL
[Unit]
Description=FastAPI app
After=network.target

[Service]
User=ubuntu
WorkingDirectory=$APP_DIR
ExecStart=$APP_DIR/venv/bin/gunicorn -w 4 -k uvicorn.workers.UvicornWorker api.main:app --bind 0.0.0.0:8000
Restart=always

[Install]
WantedBy=multi-user.target
EOL

echo "👉 Reloading systemd..."
sudo systemctl daemon-reload

echo "👉 Enabling service..."
sudo systemctl enable $SERVICE_NAME

echo "👉 Starting service..."
sudo systemctl start $SERVICE_NAME

echo "✅ FastAPI service setup complete. Check status with:"
echo "   sudo systemctl status $SERVICE_NAME"
