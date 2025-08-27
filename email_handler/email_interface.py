from typing import Protocol, Optional, List
from dataclasses import dataclass


@dataclass
class EmailAttachment:
    """Email attachment data."""
    filename: str
    content: bytes
    content_type: str


@dataclass
class EmailMessage:
    """Email message data structure."""
    to_email: str
    subject: str
    text_content: str
    html_content: Optional[str] = None
    from_email: Optional[str] = None
    from_name: Optional[str] = None
    attachments: Optional[List[EmailAttachment]] = None
    
    def to_graph_api(self) -> dict:
        """Convert to Microsoft Graph API format."""
        message_data = {
            "message": {
                "subject": self.subject,
                "body": {
                    "contentType": "HTML" if self.html_content else "Text",
                    "content": self.html_content or self.text_content
                },
                "toRecipients": [
                    {
                        "emailAddress": {
                            "address": self.to_email
                        }
                    }
                ]
            }
        }
        
        if self.attachments:
            message_data["message"]["attachments"] = [
                {
                    "@odata.type": "#microsoft.graph.fileAttachment",
                    "name": att.filename,
                    "contentType": att.content_type,
                    "contentBytes": att.content.decode('utf-8') if isinstance(att.content, bytes) else att.content
                }
                for att in self.attachments
            ]
        
        return message_data


class EmailSender(Protocol):
    """Protocol for email sending implementations."""
    
    def send_email(self, email: EmailMessage) -> bool:
        """Send an email message. Returns True if successful."""
        ...


class EmailFetcher(Protocol):
    """Protocol for email fetching implementations."""
    
    def fetch_email(self, email_id: str) -> EmailMessage:
        """Fetch an email by ID."""
        ...
