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
import os

# Import our new database system
from database.database import ProjectDatabase

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
def get_session_id(x_session_id: str = Header(None)) -> Optional[str]:
    """Get session ID from header, don't create new ones"""
    return x_session_id

def get_or_create_session_id(x_session_id: str = Header(None)) -> str:
    """Get or create session ID from header - only used for join endpoint"""
    if not x_session_id:
        return str(uuid.uuid4())
    return x_session_id

async def run_agent_conversation(message: str, project_id: str) -> str:
    """Run the agent conversation and return the response"""
    try:
        # Load project-specific document before running agents
        load_document_for_project(project_id)
        
        # Temporarily replace the main document with project-specific one
        main_doc_path = "./project_docs/NAI_system_configuration.md"
        project_doc_path = f"./project_docs/{project_id}_NAI_system_configuration.md"
        backup_path = "./project_docs/NAI_system_configuration.md.backup"
        
        # Backup original if it exists
        if os.path.exists(main_doc_path):
            if os.path.exists(project_doc_path):
                os.rename(main_doc_path, backup_path)
                os.rename(project_doc_path, main_doc_path)
            # If no project-specific doc exists, keep the main one
        else:
            # If no main doc, copy project-specific or create empty
            if os.path.exists(project_doc_path):
                os.rename(project_doc_path, main_doc_path)
        
        # Create session for this project
        session = SQLiteSession(f"fastapi-{project_id}", "nai_conversations.sqlite")
        
        # Run the agent system
        result = await Runner.run(
            starting_agent=product_manager,
            input=message,
            session=session,
        )
        
        # Restore the document structure after agent processing
        if os.path.exists(main_doc_path):
            os.rename(main_doc_path, project_doc_path)
        if os.path.exists(backup_path):
            os.rename(backup_path, main_doc_path)
        
        return result.final_output or "I apologize, but I wasn't able to process your request. Could you please try rephrasing?"
        
    except Exception as e:
        logger.error(f"Error running agents: {e}")
        # Ensure we restore the document structure even if there's an error
        try:
            if os.path.exists("./project_docs/NAI_system_configuration.md"):
                os.rename("./project_docs/NAI_system_configuration.md", f"./project_docs/{project_id}_NAI_system_configuration.md")
            if os.path.exists("./project_docs/NAI_system_configuration.md.backup"):
                os.rename("./project_docs/NAI_system_configuration.md.backup", "./project_docs/NAI_system_configuration.md")
        except:
            pass
        raise HTTPException(status_code=500, detail=f"Agent processing error: {str(e)}")

def save_document_to_project(project_id: str):
    """Save current working document to project-specific database storage"""
    try:
        # Read the current document that the agents modified
        doc_path = f"./project_docs/{project_id}_NAI_system_configuration.md"
        current_doc = None
        if os.path.exists(doc_path) and os.path.getsize(doc_path) > 0:
            with open(doc_path, "r", encoding="utf-8") as f:
                current_doc = f.read()
        
        if current_doc and current_doc.strip() and current_doc != "document could not be found":
            # Save directly to database
            document_id = f"doc_{project_id}"
            if not db.documents.update_content(document_id, current_doc):
                # Document doesn't exist, create it
                db.documents.create(document_id, current_doc, project_id)
            return current_doc
        return None
    except Exception as e:
        logger.error(f"Error saving document for project {project_id}: {e}")
        return None

def load_document_for_project(project_id: str):
    """Load project-specific document from database for agent processing"""
    try:
        # Get document from database
        document_id = f"doc_{project_id}"
        document = db.documents.get(document_id)
        if document:
            # Write it to project-specific working document for agents to use
            doc_path = f"./project_docs/{project_id}_NAI_system_configuration.md"
            os.makedirs("./project_docs/", exist_ok=True)
            with open(doc_path, "w", encoding="utf-8") as f:
                f.write(document.content)
        else:
            # Create empty document if none exists
            doc_path = f"./project_docs/{project_id}_NAI_system_configuration.md"
            os.makedirs("./project_docs/", exist_ok=True)
            with open(doc_path, "w", encoding="utf-8") as f:
                f.write("# No document available")
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
            # Cleanup inactive sessions (you can implement this logic later)
            logger.info("Cleanup task ran")
    
    cleanup_task_handle = asyncio.create_task(cleanup_task())
    
    yield
    
    # Shutdown
    cleanup_task_handle.cancel()

app.router.lifespan_context = lifespan

# API Endpoints

@app.get("/")
async def root():
    return {"message": "NAI Project Planning API v2.0 is running"}

@app.post("/join", response_model=JoinProjectResponse)
async def join_project(request: JoinProjectRequest, 
                       session_id: str = Depends(get_or_create_session_id)):
    """Join a project and get session ID"""
    try:
        # Ensure project exists
        if not db.projects.get(request.projectId):
            db.projects.create(request.projectId)
        
        # Create session for this user/project
        success = db.sessions.create(
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
async def leave_project(session_id: Optional[str] = Depends(get_session_id)):
    """Leave current project"""
    try:
        if not session_id:
            return {"message": "No active session found"}
        success = db.sessions.set_inactive(session_id)
        return {"message": "Left project successfully" if success else "No active session found"}
    except Exception as e:
        logger.error(f"Error leaving project: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, 
               session_id: Optional[str] = Depends(get_session_id)):
    """
    Send a chat message and get AI response.
    Also returns updated document if it was modified.
    """
    try:
        if not session_id:
            raise HTTPException(status_code=401, detail="No active session. Please join a project first.")
        
        # Update session activity
        db.sessions.update_activity(session_id)
        
        # Load project-specific document for agent processing
        load_document_for_project(request.projectId)
        
        # Get document content before processing
        document_id = f"doc_{request.projectId}"
        doc_before_obj = db.documents.get(document_id)
        doc_before = doc_before_obj.content if doc_before_obj else ""
        
        # Create conversation if needed and add user message
        conversation_id = f"conv_{request.projectId}_{session_id}"
        if not db.conversations.get(conversation_id):
            db.conversations.create(conversation_id, request.projectId, session_id)
        db.conversations.add_message(conversation_id, "user", request.message)
        
        # Process message through agent system
        ai_response = await run_agent_conversation(request.message, request.projectId)
        
        # Add AI response to history
        db.conversations.add_message(conversation_id, "assistant", ai_response)
        
        # Save any document changes back to project storage
        doc_after = save_document_to_project(request.projectId)
        
        # Get active users
        active_sessions = db.sessions.get_active_by_project(request.projectId)
        active_users = [{"sessionId": s.session_id, "userName": s.user_name, "joinedAt": s.joined_at_ts} for s in active_sessions]
        
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
        document_id = f"doc_{project_id}"
        document_obj = db.documents.get(document_id)
        document = document_obj.content if document_obj else ""
        return DocumentResponse(document=document)
    except Exception as e:
        logger.error(f"Error getting document: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/history/{project_id}", response_model=HistoryResponse)
async def get_history(project_id: str):
    """Get the entire conversation history and current document for a project"""
    try:
        # Get all conversations for this project
        conversations = db.conversations.get_by_project(project_id)
        
        # Flatten messages from all conversations with timestamps and user names
        history = []
        for conv in conversations:
            if conv.messages:
                # Get session info to get user name
                session = db.sessions.get(conv.session_id)
                user_name = session.user_name if session else None
                
                # Debug logging
                logger.info(f"Conversation {conv.conversation_id}: session_id={conv.session_id}, user_name={user_name}")
                
                for msg in conv.messages:
                    history.append({
                        "role": msg["role"],
                        "content": msg["content"],
                        "timestamp": msg.get("timestamp", conv.timestamp_ts),
                        "conversationId": conv.conversation_id,
                        "userName": user_name if msg["role"] == "user" else None
                    })
        
        # Sort by timestamp
        history.sort(key=lambda x: x["timestamp"])
        
        # Get document
        document_id = f"doc_{project_id}"
        document_obj = db.documents.get(document_id)
        document = document_obj.content if document_obj else ""
        
        # Get active users
        active_sessions = db.sessions.get_active_by_project(project_id)
        active_users = [{"sessionId": s.session_id, "userName": s.user_name, "joinedAt": s.joined_at_ts} for s in active_sessions]
        
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
        projects_data = db.projects.list_all()
        projects = [{
            "projectId": p.project_id,
            "createdAt": p.created_at_ts,
            "updatedAt": p.updated_at_ts,
            "activeUsers": len(db.sessions.get_active_by_project(p.project_id))
        } for p in projects_data]
        return ProjectListResponse(projects=projects)
    except Exception as e:
        logger.error(f"Error listing projects: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/projects/{project_id}/status", response_model=ProjectStatusResponse)
async def get_project_status(project_id: str):
    """Get project status including active users"""
    try:
        # Get active users
        active_sessions = db.sessions.get_active_by_project(project_id)
        active_users = [{"sessionId": s.session_id, "userName": s.user_name, "joinedAt": s.joined_at_ts} for s in active_sessions]
        
        # Get project info
        project = db.projects.get(project_id)
        
        # Get document
        document_id = f"doc_{project_id}"
        document_obj = db.documents.get(document_id)
        document = document_obj.content if document_obj else ""
        
        return ProjectStatusResponse(
            projectId=project_id,
            activeUsers=active_users,
            lastActivity=datetime.fromtimestamp(project.updated_at_ts).isoformat() if project else None,
            documentLength=len(document)
        )
    except Exception as e:
        logger.error(f"Error getting project status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/projects/{project_id}/users", response_model=ActiveUsersResponse)
async def get_active_users(project_id: str):
    """Get active users for a project"""
    try:
        active_sessions = db.sessions.get_active_by_project(project_id)
        active_users = [{"sessionId": s.session_id, "userName": s.user_name, "joinedAt": s.joined_at_ts} for s in active_sessions]
        return ActiveUsersResponse(activeUsers=active_users)
    except Exception as e:
        logger.error(f"Error getting active users: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/projects/{project_id}")
async def delete_project(project_id: str):
    """Delete a project and all its data"""
    try:
        # Clear conversations
        conversations = db.conversations.get_by_project(project_id)
        for conv in conversations:
            db.conversations.clear_messages(conv.conversation_id)
        
        # Clear document
        document_id = f"doc_{project_id}"
        db.documents.update_content(document_id, "")
        
        # Set all sessions for this project as inactive
        sessions = db.sessions.get_active_by_project(project_id)
        for session in sessions:
            db.sessions.set_inactive(session.session_id)
        
        # Actually delete the project record
        success = db.projects.delete(project_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
        
        return {"message": f"Project {project_id} deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting project: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)