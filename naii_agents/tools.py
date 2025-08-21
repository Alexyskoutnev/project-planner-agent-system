import os
import logging
from agents import function_tool


# --- Configuration & Setup ---
# Set the path for the project document
DOC_DIRECTORY = "./project_docs/"
DOC_FILENAME = "NAI_system_configuration.md"
CURRENT_WORKING_DOC = os.path.join(DOC_DIRECTORY, DOC_FILENAME)

# Ensure the document directory exists
os.makedirs(DOC_DIRECTORY, exist_ok=True)

# TOOLS 
@function_tool
def overwrite_doc(content: str) -> str:
    """
    Overwrites the entire project document with new content.
    This is used to update the plan with a clean, structured format.
    """
    try:
        with open(CURRENT_WORKING_DOC, "w", encoding="utf-8") as f:
            f.write(content)
        logging.info("Document updated successfully")
        return "Document updated successfully."
    except Exception as e:
        logging.error(f"Error updating document: {e}")
        return f"Error updating document: {str(e)}"

@function_tool
def read_current_doc() -> str:
    try:
        if os.path.exists(CURRENT_WORKING_DOC) and os.path.getsize(CURRENT_WORKING_DOC) > 0:
            with open(CURRENT_WORKING_DOC, "r", encoding="utf-8") as f:
                content = f.read()
                logging.info("Successfully read current document")
                return content
    except Exception as e:
        logging.error(f"Error reading document: {e}")
    return "document could not be found"

@function_tool
def get_current_date() -> str:
    "Gets the current time for the document."
    import datetime
    return datetime.now().strftime("%Y-%m-%d")

def read_doc() -> str:
    try:
        if os.path.exists(CURRENT_WORKING_DOC) and os.path.getsize(CURRENT_WORKING_DOC) > 0:
            with open(CURRENT_WORKING_DOC, "r", encoding="utf-8") as f:
                return f.read()
    except Exception as e:
        logging.error(f"Error reading document for display: {e}")
    return "# No document available"