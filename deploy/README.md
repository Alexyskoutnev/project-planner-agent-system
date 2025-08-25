# Project Planner – EC2 Deployment Guide

Deploy the **Project Planner** fullstack app on AWS EC2 Ubuntu.

---

## Prerequisites
- AWS EC2 Ubuntu instance running
- SSH key pair (`.pem` file) for EC2 access
- Security group allowing ports 80 (HTTP) and 22 (SSH)

---

## Deployment

### 1. Connect to EC2
```bash
ssh -i your-key.pem ubuntu@<EC2_PUBLIC_IP>
```

### 2. Install Dependencies & Clone Repository
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3-pip python3-venv git nginx nodejs npm
git clone https://github.com/Alexyskoutnev/project-planner-agent-system project-planner-naii
cd project-planner-naii
```

### 3. Setup Python Backend
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install gunicorn
```

### 4. Build & Deploy Frontend
```bash
chmod +x deploy/build_frontend.sh
./deploy/build_frontend.sh
npm run build
```

### 5. Setup Backend Service
```bash
chmod +x deploy/run_backend_service.sh
./deploy/run_backend_service.sh
```

### 6. Configure Nginx
```bash
chmod +x deploy/run_nginx.sh
./deploy/run_nginx.sh
```

---

## Verify Deployment

Check services are running:
```bash
sudo systemctl status fastapi
sudo systemctl status nginx
```

Visit your app: `http://<EC2_PUBLIC_IP>`

---