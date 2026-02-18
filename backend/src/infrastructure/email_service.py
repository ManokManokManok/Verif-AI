"""
Email Service Implementation

Supports multiple email backends:
- SendGrid (recommended for production)
- SMTP (for development/testing with Gmail, Outlook, etc.)
- Mock (for unit tests and local development)

Configuration (via .env):
    EMAIL_BACKEND=sendgrid|smtp|mock   (default: mock)
    SENDGRID_API_KEY=...               (required for SendGrid)
    EMAIL_FROM_ADDRESS=noreply@verfai.com
    EMAIL_FROM_NAME=Verif-AI
    FRONTEND_URL=http://localhost:5173

Usage:
    from src.infrastructure.email_service import get_email_service

    email_svc = get_email_service()
    email_svc.send_mfa_code_email("user@example.com", "123456")
"""

import os
import logging
from typing import Protocol, Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Protocol (interface)
# ---------------------------------------------------------------------------

class EmailServiceProtocol(Protocol):
    """Email service interface that all backends must satisfy."""

    def send_verification_email(self, email: str, token: str) -> bool: ...

    def send_password_reset_email(self, email: str, token: str) -> bool: ...

    def send_mfa_code_email(self, email: str, code: str) -> bool: ...


# ---------------------------------------------------------------------------
# HTML template helpers
# ---------------------------------------------------------------------------

def _base_html(body_html: str) -> str:
    """Wrap body content in a consistent HTML email template."""
    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
    .button {{
        display: inline-block;
        padding: 12px 24px;
        color: #ffffff;
        text-decoration: none;
        border-radius: 4px;
        margin: 20px 0;
    }}
    .btn-green {{ background-color: #4CAF50; }}
    .btn-red   {{ background-color: #f44336; }}
    .code {{
        font-size: 32px;
        font-weight: bold;
        color: #4CAF50;
        letter-spacing: 5px;
        padding: 20px;
        background-color: #f5f5f5;
        border-radius: 4px;
        text-align: center;
        margin: 20px 0;
    }}
    .footer {{ color: #666; font-size: 12px; margin-top: 30px; }}
</style>
</head>
<body>
<div class="container">
{body_html}
<div class="footer">
    <p>&copy; 2026 Verif-AI. All rights reserved.</p>
</div>
</div>
</body>
</html>"""


def _verification_html(verification_link: str) -> str:
    return _base_html(f"""
<h2>Welcome to Verif-AI!</h2>
<p>Thank you for registering. Please verify your email address to activate your account.</p>
<p><a href="{verification_link}" class="button btn-green">Verify Email Address</a></p>
<p>Or copy and paste this link into your browser:</p>
<p>{verification_link}</p>
<p>This link will expire in 24 hours.</p>
<p class="footer">If you didn't create an account, please ignore this email.</p>
""")


def _password_reset_html(reset_link: str) -> str:
    return _base_html(f"""
<h2>Password Reset Request</h2>
<p>We received a request to reset your password. Click the button below to create a new password:</p>
<p><a href="{reset_link}" class="button btn-red">Reset Password</a></p>
<p>Or copy and paste this link into your browser:</p>
<p>{reset_link}</p>
<p>This link will expire in 1 hour.</p>
<p class="footer">If you didn't request a password reset, please ignore this email or contact support.</p>
""")


def _mfa_code_html(code: str) -> str:
    return _base_html(f"""
<h2>Your Verification Code</h2>
<p>Enter this code to complete your login:</p>
<div class="code">{code}</div>
<p><strong>This code will expire in 5 minutes.</strong></p>
<p class="footer">If you didn't request this code, please secure your account immediately.</p>
""")


# ---------------------------------------------------------------------------
# SendGrid backend
# ---------------------------------------------------------------------------

class SendGridEmailService:
    """
    Production email service powered by SendGrid.

    Requires:
        pip install sendgrid
        SENDGRID_API_KEY env var
    """

    def __init__(self):
        self.api_key = os.getenv('SENDGRID_API_KEY')
        self.from_address = os.getenv('EMAIL_FROM_ADDRESS', 'noreply@verfai.com')
        self.from_name = os.getenv('EMAIL_FROM_NAME', 'Verif-AI')
        self.frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:5173')

        if not self.api_key:
            raise ValueError("SENDGRID_API_KEY environment variable not set")

        try:
            from sendgrid import SendGridAPIClient
            from sendgrid.helpers.mail import Mail
            self._client = SendGridAPIClient(self.api_key)
            self._Mail = Mail
        except ImportError:
            raise ImportError(
                "sendgrid package not installed. Run: pip install sendgrid"
            )

    # -- internal -----------------------------------------------------------

    def _send(self, to_email: str, subject: str, html: str) -> bool:
        try:
            message = self._Mail(
                from_email=(self.from_address, self.from_name),
                to_emails=to_email,
                subject=subject,
                html_content=html,
            )
            response = self._client.send(message)
            if response.status_code in (200, 201, 202):
                logger.info(f"Email sent to {to_email} via SendGrid")
                return True
            logger.error(f"SendGrid status {response.status_code} for {to_email}")
            return False
        except Exception as exc:
            logger.error(f"SendGrid error sending to {to_email}: {exc}")
            return False

    # -- public API ---------------------------------------------------------

    def send_verification_email(self, email: str, token: str) -> bool:
        link = f"{self.frontend_url}/verify-email?token={token}"
        return self._send(email, "Verify Your Email - Verif-AI", _verification_html(link))

    def send_password_reset_email(self, email: str, token: str) -> bool:
        link = f"{self.frontend_url}/reset-password?token={token}"
        return self._send(email, "Reset Your Password - Verif-AI", _password_reset_html(link))

    def send_mfa_code_email(self, email: str, code: str) -> bool:
        return self._send(email, "Your Verification Code - Verif-AI", _mfa_code_html(code))


# ---------------------------------------------------------------------------
# SMTP backend (Gmail, Outlook, etc.)
# ---------------------------------------------------------------------------

class SMTPEmailService:
    """
    SMTP email service for development / smaller deployments.

    Reads config from env vars:
        EMAIL_HOST, EMAIL_PORT, EMAIL_USE_TLS,
        EMAIL_HOST_USER, EMAIL_HOST_PASSWORD
    """

    def __init__(self):
        self.host = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
        self.port = int(os.getenv('EMAIL_PORT', '587'))
        self.use_tls = os.getenv('EMAIL_USE_TLS', 'True').lower() == 'true'
        self.username = os.getenv('EMAIL_HOST_USER')
        self.password = os.getenv('EMAIL_HOST_PASSWORD')
        self.from_address = os.getenv('EMAIL_FROM_ADDRESS', self.username or 'noreply@verfai.com')
        self.from_name = os.getenv('EMAIL_FROM_NAME', 'Verif-AI')
        self.frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:5173')

        if not self.username or not self.password:
            raise ValueError(
                "EMAIL_HOST_USER and EMAIL_HOST_PASSWORD are required for SMTP backend"
            )

    def _send(self, to_email: str, subject: str, html: str) -> bool:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart

        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.from_name} <{self.from_address}>"
            msg['To'] = to_email
            msg.attach(MIMEText(html, 'html'))

            with smtplib.SMTP(self.host, self.port) as server:
                if self.use_tls:
                    server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)

            logger.info(f"Email sent to {to_email} via SMTP")
            return True
        except Exception as exc:
            logger.error(f"SMTP error sending to {to_email}: {exc}")
            return False

    def send_verification_email(self, email: str, token: str) -> bool:
        link = f"{self.frontend_url}/verify-email?token={token}"
        return self._send(email, "Verify Your Email - Verif-AI", _verification_html(link))

    def send_password_reset_email(self, email: str, token: str) -> bool:
        link = f"{self.frontend_url}/reset-password?token={token}"
        return self._send(email, "Reset Your Password - Verif-AI", _password_reset_html(link))

    def send_mfa_code_email(self, email: str, code: str) -> bool:
        return self._send(email, "Your Verification Code - Verif-AI", _mfa_code_html(code))


# ---------------------------------------------------------------------------
# Mock backend (development / testing)
# ---------------------------------------------------------------------------

class MockEmailService:
    """
    Mock email service — logs to stdout instead of sending.
    Used when EMAIL_BACKEND=mock or is unset.
    """

    def __init__(self):
        self.frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:5173')

    def send_verification_email(self, email: str, token: str) -> bool:
        link = f"{self.frontend_url}/verify-email?token={token}"
        logger.info(f"[MockEmail] Verification email to {email}")
        logger.info(f"[MockEmail] Link: {link}")
        print(f"MOCK: Verification email to {email} | Link: {link}")
        return True

    def send_password_reset_email(self, email: str, token: str) -> bool:
        link = f"{self.frontend_url}/reset-password?token={token}"
        logger.info(f"[MockEmail] Password reset email to {email}")
        logger.info(f"[MockEmail] Link: {link}")
        print(f"MOCK: Password reset email to {email} | Link: {link}")
        return True

    def send_mfa_code_email(self, email: str, code: str) -> bool:
        logger.info(f"[MockEmail] MFA code email to {email}")
        logger.info(f"[MockEmail] Code: {code}")
        print(f"MOCK: MFA code to {email} | Code: {code}")
        return True


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

_email_service_instance = None


def get_email_service() -> EmailServiceProtocol:
    """
    Get configured email service singleton.

    Reads EMAIL_BACKEND env var:
        'sendgrid' → SendGridEmailService
        'smtp'     → SMTPEmailService
        'mock'     → MockEmailService (default)
    """
    global _email_service_instance

    if _email_service_instance is not None:
        return _email_service_instance

    backend = os.getenv('EMAIL_BACKEND', 'mock').lower().strip()

    if backend == 'sendgrid':
        _email_service_instance = SendGridEmailService()
    elif backend == 'smtp':
        _email_service_instance = SMTPEmailService()
    else:
        if backend != 'mock':
            logger.warning(f"Unknown EMAIL_BACKEND '{backend}', falling back to mock")
        logger.info("Using MockEmailService — emails will NOT be sent")
        _email_service_instance = MockEmailService()

    return _email_service_instance


def reset_email_service():
    """Reset the singleton (useful for testing)."""
    global _email_service_instance
    _email_service_instance = None
