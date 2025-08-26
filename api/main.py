import os
import logging
import asyncio
import uuid
import sqlite3
from typing import Dict, List, Optional
from datetime import datetime
from dotenv import load_dotenv

from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Import existing agent system
from agents import Runner, SQLiteSession
from naii_agents.agents import product_manager
from naii_agents.tools import set_project_context
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
        # Set project context for database-aware tools
        set_project_context(project_id, db)
        
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

def get_document_content(project_id: str) -> str:
    """Get document content from database"""
    try:
        document_id = f"doc_{project_id}"
        document = db.documents.get(document_id)
        if document and document.content.strip():
            return document.content
        return ""
    except Exception as e:
        logger.error(f"Error getting document for project {project_id}: {e}")
        return ""

def cleanup_chat_sessions_for_project(project_id: str):
    try:
        session_id = f"fastapi-{project_id}"
        chat_db_path = "nai_conversations.sqlite"
        
        if os.path.exists(chat_db_path):
            # Connect to the chat sessions database
            conn = sqlite3.connect(chat_db_path)
            cursor = conn.cursor()
            
            # Delete messages associated with this session
            cursor.execute("DELETE FROM agent_messages WHERE session_id = ?", (session_id,))
            messages_deleted = cursor.rowcount
            
            # Delete the session itself
            cursor.execute("DELETE FROM agent_sessions WHERE session_id = ?", (session_id,))
            session_deleted = cursor.rowcount
            
            conn.commit()
            conn.close()
            
            logger.info(f"Cleaned up chat session for project {project_id}: deleted {messages_deleted} messages and {session_deleted} session record")
            return True
        else:
            logger.info(f"Chat database not found, no cleanup needed for project {project_id}")
            return True
            
    except Exception as e:
        logger.error(f"Error cleaning up chat sessions for project {project_id}: {e}")
        return False

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
        
        # Check if this session already exists and is active
        existing_session = db.sessions.get(session_id)
        if existing_session and existing_session.is_active:
            # Update the existing session with new user name if provided
            if request.userName and existing_session.user_name != request.userName:
                # Update user name and activity
                db.sessions.update_activity(session_id)
                # Note: We'd need a method to update user_name, for now just log it
                logger.info(f"Session {session_id} already exists, updating activity")
            
            return JoinProjectResponse(
                sessionId=session_id,
                projectId=request.projectId,
                message=f"Rejoined project {request.projectId}"
            )
        
        # Deactivate any existing sessions for this user/project combination to prevent duplicates
        if request.userName:
            active_sessions = db.sessions.get_active_by_project(request.projectId)
            for session in active_sessions:
                if session.user_name == request.userName:
                    db.sessions.set_inactive(session.session_id)
                    logger.info(f"Deactivated duplicate session {session.session_id} for user {request.userName}")
        
        # Create new session for this user/project
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
        
        # Get document content before processing
        doc_before = get_document_content(request.projectId)
        
        # Create conversation if needed and add user message
        conversation_id = f"conv_{request.projectId}_{session_id}"
        if not db.conversations.get(conversation_id):
            db.conversations.create(conversation_id, request.projectId, session_id)
        db.conversations.add_message(conversation_id, "user", request.message)
        
        # Process message through agent system
        ai_response = await run_agent_conversation(request.message, request.projectId)
        
        # Add AI response to history
        db.conversations.add_message(conversation_id, "assistant", ai_response)
        
        # Get document content after processing
        doc_after = get_document_content(request.projectId)
        
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

@app.post("/projects/{project_id}/cleanup-sessions")
async def cleanup_orphaned_sessions(project_id: str):
    """Clean up orphaned or duplicate sessions for a project"""
    try:
        active_sessions = db.sessions.get_active_by_project(project_id)
        
        # Group sessions by username
        user_sessions = {}
        orphaned_sessions = []
        
        for session in active_sessions:
            if not session.user_name or session.user_name.strip() == "":
                orphaned_sessions.append(session)
            else:
                if session.user_name not in user_sessions:
                    user_sessions[session.user_name] = []
                user_sessions[session.user_name].append(session)
        
        cleanup_count = 0
        
        # Clean up orphaned sessions (no username)
        for session in orphaned_sessions:
            db.sessions.set_inactive(session.session_id)
            cleanup_count += 1
            logger.info(f"Cleaned up orphaned session {session.session_id}")
        
        # Clean up duplicate sessions (keep the most recent one per user)
        for user_name, sessions in user_sessions.items():
            if len(sessions) > 1:
                # Sort by joined_at_ts, keep the most recent
                sessions.sort(key=lambda s: s.joined_at_ts, reverse=True)
                for session in sessions[1:]:  # Deactivate all but the first (most recent)
                    db.sessions.set_inactive(session.session_id)
                    cleanup_count += 1
                    logger.info(f"Cleaned up duplicate session {session.session_id} for user {user_name}")
        
        return {"message": f"Cleaned up {cleanup_count} sessions", "cleaned": cleanup_count}
    except Exception as e:
        logger.error(f"Error cleaning up sessions: {e}")
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
        
        chat_cleanup_success = cleanup_chat_sessions_for_project(project_id)
        if not chat_cleanup_success:
            logger.warning(f"Failed to clean up chat sessions for project {project_id}, but continuing with project deletion")
        
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
    
@app.get("/health")
async def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)