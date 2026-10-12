"""
Email Service Implementation

Supports multiple email backends:
- SendGrid (recommended for production)
- Nodemailer bridge (Node.js-based alternative)
- SMTP (for development/testing with Gmail, Outlook, etc.)
- Mock (for unit tests and local development)

Configuration (via .env):
    EMAIL_BACKEND=sendgrid|nodemailer|smtp|mock   (default: mock)
    SENDGRID_API_KEY=...               (required for SendGrid)
    EMAIL_FROM_ADDRESS=verifaisupportacc@gmail.com
    EMAIL_FROM_NAME=Verif-AI
    FRONTEND_URL=http://localhost:5173

Usage:
    from src.infrastructure.email_service import get_email_service

    email_svc = get_email_service()
    email_svc.send_mfa_code_email("user@example.com", "123456")
"""

import os
import json
import logging
import shutil
import subprocess
from html import escape
from pathlib import Path
from typing import Protocol

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Protocol (interface)
# ---------------------------------------------------------------------------

class EmailServiceProtocol(Protocol):
    """Email service interface that all backends must satisfy."""

    def send_verification_email(self, email: str, token: str) -> bool: ...

    def send_password_reset_email(self, email: str, token: str) -> bool: ...

    def send_password_reset_code_email(self, email: str, code: str) -> bool: ...

    def send_mfa_code_email(self, email: str, code: str) -> bool: ...

    def send_password_change_code_email(self, email: str, code: str) -> bool: ...

    def send_verification_code_email(self, email: str, code: str) -> bool: ...


class _TemplatedEmailServiceBase:
    """Shared email template/link behavior for all providers."""

    def __init__(self):
        self.frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:5173')
        self.support_email = os.getenv('VERIFAI_SUPPORT_EMAIL', 'verifaisupportacc@gmail.com')

    def _send(self, to_email: str, subject: str, html: str) -> bool:
        raise NotImplementedError

    def send_verification_email(self, email: str, token: str) -> bool:
        link = f"{self.frontend_url}/verify-email?token={token}"
        return self._send(email, "Verify Your Email - Verif-AI", _verification_html(link))

    def send_password_reset_email(self, email: str, token: str) -> bool:
        link = f"{self.frontend_url}/reset-password?token={token}"
        return self._send(email, "Reset Your Password - Verif-AI", _password_reset_html(link))

    def send_password_reset_code_email(self, email: str, code: str) -> bool:
        return self._send(
            email,
            "Your Password Reset Code - Verif-AI",
            _password_reset_code_html(code),
        )

    def send_mfa_code_email(self, email: str, code: str) -> bool:
        return self._send(email, "Your Verification Code - Verif-AI", _mfa_code_html(code))

    def send_password_change_code_email(self, email: str, code: str) -> bool:
        return self._send(email, "Password Change Verification Code - Verif-AI", _password_change_code_html(code))

    def send_verification_code_email(self, email: str, code: str) -> bool:
        return self._send(email, "Verify Your Email - Verif-AI", _email_verification_code_html(code))


# ---------------------------------------------------------------------------
# HTML template helpers
# ---------------------------------------------------------------------------

def _base_html(title: str, preheader: str, body_html: str) -> str:
    """Build responsive, table-based HTML that remains readable in email clients."""
    safe_title = escape(title)
    safe_preheader = escape(preheader)
    safe_support_email = escape(
        os.getenv('VERIFAI_SUPPORT_EMAIL', 'verifaisupportacc@gmail.com'),
        quote=True,
    )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="color-scheme" content="light">
<meta name="supported-color-schemes" content="light">
<title>{safe_title}</title>
</head>
<body style="margin:0;padding:0;background-color:#f1f5f9;font-family:Arial,Helvetica,sans-serif;color:#172033;">
<div style="display:none!important;visibility:hidden;opacity:0;color:transparent;height:0;width:0;overflow:hidden;mso-hide:all;">{safe_preheader}</div>
<table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background-color:#f1f5f9;">
  <tr><td align="center" style="padding:32px 14px;">
    <table role="presentation" width="600" cellspacing="0" cellpadding="0" border="0" style="width:100%;max-width:600px;">
      <tr><td style="padding:0 0 16px 4px;">
        <span style="font-size:22px;line-height:28px;font-weight:800;letter-spacing:-.5px;color:#172033;">Verif<span style="color:#2563eb;">-AI</span></span>
      </td></tr>
      <tr><td style="background-color:#ffffff;border:1px solid #e2e8f0;border-radius:16px;padding:36px 34px;">
        {body_html}
      </td></tr>
      <tr><td style="padding:20px 8px 0;color:#64748b;font-size:12px;line-height:19px;">
        <p style="margin:0 0 8px;">This automated message was sent because an action was started in Verif-AI.</p>
        <p style="margin:0 0 8px;">Need help? Contact <a href="mailto:{safe_support_email}" style="color:#1d4ed8;text-decoration:underline;">{safe_support_email}</a>.</p>
        <p style="margin:0;">&copy; 2026 Verif-AI. Please do not reply with passwords or verification codes.</p>
      </td></tr>
    </table>
  </td></tr>
</table>
</body>
</html>"""


def _email_heading(eyebrow: str, heading: str, description: str) -> str:
    return (
        f'<p style="margin:0 0 10px;color:#2563eb;font-size:12px;line-height:18px;'
        f'font-weight:700;letter-spacing:1.4px;text-transform:uppercase;">{escape(eyebrow)}</p>'
        f'<h1 style="margin:0 0 12px;color:#0f172a;font-size:26px;line-height:34px;'
        f'font-weight:750;letter-spacing:-.4px;">{escape(heading)}</h1>'
        f'<p style="margin:0 0 22px;color:#475569;font-size:15px;line-height:24px;">'
        f'{escape(description)}</p>'
    )


def _email_code_steps(action: str, expiry: str) -> str:
    return f"""
<table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="margin:22px 0;">
  <tr><td style="padding:18px 20px;background-color:#eff6ff;border:1px solid #dbeafe;border-radius:12px;">
    <p style="margin:0 0 10px;color:#1e3a8a;font-size:14px;line-height:21px;font-weight:700;">How to use your code</p>
    <ol style="margin:0;padding:0 0 0 20px;color:#334155;font-size:14px;line-height:23px;">
      <li style="padding:0 0 5px;">Return to the Verif-AI page where you requested the code.</li>
      <li style="padding:0 0 5px;">Enter the code exactly as shown and continue with {escape(action)}.</li>
      <li>If it has expired, request a new code on that page and use the newest email.</li>
    </ol>
    <p style="margin:12px 0 0;color:#475569;font-size:13px;line-height:20px;"><strong>Expires in {escape(expiry)}.</strong> Codes may be replaced when you request another one.</p>
  </td></tr>
</table>
"""


def _security_notice(did_not_request: str) -> str:
    safe_support_email = escape(
        os.getenv('VERIFAI_SUPPORT_EMAIL', 'verifaisupportacc@gmail.com'),
        quote=True,
    )
    return f"""
<table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="margin-top:22px;">
  <tr><td style="padding:16px 18px;background-color:#fff7ed;border-left:4px solid #f59e0b;border-radius:6px;">
    <p style="margin:0;color:#7c2d12;font-size:13px;line-height:21px;">
      {escape(did_not_request)} Ignore this email; do not share or forward the code. If you are concerned about your account, contact
      <a href="mailto:{safe_support_email}" style="color:#9a3412;text-decoration:underline;">{safe_support_email}</a>.
    </p>
  </td></tr>
</table>
"""


def _verification_html(verification_link: str) -> str:
    safe_link = escape(verification_link, quote=True)
    body = f"""
{_email_heading('Account security', 'Confirm your email', 'Welcome to Verif-AI. Verify this email address to activate your account.')}
<p style="margin:0 0 20px;">
  <a href="{safe_link}" style="display:inline-block;padding:13px 20px;background-color:#2563eb;border-radius:9px;color:#ffffff;font-size:14px;line-height:20px;font-weight:700;text-decoration:none;">Verify email address</a>
</p>
<p style="margin:0 0 8px;color:#475569;font-size:13px;line-height:20px;">If the button does not work, copy this link into your browser:</p>
<p style="margin:0 0 20px;overflow-wrap:anywhere;font-size:13px;line-height:20px;"><a href="{safe_link}" style="color:#1d4ed8;">{safe_link}</a></p>
<p style="margin:0;padding:12px 14px;background-color:#f8fafc;border-radius:8px;color:#334155;font-size:13px;line-height:20px;">This verification link expires in <strong>24 hours</strong>. Once verified, return to Verif-AI and sign in.</p>
{_security_notice("If you didn't create a Verif-AI account,")}
"""
    return _base_html(
        'Confirm your Verif-AI email',
        'Verify your email address to activate your account.',
        body,
    )


def _password_reset_html(reset_link: str) -> str:
    safe_link = escape(reset_link, quote=True)
    body = f"""
{_email_heading('Account security', 'Reset your password', 'A password reset was requested for your Verif-AI account.')}
<p style="margin:0 0 20px;">
  <a href="{safe_link}" style="display:inline-block;padding:13px 20px;background-color:#2563eb;border-radius:9px;color:#ffffff;font-size:14px;line-height:20px;font-weight:700;text-decoration:none;">Choose a new password</a>
</p>
<p style="margin:0 0 8px;color:#475569;font-size:13px;line-height:20px;">If the button does not work, copy this link into your browser:</p>
<p style="margin:0 0 20px;overflow-wrap:anywhere;font-size:13px;line-height:20px;"><a href="{safe_link}" style="color:#1d4ed8;">{safe_link}</a></p>
<p style="margin:0;padding:12px 14px;background-color:#f8fafc;border-radius:8px;color:#334155;font-size:13px;line-height:20px;">This reset link expires in <strong>1 hour</strong>. Use it only once, then sign in with your new password.</p>
{_security_notice("If you didn't request a password reset,")}
"""
    return _base_html(
        'Reset your Verif-AI password',
        'Use the secure link to choose a new password.',
        body,
    )


def _password_reset_code_html(code: str) -> str:
    body = f"""
{_email_heading('Account security', 'Reset your password', 'Use the code below to continue resetting your Verif-AI password.')}
<div style="margin:0;padding:18px 16px;background-color:#f8fafc;border:1px solid #e2e8f0;border-radius:12px;text-align:center;color:#0f172a;font-size:34px;line-height:42px;font-weight:800;letter-spacing:9px;">{escape(str(code))}</div>
{_email_code_steps('reset your password', '10 minutes')}
{_security_notice("If you didn't request a password reset,")}
"""
    return _base_html(
        'Your Verif-AI password reset code',
        'Enter this code on the password reset page.',
        body,
    )


def _mfa_code_html(code: str) -> str:
    body = f"""
{_email_heading('Sign-in verification', 'Your login code', 'Enter this code in the Verif-AI sign-in screen to complete your login.')}
<div style="margin:0;padding:18px 16px;background-color:#f8fafc;border:1px solid #e2e8f0;border-radius:12px;text-align:center;color:#0f172a;font-size:34px;line-height:42px;font-weight:800;letter-spacing:9px;">{escape(str(code))}</div>
{_email_code_steps('complete your sign-in', '5 minutes')}
{_security_notice("If you didn't try to sign in,")}
"""
    return _base_html(
        'Your Verif-AI sign-in code',
        'Enter this code in Verif-AI to complete sign-in.',
        body,
    )


def _password_change_code_html(code: str) -> str:
    body = f"""
{_email_heading('Account security', 'Confirm password change', 'Use this code in Settings to continue changing your Verif-AI password.')}
<div style="margin:0;padding:18px 16px;background-color:#f8fafc;border:1px solid #e2e8f0;border-radius:12px;text-align:center;color:#0f172a;font-size:34px;line-height:42px;font-weight:800;letter-spacing:9px;">{escape(str(code))}</div>
{_email_code_steps('confirm the password change', '5 minutes')}
<p style="margin:0;color:#475569;font-size:13px;line-height:21px;">The password change also requires your current password in the app.</p>
{_security_notice("If you didn't request a password change,")}
"""
    return _base_html(
        'Your Verif-AI password change code',
        'Enter this code in Settings to confirm a password change.',
        body,
    )


def _email_verification_code_html(code: str) -> str:
    body = f"""
{_email_heading('Account security', 'Verify your email', 'Enter this code on the email verification screen to confirm your address.')}
<div style="margin:0;padding:18px 16px;background-color:#f8fafc;border:1px solid #e2e8f0;border-radius:12px;text-align:center;color:#0f172a;font-size:34px;line-height:42px;font-weight:800;letter-spacing:9px;">{escape(str(code))}</div>
{_email_code_steps('verify your email address', '15 minutes')}
{_security_notice("If you didn't try to verify an email address,")}
"""
    return _base_html(
        'Your Verif-AI email verification code',
        'Enter this code to verify your email address.',
        body,
    )


# ---------------------------------------------------------------------------
# SendGrid backend
# ---------------------------------------------------------------------------

class SendGridEmailService(_TemplatedEmailServiceBase):
    """
    Production email service powered by SendGrid.

    Requires:
        pip install sendgrid
        SENDGRID_API_KEY env var
    """

    def __init__(self):
        super().__init__()
        self.api_key = os.getenv('SENDGRID_API_KEY')
        self.from_address = os.getenv('EMAIL_FROM_ADDRESS', 'verifaisupportacc@gmail.com')
        self.from_name = os.getenv('EMAIL_FROM_NAME', 'Verif-AI')

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

class NodeMailerEmailService(_TemplatedEmailServiceBase):
    """
    NodeMailer email service invoked through a Node.js bridge script.

    Requires:
        npm install (in backend directory, to install nodemailer)
        Node.js available on PATH (or NODE_EXECUTABLE configured)

    Env vars:
        NODE_EXECUTABLE=node
        NODEMAILER_SCRIPT_PATH=backend/scripts/nodemailer_sender.js
        NODEMAILER_HOST / NODEMAILER_PORT / NODEMAILER_SECURE
        NODEMAILER_USER / NODEMAILER_PASS
        NODEMAILER_TIMEOUT_SECONDS=15
    """

    def __init__(self):
        super().__init__()
        self.from_address = os.getenv('EMAIL_FROM_ADDRESS', 'verifaisupportacc@gmail.com')
        self.from_name = os.getenv('EMAIL_FROM_NAME', 'Verif-AI')
        self.node_executable = self._get_env('NODE_EXECUTABLE', 'node')
        self.timeout_seconds = int(self._get_env('NODEMAILER_TIMEOUT_SECONDS', '15'))
        self.script_path = self._resolve_script_path()
        self.host = self._get_env('NODEMAILER_HOST', self._get_env('EMAIL_HOST', 'smtp.gmail.com'))
        self.port = int(self._get_env('NODEMAILER_PORT', self._get_env('EMAIL_PORT', '587')))
        secure_default = 'True' if self.port == 465 else 'False'
        self.secure = self._get_env('NODEMAILER_SECURE', secure_default).lower() == 'true'
        self.username = self._get_env('NODEMAILER_USER', self._get_env('EMAIL_HOST_USER', ''))
        self.password = self._get_env('NODEMAILER_PASS', self._get_env('EMAIL_HOST_PASSWORD', ''))

        if not shutil.which(self.node_executable):
            raise ValueError(
                f"Node executable '{self.node_executable}' not found. "
                "Install Node.js or set NODE_EXECUTABLE."
            )

        if not self.script_path.exists():
            raise ValueError(
                f"Nodemailer bridge script not found: {self.script_path}. "
                "Ensure backend/scripts/nodemailer_sender.js exists."
            )

    @staticmethod
    def _get_env(key: str, default: str = '') -> str:
        value = os.getenv(key)
        if value is None:
            return default
        value = value.strip()
        return value if value else default

    def _resolve_script_path(self) -> Path:
        configured_path = os.getenv('NODEMAILER_SCRIPT_PATH', '').strip()
        if configured_path:
            return Path(configured_path).expanduser().resolve()
        backend_root = Path(__file__).resolve().parents[2]
        return (backend_root / 'scripts' / 'nodemailer_sender.js').resolve()

    def _send(self, to_email: str, subject: str, html: str) -> bool:
        payload = {
            'transport': {
                'host': self.host,
                'port': self.port,
                'secure': self.secure,
                'auth': {
                    'user': self.username,
                    'pass': self.password,
                },
            },
            'message': {
                'from': f"{self.from_name} <{self.from_address}>",
                'to': to_email,
                'subject': subject,
                'html': html,
            }
        }

        try:
            result = subprocess.run(
                [self.node_executable, str(self.script_path)],
                input=json.dumps(payload),
                text=True,
                capture_output=True,
                timeout=self.timeout_seconds,
                check=False,
            )
        except subprocess.TimeoutExpired:
            logger.error(
                f"Nodemailer timed out after {self.timeout_seconds}s while sending to {to_email}"
            )
            return False
        except Exception as exc:
            logger.error(f"Nodemailer execution error for {to_email}: {exc}")
            return False

        if result.returncode != 0:
            stderr = (result.stderr or '').strip()
            logger.error(
                f"Nodemailer failed for {to_email} (code={result.returncode}): {stderr}"
            )
            return False

        try:
            response = json.loads(result.stdout or '')
        except (json.JSONDecodeError, TypeError) as exc:
            logger.error(f"Nodemailer returned an invalid response for {to_email}: {exc}")
            return False

        accepted = response.get('accepted') if isinstance(response, dict) else None
        if (
            not isinstance(response, dict)
            or response.get('ok') is not True
            or not isinstance(accepted, list)
            or not any(
                isinstance(address, str) and address.casefold() == to_email.casefold()
                for address in accepted
            )
        ):
            logger.error(f"Nodemailer did not accept recipient {to_email}")
            return False

        logger.info(f"Email sent to {to_email} via Nodemailer")
        return True


# ---------------------------------------------------------------------------
# SMTP backend (Gmail, Outlook, etc.)
# ---------------------------------------------------------------------------

class SMTPEmailService(_TemplatedEmailServiceBase):
    """
    SMTP email service for development / smaller deployments.

    Reads config from env vars:
        EMAIL_HOST, EMAIL_PORT, EMAIL_USE_TLS,
        EMAIL_HOST_USER, EMAIL_HOST_PASSWORD
    """

    def __init__(self):
        super().__init__()
        self.host = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
        self.port = int(os.getenv('EMAIL_PORT', '587'))
        self.use_tls = os.getenv('EMAIL_USE_TLS', 'True').lower() == 'true'
        self.username = os.getenv('EMAIL_HOST_USER')
        self.password = os.getenv('EMAIL_HOST_PASSWORD')
        self.from_address = os.getenv(
            'EMAIL_FROM_ADDRESS',
            self.username or 'verifaisupportacc@gmail.com',
        )
        self.from_name = os.getenv('EMAIL_FROM_NAME', 'Verif-AI')

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

# ---------------------------------------------------------------------------
# Mock backend (development / testing)
# ---------------------------------------------------------------------------

class MockEmailService(_TemplatedEmailServiceBase):
    """
    Mock email service — logs to stdout instead of sending.
    Used when EMAIL_BACKEND=mock or is unset.
    """

    def __init__(self):
        super().__init__()

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

    def send_password_reset_code_email(self, email: str, code: str) -> bool:
        logger.info(f"[MockEmail] Password reset code email to {email}")
        logger.info(f"[MockEmail] Code: {code}")
        print(f"MOCK: Password reset code to {email} | Code: {code}")
        return True

    def send_mfa_code_email(self, email: str, code: str) -> bool:
        logger.info(f"[MockEmail] MFA code email to {email}")
        logger.info(f"[MockEmail] Code: {code}")
        print(f"MOCK: MFA code to {email} | Code: {code}")
        return True

    def send_password_change_code_email(self, email: str, code: str) -> bool:
        logger.info(f"[MockEmail] Password change code email to {email}")
        logger.info(f"[MockEmail] Code: {code}")
        print(f"MOCK: Password change code to {email} | Code: {code}")
        return True

    def send_verification_code_email(self, email: str, code: str) -> bool:
        logger.info(f"[MockEmail] Verification code email to {email}")
        logger.info(f"[MockEmail] Code: {code}")
        print(f"MOCK: Verification code to {email} | Code: {code}")
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
        'nodemailer' → NodeMailerEmailService
        'smtp'     → SMTPEmailService
        'mock'     → MockEmailService (default)
    """
    global _email_service_instance

    if _email_service_instance is not None:
        return _email_service_instance

    backend = os.getenv('EMAIL_BACKEND', 'mock').lower().strip()

    if backend == 'sendgrid':
        _email_service_instance = SendGridEmailService()
    elif backend == 'nodemailer':
        _email_service_instance = NodeMailerEmailService()
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
