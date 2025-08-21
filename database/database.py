import sqlite3
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from contextlib import contextmanager

logger = logging.getLogger(__name__)

class ProjectDatabase:
    
    def __init__(self, 
                 db_path: str = "project_planning.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database with required tables"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Projects table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS projects (
                    id TEXT PRIMARY KEY,
                    name TEXT,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Project documents table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS project_documents (
                    project_id TEXT PRIMARY KEY,
                    content TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (project_id) REFERENCES projects(id)
                )
            """)
            
            # User sessions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_sessions (
                    session_id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    user_name TEXT,
                    user_id TEXT,
                    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1,
                    FOREIGN KEY (project_id) REFERENCES projects(id)
                )
            """)
            
            # Conversation history table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS conversation_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id TEXT NOT NULL,
                    session_id TEXT,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (project_id) REFERENCES projects(id),
                    FOREIGN KEY (session_id) REFERENCES user_sessions(session_id)
                )
            """)
            
            # Create indexes for better performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_project ON user_sessions(project_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_active ON user_sessions(is_active)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_history_project ON conversation_history(project_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_history_timestamp ON conversation_history(timestamp)")
            
            conn.commit()
            logger.info("Database initialized successfully")
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable dict-like access to rows
        try:
            yield conn
        finally:
            conn.close()
    
    # Project management
    def create_project(self, project_id: str, name: str = None, description: str = None) -> bool:
        """Create a new project"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR IGNORE INTO projects (id, name, description)
                    VALUES (?, ?, ?)
                """, (project_id, name or f"Project {project_id}", description))
                
                # Initialize empty document
                cursor.execute("""
                    INSERT OR IGNORE INTO project_documents (project_id, content)
                    VALUES (?, ?)
                """, (project_id, "# Project Plan\n\nWaiting for project details..."))
                
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error creating project {project_id}: {e}")
            return False
    
    def get_project(self, project_id: str) -> Optional[Dict]:
        """Get project details"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM projects WHERE id = ?
                """, (project_id,))
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            logger.error(f"Error getting project {project_id}: {e}")
            return None
    
    def list_projects(self) -> List[Dict]:
        """List all projects"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT p.*, 
                           COUNT(DISTINCT us.session_id) as active_users,
                           MAX(ch.timestamp) as last_activity
                    FROM projects p
                    LEFT JOIN user_sessions us ON p.id = us.project_id AND us.is_active = 1
                    LEFT JOIN conversation_history ch ON p.id = ch.project_id
                    GROUP BY p.id
                    ORDER BY p.updated_at DESC
                """)
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error listing projects: {e}")
            return []
    
    # Document management
    def save_document(self, project_id: str, content: str) -> bool:
        """Save document content for a project"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Ensure project exists
                self.create_project(project_id)
                
                # Update document
                cursor.execute("""
                    INSERT OR REPLACE INTO project_documents (project_id, content, updated_at)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                """, (project_id, content))
                
                # Update project timestamp
                cursor.execute("""
                    UPDATE projects SET updated_at = CURRENT_TIMESTAMP WHERE id = ?
                """, (project_id,))
                
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error saving document for project {project_id}: {e}")
            return False
    
    def get_document(self, project_id: str) -> str:
        """Get document content for a project"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT content FROM project_documents WHERE project_id = ?
                """, (project_id,))
                row = cursor.fetchone()
                if row:
                    return row['content']
                else:
                    # Create project and return default document
                    self.create_project(project_id)
                    return "# Project Plan\n\nWaiting for project details..."
        except Exception as e:
            logger.error(f"Error getting document for project {project_id}: {e}")
            return "# Project Plan\n\nError loading document"
    
    # User session management
    def join_project(self, session_id: str, project_id: str, user_name: str = None, user_id: str = None) -> bool:
        """Add user session to a project"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Ensure project exists
                self.create_project(project_id)
                
                # Deactivate any existing session for this session_id
                cursor.execute("""
                    UPDATE user_sessions SET is_active = 0 WHERE session_id = ?
                """, (session_id,))
                
                # Create new active session
                cursor.execute("""
                    INSERT INTO user_sessions 
                    (session_id, project_id, user_name, user_id, joined_at, last_activity, is_active)
                    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 1)
                """, (session_id, project_id, user_name, user_id))
                
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error joining project {project_id} for session {session_id}: {e}")
            return False
    
    def leave_project(self, session_id: str) -> bool:
        """Remove user session from project"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE user_sessions SET is_active = 0 WHERE session_id = ?
                """, (session_id,))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error leaving project for session {session_id}: {e}")
            return False
    
    def update_session_activity(self, session_id: str) -> bool:
        """Update last activity timestamp for a session"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE user_sessions 
                    SET last_activity = CURRENT_TIMESTAMP 
                    WHERE session_id = ? AND is_active = 1
                """, (session_id,))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error updating activity for session {session_id}: {e}")
            return False
    
    def get_active_users(self, project_id: str) -> List[Dict]:
        """Get list of active users in a project"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                # Consider users active if they've been active in the last 5 minutes
                cursor.execute("""
                    SELECT session_id, user_name, user_id, joined_at, last_activity
                    FROM user_sessions
                    WHERE project_id = ? 
                      AND is_active = 1 
                      AND last_activity > datetime('now', '-5 minutes')
                    ORDER BY joined_at
                """, (project_id,))
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting active users for project {project_id}: {e}")
            return []
    
    def cleanup_inactive_sessions(self, inactive_minutes: int = 30):
        """Mark sessions as inactive if no activity for specified minutes"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE user_sessions 
                    SET is_active = 0 
                    WHERE is_active = 1 
                      AND last_activity < datetime('now', '-{} minutes')
                """.format(inactive_minutes))
                conn.commit()
                if cursor.rowcount > 0:
                    logger.info(f"Cleaned up {cursor.rowcount} inactive sessions")
        except Exception as e:
            logger.error(f"Error cleaning up inactive sessions: {e}")
    
    # Conversation history
    def add_message(self, project_id: str, role: str, content: str, session_id: str = None) -> bool:
        """Add message to conversation history"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO conversation_history (project_id, session_id, role, content)
                    VALUES (?, ?, ?, ?)
                """, (project_id, session_id, role, content))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error adding message to project {project_id}: {e}")
            return False
    
    def get_conversation_history(self, project_id: str, limit: int = 100) -> List[Dict]:
        """Get conversation history for a project"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT ch.*, us.user_name
                    FROM conversation_history ch
                    LEFT JOIN user_sessions us ON ch.session_id = us.session_id
                    WHERE ch.project_id = ?
                    ORDER BY ch.timestamp
                    LIMIT ?
                """, (project_id, limit))
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting conversation history for project {project_id}: {e}")
            return []
    
    def clear_project_data(self, project_id: str) -> bool:
        """Clear all data for a project"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Clear in order due to foreign key constraints
                cursor.execute("DELETE FROM conversation_history WHERE project_id = ?", (project_id,))
                cursor.execute("DELETE FROM user_sessions WHERE project_id = ?", (project_id,))
                cursor.execute("DELETE FROM project_documents WHERE project_id = ?", (project_id,))
                cursor.execute("DELETE FROM projects WHERE id = ?", (project_id,))
                
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error clearing project data for {project_id}: {e}")
            return False