from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from bson import ObjectId

@api_view(['GET'])
def history_detail(request: Request, analysis_id: str) -> Response:
    """
    Get a single analysis result by its database id (for chat history details).
    Requires authentication (JWT in Authorization header).
    """
    try:
        user_id = None
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ', 1)[1]
            try:
                jwt_service = get_jwt_service()
                payload = jwt_service.verify_access_token(token)
                user_id = payload.get('user_id')
            except Exception as jwt_error:
                logger.warning(f"[JWT] Could not extract user_id for history detail: {jwt_error}")
        if not user_id:
            return Response({
                'error': {
                    'code': 'AUTHENTICATION_REQUIRED',
                    'message': 'Authentication required'
                }
            }, status=status.HTTP_401_UNAUTHORIZED)

        repository = get_analysis_repository()
        result = repository.get_by_id(analysis_id)
        if not result or str(result.user_id) != str(user_id):
            return Response({'error': {'code': 'NOT_FOUND', 'message': 'Analysis not found'}}, status=status.HTTP_404_NOT_FOUND)

        # Return all fields for the analysis result
        return Response({
            'id': result.id,
            'ref_id': result.ref_id,
            'title': result.scam_type or "Analysis Result",
            'description': result.summary or "",
            'summary': result.summary or "",
            'timestamp': result.created_at.isoformat() if result.created_at else None,
            'is_scam': result.is_scam,
            'scam_score': result.scam_score,
            'legit_score': result.legit_score,
            'label': result.label,
            'scam_type': result.scam_type,
            'type_confidence': result.type_confidence,
            'key_markers': result.key_markers,
            'message': result.message,
            # Add any other fields you want to expose
        }, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"[HISTORY_DETAIL] Error: {str(e)}", exc_info=True)
        return Response({
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'Failed to fetch analysis detail'
            }
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
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
from ...use_cases.ai.scam_detection import ScamDetectionUseCase
from ...use_cases.ai.llm_analysis import LLMAnalysisUseCase
from ...domain.services import (
    BCryptPasswordHasher, EmailValidator, PasswordValidator,
    TokenGenerator, MockEmailService
)
from ...domain.analysis_entities import AnalysisResult
from ...domain.scam_types import scam_types as SCAM_TYPES_MAP
from ...infrastructure.mongodb.connection import get_mongo_client, get_database_name
from ...infrastructure.mongodb.repositories import MongoDBUserRepository, MongoDBTokenRepository
from ...infrastructure.mongodb.analysis_repository import AnalysisResultRepository
from ...infrastructure.jwt_service import JWTService
from ...infrastructure.token_blacklist_service import MockTokenBlacklistService
from ...infrastructure.ai.loaders import load_multihead_model, load_gemma_model
from ...domain.entities import UserAlreadyExistsError, InvalidCredentialsError, UserNotFoundError

logger = logging.getLogger(__name__)

@api_view(['GET'])
def history(request: Request) -> Response:
    """
    Get the current user's detection analysis history (chat history).
    Requires authentication (JWT in Authorization header).
    """
    try:
        # Extract user_id from JWT (same as in detect_scam)
        user_id = None
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ', 1)[1]
            try:
                jwt_service = get_jwt_service()
                payload = jwt_service.verify_access_token(token)
                user_id = payload.get('user_id')
            except Exception as jwt_error:
                logger.warning(f"[JWT] Could not extract user_id for history: {jwt_error}")
        if not user_id:
            return Response({
                'error': {
                    'code': 'AUTHENTICATION_REQUIRED',
                    'message': 'Authentication required'
                }
            }, status=status.HTTP_401_UNAUTHORIZED)

        # Query analysis results for this user using repository method
        repository = get_analysis_repository()
        analysis_results = repository.get_by_user_id(user_id, limit=50)
        history = []
        for result in analysis_results:
            history.append({
                "id": result.id,
                "ref_id": result.ref_id,
                "title": result.scam_type or "Analysis Result",
                "description": result.summary or "",
                "timestamp": result.created_at.isoformat() if result.created_at else None,
                "is_scam": result.is_scam,
                "scam_score": result.scam_score,
                "legit_score": result.legit_score,
                "label": result.label,
                "scam_type": result.scam_type,
                "type_confidence": result.type_confidence,
                "key_markers": result.key_markers,
                "message": result.message,
            })
        return Response({"history": history}, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"[HISTORY] Error: {str(e)}", exc_info=True)
        return Response({
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'Failed to fetch chat history'
            }
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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


def get_analysis_repository():
    """Get analysis repository instance."""
    client = get_mongo_client()
    db_name = get_database_name()
    return AnalysisResultRepository(client, db_name)


def get_email_service():
    """Get email service instance."""
    return MockEmailService()


def user_to_dict(user) -> Dict[str, Any]:
    """Convert User entity to dictionary for API response."""
    return {
        'id': user.id,
        'email': user.email,
        'username': getattr(user, 'username', None),
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
        "password": "SecurePass123!"
    }
    """
    try:
        email = request.data.get('email', '').strip().lower()
        username = request.data.get('username', '').strip()
        password = request.data.get('password', '')
        
        if not email or not username or not password:
            return Response({
                'error': {
                    'code': 'MISSING_FIELDS',
                    'message': 'Email, username, and password are required'
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
        user = signup_usecase.execute(email, username, password)
        
        return Response({
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
        import traceback
        traceback.print_exc()  # Print full traceback to console
        return Response({
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': f'An unexpected error occurred: {str(e)}'
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


@api_view(['POST'])
@permission_classes([AllowAny])
def detect_scam(request: Request) -> Response:

    """
    Detect if a message is a scam using multi-head BERT + Gemma LLM analysis.
    
    Analysis results are automatically saved to the database for optional
    blockchain anchoring by administrators.
    
    Request body:
    {
        "message": "Text to analyze for scam indicators"
    }
    
    Response:
    {
        "message": "original user input text",
        "ref_id": "uuid-for-blockchain-anchoring",
        "is_anchored": false,
        "scam_score": 85.5,
        "legit_score": 14.5,
        "is_scam": true,
        "label": "Scam",
        "scam_type": "Banking Access & Payment",
        "type_confidence": 92.3,
        "summary": "Short explanation from Gemma",
        "key_markers": ["marker 1", "marker 2", ...]
    }
    """

    try:
        message = request.data.get('message', '').strip()

        # Extract user_id from JWT if present

        user_id = None
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ', 1)[1]
            try:
                jwt_service = get_jwt_service()
                payload = jwt_service.verify_access_token(token)
                logger.debug(f"[JWT PAYLOAD] {payload}")
                user_id = payload.get('user_id')
                logger.debug(f"[JWT user_id] value={user_id} type={type(user_id)}")
                logger.debug(f"[DEBUG] Extracted user_id from JWT: {user_id}")
            except Exception as jwt_error:
                logger.warning(f"[JWT] Could not extract user_id: {jwt_error}")

        if not message:
            return Response({
                'error': {
                    'code': 'MISSING_MESSAGE',
                    'message': 'Message is required for scam detection'
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        logger.info(f"[SCAM DETECTION] Analyzing message: {message[:100]}...")
        
        # Load BERT model (cached after first load)
        tokenizer, model, scam_types = load_multihead_model()
        
        if model is None or tokenizer is None:
            logger.error("[SCAM DETECTION] Model or tokenizer is None")
            return Response({
                'error': {
                    'code': 'MODEL_NOT_LOADED',
                    'message': 'Scam detection model is not available'
                }
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
        # Step 1: BERT Analysis
        scam_detection = ScamDetectionUseCase(tokenizer, model, scam_types)
        bert_result = scam_detection.detect(message)
        
        # Log BERT result
        logger.info(f"[BERT] Label: {bert_result['label']}")
        logger.info(f"[BERT] Scam Score: {bert_result['scam_score']:.2f}%")
        logger.info(f"[BERT] Legit Score: {bert_result['legit_score']:.2f}%")
        if bert_result['is_scam']:
            logger.info(f"[BERT] Scam Type: {bert_result['scam_type']}")
            logger.info(f"[BERT] Type Confidence: {bert_result['type_confidence']:.2f}%")
        
        # Step 2: Gemma LLM Analysis (only if scam detected)
        llm_result = {'summary': '', 'key_markers': []}
        
        if bert_result['is_scam']:
            try:
                llm = load_gemma_model()
                if llm is not None:
                    llm_analysis = LLMAnalysisUseCase(llm)
                    llm_result = llm_analysis.analyze(message, bert_result)
                    logger.info(f"[GEMMA] Summary: {llm_result['summary'][:100]}...")
                    logger.info(f"[GEMMA] Key Markers: {llm_result['key_markers']}")
                else:
                    logger.warning("[GEMMA] LLM not loaded, skipping analysis")
                    llm_result = {
                        'summary': f"This appears to be a {bert_result['scam_type']} scam attempt.",
                        'key_markers': ['Suspicious patterns detected']
                    }
            except Exception as llm_error:
                logger.error(f"[GEMMA] Error during LLM analysis: {str(llm_error)}")
                # Provide fallback if Gemma fails
                llm_result = {
                    'summary': f"This appears to be a {bert_result['scam_type']} scam attempt.",
                    'key_markers': ['Suspicious patterns detected']
                }
        else:
            llm_result = {
                'summary': 'This message appears to be legitimate with no scam indicators detected.',
                'key_markers': []
            }
        
        # Step 3: Save analysis result to database for blockchain anchoring
        import hashlib
        try:
            # Create message hash for lookup (privacy: we don't store raw message)
            message_hash = hashlib.sha256(message.encode('utf-8')).hexdigest()

            # Map scam_type string to scam_class integer
            scam_class = -1  # Default: not scam
            if bert_result['is_scam'] and bert_result.get('scam_type'):
                # Find the scam_class from the type name
                for class_id, type_name in SCAM_TYPES_MAP.items():
                    if type_name == bert_result['scam_type']:
                        scam_class = class_id
                        break

            # Convert confidence to basis points (0-10000)
            # type_confidence is 0-100, scam_score is 0-100
            if bert_result['is_scam']:
                confidence_bps = int(bert_result.get('type_confidence', 0) * 100)
            else:
                confidence_bps = int(bert_result.get('legit_score', 0) * 100)

            # Ensure user_account is defined in this scope
            user_account = None
            if user_id:
                try:
                    user_repo = get_user_repository()
                    user_account = user_repo.get_by_id(user_id)
                except Exception as user_lookup_error:
                    logger.warning(f"[USER] Could not fetch user_account for user_id={user_id}: {user_lookup_error}")

            # Create analysis result entity (store full details for authenticated users only)
            # Always set user_id from user_account.id if available, else None
            resolved_user_id = str(user_account.id) if user_account and getattr(user_account, 'id', None) else None
            analysis = AnalysisResult.create(
                scam_class=scam_class,
                scam_type=bert_result.get('scam_type') or 'Not Scam',
                confidence_bps=confidence_bps,
                is_scam=bert_result['is_scam'],
                analyzer_type='bert',
                analyzer_version='v1',
                message_hash=message_hash,
                user_id=resolved_user_id,
                message=message if resolved_user_id else None,
                scam_score=bert_result.get('scam_score'),
                legit_score=bert_result.get('legit_score'),
                label=bert_result.get('label'),
                type_confidence=bert_result.get('type_confidence'),
                summary=llm_result.get('summary'),
                key_markers=llm_result.get('key_markers'),
            )

            # Log the analysis entity before saving
            logger.debug(f"[DEBUG] AnalysisResult entity before save: {{'ref_id': {analysis.ref_id}, 'user_id': {analysis.user_id}, 'scam_class': {analysis.scam_class}, 'scam_type': {analysis.scam_type}, 'confidence_bps': {analysis.confidence_bps}, 'is_scam': {analysis.is_scam}, 'analyzer_type': {analysis.analyzer_type}, 'analyzer_version': {analysis.analyzer_version}, 'message_hash': {analysis.message_hash}, 'created_at': {analysis.created_at}}}")

            # Save to database
            repository = get_analysis_repository()
            saved_analysis = repository.save(analysis)

            # Log the document as it will be sent to MongoDB
            doc_for_db = repository._entity_to_document(analysis)
            logger.debug(f"[DEBUG] Document sent to MongoDB: {doc_for_db}")

            logger.info(f"[DB] Analysis saved: ref_id={saved_analysis.ref_id}")

            # Include ref_id in response for blockchain anchoring
            ref_id = saved_analysis.ref_id
            is_anchored = saved_analysis.is_anchored

        except Exception as db_error:
            logger.error(f"[DB] Error saving analysis: {str(db_error)}")
            # Don't fail the request if DB save fails
            ref_id = None
            is_anchored = False
        
        # Combine results
        combined_result = {
            'message': message,  # Include original message for display
            'ref_id': ref_id,  # For blockchain anchoring
            'is_anchored': is_anchored,  # Blockchain status
            'created_at': (saved_analysis.created_at.isoformat() if saved_analysis and hasattr(saved_analysis, 'created_at') and saved_analysis.created_at else None),
            **bert_result,
            **llm_result,
            # Debug info for browser console
            'jwt_debug': {
                'payload': payload if 'payload' in locals() else None,
                'user_id_value': user_id if 'user_id' in locals() else None,
                'user_id_type': str(type(user_id)) if 'user_id' in locals() else None,
            }
        }
        
        logger.info("=" * 80)
        
        return Response(combined_result, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"[SCAM DETECTION] Error: {str(e)}", exc_info=True)
        return Response({
            'error': {
                'code': 'DETECTION_ERROR',
                'message': f'Error during scam detection: {str(e)}'
            }
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
