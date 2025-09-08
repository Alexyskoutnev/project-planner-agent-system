import os
import sys
import logging
import asyncio
import uuid
import sqlite3
import io
import time
import base64

import secrets
from typing import Dict, List, Optional
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
import PyPDF2
import requests

try:
    import jwt  # PyJWT
    if not hasattr(jwt, 'encode'):
        raise ImportError("Wrong JWT library - need PyJWT")
except ImportError:
    print("ERROR: PyJWT library not found. Install with: pip install PyJWT")
    raise


from fastapi import FastAPI, HTTPException, Header, Depends, UploadFile, File, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, JSONResponse
from pydantic import BaseModel
from starlette.middleware.sessions import SessionMiddleware

from agents import Runner, SQLiteSession
from naii_agents.agents import product_manager
from naii_agents.tools import set_project_context
import os

from database.database import ProjectDatabase

logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

load_dotenv()

# Duo Configuration - Environment-based for local/production
DUO_CLIENT_ID = os.getenv("DUO_CLIENT_ID", "")
DUO_SECRET = os.getenv("DUO_SECRET", "")
DUO_API_HOST = os.getenv("DUO_API_HOST", "")

# Environment-aware URLs
ENVIRONMENT = os.getenv("NODE_ENV", "development")
if ENVIRONMENT == "production":
    REDIRECT_URI = os.getenv("REDIRECT_URI", "https://naii-project-planner.naii.com/auth/duocallback")
    FRONTEND_URL = os.getenv("FRONTEND_URL", "https://naii-project-planner.naii.com")
else:
    REDIRECT_URI = os.getenv("REDIRECT_URI", "http://localhost:8000/auth/duocallback")
    FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

# Default Duo username (from C# code)
DEFAULT_DUO_USERNAME = "ddicocco"

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    logger.error("OpenAI API key not found. Please set OPENAI_API_KEY environment variable.")
    raise ValueError("OpenAI API key is required")

os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

db = ProjectDatabase()

def _now_utc() -> int:
    return int(time.time())

def _random_state(n: int = 16) -> str:
    return base64.urlsafe_b64encode(secrets.token_bytes(n)).decode().rstrip("=")

app = FastAPI(
    title="NAI Project Planning API",
    description="Multi-user AI-powered project planning with state management",
    version="2.0.0"
)

app.add_middleware(SessionMiddleware, 
                   secret_key=os.getenv("SESSION_SECRET", "dev-session-secret-for-duo"))

# CORS middleware for frontend
# Environment-aware CORS origins
allowed_origins = [
    "http://localhost:3000",      # React dev server
    "http://127.0.0.1:3000",     # React dev server alternative
    "http://localhost:8000",      # Development API testing
    "http://127.0.0.1:8000",     # Development API testing alternative
]

# Add production origins
if ENVIRONMENT == "production":
    allowed_origins.extend([
        "https://naii-project-planner.naii.com",
        "http://172.28.3.20:8000",      # Internal IP for API
        "http://172.28.3.20:3000",      # Internal IP for frontend
    ])

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
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

class DocumentUploadResponse(BaseModel):
    uploadId: str
    filename: str
    fileSize: int
    message: str

class UploadedDocumentsResponse(BaseModel):
    documents: List[Dict]

class InviteRequest(BaseModel):
    email: str
    inviterName: Optional[str] = None

class InviteResponse(BaseModel):
    success: bool
    message: str
    invitationId: Optional[str] = None

class ValidateInvitationResponse(BaseModel):
    valid: bool
    projectId: Optional[str] = None
    message: str

# Duo Authentication Models
class TokenResponseDUO(BaseModel):
    access_token: str
    id_token: str
    token_type: Optional[str] = None
    expires_in: Optional[int] = None
    scope: Optional[str] = None

class DuoUserInfo(BaseModel):
    userId: str
    username: str
    authenticated: bool = True

# Helper functions
def get_session_id(x_session_id: str = Header(None)) -> Optional[str]:
    """Get session ID from header, don't create new ones"""
    return x_session_id

def get_or_create_session_id(x_session_id: str = Header(None)) -> str:
    """Get or create session ID from header - only used for join endpoint"""
    if not x_session_id:
        return str(uuid.uuid4())
    return x_session_id

def extract_text_from_pdf(pdf_content: bytes) -> str:
    """Extract text content from PDF bytes"""
    try:
        pdf_file = io.BytesIO(pdf_content)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        
        text_content = []
        for page_num, page in enumerate(pdf_reader.pages):
            try:
                page_text = page.extract_text()
                if page_text.strip():  # Only add non-empty pages
                    text_content.append(f"=== Page {page_num + 1} ===\n{page_text}\n")
            except Exception as e:
                logger.warning(f"Failed to extract text from page {page_num + 1}: {e}")
                text_content.append(f"=== Page {page_num + 1} ===\n[Text extraction failed]\n")
        
        if not text_content:
            return "[PDF appears to be empty or text extraction failed]"
        
        return "\n".join(text_content)
    except Exception as e:
        logger.error(f"PDF processing error: {e}")
        return f"[PDF processing error: {str(e)}]"

def send_invitation_email(email: str, 
                          project_id: str, 
                          invitation_token: str, 
                          inviter_name: Optional[str] = None) -> bool:
    """Send invitation email to the specified email address"""
    from email_handler.email_service import get_email_service
    
    try:
        logger.info(f"Attempting to send invitation email to {email} for project {project_id}")
        
        # Get email service and check what handler it's using
        email_service = get_email_service()
        handler = email_service._get_handler()
        logger.info(f"Using email handler: {type(handler).__name__}")
        
        # Log environment variables (without exposing secrets)
        env_vars = {
            'TENANT_ID': 'SET' if os.getenv('TENANT_ID') else 'MISSING',
            'CLIENT_ID': 'SET' if os.getenv('CLIENT_ID') else 'MISSING', 
            'CLIENT_SECRET': 'SET' if os.getenv('CLIENT_SECRET') else 'MISSING',
            'USER_EMAIL': os.getenv('USER_EMAIL', 'MISSING'),
            'SENDER_EMAIL': 'SET' if os.getenv('SENDER_EMAIL') else 'MISSING',
            'SENDER_PASSWORD': 'SET' if os.getenv('SENDER_PASSWORD') else 'MISSING',
            'SMTP_SERVER': os.getenv('SMTP_SERVER', 'MISSING')
        }
        logger.info(f"Email configuration status: {env_vars}")
        
        result = email_service.send_invitation_email(
            email=email,
            project_id=project_id,
            invitation_token=invitation_token,
            inviter_name=inviter_name
        )
        
        if result:
            logger.info(f"Successfully sent invitation email to {email}")
        else:
            logger.error(f"Failed to send invitation email to {email} - email service returned False")
            
        return result
        
    except Exception as e:
        logger.error(f"Exception while sending invitation email to {email}: {type(e).__name__}: {e}", exc_info=True)
        return False

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

# Duo Authentication Endpoints
@app.get("/start-duo-login")
def start_duo_login(request: Request, 
                    duo_uname: Optional[str] = None) -> RedirectResponse:
    """
    Builds Duo 'request' JWT and redirects to Duo /oauth/v1/authorize.
    Stores CSRF 'state' in session.
    """
    # Use provided username or default (matching C# implementation)
    username = duo_uname or DEFAULT_DUO_USERNAME
    
    # 1) state
    state = _random_state()
    request.session["duo_state"] = state
    
    # 2) request JWT for Duo authorize
    claims = {
        "iss": DUO_CLIENT_ID,                           # Required
        "aud": f"https://{DUO_API_HOST}",               # Required
        "exp": _now_utc() + 5 * 60,                     # 5 minutes
        # Duo requires these inside the JWT body:
        "client_id": DUO_CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": "openid",
        "state": state,
        "duo_uname": username,                        
    }
    request_jwt = jwt.encode(claims, DUO_SECRET, algorithm="HS256")
    
    # 3) redirect to Duo
    url = (
        f"https://{DUO_API_HOST}/oauth/v1/authorize"
        f"?request={request_jwt}&client_id={DUO_CLIENT_ID}&response_type=code"
    )
    
    return RedirectResponse(url, status_code=307)

@app.get("/auth/duocallback")
def duo_callback(request: Request, 
                 code: Optional[str] = None, 
                 state: Optional[str] = None,
                 duo_uname: Optional[str] = None):
    """
    Exchanges authorization code for tokens. Validates id_token and creates/finds a local user.
    """
    if not code:
        raise HTTPException(status_code=400, detail="Missing 'code'")
    if not state:
        raise HTTPException(status_code=400, detail="Missing 'state'")
    
    stored_state = request.session.get("duo_state")
    if not stored_state or stored_state != state:
        raise HTTPException(status_code=400, detail="Invalid state parameter")
    
    # 1) client_assertion JWT
    client_assertion_claims = {
        "iss": DUO_CLIENT_ID,
        "sub": DUO_CLIENT_ID,
        "aud": f"https://{DUO_API_HOST}/oauth/v1/token",
        "exp": _now_utc() + 5 * 60,
        "jti": secrets.token_hex(16),
    }
    client_assertion = jwt.encode(client_assertion_claims, DUO_SECRET, algorithm="HS256")
    
    # 2) token exchange
    token_url = f"https://{DUO_API_HOST}/oauth/v1/token"
    form = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
        "client_assertion": client_assertion,
    }
    
    try:
        r = requests.post(token_url, data=form, timeout=10)
        r.raise_for_status()
    except requests.RequestException as ex:
        raise HTTPException(status_code=502, detail=f"Error communicating with Duo: {ex}")
    
    try:
        token_resp = TokenResponseDUO(**r.json())
    except Exception:
        raise HTTPException(status_code=502, detail="Bad token response from Duo")
    
    # 3) id_token validation / parse
    options = {"verify_signature": False, "verify_aud": False, "verify_iss": False}
    
    try:
        decoded = jwt.decode(token_resp.id_token, options=options)
    except Exception as ex:
        raise HTTPException(status_code=400, detail=f"Invalid id_token: {ex}")
    
    user_id = decoded.get("sub")
    username = decoded.get("preferred_username") or user_id
    
    # Store user info in session
    request.session["duo_authenticated"] = True
    request.session["duo_user_id"] = user_id
    request.session["duo_username"] = username
    request.session["current_user"] = username
    
    # Store user info in session
    request.session["duo_authenticated"] = True
    request.session["duo_user_id"] = user_id
    request.session["duo_username"] = username
    request.session["current_user"] = username
    
    # Redirect to frontend with success parameters
    frontend_success_url = f"{FRONTEND_URL}/duo-success"
    return RedirectResponse(f"{frontend_success_url}?user={username}&authenticated=true")

@app.get("/auth/duo-status")
def get_duo_status(request: Request):
    """
    Check if user is authenticated via Duo
    """
    if request.session.get("duo_authenticated"):
        return DuoUserInfo(
            userId=request.session.get("duo_user_id"),
            username=request.session.get("duo_username"),
            authenticated=True
        )
    else:
        raise HTTPException(status_code=401, detail="Not authenticated via Duo")

@app.post("/auth/duo-logout")
def duo_logout(request: Request):
    """
    Logout from Duo authentication
    """
    request.session.pop("duo_authenticated", None)
    request.session.pop("duo_user_id", None)
    request.session.pop("duo_username", None)
    request.session.pop("current_user", None)
    request.session.pop("duo_state", None)
    
    return {"message": "Logged out successfully"}

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
    
@app.post("/projects/{project_id}/upload", response_model=DocumentUploadResponse)
async def upload_document(
    project_id: str,
    file: UploadFile = File(...),
    session_id: Optional[str] = Depends(get_session_id)
):
    """Upload a document to a project"""
    try:
        if not session_id:
            raise HTTPException(status_code=401, detail="No active session. Please join a project first.")
        
        # Verify session belongs to this project
        session = db.sessions.get(session_id)
        if not session or session.project_id != project_id:
            raise HTTPException(status_code=403, detail="Session does not belong to this project")
        
        # Check file size (limit to 10MB)
        if file.size and file.size > 10 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="File too large. Maximum size is 10MB.")
        
        # Read file content
        content = await file.read()
        
        # Handle different file types
        if file.content_type == "application/pdf" or (file.filename and file.filename.lower().endswith('.pdf')):
            # Extract text from PDF
            content_str = extract_text_from_pdf(content)
            file_type = "application/pdf"
        else:
            # Handle text files
            try:
                content_str = content.decode('utf-8')
                file_type = file.content_type or "text/plain"
            except UnicodeDecodeError:
                raise HTTPException(status_code=400, detail="File must be a text file or PDF")
        
        # Generate upload ID
        upload_id = str(uuid.uuid4())
        
        # Save to database
        success = db.uploaded_documents.create(
            upload_id=upload_id,
            project_id=project_id,
            filename=file.filename or "untitled.txt",
            content=content_str,
            file_size=len(content),
            file_type=file_type,
            uploaded_by=session.user_name
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to save document")
        
        # Update session activity
        db.sessions.update_activity(session_id)
        
        return DocumentUploadResponse(
            uploadId=upload_id,
            filename=file.filename or "untitled.txt",
            fileSize=len(content),
            message="Document uploaded successfully"
        )
        
    except Exception as e:
        logger.error(f"Error uploading document: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/projects/{project_id}/uploads", response_model=UploadedDocumentsResponse)
async def get_uploaded_documents(
    project_id: str,
    session_id: Optional[str] = Depends(get_session_id)
):
    """Get all uploaded documents for a project"""
    try:
        if not session_id:
            raise HTTPException(status_code=401, detail="No active session. Please join a project first.")
        
        # Verify session belongs to this project
        session = db.sessions.get(session_id)
        if not session or session.project_id != project_id:
            raise HTTPException(status_code=403, detail="Session does not belong to this project")
        
        documents = db.uploaded_documents.get_by_project(project_id)
        docs_data = [{
            "uploadId": doc.upload_id,
            "filename": doc.filename,
            "fileSize": doc.file_size,
            "fileType": doc.file_type,
            "uploadedBy": doc.uploaded_by,
            "uploadedAt": doc.uploaded_at_ts,
            "content": doc.content[:500] + ("..." if len(doc.content) > 500 else "")  # Preview
        } for doc in documents]
        
        return UploadedDocumentsResponse(documents=docs_data)
        
    except Exception as e:
        logger.error(f"Error getting uploaded documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/uploads/{upload_id}")
async def get_uploaded_document_content(
    upload_id: str,
    session_id: Optional[str] = Depends(get_session_id)
):
    """Get full content of an uploaded document"""
    try:
        if not session_id:
            raise HTTPException(status_code=401, detail="No active session. Please join a project first.")
        
        document = db.uploaded_documents.get(upload_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Verify session belongs to the document's project
        session = db.sessions.get(session_id)
        if not session or session.project_id != document.project_id:
            raise HTTPException(status_code=403, detail="Session does not belong to this project")
        
        return {
            "uploadId": document.upload_id,
            "filename": document.filename,
            "content": document.content,
            "fileSize": document.file_size,
            "fileType": document.file_type,
            "uploadedBy": document.uploaded_by,
            "uploadedAt": document.uploaded_at_ts
        }
        
    except Exception as e:
        logger.error(f"Error getting document content: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/uploads/{upload_id}")
async def delete_uploaded_document(
    upload_id: str,
    session_id: Optional[str] = Depends(get_session_id)
):
    """Delete an uploaded document"""
    try:
        if not session_id:
            raise HTTPException(status_code=401, detail="No active session. Please join a project first.")
        
        document = db.uploaded_documents.get(upload_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Verify session belongs to the document's project
        session = db.sessions.get(session_id)
        if not session or session.project_id != document.project_id:
            raise HTTPException(status_code=403, detail="Session does not belong to this project")
        
        success = db.uploaded_documents.delete(upload_id)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete document")
        
        return {"message": "Document deleted successfully"}
        
    except Exception as e:
        logger.error(f"Error deleting document: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/projects/{project_id}/invite", response_model=InviteResponse)
async def invite_to_project(
    project_id: str,
    invite_request: InviteRequest,
    session_id: Optional[str] = Depends(get_session_id)
):
    """Send an email invitation to join a project"""
    try:
        if not session_id:
            raise HTTPException(status_code=401, detail="No active session. Please join a project first.")
        
        # Verify session belongs to this project
        session = db.sessions.get(session_id)
        if not session or session.project_id != project_id:
            raise HTTPException(status_code=403, detail="Session does not belong to this project")
        
        # Check if project exists
        if not db.projects.get(project_id):
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Generate unique invitation ID and token
        invitation_id = str(uuid.uuid4())
        invitation_token = secrets.token_urlsafe(32)
        
        # Set expiration to 7 days from now
        expires_at = datetime.now(timezone.utc) + timedelta(days=7)
        expires_at_ts = int(expires_at.timestamp())
        
        # Create invitation in database
        success = db.invitations.create(
            invitation_id=invitation_id,
            project_id=project_id,
            email=invite_request.email,
            invitation_token=invitation_token,
            invited_by=invite_request.inviterName or session.user_name,
            expires_at_ts=expires_at_ts
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to create invitation")
        
        email_sent = send_invitation_email(
            invite_request.email,
            project_id,
            invitation_token,
            invite_request.inviterName or session.user_name
        )
        logger.info(f"Email sent details: {email_sent}")
        
        if not email_sent:
            # Still return success if invitation was created, even if email failed
            return InviteResponse(
                success=True,
                message=f"Invitation created but email could not be sent. Ask them to visit the site directly to join project '{project_id}'.",
                invitationId=invitation_id
            )
        
        return InviteResponse(
            success=True,
            message=f"Invitation sent to {invite_request.email}. They will receive a link to join the project.",
            invitationId=invitation_id
        )
        
    except Exception as e:
        logger.error(f"Error inviting user to project {project_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/invitations/{token}/validate", response_model=ValidateInvitationResponse)
async def validate_invitation(token: str):
    """Validate an invitation token and return project details"""
    try:
        invitation = db.invitations.get_by_token(token)
        
        if not invitation:
            return ValidateInvitationResponse(
                valid=False,
                message="Invalid invitation token"
            )
        
        if invitation.is_used:
            return ValidateInvitationResponse(
                valid=False,
                message="This invitation has already been used"
            )
        
        # Check if expired
        if invitation.expires_at_ts:
            current_ts = int(datetime.now(timezone.utc).timestamp())
            if current_ts > invitation.expires_at_ts:
                return ValidateInvitationResponse(
                    valid=False,
                    message="This invitation has expired"
                )
        
        # Check if project still exists
        project = db.projects.get(invitation.project_id)
        if not project:
            return ValidateInvitationResponse(
                valid=False,
                message="The project no longer exists"
            )
        
        return ValidateInvitationResponse(
            valid=True,
            projectId=invitation.project_id,
            message="Invitation is valid"
        )
        
    except Exception as e:
        logger.error(f"Error validating invitation token {token}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/invitations/{token}/accept")
async def accept_invitation(
    token: str,
    session_id: str = Depends(get_or_create_session_id)
):
    """Accept an invitation and join the project"""
    try:
        invitation = db.invitations.get_by_token(token)
        
        if not invitation or not db.invitations.is_valid(token):
            raise HTTPException(status_code=400, detail="Invalid or expired invitation")
        
        # Check if project still exists
        project = db.projects.get(invitation.project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project no longer exists")
        
        # Mark invitation as used
        db.invitations.mark_used(invitation.invitation_id)
        
        # Create or update session to join the project
        existing_session = db.sessions.get(session_id)
        if existing_session:
            # Update existing session
            db.sessions.update_project(session_id, invitation.project_id)
        else:
            # Create new session
            db.sessions.create(session_id, invitation.project_id)
        
        return JoinProjectResponse(
            success=True,
            message=f"Successfully joined project: {invitation.project_id}",
            projectId=invitation.project_id,
            sessionId=session_id
        )
        
    except Exception as e:
        logger.error(f"Error accepting invitation {token}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/projects/{project_id}/invitations")
async def get_project_invitations(
    project_id: str,
    session_id: Optional[str] = Depends(get_session_id)
):
    """Get all invitations for a project"""
    try:
        if not session_id:
            raise HTTPException(status_code=401, detail="No active session. Please join a project first.")
        
        # Verify session belongs to this project
        session = db.sessions.get(session_id)
        if not session or session.project_id != project_id:
            raise HTTPException(status_code=403, detail="Session does not belong to this project")
        
        invitations = db.invitations.get_by_project(project_id)
        
        invitations_data = [{
            "invitationId": inv.invitation_id,
            "email": inv.email,
            "invitedBy": inv.invited_by,
            "createdAt": inv.created_at_ts,
            "expiresAt": inv.expires_at_ts,
            "isUsed": inv.is_used,
            "usedAt": inv.used_at_ts
        } for inv in invitations]
        
        return {"invitations": invitations_data}
        
    except Exception as e:
        logger.error(f"Error getting project invitations for {project_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.post("/test-email")
async def test_email_sending():
    """Test endpoint to verify email sending works - bypasses session validation"""
    try:
        logger.info("=== TESTING EMAIL SENDING ===")
        
        # Test email sending directly
        result = send_invitation_email(
            email="test@example.com",
            project_id="TestProject", 
            invitation_token="test-token-123",
            inviter_name="Test User"
        )
        
        logger.info(f"=== EMAIL TEST RESULT: {result} ===")
        
        return {
            "success": result, 
            "message": "Email test completed. Check logs for detailed results.",
            "check_logs_command": "sudo journalctl -u fastapi -n 50 --no-pager"
        }
        
    except Exception as e:
        logger.error(f"Test email failed: {type(e).__name__}: {e}", exc_info=True)
        return {
            "success": False, 
            "error": str(e),
            "message": "Email test failed. Check logs for details."
        }

@app.get("/test-credentials")
async def test_credentials():
    """Test endpoint to check if Microsoft Graph credentials are loaded"""
    try:
        logger.info("=== TESTING CREDENTIAL LOADING ===")
        
        # Check environment variables
        env_status = {
            'TENANT_ID': 'SET' if os.getenv('TENANT_ID') else 'MISSING',
            'CLIENT_ID': 'SET' if os.getenv('CLIENT_ID') else 'MISSING', 
            'CLIENT_SECRET': 'SET' if os.getenv('CLIENT_SECRET') else 'MISSING',
            'USER_EMAIL': os.getenv('USER_EMAIL', 'MISSING')
        }
        logger.info(f"Environment variables: {env_status}")
        
        # Test email service initialization
        from email_handler.email_service import get_email_service
        email_service = get_email_service()
        handler = email_service._get_handler()
        handler_type = type(handler).__name__
        
        logger.info(f"Email handler type: {handler_type}")
        
        # Test Microsoft Graph token (if using Microsoft handler)
        if handler_type == "MicrosoftGraphAPIEmailHandler":
            try:
                logger.info("Testing Microsoft Graph API token...")
                access_token = handler._get_access_token()
                token_preview = access_token[:10] + "..." if access_token else "None"
                logger.info(f"Successfully obtained access token: {token_preview}")
                token_status = "SUCCESS"
            except Exception as token_error:
                logger.error(f"Failed to get access token: {token_error}")
                token_status = f"FAILED: {str(token_error)}"
        else:
            token_status = f"N/A (using {handler_type})"
        
        logger.info("=== CREDENTIAL TEST COMPLETE ===")
        
        return {
            "credentials_loaded": env_status,
            "email_handler": handler_type,
            "token_test": token_status,
            "message": "Credential test completed. Check logs for details."
        }
        
    except Exception as e:
        logger.error(f"Credential test failed: {type(e).__name__}: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "message": "Credential test failed. Check logs for details."
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)