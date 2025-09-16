import logging
import os
from typing import Optional
from enum import Enum
from dotenv import load_dotenv

from .email_interface import EmailSender, EmailMessage
from .smtp_handler import SMTPEmailHandler, OutlookSMTPHandler, GmailSMTPHandler
from .microsoft_handler import MicrosoftGraphAPIEmailHandler

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class EmailProvider(Enum):
    SMTP = "smtp"
    OUTLOOK_SMTP = "outlook_smtp"
    GMAIL_SMTP = "gmail_smtp"
    MICROSOFT_GRAPH = "microsoft_graph"
    AUTO = "auto"


class EmailService:
    
    def __init__(self, provider: EmailProvider = EmailProvider.AUTO, **kwargs):
        
        self.provider = provider
        self._handler: Optional[EmailSender] = None
        self._kwargs = kwargs
        
    def _get_handler(self) -> EmailSender:
        if self._handler is None:
            self._handler = self._create_handler()
        return self._handler
    
    def _create_handler(self) -> EmailSender:
        """Create appropriate email handler based on provider."""
        if self.provider == EmailProvider.AUTO:
            return self._auto_detect_handler()
        elif self.provider == EmailProvider.SMTP:
            return SMTPEmailHandler(**self._kwargs)
        elif self.provider == EmailProvider.OUTLOOK_SMTP:
            return OutlookSMTPHandler(**self._kwargs)
        elif self.provider == EmailProvider.GMAIL_SMTP:
            return GmailSMTPHandler(**self._kwargs)
        elif self.provider == EmailProvider.MICROSOFT_GRAPH:
            return MicrosoftGraphAPIEmailHandler.from_env()
        else:
            raise ValueError(f"Unsupported email provider: {self.provider}")
    
    def _auto_detect_handler(self) -> EmailSender:
        """Auto-detect the best email handler based on environment variables."""
        # Check for Microsoft Graph API credentials
        if all(os.getenv(var) for var in ["TENANT_ID", "CLIENT_ID", "CLIENT_SECRET", "USER_EMAIL"]):
            logger.info("Detected Microsoft Graph API credentials, using Graph API handler")
            try:
                return MicrosoftGraphAPIEmailHandler.from_env()
            except Exception as e:
                logger.warning(f"Failed to initialize Graph API handler: {e}")
        
        # Check for SMTP credentials
        if os.getenv("SENDER_EMAIL") and os.getenv("SENDER_PASSWORD"):
            smtp_server = os.getenv("SMTP_SERVER", "").lower()
            
            # Auto-detect provider based on SMTP server
            if "outlook" in smtp_server:
                logger.info("Detected Outlook SMTP configuration")
                return OutlookSMTPHandler(**self._kwargs)
            elif "gmail" in smtp_server:
                logger.info("Detected Gmail SMTP configuration")
                return GmailSMTPHandler(**self._kwargs)
            else:
                logger.info("Using generic SMTP handler")
                return SMTPEmailHandler(**self._kwargs)
        
        # Fallback to SMTP with default settings
        logger.warning("No email configuration detected, using default SMTP handler")
        return SMTPEmailHandler(**self._kwargs)
    
    def send_email(self, email: EmailMessage) -> bool:
        """Send an email message.
        
        Args:
            email: EmailMessage to send
            
        Returns:
            True if email was sent successfully, False otherwise
        """
        try:
            handler = self._get_handler()
            logger.info(f"Using {type(handler).__name__} to send email to {email.to_email}")
            result = handler.send_email(email)
            
            if result:
                logger.info(f"Email handler successfully sent email to {email.to_email}")
            else:
                logger.warning(f"Email handler failed to send email to {email.to_email}")
                
            return result
        except Exception as e:
            logger.error(f"Error in email service send_email: {type(e).__name__}: {e}", exc_info=True)
            return False
    
    def send_invitation_email(
        self,
        email: str,
        project_id: str,
        invitation_token: str,
        inviter_name: Optional[str] = None,
        base_url: Optional[str] = None
    ) -> bool:
        """Send a project invitation email.
        
        Args:
            email: Recipient email address
            project_id: Project ID
            invitation_token: Invitation token
            inviter_name: Name of the person sending the invitation
            base_url: Base URL for the invitation link
            
        Returns:
            True if email was sent successfully, False otherwise
        """
        base_url = base_url or os.getenv("BASE_URL", "https://naii-project-planner.naii.com")
        invitation_url = f"{base_url}/"
        
        # Create email content
        inviter_text = f" by {inviter_name}" if inviter_name else ""
        
        html_content = f"""
        <html>
          <head></head>
          <body>
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
              <h2 style="color: #6366f1;">Project Collaboration Invitation</h2>
              <p>Hi there!</p>
              <p>You've been invited{inviter_text} to collaborate on the project "<strong>{project_id}</strong>".</p>
              <p>Click the button below to get started:</p>
              <div style="text-align: center; margin: 30px 0;">
                <a href="{invitation_url}"
                   style="background: linear-gradient(135deg, #007aff 0%, #0056b3 100%);
                          color: white;
                          padding: 12px 24px;
                          text-decoration: none;
                          border-radius: 8px;
                          display: inline-block;
                          font-weight: bold;">
                  Get Started
                </a>
              </div>
              <hr style="margin: 30px 0; border: none; border-top: 1px solid #e5e7eb;">
              <p style="color: #6b7280; font-size: 14px;">
                You can join the project "{project_id}" and start collaborating with the team.
                If you didn't expect this invitation, you can safely ignore this email.
              </p>
            </div>
          </body>
        </html>
        """
        
        text_content = f"""
        Project Collaboration Invitation
        
        Hi there!
        
        You've been invited{inviter_text} to collaborate on the project "{project_id}".
        
        To get started, visit: {invitation_url}
        
        If you didn't expect this invitation, you can safely ignore this email.
        """
        
        email_message = EmailMessage(
            to_email=email,
            subject=f"You're invited to collaborate on project: {project_id}",
            text_content=text_content,
            html_content=html_content
        )
        
        return self.send_email(email_message)


_email_service: Optional[EmailService] = None


def get_email_service() -> EmailService:
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service


def configure_email_service(provider: EmailProvider = EmailProvider.AUTO, **kwargs) -> EmailService:
    """Configure the global email service.
    
    Args:
        provider: Email provider to use
        **kwargs: Additional arguments passed to the email handler
        
    Returns:
        Configured EmailService instance
    """
    global _email_service
    _email_service = EmailService(provider=provider, **kwargs)
    return _email_service
