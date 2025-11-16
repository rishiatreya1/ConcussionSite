"""
Gmail OAuth email service for sending referral emails.
Handles OAuth authentication and email sending via Gmail API.
"""

import os
import base64
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Gmail API scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.send']

# Token and credentials file paths
TOKEN_FILE = 'email_service/token.json'
CREDENTIALS_FILE = 'email_service/credentials.json'


def get_gmail_service() -> Optional[object]:
    """
    Authenticate and return Gmail API service object.
    
    Returns:
        Gmail API service object or None if authentication fails
    """
    logger.debug("Getting Gmail service...")
    
    creds = None
    
    # Load existing token
    if os.path.exists(TOKEN_FILE):
        logger.debug(f"Loading token from {TOKEN_FILE}")
        try:
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        except Exception as e:
            logger.error(f"Error loading token: {e}")
            creds = None
    
    # If no valid credentials, request authorization
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            logger.debug("Refreshing expired token...")
            try:
                creds.refresh(Request())
            except Exception as e:
                logger.error(f"Error refreshing token: {e}")
                creds = None
        
        if not creds:
            if not os.path.exists(CREDENTIALS_FILE):
                logger.error(f"Credentials file not found: {CREDENTIALS_FILE}")
                logger.error("Please download OAuth credentials from Google Cloud Console")
                return None
            
            logger.debug("Starting OAuth flow...")
            try:
                flow = InstalledAppFlow.from_client_secrets_file(
                    CREDENTIALS_FILE, SCOPES)
                creds = flow.run_local_server(port=0)
            except Exception as e:
                logger.error(f"Error during OAuth flow: {e}")
                return None
        
        # Save credentials for next run
        try:
            os.makedirs(os.path.dirname(TOKEN_FILE), exist_ok=True)
            with open(TOKEN_FILE, 'w') as token:
                token.write(creds.to_json())
            logger.info("Token saved successfully")
        except Exception as e:
            logger.error(f"Error saving token: {e}")
    
    try:
        service = build('gmail', 'v1', credentials=creds)
        logger.info("Gmail service created successfully")
        return service
    except Exception as e:
        logger.error(f"Error building Gmail service: {e}")
        return None


def create_message(to: str, subject: str, body: str) -> dict:
    """
    Create a message for an email.
    
    Args:
        to: Email address of the recipient
        subject: Subject of the email
        body: Body text of the email
    
    Returns:
        Message dict with base64-encoded email
    """
    logger.debug(f"Creating message to {to}")
    
    message = MIMEMultipart()
    message['to'] = to
    message['subject'] = subject
    
    # Add body
    message.attach(MIMEText(body, 'plain'))
    
    # Encode message
    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
    
    return {'raw': raw_message}


def send_email_oauth(recipient: str, subject: str, body: str) -> tuple[bool, str]:
    """
    Send an email using Gmail OAuth API.
    
    Args:
        recipient: Email address of the recipient
        subject: Subject of the email
        body: Body text of the email
    
    Returns:
        Tuple of (success: bool, message: str)
    """
    logger.info(f"Attempting to send email to {recipient}")
    logger.debug(f"Subject: {subject}")
    logger.debug(f"Body length: {len(body)} characters")
    
    try:
        service = get_gmail_service()
        if not service:
            return False, "Failed to authenticate with Gmail. Please check your OAuth credentials."
        
        message = create_message(recipient, subject, body)
        
        # Send message
        sent_message = service.users().messages().send(
            userId='me', body=message).execute()
        
        logger.info(f"Email sent successfully! Message ID: {sent_message['id']}")
        return True, f"Email sent successfully! Message ID: {sent_message['id']}"
    
    except HttpError as error:
        error_msg = f"Gmail API error: {error}"
        logger.error(error_msg)
        return False, error_msg
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        logger.error(error_msg)
        return False, error_msg


def check_oauth_setup() -> tuple[bool, str]:
    """
    Check if OAuth is properly set up.
    
    Returns:
        Tuple of (is_setup: bool, message: str)
    """
    if not os.path.exists(CREDENTIALS_FILE):
        return False, f"OAuth credentials file not found at {CREDENTIALS_FILE}. Please download from Google Cloud Console."
    
    if not os.path.exists(TOKEN_FILE):
        return False, "OAuth token not found. First email send will trigger authentication flow."
    
    return True, "OAuth appears to be set up correctly."

def send_test_email():
    """
    Sends a simple test email to trigger Gmail OAuth authentication.
    Use this ONCE to generate token.json.

    After the first successful send, OAuth will no longer require login.
    """
    logger.info("Running send_test_email() - starting OAuth test...")

    try:
        service = get_gmail_service()
        if not service:
            return False, "Failed to create Gmail service. OAuth setup incomplete."

        subject = "ConcussionSite OAuth Test Email"
        body = (
            "Hello!\n\n"
            "This is a test email confirming that Gmail OAuth for ConcussionSite "
            "is configured correctly.\n\n"
            "If you received this email, OAuth is working.\n\n"
            "- ConcussionSite System"
        )

        message = create_message(
            to="me",  # Gmail API interprets "me" as the authenticated user
            subject=subject,
            body=body
        )

        result = service.users().messages().send(
            userId="me",
            body=message
        ).execute()

        logger.info(f"Test email sent successfully! Message ID: {result.get('id')}")
        return True, f"Sent test email! Message ID: {result.get('id')}"

    except Exception as e:
        logger.error(f"Error during send_test_email: {e}")
        return False, f"Error: {e}"
