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

@function_tool
def list_uploaded_documents() -> str:
    """
    Lists all uploaded documents for the current project with their IDs, filenames, and sizes.
    Use this to see what documents users have uploaded.
    """
    try:
        project_id, db = get_project_context()
        if not project_id or not db:
            return "Error: No project context available"
        
        documents = db.uploaded_documents.get_by_project(project_id)
        
        if not documents:
            return "No documents have been uploaded yet."
        
        doc_list = []
        for doc in documents:
            uploaded_by = doc.uploaded_by or "Anonymous"
            size_kb = round(doc.file_size / 1024, 1)
            doc_list.append(f"- {doc.filename} ({size_kb}KB, uploaded by {uploaded_by}) [ID: {doc.upload_id}]")
        
        return f"Uploaded Documents ({len(documents)}):\n" + "\n".join(doc_list)
    except Exception as e:
        logging.error(f"Error listing uploaded documents: {e}")
        return f"Error listing documents: {str(e)}"

@function_tool
def read_uploaded_document(filename_or_id: str) -> str:
    """
    Reads the content of an uploaded document by filename or upload ID.
    Use this when you need to analyze or reference content from user-uploaded documents.
    """
    try:
        project_id, db = get_project_context()
        if not project_id or not db:
            return "Error: No project context available"
        
        documents = db.uploaded_documents.get_by_project(project_id)
        
        # Try to find by exact filename first, then by upload ID, then partial filename match
        target_doc = None
        for doc in documents:
            if doc.filename == filename_or_id or doc.upload_id == filename_or_id:
                target_doc = doc
                break
        
        if not target_doc:
            # Try partial filename match
            for doc in documents:
                if filename_or_id.lower() in doc.filename.lower():
                    target_doc = doc
                    break
        
        if not target_doc:
            available_docs = [doc.filename for doc in documents]
            return f"Document not found. Available documents: {', '.join(available_docs)}"
        
        uploaded_by = target_doc.uploaded_by or "Anonymous"
        size_kb = round(target_doc.file_size / 1024, 1)
        header = f"=== {target_doc.filename} ({size_kb}KB, uploaded by {uploaded_by}) ===\n\n"
        
        return header + target_doc.content
    except Exception as e:
        logging.error(f"Error reading uploaded document: {e}")
        return f"Error reading document: {str(e)}"

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