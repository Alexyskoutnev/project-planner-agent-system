import os
import logging
from agents import function_tool
import threading

# Global project context for agents - thread-safe storage
_project_context = threading.local()

def set_project_context(project_id: str, db_instance):
    """Set the current project context for the agents"""
    _project_context.project_id = project_id
    _project_context.db = db_instance

def get_project_context():
    """Get the current project context"""
    return getattr(_project_context, 'project_id', None), getattr(_project_context, 'db', None)

# TOOLS 
@function_tool
def write_doc(content: str) -> str:
    """
    write the entire project document with new content.
    This is used to update the plan with a clean, structured format.
    """
    try:
        project_id, db = get_project_context()
        if not project_id or not db:
            logging.error("No project context available for document update")
            return "Error: No project context available for document update"
        
        document_id = f"doc_{project_id}"
        
        # Try to update existing document, create if it doesn't exist
        if not db.documents.update_content(document_id, content):
            # Document doesn't exist, create it
            success = db.documents.create(document_id, content, project_id)
            if not success:
                logging.error("Failed to create new document")
                return "Error: Failed to create new document"
        
        logging.info(f"Document updated successfully for project {project_id}")
        return "Document updated successfully."
    except Exception as e:
        logging.error(f"Error updating document: {e}")
        return f"Error updating document: {str(e)}"

@function_tool
def read_current_doc() -> str:
    """
    Reads the current project document from the database.
    """
    try:
        project_id, db = get_project_context()
        if not project_id or not db:
            logging.error("No project context available for document reading")
            return "document could not be found"
        
        document_id = f"doc_{project_id}"
        document = db.documents.get(document_id)
        
        if document and document.content.strip():
            logging.info(f"Successfully read current document for project {project_id}")
            return document.content
        else:
            logging.info(f"No document found for project {project_id}")
            return "document could not be found"
    except Exception as e:
        logging.error(f"Error reading document: {e}")
        return "document could not be found"

@function_tool
def get_current_date() -> str:
    "Gets the current time for the document."
    import datetime
    return datetime.datetime.now().strftime("%Y-%m-%d")

@function_tool
def verify_document_saved() -> str:
    """
    Verify that the document was successfully saved to the database.
    Returns the length of the saved document for confirmation.
    """
    try:
        project_id, db = get_project_context()
        if not project_id or not db:
            return "Error: No project context available"
        
        document_id = f"doc_{project_id}"
        document = db.documents.get(document_id)
        
        if document and document.content.strip():
            return f"✓ Document successfully saved! ({len(document.content)} characters)"
        else:
            return "✗ No document found in database"
    except Exception as e:
        return f"Error verifying document: {str(e)}"

def read_doc() -> str:
    """
    Reads the current project document from the database for display purposes.
    This is a non-tool version of read_current_doc for internal use.
    """
    try:
        project_id, db = get_project_context()
        if not project_id or not db:
            return "# No document available"
        
        document_id = f"doc_{project_id}"
        document = db.documents.get(document_id)
        
        if document and document.content.strip():
            return document.content
        else:
            return "# No document available"
    except Exception as e:
        logging.error(f"Error reading document for display: {e}")
        return "# No document available"