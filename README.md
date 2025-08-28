# Project Planner

An AI-powered collaborative project planning system with real-time multi-user support and AI agents (A Project Manager, Engineer, and PMO).

## Quick Start

```bash
pip install -r requirements.txt

echo "OPENAI_API_KEY=your-key-here" > .env

python -m uvicorn api.main:app --host 0.0.0.0 --port 8000

cd frontend && npm install && npm start
```

Visit: **http://localhost:3000**

## Key Features

- ** Multi-user collaboration** - Real-time project sharing
- ** AI agents** - Product Manager, Engineer, and PMO assistants  
- ** Project persistence** - All data saved automatically
- ** Email invitations** - Invite team members via email
- ** Modern UI** - React-based responsive interface

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React App     │───▶│   FastAPI       │───▶│   SQLite DB     │
│   (Port 3000)   │    │   (Port 8000)   │    │   + Documents   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Project Structure

```
├── api/              # FastAPI backend
├── frontend/         # React frontend  
├── email_handler/    # Email system
├── database/         # Data persistence
├── naii_agents/      # AI agents
└── deploy/          # Deployment scripts
```

**Server Setup:**
```bash
./deploy/run_backend_service.sh    # Sets up systemd service
```
**Frontend Build**
```bash
./deploy/build_frontend.sh
```
**Setting up Reverse Poxy**
```bash
./deploy/run_ngunx.sh
```


## Usage

1. **Create/Join Project** - Enter project name to start
2. **Chat with AI** - Get help from specialized agents
3. **Invite Team** - Send email invitations to collaborators  
4. **View Documents** - Auto-generated project documentation
5. **Track Progress** - Real-time collaboration and updates

## API Endpoints

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