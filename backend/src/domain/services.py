import bcrypt
import re
import secrets
import string
from typing import Protocol


class PasswordHasher(Protocol):
    def hash_password(self, password: str) -> str:
        ...
    
    def verify_password(self, password: str, hashed: str) -> bool:
        ...


class BCryptPasswordHasher:
    def __init__(self, rounds: int = 12):
        self.rounds = rounds
    
    def hash_password(self, password: str) -> str:
        """
        Hash a password using bcrypt.
        
        Args:
            password: Plain text password
        
        Returns:
            Hashed password as string
        """
        salt = bcrypt.gensalt(rounds=self.rounds)
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """
        Verify a password against its hash.
        
        Args:
            password: Plain text password to verify
            hashed: Hashed password to verify against
        
        Returns:
            True if password matches hash, False otherwise
        """
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))


class PasswordValidator:
    @staticmethod
    def validate(password: str) -> tuple[bool, list[str]]:
        """
        Validate password strength.
        
        Args:
            password: Password to validate
        
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        
        if len(password) < 8:
            errors.append("Password must be at least 8 characters long")
        
        if not re.search(r'[A-Z]', password):
            errors.append("Password must contain at least one uppercase letter")
        
        if not re.search(r'[a-z]', password):
            errors.append("Password must contain at least one lowercase letter")
        
        if not re.search(r'\d', password):
            errors.append("Password must contain at least one digit")
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>\[\]\\;\'`~_+=/-]', password):
            errors.append("Password must contain at least one special character")
        
        # Check against common password blacklist
        from ..infrastructure.validators import is_common_password
        if is_common_password(password):
            errors.append("This password is too common. Please choose a stronger password.")
        
        return len(errors) == 0, errors


class EmailValidator:
    @staticmethod
    def validate(email: str) -> tuple[bool, str]:
        """
        Validate email format.
        
        Args:
            email: Email to validate
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, email):
            return False, "Invalid email format"
        return True, ""


class TokenGenerator:
    @staticmethod
    def generate_secure_token(length: int = 32) -> str:
        """
        Generate a cryptographically secure random token.
        
        Args:
            length: Length of the token to generate
        
        Returns:
            Secure random token as hex string
        """
        return secrets.token_hex(length)
    
    @staticmethod
    def generate_verification_token() -> str:
        """
        Generate an email verification token.
        Returns:
            32-character verification token
        """
        return TokenGenerator.generate_secure_token(16)
    
    @staticmethod
    def generate_password_reset_token() -> str:
        """
        Generate password reset token.
        
        Returns:
            32-character password reset token
        """
        return TokenGenerator.generate_secure_token(16)


class EmailService(Protocol):
    def send_verification_email(self, email: str, token: str) -> bool:
        ...
    
    def send_password_reset_email(self, email: str, token: str) -> bool:
        ...

    def send_password_reset_code_email(self, email: str, code: str) -> bool:
        ...


class MFACodeGenerator:
    """
    Multi-Factor Authentication code generator.

    Generates cryptographically secure 6-digit numeric codes
    for email-based two-factor authentication.
    """

    @staticmethod
    def generate_code(length: int = 6) -> str:
        """
        Generate a numeric MFA code.

        Args:
            length: Number of digits (default 6).

        Returns:
            Zero-padded numeric string, e.g. "042917".
        """
        return ''.join(secrets.choice(string.digits) for _ in range(length))

    @staticmethod
    def generate_code_with_expiry(
        lifetime_minutes: int = 5,
        length: int = 6,
    ) -> tuple[str, 'datetime']:
        """
        Generate MFA code together with its expiration timestamp.

        Args:
            lifetime_minutes: Validity window in minutes (default 5).
            length: Number of digits (default 6).

        Returns:
            Tuple of (code, expires_at_datetime).
        """
        from datetime import datetime, timedelta
        code = MFACodeGenerator.generate_code(length)
        expires_at = datetime.utcnow() + timedelta(minutes=lifetime_minutes)
        return code, expires_at
