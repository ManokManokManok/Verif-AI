from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from typing import Dict, Any

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
from ...domain.entities import UserAlreadyExistsError, InvalidCredentialsError, UserNotFoundError


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
    """
    try:
        email = request.data.get('email', '').strip().lower()
        password = request.data.get('password', '')
        username = request.data.get('username', '').strip() if request.data.get('username') else None
        
        if not email or not password:
            return Response({
                'error': {
                    'code': 'MISSING_FIELDS',
                    'message': 'Email and password are required'
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
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
        
        return Response({
            'success': True,
            'message': 'User registered successfully',
            'user': user_to_dict(user)
        }, status=status.HTTP_201_CREATED)
        
    except UserAlreadyExistsError as e:
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
    """
    try:
        email = request.data.get('email', '').strip().lower()
        password = request.data.get('password', '')
        
        if not email or not password:
            return Response({
                'error': {
                    'code': 'MISSING_FIELDS',
                    'message': 'Email and password are required'
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
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
        
        return Response({
            'success': True,
            'message': 'Login successful',
            'user': user_to_dict(auth_result.user),
            'tokens': tokens_to_dict(auth_result.tokens)
        }, status=status.HTTP_200_OK)
        
    except InvalidCredentialsError as e:
        return Response({
            'error': {
                'code': 'INVALID_CREDENTIALS',
                'message': str(e)
            }
        }, status=status.HTTP_401_UNAUTHORIZED)
    
    except Exception as e:
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
        
        permission = request.data.get('permission', '')
        resource = request.data.get('resource', None)
        
        if not permission:
            return Response({
                'error': {
                    'code': 'MISSING_PERMISSION',
                    'message': 'Permission is required'
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
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
    """
    try:
        email = request.data.get('email', '').strip().lower()
        
        if not email:
            return Response({
                'error': {
                    'code': 'MISSING_EMAIL',
                    'message': 'Email is required'
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
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
        
        return Response({
            'message': 'Verification email sent successfully'
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
@permission_classes([AllowAny])
def verify_email(request: Request) -> Response:
    """
    Verify email using token.
    
    Request body:
    {
        "token": "verification_token_here"
    }
    """
    try:
        token = request.data.get('token', '')
        
        if not token:
            return Response({
                'error': {
                    'code': 'MISSING_TOKEN',
                    'message': 'Verification token is required'
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
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
        
        return Response({
            'message': 'Email verified successfully'
        }, status=status.HTTP_200_OK)
        
    except InvalidTokenError as e:
        return Response({
            'error': {
                'code': 'INVALID_TOKEN',
                'message': str(e)
            }
        }, status=status.HTTP_400_BAD_REQUEST)
    
    except Exception as e:
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
    """
    try:
        email = request.data.get('email', '').strip().lower()
        
        if not email:
            return Response({
                'error': {
                    'code': 'MISSING_EMAIL',
                    'message': 'Email is required'
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
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
        
        return Response({
            'message': 'Password reset email sent successfully'
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
@permission_classes([AllowAny])
def reset_password(request: Request) -> Response:
    """
    Reset password using token.
    
    Request body:
    {
        "token": "reset_token_here",
        "new_password": "NewSecurePass123!"
    }
    """
    try:
        token = request.data.get('token', '')
        new_password = request.data.get('new_password', '')
        
        if not token or not new_password:
            return Response({
                'error': {
                    'code': 'MISSING_FIELDS',
                    'message': 'Token and new password are required'
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
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
        
        return Response({
            'message': 'Password reset successfully'
        }, status=status.HTTP_200_OK)
        
    except InvalidTokenError as e:
        return Response({
            'error': {
                'code': 'INVALID_TOKEN',
                'message': str(e)
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
        refresh_token = request.data.get('refresh_token', '')
        
        # Initialize use case
        jwt_service = get_jwt_service()
        token_blacklist_service = MockTokenBlacklistService()
        
        logout_usecase = LogoutUseCase(
            jwt_service=jwt_service,
            token_blacklist_service=token_blacklist_service
        )
        
        # Execute use case
        logout_usecase.logout(access_token, refresh_token)
        
        return Response({
            'success': True,
            'message': 'Logout successful'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
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
    """
    try:
        refresh_token = request.data.get('refresh_token', '')
        
        if not refresh_token:
            return Response({
                'error': {
                    'code': 'MISSING_REFRESH_TOKEN',
                    'message': 'Refresh token is required'
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
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
        auth_result = refresh_usecase.refresh_token(refresh_token)
        
        return Response({
            'success': True,
            'message': 'Token refreshed successfully',
            'user': user_to_dict(auth_result.user),
            'tokens': tokens_to_dict(auth_result.tokens)
        }, status=status.HTTP_200_OK)
        
    except InvalidTokenError as e:
        return Response({
            'error': {
                'code': 'INVALID_TOKEN',
                'message': str(e)
            }
        }, status=status.HTTP_401_UNAUTHORIZED)
    
    except Exception as e:
        return Response({
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'An unexpected error occurred'
            }
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
