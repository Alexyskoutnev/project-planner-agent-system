# NAI Project Planner

A multi-user AI-powered project planning system with both web and API interfaces. Features real-time collaboration, persistent state management, and integration with NAI's specialized hardware planning agents.

## 🚀 Quick Start

### Option 1: Enhanced Multi-User API (Recommended)
```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment
echo "OPENAI_API_KEY=your-key-here" > .env

# Run API server
python run_api_server.py

# Run React frontend (in another terminal)
cd frontend
npm install
REACT_APP_USE_MOCK=false npm start
```

### Option 2: Original Streamlit App
```bash
pip install -r requirements.txt
streamlit run app.py
```

## 🎯 Features

### Enhanced API System
- **Multi-user collaboration**: Real-time session management with active user tracking
- **Project-specific storage**: Each project gets its own document and conversation history
- **SQLite persistence**: All data survives server restarts
- **REST API**: Clean HTTP endpoints for integration
- **React frontend**: Modern, responsive user interface

### Agent System
- **Product Manager**: Orchestrates project planning and user communication
- **Engineer**: Provides NAI hardware expertise and technical guidance
- **PMO**: Maintains structured project documentation

## 📁 Project Structure

```
├── api/                   # FastAPI backend
│   └── main.py               # Complete API with state management
├── database/              # Database layer
│   └── database.py           # SQLite state management
├── frontend/              # React frontend
│   ├── src/
│   └── package.json
├── naii_agents/           # AI agents
│   ├── agents.py             # Agent definitions
│   └── tools.py              # Agent tools
├── project_docs/          # Generated documents
├── app.py                 # Original Streamlit app
├── run_api_server.py      # Main API runner
└── test_system.py         # System tests
```

## 🔗 API Endpoints

### Enhanced API (Port 8000)
- `POST /join` - Join project with session management
- `POST /chat` - Send message and get AI response
- `GET /document/{project_id}` - Get project document
- `GET /history/{project_id}` - Get conversation history
- `GET /projects` - List all projects
- `GET /projects/{project_id}/status` - Get project status
- `DELETE /projects/{project_id}` - Clear project data

### Frontend (Port 3000)
- Modern React interface with real-time updates
- Split-screen chat and document view
- User session management

## 🧪 Testing

```bash
# Test the reorganized system
python test_system.py

# Test API components
cd api && python test_enhanced_api.py
```

## 📊 Database Schema

- **projects**: Project metadata and tracking
- **project_documents**: Per-project document storage  
- **user_sessions**: Active user session management
- **conversation_history**: Full chat history per project

## 🔧 Configuration

Environment variables:
- `OPENAI_API_KEY`: Required for AI agents
- `REACT_APP_USE_MOCK`: Set to `false` to use real API
- `REACT_APP_API_URL`: API base URL (default: http://localhost:8000)