"""
Orizon Email Service

Handles sending authentication emails:
- Magic link for signup/login
- Password reset (future)
- Email verification (future)
"""

import logging
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

logger = logging.getLogger(__name__)

# SMTP Configuration
SMTP_HOST = os.getenv("SMTP_HOST", "localhost")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL", "noreply@orizon.local")
SMTP_FROM_NAME = os.getenv("SMTP_FROM_NAME", "Orizon")
SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "true").lower() == "true"

# App URL for magic links
APP_URL = os.getenv("APP_URL", "http://localhost:4010")


class EmailService:
    """Service for sending emails via SMTP."""

    def __init__(
        self,
        host: str = SMTP_HOST,
        port: int = SMTP_PORT,
        user: str = SMTP_USER,
        password: str = SMTP_PASSWORD,
        from_email: str = SMTP_FROM_EMAIL,
        from_name: str = SMTP_FROM_NAME,
        use_tls: bool = SMTP_USE_TLS,
    ):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.from_email = from_email
        self.from_name = from_name
        self.use_tls = use_tls

    def _create_message(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: Optional[str] = None,
    ) -> MIMEMultipart:
        """Create a MIME message."""
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = f"{self.from_name} <{self.from_email}>"
        message["To"] = to_email

        # Plain text version (fallback)
        if text_body:
            text_part = MIMEText(text_body, "plain")
            message.attach(text_part)

        # HTML version
        html_part = MIMEText(html_body, "html")
        message.attach(html_part)

        return message

    def send_email(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: Optional[str] = None,
    ) -> bool:
        """Send an email via SMTP.

        Args:
            to_email: Recipient email address
            subject: Email subject
            html_body: HTML email body
            text_body: Plain text body (optional fallback)

        Returns:
            True if sent successfully, False otherwise
        """
        try:
            message = self._create_message(to_email, subject, html_body, text_body)

            # Connect to SMTP server
            if self.use_tls:
                server = smtplib.SMTP(self.host, self.port)
                server.starttls()
            else:
                server = smtplib.SMTP(self.host, self.port)

            # Authenticate if credentials provided
            if self.user and self.password:
                server.login(self.user, self.password)

            # Send email
            server.sendmail(self.from_email, to_email, message.as_string())
            server.quit()

            logger.info(f"Email sent to {to_email}: {subject}")
            return True

        except smtplib.SMTPException as e:
            logger.error(f"SMTP error sending to {to_email}: {e}")
            return False
        except Exception as e:
            logger.error(f"Error sending email to {to_email}: {e}")
            return False


# Default email service instance
_email_service: Optional[EmailService] = None


def get_email_service() -> EmailService:
    """Get or create the default email service."""
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service


async def send_magic_link_email(
    to_email: str,
    token: str,
    name: Optional[str] = None,
    is_signup: bool = False,
) -> bool:
    """Send magic link email for authentication.

    Args:
        to_email: Recipient email
        token: Magic link token
        name: User name (for personalization)
        is_signup: Whether this is signup or login

    Returns:
        True if sent successfully
    """
    magic_link = f"{APP_URL}/api/auth/verify?token={token}"

    if is_signup:
        subject = "Complete your Orizon signup"
        action_text = "complete your signup"
        greeting = f"Hi{' ' + name if name else ''},"
    else:
        subject = "Log in to Orizon"
        action_text = "log in"
        greeting = "Hi,"

    html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #1f2937; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="background: #f9fafb; border-radius: 12px; padding: 40px; text-align: center;">
        <h1 style="color: #4f46e5; margin-bottom: 24px;">Orizon</h1>

        <p style="font-size: 16px; margin-bottom: 24px;">
            {greeting}<br>
            Click the button below to {action_text}.
        </p>

        <a href="{magic_link}"
           style="display: inline-block; background-color: #4f46e5; color: white; padding: 14px 28px; border-radius: 8px; text-decoration: none; font-weight: 500; font-size: 16px;">
            {subject.split()[0]} {'to Orizon' if not is_signup else 'Signup'}
        </a>

        <p style="font-size: 14px; color: #6b7280; margin-top: 24px;">
            This link expires in 15 minutes.<br>
            If you didn't request this, you can safely ignore this email.
        </p>

        <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 24px 0;">

        <p style="font-size: 12px; color: #9ca3af;">
            If the button doesn't work, copy and paste this link:<br>
            <a href="{magic_link}" style="color: #4f46e5; word-break: break-all;">{magic_link}</a>
        </p>
    </div>
</body>
</html>
"""

    text_body = f"""
{greeting}

Click the link below to {action_text}:

{magic_link}

This link expires in 15 minutes.
If you didn't request this, you can safely ignore this email.

- Orizon
"""

    service = get_email_service()
    return service.send_email(to_email, subject, html_body, text_body)
