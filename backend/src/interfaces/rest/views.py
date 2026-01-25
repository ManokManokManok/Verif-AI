"""
REST API Views

Implements secure API endpoints following OWASP best practices:
- Strict input validation and sanitization
- Proper error handling without information leakage
- Rate limiting via middleware
- Secure authentication with JWT

OWASP References:
- https://cheatsheetseries.owasp.org/cheatsheets/REST_Security_Cheat_Sheet.html
- https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html
"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from typing import Dict, Any
import logging

from ...use_cases.auth import (
    SignupUseCase, LoginUseCase, GetUserProfileUseCase,
    CheckPermissionUseCase
)
from ...use_cases.security_auth import (
    EmailVerificationUseCase, PasswordResetUseCase, LogoutUseCase,
    RefreshTokenUseCase, InvalidTokenError
)
from ...domain.services import (
    BCryptPasswordHasher, EmailValidator, PasswordValidator,
    TokenGenerator, MockEmailService
)
from ...infrastructure.mongodb.connection import get_mongo_client, get_database_name
from ...infrastructure.mongodb.repositories import MongoDBUserRepository, MongoDBTokenRepository
from ...infrastructure.jwt_service import JWTService
from ...infrastructure.token_blacklist_service import MockTokenBlacklistService
from ...infrastructure.input_validator import (
    validate_input, validate_content_type, validate_request_size,
    SIGNUP_SCHEMA, LOGIN_SCHEMA, EMAIL_ONLY_SCHEMA, TOKEN_ONLY_SCHEMA,
    PASSWORD_RESET_SCHEMA, REFRESH_TOKEN_SCHEMA, LOGOUT_SCHEMA,
    CHECK_PERMISSION_SCHEMA, sanitize_email
)
from ...domain.entities import UserAlreadyExistsError, InvalidCredentialsError, UserNotFoundError


# Configure logger for security events
security_logger = logging.getLogger('security')


# Initialize dependencies
def get_user_repository():
    """Get user repository instance."""
    client = get_mongo_client()
    db_name = get_database_name()
    return MongoDBUserRepository(client, db_name)


def get_jwt_service():
    """Get JWT service instance."""
    import os
    secret_key = os.getenv('JWT_SECRET_KEY')
    if not secret_key:
        raise ValueError("JWT_SECRET_KEY environment variable is not set")
    
    access_lifetime = int(os.getenv('JWT_ACCESS_TOKEN_LIFETIME', '900'))
    refresh_lifetime = int(os.getenv('JWT_REFRESH_TOKEN_LIFETIME', '604800'))
    
    # Initialize token blacklist service
    token_blacklist_service = MockTokenBlacklistService()
    
    return JWTService(secret_key, access_lifetime, refresh_lifetime, token_blacklist_service)


def get_token_repository():
    """Get token repository instance."""
    client = get_mongo_client()
    db_name = get_database_name()
    return MongoDBTokenRepository(client, db_name)


def get_email_service():
    """Get email service instance."""
    return MockEmailService()


def user_to_dict(user) -> Dict[str, Any]:
    """Convert User entity to dictionary for API response."""
    return {
        'id': user.id,
        'email': user.email,
        'username': user.username,
        'roles': user.roles,
        'is_active': user.is_active,
        'is_verified': user.is_verified,
        'created_at': user.created_at.isoformat() if user.created_at else None,
        'last_login': user.last_login.isoformat() if user.last_login else None
    }


def tokens_to_dict(tokens) -> Dict[str, Any]:
    """Convert AuthTokens to dictionary for API response."""
    return {
        'access_token': tokens.access_token,
        'refresh_token': tokens.refresh_token,
        'token_type': tokens.token_type
    }


@api_view(['POST'])
@permission_classes([AllowAny])
def signup(request: Request) -> Response:
    """
    Register a new user.
    
    Request body:
    {
        "email": "user@example.com",
        "password": "SecurePass123!",
        "username": "johndoe" (optional)
    }
    
    Security:
    - Strict input validation with schema
    - Password strength enforcement
    - Email format validation
    - Mass assignment prevention
    """
    try:
        # Validate Content-Type header
        content_error = validate_content_type(request)
        if content_error:
            return Response(content_error, status=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)
        
        # Validate request size (prevent DoS via large payloads)
        size_error = validate_request_size(request, max_bytes=10240)  # 10KB max
        if size_error:
            return Response(size_error, status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)
        
        # Validate and sanitize input using schema
        validation_result = validate_input(request.data, SIGNUP_SCHEMA, strict=True)
        if not validation_result.is_valid:
            return Response(
                validation_result.to_error_response(),
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Extract validated data
        email = sanitize_email(validation_result.data['email'])
        password = validation_result.data['password']  # Not sanitized (passwords as-is)
        username = validation_result.data.get('username')
        
        # Initialize use case
        user_repo = get_user_repository()
        password_hasher = BCryptPasswordHasher()
        email_validator = EmailValidator()
        password_validator = PasswordValidator()
        
        signup_usecase = SignupUseCase(
            user_repository=user_repo,
            password_hasher=password_hasher,
            email_validator=email_validator,
            password_validator=password_validator
        )
        
        # Execute use case
        user = signup_usecase.execute(email, password, username)
        
        # Log successful registration
        security_logger.info(f"User registered: email={email}")
        
        return Response({
            'success': True,
            'message': 'User registered successfully',
            'user': user_to_dict(user)
        }, status=status.HTTP_201_CREATED)
        
    except UserAlreadyExistsError as e:
        # Log failed registration attempt
        security_logger.warning(f"Registration failed - email exists: {request.data.get('email', 'unknown')}")
        return Response({
            'error': {
                'code': 'EMAIL_ALREADY_EXISTS',
                'message': str(e)
            }
        }, status=status.HTTP_409_CONFLICT)
    
    except ValueError as e:
        return Response({
            'error': {
                'code': 'VALIDATION_ERROR',
                'message': str(e)
            }
        }, status=status.HTTP_400_BAD_REQUEST)
    
    except Exception as e:
        # Log internal errors for debugging (don't expose details to client)
        security_logger.error(f"Signup error: {type(e).__name__}")
        return Response({
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'An unexpected error occurred'
            }
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def login(request: Request) -> Response:
    """
    Authenticate user and return tokens.
    
    Request body:
    {
        "email": "user@example.com",
        "password": "SecurePass123!"
    }
    
    Security:
    - Strict input validation
    - Generic error messages to prevent user enumeration
    - Rate limited via middleware
    """
    try:
        # Validate Content-Type header
        content_error = validate_content_type(request)
        if content_error:
            return Response(content_error, status=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)
        
        # Validate request size
        size_error = validate_request_size(request, max_bytes=4096)  # 4KB max
        if size_error:
            return Response(size_error, status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)
        
        # Validate and sanitize input using schema
        validation_result = validate_input(request.data, LOGIN_SCHEMA, strict=True)
        if not validation_result.is_valid:
            return Response(
                validation_result.to_error_response(),
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Extract validated data
        email = sanitize_email(validation_result.data['email'])
        password = validation_result.data['password']
        
        # Initialize use case
        user_repo = get_user_repository()
        password_hasher = BCryptPasswordHasher()
        jwt_service = get_jwt_service()
        
        login_usecase = LoginUseCase(
            user_repository=user_repo,
            password_hasher=password_hasher,
            jwt_service=jwt_service
        )
        
        # Execute use case
        auth_result = login_usecase.execute(email, password)
        
        # Log successful login
        security_logger.info(f"Login successful: email={email}")
        
        return Response({
            'success': True,
            'message': 'Login successful',
            'user': user_to_dict(auth_result.user),
            'tokens': tokens_to_dict(auth_result.tokens)
        }, status=status.HTTP_200_OK)
        
    except InvalidCredentialsError as e:
        # Log failed login attempt (for security monitoring)
        security_logger.warning(f"Login failed: email={request.data.get('email', 'unknown')}")
        # Generic error message to prevent user enumeration
        return Response({
            'error': {
                'code': 'INVALID_CREDENTIALS',
                'message': 'Invalid email or password'
            }
        }, status=status.HTTP_401_UNAUTHORIZED)
    
    except Exception as e:
        security_logger.error(f"Login error: {type(e).__name__}")
        return Response({
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'An unexpected error occurred'
            }
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def profile(request: Request) -> Response:
    """
    Get current user profile.
    
    Requires authentication.
    """
    try:
        # Get user ID from request (set by middleware)
        user_id = getattr(request, 'user_id', None)
        if not user_id:
            return Response({
                'error': {
                    'code': 'AUTHENTICATION_REQUIRED',
                    'message': 'Authentication required'
                }
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        # Initialize use case
        user_repo = get_user_repository()
        profile_usecase = GetUserProfileUseCase(user_repository=user_repo)
        
        # Execute use case
        user = profile_usecase.execute(user_id)
        
        return Response({
            'user': user_to_dict(user)
        }, status=status.HTTP_200_OK)
        
    except UserNotFoundError as e:
        return Response({
            'error': {
                'code': 'USER_NOT_FOUND',
                'message': str(e)
            }
        }, status=status.HTTP_404_NOT_FOUND)
    
    except Exception as e:
        return Response({
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'An unexpected error occurred'
            }
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def check_permission(request: Request) -> Response:
    """
    Check if current user has a specific permission.
    
    Request body:
    {
        "permission": "create_user",
        "resource": "user"  # optional
    }
    
    Security:
    - Requires authentication
    - Validates permission/resource format
    """
    try:
        # Get user ID from request (set by middleware)
        user_id = getattr(request, 'user_id', None)
        if not user_id:
            return Response({
                'error': {
                    'code': 'AUTHENTICATION_REQUIRED',
                    'message': 'Authentication required'
                }
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        # Validate input
        validation_result = validate_input(request.data, CHECK_PERMISSION_SCHEMA, strict=True)
        if not validation_result.is_valid:
            return Response(
                validation_result.to_error_response(),
                status=status.HTTP_400_BAD_REQUEST
            )
        
        permission = validation_result.data['permission']
        resource = validation_result.data.get('resource')
        
        # Initialize use case
        user_repo = get_user_repository()
        check_permission_usecase = CheckPermissionUseCase(user_repository=user_repo)
        
        # Execute use case
        has_permission = check_permission_usecase.execute(user_id, permission, resource)
        
        return Response({
            'has_permission': has_permission,
            'permission': permission,
            'resource': resource
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        security_logger.error(f"Check permission error: {type(e).__name__}")
        return Response({
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'An unexpected error occurred'
            }
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Phase 2 Endpoints

@api_view(['POST'])
@permission_classes([AllowAny])
def send_verification_email(request: Request) -> Response:
    """
    Send email verification token.
    
    Request body:
    {
        "email": "user@example.com"
    }
    
    Security:
    - Rate limited to prevent email bombing
    - Generic response to prevent user enumeration
    """
    try:
        # Validate input
        validation_result = validate_input(request.data, EMAIL_ONLY_SCHEMA, strict=True)
        if not validation_result.is_valid:
            return Response(
                validation_result.to_error_response(),
                status=status.HTTP_400_BAD_REQUEST
            )
        
        email = sanitize_email(validation_result.data['email'])
        
        # Initialize use case
        user_repo = get_user_repository()
        token_repo = get_token_repository()
        email_service = get_email_service()
        token_generator = TokenGenerator()
        
        verification_usecase = EmailVerificationUseCase(
            user_repository=user_repo,
            token_repository=token_repo,
            email_service=email_service,
            token_generator=token_generator
        )
        
        # Execute use case
        verification_usecase.send_verification_email(email)
        
        # Always return success to prevent user enumeration
        # Even if user doesn't exist, return same response
        return Response({
            'message': 'If the email exists, a verification email has been sent'
        }, status=status.HTTP_200_OK)
        
    except UserNotFoundError as e:
        # Return generic success to prevent user enumeration (OWASP)
        security_logger.info(f"Verification email requested for non-existent: {email}")
        return Response({
            'message': 'If the email exists, a verification email has been sent'
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        security_logger.error(f"Send verification error: {type(e).__name__}")
        return Response({
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'An unexpected error occurred'
            }
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def verify_email(request: Request) -> Response:
    """
    Verify email using token.
    
    Request body:
    {
        "token": "verification_token_here"
    }
    
    Security:
    - Token format validation
    - Rate limited via middleware
    """
    try:
        # Validate input
        validation_result = validate_input(request.data, TOKEN_ONLY_SCHEMA, strict=True)
        if not validation_result.is_valid:
            return Response(
                validation_result.to_error_response(),
                status=status.HTTP_400_BAD_REQUEST
            )
        
        token = validation_result.data['token']
        
        # Initialize use case
        user_repo = get_user_repository()
        token_repo = get_token_repository()
        email_service = get_email_service()
        token_generator = TokenGenerator()
        
        verification_usecase = EmailVerificationUseCase(
            user_repository=user_repo,
            token_repository=token_repo,
            email_service=email_service,
            token_generator=token_generator
        )
        
        # Execute use case
        verification_usecase.verify_email(token)
        
        security_logger.info("Email verified successfully")
        
        return Response({
            'message': 'Email verified successfully'
        }, status=status.HTTP_200_OK)
        
    except InvalidTokenError as e:
        security_logger.warning("Invalid email verification token used")
        return Response({
            'error': {
                'code': 'INVALID_TOKEN',
                'message': 'Invalid or expired verification token'
            }
        }, status=status.HTTP_400_BAD_REQUEST)
    
    except Exception as e:
        security_logger.error(f"Verify email error: {type(e).__name__}")
        return Response({
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'An unexpected error occurred'
            }
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def request_password_reset(request: Request) -> Response:
    """
    Request password reset email.
    
    Request body:
    {
        "email": "user@example.com"
    }
    
    Security:
    - Rate limited to prevent email bombing
    - Generic response to prevent user enumeration
    """
    try:
        # Validate input
        validation_result = validate_input(request.data, EMAIL_ONLY_SCHEMA, strict=True)
        if not validation_result.is_valid:
            return Response(
                validation_result.to_error_response(),
                status=status.HTTP_400_BAD_REQUEST
            )
        
        email = sanitize_email(validation_result.data['email'])
        
        # Initialize use case
        user_repo = get_user_repository()
        token_repo = get_token_repository()
        email_service = get_email_service()
        token_generator = TokenGenerator()
        password_hasher = BCryptPasswordHasher()
        password_validator = PasswordValidator()
        
        reset_usecase = PasswordResetUseCase(
            user_repository=user_repo,
            token_repository=token_repo,
            email_service=email_service,
            token_generator=token_generator,
            password_hasher=password_hasher,
            password_validator=password_validator
        )
        
        # Execute use case
        reset_usecase.request_password_reset(email)
        
        # Always return success to prevent user enumeration (OWASP)
        return Response({
            'message': 'If the email exists, a password reset email has been sent'
        }, status=status.HTTP_200_OK)
        
    except UserNotFoundError as e:
        # Return generic success to prevent user enumeration
        security_logger.info(f"Password reset requested for non-existent: {email}")
        return Response({
            'message': 'If the email exists, a password reset email has been sent'
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        security_logger.error(f"Password reset request error: {type(e).__name__}")
        return Response({
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'An unexpected error occurred'
            }
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def reset_password(request: Request) -> Response:
    """
    Reset password using token.
    
    Request body:
    {
        "token": "reset_token_here",
        "new_password": "NewSecurePass123!"
    }
    
    Security:
    - Token and password validation
    - Password strength enforcement
    """
    try:
        # Validate input
        validation_result = validate_input(request.data, PASSWORD_RESET_SCHEMA, strict=True)
        if not validation_result.is_valid:
            return Response(
                validation_result.to_error_response(),
                status=status.HTTP_400_BAD_REQUEST
            )
        
        token = validation_result.data['token']
        new_password = validation_result.data['new_password']
        
        # Initialize use case
        user_repo = get_user_repository()
        token_repo = get_token_repository()
        email_service = get_email_service()
        token_generator = TokenGenerator()
        password_hasher = BCryptPasswordHasher()
        password_validator = PasswordValidator()
        
        reset_usecase = PasswordResetUseCase(
            user_repository=user_repo,
            token_repository=token_repo,
            email_service=email_service,
            token_generator=token_generator,
            password_hasher=password_hasher,
            password_validator=password_validator
        )
        
        # Execute use case
        reset_usecase.reset_password(token, new_password)
        
        security_logger.info("Password reset completed")
        
        return Response({
            'message': 'Password reset successfully'
        }, status=status.HTTP_200_OK)
        
    except InvalidTokenError as e:
        security_logger.warning("Invalid password reset token used")
        return Response({
            'error': {
                'code': 'INVALID_TOKEN',
                'message': 'Invalid or expired reset token'
            }
        }, status=status.HTTP_400_BAD_REQUEST)
    
    except ValueError as e:
        return Response({
            'error': {
                'code': 'VALIDATION_ERROR',
                'message': str(e)
            }
        }, status=status.HTTP_400_BAD_REQUEST)
    
    except Exception as e:
        security_logger.error(f"Password reset error: {type(e).__name__}")
        return Response({
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'An unexpected error occurred'
            }
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def logout(request: Request) -> Response:
    """
    Logout user by blacklisting tokens.
    
    Request body:
    {
        "refresh_token": "optional_refresh_token_here"
    }
    
    Security:
    - Requires valid access token
    - Blacklists both access and refresh tokens
    """
    try:
        # Get access token from Authorization header
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if not auth_header.startswith('Bearer '):
            return Response({
                'error': {
                    'code': 'MISSING_TOKEN',
                    'message': 'Access token is required in Authorization header'
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        access_token = auth_header[7:]  # Remove 'Bearer ' prefix
        
        # Validate optional refresh_token in body
        validation_result = validate_input(request.data, LOGOUT_SCHEMA, strict=True)
        refresh_token = ''
        if validation_result.is_valid and validation_result.data:
            refresh_token = validation_result.data.get('refresh_token', '')
        
        # Initialize use case
        jwt_service = get_jwt_service()
        token_blacklist_service = MockTokenBlacklistService()
        
        logout_usecase = LogoutUseCase(
            jwt_service=jwt_service,
            token_blacklist_service=token_blacklist_service
        )
        
        # Execute use case
        logout_usecase.logout(access_token, refresh_token)
        
        security_logger.info(f"User logged out: user_id={getattr(request, 'user_id', 'unknown')}")
        
        return Response({
            'success': True,
            'message': 'Logout successful'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        security_logger.error(f"Logout error: {type(e).__name__}")
        return Response({
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'An unexpected error occurred'
            }
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def refresh_token(request: Request) -> Response:
    """
    Refresh access token using refresh token.
    
    Request body:
    {
        "refresh_token": "refresh_token_here"
    }
    
    Security:
    - JWT format validation
    - Rate limited via middleware
    """
    try:
        # Validate input
        validation_result = validate_input(request.data, REFRESH_TOKEN_SCHEMA, strict=True)
        if not validation_result.is_valid:
            return Response(
                validation_result.to_error_response(),
                status=status.HTTP_400_BAD_REQUEST
            )
        
        refresh_token_value = validation_result.data['refresh_token']
        
        # Initialize use case
        jwt_service = get_jwt_service()
        user_repo = get_user_repository()
        token_blacklist_service = MockTokenBlacklistService()
        
        refresh_usecase = RefreshTokenUseCase(
            jwt_service=jwt_service,
            user_repository=user_repo,
            token_blacklist_service=token_blacklist_service
        )
        
        # Execute use case
        auth_result = refresh_usecase.refresh_token(refresh_token_value)
        
        return Response({
            'success': True,
            'message': 'Token refreshed successfully',
            'user': user_to_dict(auth_result.user),
            'tokens': tokens_to_dict(auth_result.tokens)
        }, status=status.HTTP_200_OK)
        
    except InvalidTokenError as e:
        security_logger.warning("Invalid refresh token used")
        return Response({
            'error': {
                'code': 'INVALID_TOKEN',
                'message': 'Invalid or expired refresh token'
            }
        }, status=status.HTTP_401_UNAUTHORIZED)
    
    except Exception as e:
        security_logger.error(f"Token refresh error: {type(e).__name__}")
        return Response({
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'An unexpected error occurred'
            }
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
