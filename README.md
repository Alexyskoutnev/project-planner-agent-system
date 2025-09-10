# Project Planner

AI-powered collaborative project planning with Duo Security authentication, real-time multi-user support, and specialized AI agents.

## Quick Start

**Backend:**
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
echo "OPENAI_API_KEY=your-key-here" > .env
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000
```

**Frontend:**
```bash
cd frontend && npm install && npm start
```

Visit: **http://localhost:3000**

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React App     │───▶│   FastAPI       │───▶│   SQLite DB     │───▶│   AI Agents     │
│   (Port 3000)   │    │   (Port 8000)   │    │   + Documents   │    │   (OpenAI)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘
         │                        │
         └────────────────────────┼──────────────────────────────────────────────────────┐
                                  │                                                       │
                          ┌─────────────────┐                                  ┌─────────────────┐
                          │   Duo Security  │                                  │   Email Service │
                          │  Authentication │                                  │   (Invitations) │
                          └─────────────────┘                                  └─────────────────┘
```

## Production Deployment

**Backend Service:**
```bash
./deploy/run_backend_service.sh
```

**Frontend Build:**
```bash
./deploy/build_frontend.sh
```

**Nginx Setup:**
```bash
./deploy/run_nginx.sh
```