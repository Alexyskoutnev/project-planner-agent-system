import logging
from sqlmodel import SQLModel, Field, Column, JSON, create_engine, Session
from datetime import datetime, timezone
from typing import Optional

class Project(SQLModel, table=True):
    __tablename__ = "projects"
    
    project_id: str = Field(primary_key=True)
    created_at_ts: int = Field(default_factory=lambda: int(datetime.now(timezone.utc).timestamp()))
    updated_at_ts: int = Field(default_factory=lambda: int(datetime.now(timezone.utc).timestamp()))


class Document(SQLModel, table=True):
    __tablename__ = "documents"
    
    document_id: str = Field(primary_key=True)
    content: str = Field(default="")
    updated_at_ts: int = Field(default_factory=lambda: int(datetime.now(timezone.utc).timestamp()))
    project_id: str = Field(foreign_key="projects.project_id")


class UserSession(SQLModel, table=True):
    __tablename__ = "sessions"
    
    session_id: str = Field(primary_key=True)
    project_id: str
    user_name: Optional[str] = Field(default=None)
    joined_at_ts: int = Field(default_factory=lambda: int(datetime.now(timezone.utc).timestamp()))
    last_activity_ts: int = Field(default_factory=lambda: int(datetime.now(timezone.utc).timestamp()))
    is_active: bool = Field(default=True)


class Conversation(SQLModel, table=True):
    __tablename__ = "conversations"
    
    conversation_id: str = Field(primary_key=True)
    project_id: str = Field(foreign_key="projects.project_id")
    session_id: Optional[str] = Field(default=None)  # Optional: track which session started this conversation
    timestamp_ts: int = Field(default_factory=lambda: int(datetime.now(timezone.utc).timestamp()))
    messages: Optional[list[dict[str, str]]] = Field(default_factory=list, sa_column=Column(JSON))
    is_active: bool = Field(default=True)  # Track if conversation is still active


class DatabaseManager:
    def __init__(self, database_url: str = "sqlite:///project_database.db"):
        self.database_url = database_url
        self.engine = create_engine(database_url, echo=False)
        self.create_tables()
    
    def create_tables(self):
        SQLModel.metadata.create_all(self.engine)
        logging.info(f"Database created: {self.database_url}")
        logging.info("Tables created: projects, documents, sessions, conversations")
    
    def get_session(self):
        return Session(self.engine)
    
    def drop_all_tables(self):
        SQLModel.metadata.drop_all(self.engine)
        logging.info("All tables dropped")
    
    def recreate_tables(self):
        self.drop_all_tables()
        self.create_tables()


class ProjectCRUD:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    def create(self, project_id: str, created_at_ts: int = None, updated_at_ts: int = None) -> bool:
        try:
            with self.db.get_session() as session:
                project = Project(
                    project_id=project_id,
                    created_at_ts=created_at_ts if created_at_ts else int(datetime.now(timezone.utc).timestamp()),
                    updated_at_ts=updated_at_ts if updated_at_ts else int(datetime.now(timezone.utc).timestamp())
                )
                session.add(project)
                session.commit()
                return True
        except Exception as e:
            print(f"Error creating project: {e}")
            return False
    
    def get(self, project_id: str) -> Optional[Project]:
        with self.db.get_session() as session:
            return session.get(Project, project_id)
    
    def update_timestamp(self, project_id: str) -> bool:
        try:
            with self.db.get_session() as session:
                project = session.get(Project, project_id)
                if project:
                    project.updated_at_ts = int(datetime.now(timezone.utc).timestamp())
                    session.commit()
                    return True
                return False
        except Exception as e:
            print(f"Error updating project: {e}")
            return False
    
    def delete(self, project_id: str) -> bool:
        try:
            with self.db.get_session() as session:
                project = session.get(Project, project_id)
                if project:
                    session.delete(project)
                    session.commit()
                    return True
                return False
        except Exception as e:
            print(f"Error deleting project: {e}")
            return False
    
    def list_all(self) -> list[Project]:
        with self.db.get_session() as session:
            return session.query(Project).all()


class DocumentCRUD:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    def create(self, document_id: str, content: str, project_id: str) -> bool:
        try:
            with self.db.get_session() as session:
                document = Document(
                    document_id=document_id,
                    content=content,
                    project_id=project_id
                )
                session.add(document)
                session.commit()
                return True
        except Exception as e:
            print(f"Error creating document: {e}")
            return False
    
    def get(self, document_id: str) -> Optional[Document]:
        with self.db.get_session() as session:
            return session.get(Document, document_id)
    
    def update_content(self, document_id: str, content: str) -> bool:
        try:
            with self.db.get_session() as session:
                document = session.get(Document, document_id)
                if document:
                    document.content = content
                    document.updated_at_ts = int(datetime.now(timezone.utc).timestamp())
                    session.commit()
                    return True
                return False
        except Exception as e:
            print(f"Error updating document: {e}")
            return False


class SessionCRUD:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    def create(self, session_id: str, project_id: str, user_name: str = None) -> bool:
        try:
            with self.db.get_session() as session:
                user_session = UserSession(
                    session_id=session_id,
                    project_id=project_id,
                    user_name=user_name
                )
                session.add(user_session)
                session.commit()
                return True
        except Exception as e:
            print(f"Error creating session: {e}")
            return False
    
    def get(self, session_id: str) -> Optional[UserSession]:
        with self.db.get_session() as session:
            return session.get(UserSession, session_id)
    
    def update_activity(self, session_id: str) -> bool:
        try:
            with self.db.get_session() as session:
                user_session = session.get(UserSession, session_id)
                if user_session:
                    user_session.last_activity_ts = int(datetime.now(timezone.utc).timestamp())
                    session.commit()
                    return True
                return False
        except Exception as e:
            print(f"Error updating session activity: {e}")
            return False
    
    def set_inactive(self, session_id: str) -> bool:
        try:
            with self.db.get_session() as session:
                user_session = session.get(UserSession, session_id)
                if user_session:
                    user_session.is_active = False
                    session.commit()
                    return True
                return False
        except Exception as e:
            print(f"Error setting session inactive: {e}")
            return False
    
    def get_active_by_project(self, project_id: str) -> list[UserSession]:
        with self.db.get_session() as session:
            return session.query(UserSession).filter(
                UserSession.project_id == project_id,
                UserSession.is_active == True
            ).all()


class ConversationCRUD:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    def create(self, conversation_id: str, project_id: str, session_id: str = None, messages: list[dict[str, str]] = None) -> bool:
        """Create a new conversation"""
        try:
            with self.db.get_session() as session:
                conversation = Conversation(
                    conversation_id=conversation_id,
                    project_id=project_id,
                    session_id=session_id,
                    messages=messages or []
                )
                session.add(conversation)
                session.commit()
                return True
        except Exception as e:
            print(f"Error creating conversation: {e}")
            return False
    
    def get(self, conversation_id: str) -> Optional[Conversation]:
        """Get conversation by ID"""
        with self.db.get_session() as session:
            return session.get(Conversation, conversation_id)
    
    def add_message(self, conversation_id: str, role: str, content: str) -> bool:
        """Add a message to a specific conversation"""
        try:
            with self.db.get_session() as session:
                conversation = session.get(Conversation, conversation_id)
                if conversation:
                    if conversation.messages is None:
                        conversation.messages = []
                    conversation.messages.append({
                        "role": role, 
                        "content": content,
                        "timestamp": int(datetime.now(timezone.utc).timestamp())
                    })
                    # Mark the field as modified so SQLAlchemy detects the change
                    from sqlalchemy.orm.attributes import flag_modified
                    flag_modified(conversation, 'messages')
                    session.commit()
                    return True
                return False
        except Exception as e:
            print(f"Error adding message to conversation {conversation_id}: {e}")
            return False
    
    def get_by_project(self, project_id: str) -> list[Conversation]:
        """Get all conversations for a project"""
        with self.db.get_session() as session:
            return session.query(Conversation).filter(Conversation.project_id == project_id).all()
    
    def get_active_by_project(self, project_id: str) -> list[Conversation]:
        """Get all active conversations for a project"""
        with self.db.get_session() as session:
            return session.query(Conversation).filter(
                Conversation.project_id == project_id,
                Conversation.is_active == True
            ).all()
    
    def get_by_session(self, session_id: str) -> list[Conversation]:
        """Get all conversations for a specific session"""
        with self.db.get_session() as session:
            return session.query(Conversation).filter(Conversation.session_id == session_id).all()
    
    def set_inactive(self, conversation_id: str) -> bool:
        """Mark conversation as inactive"""
        try:
            with self.db.get_session() as session:
                conversation = session.get(Conversation, conversation_id)
                if conversation:
                    conversation.is_active = False
                    session.commit()
                    return True
                return False
        except Exception as e:
            print(f"Error setting conversation inactive: {e}")
            return False
    
    def get_latest_by_project(self, project_id: str) -> Optional[Conversation]:
        """Get the most recent conversation for a project"""
        with self.db.get_session() as session:
            return session.query(Conversation).filter(
                Conversation.project_id == project_id
            ).order_by(Conversation.timestamp_ts.desc()).first()
    
    def clear_messages(self, conversation_id: str) -> bool:
        """Clear all messages from a conversation"""
        try:
            with self.db.get_session() as session:
                conversation = session.get(Conversation, conversation_id)
                if conversation:
                    conversation.messages = []
                    session.commit()
                    return True
                return False
        except Exception as e:
            print(f"Error clearing messages: {e}")
            return False
    
    def get_message_count(self, conversation_id: str) -> int:
        """Get the number of messages in a conversation"""
        conversation = self.get(conversation_id)
        return len(conversation.messages) if conversation and conversation.messages else 0


class ProjectDatabase:
    def __init__(self, database_url: str = "sqlite:///project_database.db"):
        self.db_manager = DatabaseManager(database_url)
        self.projects = ProjectCRUD(self.db_manager)
        self.documents = DocumentCRUD(self.db_manager)
        self.sessions = SessionCRUD(self.db_manager)
        self.conversations = ConversationCRUD(self.db_manager)
    
    def get_session(self):
        return self.db_manager.get_session()
    
    def drop_all_tables(self):
        self.db_manager.drop_all_tables()
    
    def recreate_tables(self):
        self.db_manager.recreate_tables()


# Example usage showing the fixed conversation workflow
if __name__ == "__main__":
    db = ProjectDatabase("sqlite:///project_database.db")
    db.recreate_tables()
    
    # Create project and session
    db.projects.create("test_project")
    db.sessions.create("test_session", "test_project", "Alice")
    
    # Create conversation tied to project and session
    db.conversations.create("test_conversation", "test_project", "test_session")
    
    # Add messages to the specific conversation
    db.conversations.add_message("test_conversation", "user", "Hello, I need help")
    db.conversations.add_message("test_conversation", "assistant", "I'd be happy to help! What do you need?")
    db.conversations.add_message("test_conversation", "user", "Can you explain this project?")
    
    # Create another conversation for the same project
    db.conversations.create("test_conversation_2", "test_project", "test_session")
    db.conversations.add_message("test_conversation_2", "user", "Let's discuss the timeline")
    db.conversations.add_message("test_conversation_2", "assistant", "Sure, what's your target deadline?")
    
    # Query conversations
    conv1 = db.conversations.get("test_conversation")
    conv2 = db.conversations.get("test_conversation_2")
    
    print(f"Conversation 1: {len(conv1.messages)} messages")
    for msg in conv1.messages:
        print(f"  {msg['role']}: {msg['content']}")
    
    print(f"\nConversation 2: {len(conv2.messages)} messages")
    for msg in conv2.messages:
        print(f"  {msg['role']}: {msg['content']}")
    
    # Get all conversations for the project
    all_convs = db.conversations.get_by_project("test_project")
    print(f"\nTotal conversations for project: {len(all_convs)}")
    
    breakpoint()