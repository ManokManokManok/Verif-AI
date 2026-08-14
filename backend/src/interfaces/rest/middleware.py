from typing import Callable
from django.http import HttpRequest, HttpResponse
from rest_framework.request import Request
from rest_framework.response import Response
from ...infrastructure.jwt_service import JWTService
from ...infrastructure.mongodb.connection import get_mongo_client, get_database_name
from ...infrastructure.mongodb.repositories import MongoDBUserRepository
from ...domain.rbac import PermissionChecker
from ...domain.entities import AuthenticationError


class AuthenticationMiddleware:
    """
    Middleware to handle JWT authentication and set user context.
    """
    
    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]):
        self.get_response = get_response
    
    def __call__(self, request: HttpRequest) -> HttpResponse:
        # Convert to DRF Request for consistency
        drf_request = Request(request)
        
        # Extract token from Authorization header
        auth_header = drf_request.META.get('HTTP_AUTHORIZATION', '')
        if auth_header.startswith('Bearer '):
            token = auth_header[7:]  # Remove 'Bearer ' prefix
            
            try:
                # Verify token and extract user info
                jwt_service = self._get_jwt_service()
                payload = jwt_service.verify_access_token(token)
                
                # Set user context on request
                request.user_id = payload['user_id']
                request.user_email = payload['email']
                request.user_roles = payload.get('roles', [])
                request.user_permissions = payload.get('permissions', [])
                
                # Create permission checker with empty roles (will be populated if needed)
                request.permission_checker = PermissionChecker([])
                
            except Exception as e:
                # Invalid token - continue without authentication
                # Views that require authentication will handle this
                print(f"Authentication error: {e}")
        
        response = self.get_response(request)
       # ZAP finding: suppress server version disclosure
        response['Server'] = 'Verif-AI'
        return response
    
    def _get_jwt_service(self):
        """Get JWT service instance."""
        import os
        secret_key = os.getenv('JWT_SECRET_KEY')
        if not secret_key:
            raise ValueError("JWT_SECRET_KEY environment variable is not set")
        
        access_lifetime = int(os.getenv('JWT_ACCESS_TOKEN_LIFETIME', '900'))
        refresh_lifetime = int(os.getenv('JWT_REFRESH_TOKEN_LIFETIME', '604800'))
        
        return JWTService(secret_key, access_lifetime, refresh_lifetime)


def require_permission(permission: str, resource: str = None):
    """
    Decorator to require specific permission for a view.
    
    Args:
        permission: Permission required (e.g., 'create_user')
        resource: Optional resource (e.g., 'user')
    """
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            # Check if user is authenticated
            if not hasattr(request, 'user_id'):
                return Response({
                    'error': {
                        'code': 'AUTHENTICATION_REQUIRED',
                        'message': 'Authentication required'
                    }
                }, status=401)
            
            # Check permission using payload from JWT
            user_permissions = getattr(request, 'user_permissions', [])
            if permission not in user_permissions:
                return Response({
                    'error': {
                        'code': 'PERMISSION_DENIED',
                        'message': f'Permission "{permission}" required'
                    }
                }, status=403)
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def require_role(role_name: str):
    """
    Decorator to require specific role for a view.
    
    Args:
        role_name: Role required (e.g., 'admin')
    """
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            # Check if user is authenticated
            if not hasattr(request, 'user_id'):
                return Response({
                    'error': {
                        'code': 'AUTHENTICATION_REQUIRED',
                        'message': 'Authentication required'
                    }
                }, status=401)
            
            # Check role using payload from JWT
            user_roles = getattr(request, 'user_roles', [])
            if role_name not in user_roles:
                return Response({
                    'error': {
                        'code': 'PERMISSION_DENIED',
                        'message': f'Role "{role_name}" required'
                    }
                }, status=403)
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


# Convenience decorators
def admin_required(view_func):
    """Decorator to require admin role."""
    return require_role('admin')(view_func)


def moderator_required(view_func):
    """Decorator to require moderator role."""
    return require_role('moderator')(view_func)


def authenticated_required(view_func):
    """Decorator to require authentication (any role)."""
    def wrapper(request, *args, **kwargs):
        if not hasattr(request, 'user_id'):
            return Response({
                'error': {
                    'code': 'AUTHENTICATION_REQUIRED',
                    'message': 'Authentication required'
                }
            }, status=401)
        
        return view_func(request, *args, **kwargs)
    return wrapper
