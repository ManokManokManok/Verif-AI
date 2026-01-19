import jwt
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from ..domain.entities import AuthTokens
from .token_blacklist_service import TokenBlacklistService


class JWTService:
    def __init__(self, secret_key: str, access_token_lifetime: int = 900, refresh_token_lifetime: int = 604800, token_blacklist_service: Optional[TokenBlacklistService] = None):
        self.secret_key = secret_key
        self.access_token_lifetime = access_token_lifetime  # 15 minutes default
        self.refresh_token_lifetime = refresh_token_lifetime  # 7 days default
        self.algorithm = 'HS256'
        self.token_blacklist_service = token_blacklist_service
    
    def generate_tokens(self, user_id: str, email: str, roles: List[str], permissions: List[str]) -> AuthTokens:
        """
        Generate access and refresh tokens for a user.
        
        Args:
            user_id: User's unique identifier
            email: User's email
            roles: List of user's role names
            permissions: List of user's permissions
        
        Returns:
            AuthTokens object containing access and refresh tokens
        """
        now = datetime.utcnow()
        
        # Access token payload
        access_payload = {
            'user_id': user_id,
            'email': email,
            'roles': roles,
            'permissions': permissions,
            'token_type': 'access',
            'iat': now,
            'exp': now + timedelta(seconds=self.access_token_lifetime)
        }
        
        # Refresh token payload
        refresh_payload = {
            'user_id': user_id,
            'token_type': 'refresh',
            'iat': now,
            'exp': now + timedelta(seconds=self.refresh_token_lifetime)
        }
        
        access_token = jwt.encode(access_payload, self.secret_key, algorithm=self.algorithm)
        refresh_token = jwt.encode(refresh_payload, self.secret_key, algorithm=self.algorithm)
        
        return AuthTokens(
            access_token=access_token,
            refresh_token=refresh_token
        )
    
    def verify_access_token(self, token: str) -> Dict:
        """
        Verify and decode an access token.
        
        Args:
            token: JWT access token
        
        Returns:
            Decoded token payload
        
        Raises:
            jwt.InvalidTokenError: If token is invalid or expired
        """
        try:
            # Check if token is blacklisted
            if self.token_blacklist_service and self.token_blacklist_service.is_token_blacklisted(token):
                raise jwt.InvalidTokenError("Token has been revoked")
            
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            # Ensure it's an access token
            if payload.get('token_type') != 'access':
                raise jwt.InvalidTokenError("Invalid token type")
            
            return payload
        except jwt.ExpiredSignatureError:
            raise jwt.InvalidTokenError("Token has expired")
        except jwt.InvalidTokenError as e:
            raise jwt.InvalidTokenError(f"Invalid token: {str(e)}")
    
    def verify_refresh_token(self, token: str) -> Dict:
        """
        Verify and decode a refresh token.
        
        Args:
            token: JWT refresh token
        
        Returns:
            Decoded token payload
        
        Raises:
            jwt.InvalidTokenError: If token is invalid or expired
        """
        try:
            # Check if token is blacklisted
            if self.token_blacklist_service and self.token_blacklist_service.is_token_blacklisted(token):
                raise jwt.InvalidTokenError("Refresh token has been revoked")
            
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            # Ensure it's a refresh token
            if payload.get('token_type') != 'refresh':
                raise jwt.InvalidTokenError("Invalid token type")
            
            return payload
        except jwt.ExpiredSignatureError:
            raise jwt.InvalidTokenError("Refresh token has expired")
        except jwt.InvalidTokenError as e:
            raise jwt.InvalidTokenError(f"Invalid refresh token: {str(e)}")
    
    def extract_user_id_from_token(self, token: str) -> Optional[str]:
        """
        Extract user ID from token without full verification (for basic checks).
        
        Args:
            token: JWT token
        
        Returns:
            User ID if token is valid format, None otherwise
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm], options={"verify_exp": False})
            return payload.get('user_id')
        except jwt.InvalidTokenError:
            return None
