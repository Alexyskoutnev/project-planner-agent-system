# Project Planner – EC2 Deployment Guide

Deploy the **Project Planner** fullstack app on AWS EC2 Ubuntu.

---

## Prerequisites
- AWS EC2 Ubuntu instance running
- SSH key pair (`.pem` file) for EC2 access
- Security group allowing ports 80 (HTTP) and 22 (SSH)
- OpenAI API key for the AI agents

---

## Quick Deployment

### 1. Connect to EC2
```bash
ssh -i your-key.pem ubuntu@<EC2_PUBLIC_IP>
```

### 2. Clone Repository
```bash
git clone https://github.com/Alexyskoutnev/project-planner-agent-system.git
cd project-planner-agent-system
```

### 3. Set Environment Variables
```bash
echo "OPENAI_API_KEY=your_openai_api_key_here" > .env
```

### 4. Run Deployment Scripts (in order)
```bash
# Make scripts executable
chmod +x deploy/*.sh

# 1. Setup backend service
sudo ./deploy/run_backend_service.sh

# 2. Build frontend
sudo ./deploy/build_frontend.sh

# 3. Configure Nginx
sudo ./deploy/run_nginx.sh
```

---

## Verify Deployment

### Check Services
```bash
# Backend service
sudo systemctl status fastapi

# Nginx service
sudo systemctl status nginx

# Check if backend is listening
sudo ss -tlnp | grep :8000
```

### Test Endpoints
```bash
# Test frontend (should return HTML)
curl -I http://localhost/

# Test API health check
curl http://localhost/api/health

# Test API projects endpoint
curl http://localhost/api/projects
```

### Access Your App
Visit: `http://<EC2_PUBLIC_IP>`

---

## Troubleshooting

### Backend Issues
```bash
# Check backend logs
sudo journalctl -u fastapi -n 50 --no-pager

# Restart backend
sudo systemctl restart fastapi
```

### Frontend Issues
```bash
# Verify build exists
ls -la /home/ubuntu/project-planner-agent-system/frontend/build/

# Rebuild frontend
./deploy/build_frontend.sh
```

### Nginx Issues
```bash
# Test nginx config
sudo nginx -t

# Check nginx logs
sudo tail -n 50 /var/log/nginx/error.log

# Restart nginx
sudo systemctl restart nginx
```

### Update Deployment
```bash
# Pull latest changes
git pull origin main

# Rebuild and restart
./deploy/build_frontend.sh
sudo systemctl restart fastapi
sudo systemctl reload nginx
```

---