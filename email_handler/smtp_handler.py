"""SMTP email handler for Outlook, Gmail, and other SMTP providers."""
import smtplib
import logging
import os
from typing import Optional
from email.mime.text import MIMEText as MimeText
from email.mime.multipart import MIMEMultipart as MimeMultipart
from email.mime.base import MIMEBase
from email import encoders

from .email_interface import EmailSender, EmailMessage

logger = logging.getLogger(__name__)


class SMTPEmailHandler(EmailSender):
    """SMTP-based email handler supporting various providers."""
    
    def __init__(
        self,
        smtp_server: Optional[str] = None,
        smtp_port: Optional[int] = None,
        sender_email: Optional[str] = None,
        sender_password: Optional[str] = None,
        sender_name: Optional[str] = None,
        use_tls: bool = True
    ):
        """Initialize SMTP email handler.
        
        Args:
            smtp_server: SMTP server address (defaults to env SMTP_SERVER or Gmail)
            smtp_port: SMTP port (defaults to env SMTP_PORT or 587)
            sender_email: Sender email address (defaults to env SENDER_EMAIL)
            sender_password: Sender password (defaults to env SENDER_PASSWORD)
            sender_name: Sender display name (defaults to env SENDER_NAME)
            use_tls: Whether to use TLS encryption
        """
        self.smtp_server = smtp_server or os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = smtp_port or int(os.getenv("SMTP_PORT", "587"))
        self.sender_email = sender_email or os.getenv("SENDER_EMAIL")
        self.sender_password = sender_password or os.getenv("SENDER_PASSWORD")
        self.sender_name = sender_name or os.getenv("SENDER_NAME", "Project Planner")
        self.use_tls = use_tls
        
        if not self.sender_email or not self.sender_password:
            logger.warning("SMTP credentials not configured - email sending will fail")
    
    def send_email(self, email: EmailMessage) -> bool:
        """Send email via SMTP.
        
        Args:
            email: EmailMessage to send
            
        Returns:
            True if email was sent successfully, False otherwise
        """
        if not self.sender_email or not self.sender_password:
            logger.error("SMTP credentials not configured")
            return False
        
        try:
            # Create message
            message = MimeMultipart("alternative")
            message["Subject"] = email.subject
            message["From"] = f"{self.sender_name} <{self.sender_email}>" if self.sender_name else self.sender_email
            message["To"] = email.to_email
            
            # Add text content
            if email.text_content:
                text_part = MimeText(email.text_content, "plain")
                message.attach(text_part)
            
            # Add HTML content
            if email.html_content:
                html_part = MimeText(email.html_content, "html")
                message.attach(html_part)
            
            # Add attachments
            if email.attachments:
                for attachment in email.attachments:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment.content)
                    encoders.encode_base64(part)
                    part.add_header(
                        'Content-Disposition',
                        f'attachment; filename= {attachment.filename}'
                    )
                    message.attach(part)
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.sendmail(self.sender_email, email.to_email, message.as_string())
            
            logger.info(f"Email sent successfully to {email.to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {email.to_email}: {e}")
            return False


class OutlookSMTPHandler(SMTPEmailHandler):
    """Outlook-specific SMTP handler with predefined settings."""
    
    def __init__(
        self,
        sender_email: Optional[str] = None,
        sender_password: Optional[str] = None,
        sender_name: Optional[str] = None
    ):
        super().__init__(
            smtp_server="smtp-mail.outlook.com",
            smtp_port=587,
            sender_email=sender_email,
            sender_password=sender_password,
            sender_name=sender_name,
            use_tls=True
        )


class GmailSMTPHandler(SMTPEmailHandler):
    """Gmail-specific SMTP handler with predefined settings."""
    
    def __init__(
        self,
        sender_email: Optional[str] = None,
        sender_password: Optional[str] = None,
        sender_name: Optional[str] = None
    ):
        super().__init__(
            smtp_server="smtp.gmail.com",
            smtp_port=587,
            sender_email=sender_email,
            sender_password=sender_password,
            sender_name=sender_name,
            use_tls=True
        )
