#!/bin/bash

# Redeploy with 502 Error Fix
echo "🚀 Redeploying with 502 error fixes..."

APP_DIR="/home/ubuntu/project-planner-agent-system"

# 1. Update the code
echo "1. Updating code from repository..."
cd $APP_DIR
git pull origin main

# 2. Rebuild frontend with correct API configuration
echo "2. Rebuilding frontend..."
cd frontend
npm install
npm run build

# 3. Copy .env file if it doesn't exist
echo "3. Checking .env configuration..."
if [ ! -f "$APP_DIR/.env" ]; then
    echo "⚠️  .env file missing! Please create it with:"
    echo "OPENAI_API_KEY=your_key_here"
    echo "SENDER_EMAIL=your_email@domain.com"
    echo "SENDER_PASSWORD=your_password"
    echo "SMTP_SERVER=smtp-mail.outlook.com"
    echo "SMTP_PORT=587"
    echo "BASE_URL=http://your-ec2-ip"
fi

# 4. Update backend dependencies
echo "4. Updating backend dependencies..."
cd $APP_DIR
source venv/bin/activate
pip install -r requirements.txt

# 5. Restart services
echo "5. Restarting services..."
sudo systemctl restart fastapi
sleep 3
sudo systemctl restart nginx

# 6. Check status
echo "6. Checking service status..."
if systemctl is-active --quiet fastapi; then
    echo "✅ FastAPI service is running"
else
    echo "❌ FastAPI service failed to start"
    sudo journalctl -u fastapi -n 10 --no-pager
fi

if systemctl is-active --quiet nginx; then
    echo "✅ Nginx is running"
else
    echo "❌ Nginx failed to start"
fi

# 7. Test connectivity
echo "7. Testing connectivity..."
sleep 2

if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ Backend direct access: OK"
else
    echo "❌ Backend direct access: FAILED"
fi

if curl -s http://localhost/api/health > /dev/null; then
    echo "✅ Nginx proxy: OK"
else
    echo "❌ Nginx proxy: FAILED"
fi

echo ""
echo "🎉 Redeployment complete!"
echo ""
echo "🌐 Your application should now be accessible at:"
echo "   http://your-ec2-public-ip"
echo ""
echo "🔧 If you still see 502 errors, run:"
echo "   ./deploy/fix_502_error.sh"
