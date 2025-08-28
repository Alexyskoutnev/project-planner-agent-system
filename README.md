# 🚀 NAI Project Planner

An AI-powered collaborative project planning system with real-time multi-user support and intelligent agents.

## ⚡ Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set up environment
echo "OPENAI_API_KEY=your-key-here" > .env

# 3. Start backend
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000

# 4. Start frontend (new terminal)
cd frontend && npm install && npm start
```

Visit: **http://localhost:3000**

## 🎯 Key Features

- **🤝 Multi-user collaboration** - Real-time project sharing
- **🤖 AI agents** - Product Manager, Engineer, and PMO assistants  
- **📊 Project persistence** - All data saved automatically
- **📧 Email invitations** - Invite team members via email
- **📱 Modern UI** - React-based responsive interface

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React App     │───▶│   FastAPI       │───▶│   SQLite DB     │
│   (Port 3000)   │    │   (Port 8000)   │    │   + Documents   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 📁 Project Structure

```
├── api/              # FastAPI backend
├── frontend/         # React frontend  
├── email_handler/    # Email system
├── database/         # Data persistence
├── naii_agents/      # AI agents
└── deploy/          # Deployment scripts
```

## 🔧 Configuration

**Required Environment Variables:**
```bash
OPENAI_API_KEY=sk-...           # OpenAI API access
TENANT_ID=...                   # Microsoft Graph (email)
CLIENT_ID=...                   # Microsoft Graph (email)  
CLIENT_SECRET=...               # Microsoft Graph (email)
USER_EMAIL=...                  # Sender email address
```

## 🚀 Deployment

**Development:**
```bash
./run_dev.sh
```

**Production:**
```bash
./run_prod.sh
```

**Server Setup:**
```bash
./deploy/run_backend_service.sh    # Sets up systemd service
```

## 📖 Usage

1. **Create/Join Project** - Enter project name to start
2. **Chat with AI** - Get help from specialized agents
3. **Invite Team** - Send email invitations to collaborators  
4. **View Documents** - Auto-generated project documentation
5. **Track Progress** - Real-time collaboration and updates

## 🛠️ Development

**API Endpoints:**
- `POST /join` - Join project
- `POST /chat` - Send message  
- `POST /projects/{id}/invite` - Send invitation
- `GET /history/{id}` - Get chat history
- `GET /health` - Health check

**Testing:**
```bash
curl http://localhost:8000/health
curl -X POST http://localhost:8000/test-email    # Test email system
```

---

**Live Demo:** http://54.226.226.2 | **API:** http://54.226.226.2/api