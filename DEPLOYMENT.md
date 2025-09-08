# NAI Project Planner - Deployment Guide

## 🚀 Production Deployment (172.28.3.20)

### Prerequisites
- Internal IP: `172.28.3.20`
- Domain: `https://naii-project-planner.naii.com/`
- Load balancer configured for HTTPS
- Python 3.11+ and Node.js 18+ installed

### 1. Server Setup

```bash
# On production server (172.28.3.20)
git clone [repository-url]
cd project-planner-naii

# Create Python virtual environment
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Install Node.js dependencies
cd frontend
npm install
cd ..
```

### 2. Environment Configuration

```bash
# Copy production environment file
cp .env.production .env

# Edit .env with your production values:
# - Set your OpenAI API key
# - Generate a secure session secret
# - Verify Duo credentials
```

### 3. Duo Admin Panel Setup

**Important**: Update your Duo application settings:

1. Go to https://admin.duosecurity.com/
2. Find your application (Integration Key: `DIFUG61X3UICQ7KLATH8`)
3. Update **Redirect URI** to: `https://naii-project-planner.naii.com/auth/duocallback`
4. Save changes

### 4. Start Services

```bash
# Start API server (backend)
source .venv/bin/activate
uvicorn api.main:app --host 0.0.0.0 --port 8000

# Start frontend (in another terminal)
cd frontend
REACT_APP_API_URL=http://172.28.3.20:8000 npm run build
npm start
```

### 5. Production Service Setup

Create systemd service files for automatic startup:

**API Service** (`/etc/systemd/system/nai-project-planner-api.service`):
```ini
[Unit]
Description=NAI Project Planner API
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/project-planner-naii
Environment=NODE_ENV=production
ExecStart=/path/to/project-planner-naii/.venv/bin/uvicorn api.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

**Frontend Service** (`/etc/systemd/system/nai-project-planner-frontend.service`):
```ini
[Unit]
Description=NAI Project Planner Frontend
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/project-planner-naii/frontend
Environment=NODE_ENV=production
Environment=REACT_APP_API_URL=http://172.28.3.20:8000
ExecStart=/usr/bin/npm start
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start services:
```bash
sudo systemctl enable nai-project-planner-api
sudo systemctl enable nai-project-planner-frontend
sudo systemctl start nai-project-planner-api
sudo systemctl start nai-project-planner-frontend
```

## 🔧 Local Development

### Environment Setup
```bash
# Use development defaults
cp .env.example .env
# Edit .env with your local settings if needed
```

### Start Development Servers
```bash
# Terminal 1: API Server
source .venv/bin/activate
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Frontend
cd frontend
npm start
```

### Access Points
- **Frontend**: http://localhost:3000
- **API**: http://localhost:8000
- **Duo Callback**: http://localhost:8000/auth/duocallback

## 🌐 URL Configuration Summary

| Environment | Frontend URL | API URL | Duo Redirect |
|-------------|-------------|---------|--------------|
| **Local** | http://localhost:3000 | http://localhost:8000 | http://localhost:8000/auth/duocallback |
| **Production** | https://naii-project-planner.naii.com | http://172.28.3.20:8000 | https://naii-project-planner.naii.com/auth/duocallback |

## ✅ Testing

### Local Testing
1. Visit http://localhost:3000
2. Enter any valid Duo username
3. Complete Duo authentication
4. Verify successful login

### Production Testing
1. Visit https://naii-project-planner.naii.com
2. Enter your NAII Duo username
3. Complete Duo authentication
4. Verify successful login

## 🔒 Security Notes

- **HTTPS**: Production uses HTTPS via load balancer
- **Internal IP**: API runs on internal IP (172.28.3.20)
- **Duo Security**: All authentication goes through Duo
- **Session Security**: Uses secure session cookies
- **CORS**: Configured for both local and production origins

## 🐛 Troubleshooting

### Common Issues

1. **Duo Redirect Error**: 
   - Check Duo Admin Panel redirect URI matches your environment
   - Verify environment variables are set correctly

2. **CORS Errors**:
   - Check `NODE_ENV` is set correctly
   - Verify allowed origins in `api/main.py`

3. **API Connection Issues**:
   - Check `REACT_APP_API_URL` in frontend environment
   - Verify API server is running and accessible

### Logs
```bash
# View API logs
journalctl -u nai-project-planner-api -f

# View Frontend logs  
journalctl -u nai-project-planner-frontend -f
```