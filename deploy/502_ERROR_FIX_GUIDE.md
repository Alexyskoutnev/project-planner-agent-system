# 502 Bad Gateway Error - Fix Guide

## 🔍 Problem Analysis

The 502 Bad Gateway error occurs when nginx can't connect to your FastAPI backend. This is typically caused by:

1. **API URL Mismatch**: Frontend trying to connect directly to `localhost:8000` instead of using nginx proxy
2. **Backend Service Down**: FastAPI service not running or crashed
3. **Port Conflicts**: Backend not listening on expected port
4. **Configuration Issues**: Nginx proxy configuration problems

## ✅ Solution Applied

### 1. Fixed Frontend API Configuration

**Problem**: `enhancedApi.ts` was using direct localhost URL
```typescript
// ❌ WRONG - Direct connection bypassing nginx
const API_BASE_URL = 'http://localhost:8000';
```

**Solution**: Changed to use nginx proxy
```typescript
// ✅ CORRECT - Uses nginx proxy
const API_BASE_URL = '/api';
```

### 2. Nginx Configuration (Verified)

Your nginx config correctly proxies `/api/` requests to the backend:
```nginx
location /api/ {
    proxy_pass http://127.0.0.1:8000/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

## 🚀 Deployment Steps

### On Your EC2 Instance:

1. **Pull Latest Code**:
   ```bash
   cd /home/ubuntu/project-planner-agent-system
   git pull origin main
   ```

2. **Run the Fix Script**:
   ```bash
   chmod +x deploy/fix_502_error.sh
   ./deploy/fix_502_error.sh
   ```

3. **Or Run Complete Redeployment**:
   ```bash
   chmod +x deploy/redeploy_fixed.sh
   ./deploy/redeploy_fixed.sh
   ```

### Manual Steps (if scripts don't work):

1. **Rebuild Frontend**:
   ```bash
   cd /home/ubuntu/project-planner-agent-system/frontend
   npm run build
   ```

2. **Restart Backend Service**:
   ```bash
   sudo systemctl restart fastapi
   sudo systemctl status fastapi
   ```

3. **Restart Nginx**:
   ```bash
   sudo systemctl restart nginx
   sudo systemctl status nginx
   ```

4. **Test Connectivity**:
   ```bash
   # Test backend directly
   curl http://localhost:8000/health
   
   # Test through nginx proxy
   curl http://localhost/api/health
   ```

## 🔧 Troubleshooting Commands

### Check Service Status:
```bash
sudo systemctl status fastapi
sudo systemctl status nginx
```

### View Logs:
```bash
# Backend logs
sudo journalctl -u fastapi -f

# Nginx error logs
sudo tail -f /var/log/nginx/error.log

# Nginx access logs
sudo tail -f /var/log/nginx/access.log
```

### Test Connectivity:
```bash
# Test backend health
curl -v http://localhost:8000/health

# Test through nginx
curl -v http://localhost/api/health

# Check what's listening on port 8000
sudo netstat -tlnp | grep :8000
```

### Check Configuration:
```bash
# Test nginx config
sudo nginx -t

# View current nginx config
cat /etc/nginx/sites-enabled/default
```

## 🎯 Expected Results

After applying the fix:

1. ✅ Frontend uses `/api` for all requests
2. ✅ Nginx proxies `/api/*` to `http://127.0.0.1:8000/*`
3. ✅ Backend runs on `localhost:8000`
4. ✅ No more 502 Bad Gateway errors

## 🚨 Common Issues

### Backend Not Starting:
- Check if `.env` file exists with required variables
- Verify Python virtual environment is set up
- Check for port conflicts

### Nginx Configuration Issues:
- Ensure nginx config file syntax is correct
- Check file paths in nginx config match actual deployment
- Verify nginx has permission to access files

### Permission Issues:
- Ensure ubuntu user owns application files
- Check nginx worker process permissions
- Verify systemd service file permissions

## 📱 Testing Your Deployment

1. **Frontend Access**: `http://your-ec2-ip/`
2. **API Health Check**: `http://your-ec2-ip/api/health`
3. **Create Project**: Try creating a new project through the UI
4. **Send Message**: Test the chat functionality

## 🆘 If Issues Persist

1. Run the diagnostic script: `./deploy/fix_502_error.sh`
2. Check all logs for specific error messages
3. Ensure EC2 security groups allow traffic on port 80
4. Verify the application directory structure matches nginx config paths

The fix should resolve the 502 Bad Gateway error by ensuring proper communication between nginx and your FastAPI backend!
