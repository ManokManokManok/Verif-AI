from typing import Protocol, List, Optional
from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import logging
import os
import secrets
from ..domain.entities import User, AuthResult, UserAlreadyExistsError, InvalidCredentialsError, UserNotFoundError
from ..domain.services import PasswordHasher, EmailValidator, PasswordValidator, TokenGenerator, EmailService
from ..infrastructure.jwt_service import JWTService
from ..infrastructure.mongodb.repositories import MongoDBUserRepository
from ..infrastructure.token_blacklist_service import TokenBlacklistService

logger = logging.getLogger(__name__)


class UserRepository(Protocol):
    def create_user(self, user: User) -> User: ...
    def get_by_email(self, email: str) -> User: ...
    def get_by_id(self, user_id: str) -> User: ...
    def update_last_login(self, user_id: str) -> None: ...
    def get_user_roles(self, user_id: str) -> List: ...


class TokenRepository(Protocol):
    def create_verification_token(self, user_id: str, token: str, expires_at: datetime) -> bool: ...
    def create_password_reset_token(self, user_id: str, token: str, expires_at: datetime) -> bool: ...
    def verify_email_token(self, token: str) -> Optional[str]: ...
    def verify_password_reset_token(self, token: str) -> Optional[str]: ...
    def invalidate_token(self, token: str) -> bool: ...
    def update_user_verification(self, user_id: str) -> bool: ...
    def update_user_password(self, user_id: str, password_hash: str) -> bool: ...


class EmailVerificationUseCase:
    def __init__(
        self,
        user_repository: UserRepository,
        token_repository: TokenRepository,
        email_service: EmailService,
        token_generator: TokenGenerator
    ):
        self.user_repository = user_repository
        self.token_repository = token_repository
        self.email_service = email_service
        self.token_generator = token_generator
    
    def send_verification_email(self, email: str) -> bool:
        """
        Send email verification token to user.
        
        Args:
            email: User's email address
        
        Returns:
            True if verification email was sent successfully
        
        Raises:
            UserNotFoundError: If user with email doesn't exist
        """
        user = self.user_repository.get_by_email(email)
        if not user:
            raise UserNotFoundError(f"User with email {email} not found")
        
        # Generate verification token
        token = self.token_generator.generate_verification_token()
        expires_at = datetime.utcnow() + timedelta(hours=24)  # Token valid for 24 hours
        
        # Store token
        self.token_repository.create_verification_token(user.id, token, expires_at)
        
        # Send email
        return self.email_service.send_verification_email(email, token)
    
    def verify_email(self, token: str) -> str:
        """
        Verify user's email using token.
        
        Args:
            token: Email verification token
        
        Returns:
            user_id: ID of the user whose email was verified
        
        Raises:
            InvalidTokenError: If token is invalid or expired
        """
        user_id = self.token_repository.verify_email_token(token)
        if not user_id:
            raise InvalidTokenError("Invalid or expired verification token")
        
        # Mark user as verified
        self.token_repository.update_user_verification(user_id)
        return user_id


class PasswordResetUseCase:
    def __init__(
        self,
        user_repository: UserRepository,
        token_repository: TokenRepository,
        email_service: EmailService,
        token_generator: TokenGenerator,
        password_hasher: PasswordHasher,
        password_validator: PasswordValidator
    ):
        self.user_repository = user_repository
        self.token_repository = token_repository
        self.email_service = email_service
        self.token_generator = token_generator
        self.password_hasher = password_hasher
        self.password_validator = password_validator

    def request_password_reset_code(self, email: str) -> dict:
        """Issue a one-time code without disclosing whether the account exists."""
        secret = os.getenv("PASSWORD_RESET_CODE_SECRET") or os.getenv("JWT_SECRET_KEY")
        if not secret:
            raise RuntimeError("PASSWORD_RESET_CODE_SECRET or JWT_SECRET_KEY must be configured")

        email_key = hmac.new(
            secret.encode(), email.strip().lower().encode(), hashlib.sha256
        ).hexdigest()
        code = f"{secrets.randbelow(1_000_000):06d}"
        code_digest = hmac.new(
            secret.encode(), f"{email_key}:{code}".encode(), hashlib.sha256
        ).hexdigest()
        try:
            user = self.user_repository.get_by_email(email)
        except UserNotFoundError:
            user = None

        result = self.token_repository.issue_password_reset_code(
            email_key, getattr(user, "id", None), code_digest, datetime.now(timezone.utc)
        )
        if result["status"] == "sent" and user:
            if not self.email_service.send_password_reset_code_email(email, code):
                self.token_repository.invalidate_password_reset_code(email_key)
                logger.error("Password reset code email delivery failed")
                result["status"] = "email_failed"
        return result

    def reset_password_with_code(self, email: str, code: str, new_password: str) -> str:
        """Validate the password before atomically consuming the emailed code."""
        is_valid, errors = self.password_validator.validate(new_password)
        if not is_valid:
            raise ValueError("Password validation failed: " + "; ".join(errors))

        secret = os.getenv("PASSWORD_RESET_CODE_SECRET") or os.getenv("JWT_SECRET_KEY")
        if not secret:
            raise RuntimeError("PASSWORD_RESET_CODE_SECRET or JWT_SECRET_KEY must be configured")
        password_hash = self.password_hasher.hash_password(new_password)
        email_key = hmac.new(
            secret.encode(), email.strip().lower().encode(), hashlib.sha256
        ).hexdigest()
        code_digest = hmac.new(
            secret.encode(), f"{email_key}:{code}".encode(), hashlib.sha256
        ).hexdigest()
        result = self.token_repository.record_password_reset_code_attempt(
            email_key, code_digest, datetime.now(timezone.utc)
        )
        if result["status"] != "valid" or not result.get("user_id"):
            raise InvalidTokenError("The code is invalid, expired, or has reached its attempt limit")

        if not self.token_repository.update_user_password(result["user_id"], password_hash):
            raise RuntimeError("Password could not be updated")
        return result["user_id"]
    
    def request_password_reset(self, email: str) -> bool:
        """
        Send password reset email to user.
        
        Args:
            email: User's email address
        
        Returns:
            True if reset email was sent successfully
        
        Raises:
            UserNotFoundError: If user with email doesn't exist
        """
        user = self.user_repository.get_by_email(email)
        if not user:
            raise UserNotFoundError(f"User with email {email} not found")
        
        # Generate password reset token
        token = self.token_generator.generate_password_reset_token()
        expires_at = datetime.utcnow() + timedelta(hours=1)  # Token valid for 1 hour
        
        # Store token
        self.token_repository.create_password_reset_token(user.id, token, expires_at)
        
        # Send email
        return self.email_service.send_password_reset_email(email, token)
    
    def reset_password(self, token: str, new_password: str) -> str:
        """
        Reset user's password using token.
        
        Args:
            token: Password reset token
            new_password: New password
        
        Returns:
            user_id: ID of the user whose password was reset
        
        Raises:
            InvalidTokenError: If token is invalid or expired
            ValueError: If new password doesn't meet requirements
        """
        # Validate new password
        is_valid, errors = self.password_validator.validate(new_password)
        if not is_valid:
            raise ValueError("Password validation failed: " + "; ".join(errors))
        
        #Verify token and get user ID
        user_id = self.token_repository.verify_password_reset_token(token)
        if not user_id:
            raise InvalidTokenError("Invalid or expired reset token")
        
        # Hash new password
        password_hash = self.password_hasher.hash_password(new_password)
        
        # Update password
        self.token_repository.update_user_password(user_id, password_hash)
        return user_id


class LogoutUseCase:
    def __init__(
        self,
        jwt_service: JWTService,
        token_blacklist_service: TokenBlacklistService
    ):
        self.jwt_service = jwt_service
        self.token_blacklist_service = token_blacklist_service
    
    def logout(self, access_token: str, refresh_token: str = None) -> bool:
        """
        Logout user by blacklisting tokens.
        
        Args:
            access_token: JWT access token to blacklist
            refresh_token: Optional refresh token to blacklist
        
        Returns:
            True if logout was successful
        """
        try:
            # Decode access token to get expiration time
            payload = self.jwt_service.verify_access_token(access_token)
            expires_at = datetime.fromtimestamp(payload['exp'])
            
            # Blacklist access token
            self.token_blacklist_service.blacklist_token(access_token, expires_at)
            
            # If refresh token provided, blacklist it too
            if refresh_token:
                refresh_payload = self.jwt_service.verify_refresh_token(refresh_token)
                refresh_expires_at = datetime.fromtimestamp(refresh_payload['exp'])
                self.token_blacklist_service.blacklist_token(refresh_token, refresh_expires_at)
            
            return True
        except Exception:
            return False


class RefreshTokenUseCase:
    def __init__(
        self,
        jwt_service: JWTService,
        user_repository: UserRepository,
        token_blacklist_service: TokenBlacklistService
    ):
        self.jwt_service = jwt_service
        self.user_repository = user_repository
        self.token_blacklist_service = token_blacklist_service
    
    def refresh_token(self, refresh_token: str) -> AuthResult:
        """
        Generate new access token using refresh token.
        
        Args:
            refresh_token: Valid refresh token
        
        Returns:
            New AuthResult with fresh tokens
        
        Raises:
            InvalidTokenError: If refresh token is invalid or expired
        """
        # Verify refresh token
        payload = self.jwt_service.verify_refresh_token(refresh_token)
        user_id = payload['user_id']
        
        # Check if refresh token is blacklisted
        if self.token_blacklist_service.is_token_blacklisted(refresh_token):
            raise InvalidTokenError("Refresh token has been revoked")
        
        # Get user data
        user = self.user_repository.get_by_id(user_id)
        if not user or not user.is_active:
            raise InvalidTokenError("User not found or inactive")
        
        # Get user roles and permissions
        user_roles = self.user_repository.get_user_roles(user.id)
        role_names = [role.name for role in user_roles]
        permissions = []
        for role in user_roles:
            permissions.extend(role.permissions)
        
        # Generate new tokens
        tokens = self.jwt_service.generate_tokens(
            user_id=user.id,
            email=user.email,
            roles=role_names,
            permissions=list(set(permissions))
        )
        
        return AuthResult(user=user, tokens=tokens)


class InvalidTokenError(Exception):
    pass
