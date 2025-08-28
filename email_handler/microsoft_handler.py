import logging
import os
import requests
from dataclasses import dataclass

from .email_interface import EmailSender, EmailFetcher, EmailMessage, EmailAttachment

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class MicrosoftGraphAPIEmailHandler(EmailSender, EmailFetcher):
    """Microsoft Graph API email handler for Office 365/Outlook.com accounts."""
    
    tenant_id: str
    client_id: str
    client_secret: str
    user_email: str
    timeout_seconds: int = 30
    
    @classmethod
    def from_env(cls) -> 'MicrosoftGraphAPIEmailHandler':
        """Create handler from environment variables."""
        tenant_id = os.getenv("TENANT_ID")
        client_id = os.getenv("CLIENT_ID") 
        client_secret = os.getenv("CLIENT_SECRET")
        user_email = os.getenv("USER_EMAIL")
        
        if not all([tenant_id, client_id, client_secret, user_email]):
            missing = [name for name, value in [
                ("TENANT_ID", tenant_id),
                ("CLIENT_ID", client_id), 
                ("CLIENT_SECRET", client_secret),
                ("USER_EMAIL", user_email)
            ] if not value]
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
        
        return cls(
            tenant_id=tenant_id,
            client_id=client_id,
            client_secret=client_secret,
            user_email=user_email
        )
    
    def _get_access_token(self) -> str:
        """Get OAuth2 access token from Microsoft."""
        token_url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token"
        token_data = {
            'grant_type': 'client_credentials',
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'scope': 'https://graph.microsoft.com/.default'
        }
        
        try:
            logger.info(f"Requesting access token from {token_url}")
            response = requests.post(token_url, data=token_data, timeout=self.timeout_seconds)
            
            if response.status_code != 200:
                logger.error(f"Token request failed with status {response.status_code}: {response.text}")
                
            response.raise_for_status()
            token_info = response.json()
            
            access_token = token_info.get('access_token')
            if not access_token:
                logger.error(f"Access token not found in response: {token_info}")
                raise ValueError("Access token not found in response")
            
            logger.info("Successfully obtained access token")
            return access_token
            
        except requests.RequestException as e:
            logger.error(f"Failed to get access token: {e}")
            raise
    
    def send_email(self, email: EmailMessage) -> bool:
        """Send email via Microsoft Graph API.
        
        Args:
            email: EmailMessage to send
            
        Returns:
            True if email was sent successfully, False otherwise
        """
        try:
            logger.info(f"Getting access token for sending email to {email.to_email}")
            access_token = self._get_access_token()
            send_mail_url = f"https://graph.microsoft.com/v1.0/users/{self.user_email}/sendMail"
            
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            
            logger.info(f"Sending email to {email.to_email} from {self.user_email} via Graph API")
            email_payload = email.to_graph_api()
            logger.debug(f"Email payload: {email_payload}")
            
            response = requests.post(
                send_mail_url,
                headers=headers,
                json=email_payload,
                timeout=self.timeout_seconds
            )
            
            if response.status_code not in [200, 202]:
                logger.error(f"Send email failed with status {response.status_code}: {response.text}")
            
            response.raise_for_status()
            
            logger.info(f"Email sent successfully to {email.to_email}")
            return True
            
        except requests.RequestException as e:
            logger.error(f"HTTP request failed when sending email to {email.to_email}: {type(e).__name__}: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response status: {e.response.status_code}, Response body: {e.response.text}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending email to {email.to_email}: {type(e).__name__}: {e}", exc_info=True)
            return False
    
    def fetch_email(self, email_id: str) -> EmailMessage:
        """Fetch email from Microsoft Graph API.
        
        Args:
            email_id: ID of the email to fetch
            
        Returns:
            EmailMessage object
        """
        try:
            access_token = self._get_access_token()
            email_url = f"https://graph.microsoft.com/v1.0/users/{self.user_email}/messages/{email_id}?$expand=attachments"
            
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            
            response = requests.get(email_url, headers=headers, timeout=self.timeout_seconds)
            response.raise_for_status()
            
            email_data = response.json()
            return self._parse_graph_api_email(email_data)
            
        except Exception as e:
            logger.error(f"Failed to fetch email {email_id}: {e}")
            raise
    
    def _parse_graph_api_email(self, email_data: dict) -> EmailMessage:
        """Parse Microsoft Graph API email response into EmailMessage."""
        # Extract basic email info
        subject = email_data.get('subject', '')
        body = email_data.get('body', {})
        content = body.get('content', '')
        content_type = body.get('contentType', 'Text')
        
        # Extract sender info
        from_field = email_data.get('from', {}).get('emailAddress', {})
        from_email = from_field.get('address', '')
        from_name = from_field.get('name', '')
        
        # Extract recipient (assuming first recipient for simplicity)
        to_recipients = email_data.get('toRecipients', [])
        to_email = to_recipients[0]['emailAddress']['address'] if to_recipients else ''
        
        # Extract attachments
        attachments = []
        for att_data in email_data.get('attachments', []):
            if att_data.get('@odata.type') == '#microsoft.graph.fileAttachment':
                attachment = EmailAttachment(
                    filename=att_data.get('name', 'attachment'),
                    content=att_data.get('contentBytes', '').encode('utf-8'),
                    content_type=att_data.get('contentType', 'application/octet-stream')
                )
                attachments.append(attachment)
        
        return EmailMessage(
            to_email=to_email,
            subject=subject,
            text_content=content if content_type == 'Text' else '',
            html_content=content if content_type == 'HTML' else None,
            from_email=from_email,
            from_name=from_name,
            attachments=attachments if attachments else None
        )
