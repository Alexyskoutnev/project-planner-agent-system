import os
import logging
import asyncio
import uuid
from typing import Dict, List, Optional
from datetime import datetime
from dotenv import load_dotenv

from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Import existing agent system
from agents import Runner, SQLiteSession
from naii_agents.agents import product_manager
from naii_agents.tools import overwrite_doc, read_current_doc

# Import our new database system
from database import ProjectDatabase

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Check for OpenAI API key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    logger.error("OpenAI API key not found. Please set OPENAI_API_KEY environment variable.")
    raise ValueError("OpenAI API key is required")

os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

# Initialize database
db = ProjectDatabase()

# FastAPI app
app = FastAPI(
    title="NAI Project Planning API",
    description="Multi-user AI-powered project planning with state management",
    version="2.0.0"
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response models
class ChatRequest(BaseModel):
    message: str
    projectId: str
    userName: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    document: Optional[str] = None
    activeUsers: List[Dict] = []

class DocumentResponse(BaseModel):
    document: str

class HistoryResponse(BaseModel):
    history: List[Dict]
    document: str
    activeUsers: List[Dict] = []

class JoinProjectRequest(BaseModel):
    projectId: str
    userName: Optional[str] = None

class JoinProjectResponse(BaseModel):
    sessionId: str
    projectId: str
    message: str

class ProjectListResponse(BaseModel):
    projects: List[Dict]

class ActiveUsersResponse(BaseModel):
    activeUsers: List[Dict]

class ProjectStatusResponse(BaseModel):
    projectId: str
    activeUsers: List[Dict]
    lastActivity: Optional[str]
    documentLength: int

# Helper functions
def get_session_id(x_session_id: str = Header(None)) -> str:
    """Get or create session ID from header"""
    if not x_session_id:
        return str(uuid.uuid4())
    return x_session_id

async def run_agent_conversation(message: str, project_id: str) -> str:
    """Run the agent conversation and return the response"""
    try:
        # Create session for this project
        session = SQLiteSession(f"fastapi-{project_id}", "nai_conversations.sqlite")
        
        # Run the agent system
        result = await Runner.run(
            starting_agent=product_manager,
            input=message,
            session=session,
        )
        
        return result.final_output or "I apologize, but I wasn't able to process your request. Could you please try rephrasing?"
        
    except Exception as e:
        logger.error(f"Error running agents: {e}")
        raise HTTPException(status_code=500, detail=f"Agent processing error: {str(e)}")

def save_document_to_project(project_id: str):
    """Save current working document to project-specific storage"""
    try:
        # Read the current document that the agents modified
        current_doc = read_current_doc()
        if current_doc and current_doc != "document could not be found":
            db.save_document(project_id, current_doc)
            return current_doc
        return None
    except Exception as e:
        logger.error(f"Error saving document for project {project_id}: {e}")
        return None

def load_document_for_project(project_id: str):
    """Load project-specific document for agent processing"""
    try:
        # Get document from database
        doc_content = db.get_document(project_id)
        if doc_content:
            # Write it to the current working document for agents to use
            overwrite_doc(doc_content)
    except Exception as e:
        logger.error(f"Error loading document for project {project_id}: {e}")

# Background task to cleanup inactive sessions
import asyncio
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    async def cleanup_task():
        while True:
            await asyncio.sleep(300)  # Run every 5 minutes
            db.cleanup_inactive_sessions()
    
    cleanup_task_handle = asyncio.create_task(cleanup_task())
    
    yield
    
    # Shutdown
    cleanup_task_handle.cancel()

app.router.lifespan_context = lifespan

# API Endpoints

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "NAI Project Planning API v2.0 is running"}

@app.post("/join", response_model=JoinProjectResponse)
async def join_project(request: JoinProjectRequest, 
                       session_id: str = Depends(get_session_id)):
    """Join a project and get session ID"""
    try:
        # Join the project
        success = db.join_project(
            session_id=session_id,
            project_id=request.projectId,
            user_name=request.userName
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to join project")
        
        return JoinProjectResponse(
            sessionId=session_id,
            projectId=request.projectId,
            message=f"Successfully joined project {request.projectId}"
        )
        
    except Exception as e:
        logger.error(f"Error joining project: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/leave")
async def leave_project(session_id: str = Depends(get_session_id)):
    """Leave current project"""
    try:
        success = db.leave_project(session_id)
        return {"message": "Left project successfully" if success else "No active session found"}
    except Exception as e:
        logger.error(f"Error leaving project: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, 
               session_id: str = Depends(get_session_id)):
    """
    Send a chat message and get AI response.
    Also returns updated document if it was modified.
    """
    try:
        # Update session activity
        db.update_session_activity(session_id)
        
        # Load project-specific document for agent processing
        load_document_for_project(request.projectId)
        
        # Get document content before processing
        doc_before = db.get_document(request.projectId)
        
        # Add user message to history
        db.add_message(request.projectId, "user", request.message, session_id)
        
        # Process message through agent system
        ai_response = await run_agent_conversation(request.message, request.projectId)
        
        # Add AI response to history
        db.add_message(request.projectId, "assistant", ai_response)
        
        # Save any document changes back to project storage
        doc_after = save_document_to_project(request.projectId)
        
        # Get active users
        active_users = db.get_active_users(request.projectId)
        
        # Return response with document if it changed
        response = ChatResponse(
            response=ai_response,
            activeUsers=active_users
        )
        
        if doc_after and doc_after != doc_before:
            response.document = doc_after
            
        return response
        
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/document/{project_id}", response_model=DocumentResponse)
async def get_document(project_id: str):
    """Get the current document state for a project"""
    try:
        document = db.get_document(project_id)
        return DocumentResponse(document=document)
    except Exception as e:
        logger.error(f"Error getting document: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/history/{project_id}", response_model=HistoryResponse)
async def get_history(project_id: str):
    """Get the entire conversation history and current document for a project"""
    try:
        history = db.get_conversation_history(project_id)
        document = db.get_document(project_id)
        active_users = db.get_active_users(project_id)
        
        return HistoryResponse(
            history=history,
            document=document,
            activeUsers=active_users
        )
    except Exception as e:
        logger.error(f"Error getting history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/projects", response_model=ProjectListResponse)
async def list_projects():
    """List all projects with activity info"""
    try:
        projects = db.list_projects()
        return ProjectListResponse(projects=projects)
    except Exception as e:
        logger.error(f"Error listing projects: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/projects/{project_id}/status", response_model=ProjectStatusResponse)
async def get_project_status(project_id: str):
    """Get project status including active users"""
    try:
        active_users = db.get_active_users(project_id)
        project = db.get_project(project_id)
        document = db.get_document(project_id)
        
        return ProjectStatusResponse(
            projectId=project_id,
            activeUsers=active_users,
            lastActivity=project.get('updated_at') if project else None,
            documentLength=len(document)
        )
    except Exception as e:
        logger.error(f"Error getting project status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/projects/{project_id}/users", response_model=ActiveUsersResponse)
async def get_active_users(project_id: str):
    """Get active users for a project"""
    try:
        active_users = db.get_active_users(project_id)
        return ActiveUsersResponse(activeUsers=active_users)
    except Exception as e:
        logger.error(f"Error getting active users: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/projects/{project_id}")
async def clear_project(project_id: str):
    """Clear all data for a project"""
    try:
        success = db.clear_project_data(project_id)
        return {"message": f"Project {project_id} cleared successfully" if success else "Project not found"}
    except Exception as e:
        logger.error(f"Error clearing project: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Backward compatibility endpoints (for existing frontend)
@app.delete("/history/{project_id}")
async def clear_history_legacy(project_id: str):
    """Legacy endpoint for clearing project history"""
    return await clear_project(project_id)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)