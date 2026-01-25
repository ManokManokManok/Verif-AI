"""
Security Middleware Module

Implements authentication, rate limiting, and security headers following OWASP best practices:
- JWT authentication with token validation
- IP and user-based rate limiting
- Security headers (CSP, X-Frame-Options, etc.)
- Request logging for security auditing

OWASP References:
- https://cheatsheetseries.owasp.org/cheatsheets/REST_Security_Cheat_Sheet.html
- https://cheatsheetseries.owasp.org/cheatsheets/HTTP_Headers_Cheat_Sheet.html
"""

import logging
import time
from typing import Callable
from django.http import HttpRequest, HttpResponse, JsonResponse
from rest_framework.request import Request
from rest_framework.response import Response
from ...infrastructure.jwt_service import JWTService
from ...infrastructure.mongodb.connection import get_mongo_client, get_database_name
from ...infrastructure.mongodb.repositories import MongoDBUserRepository
from ...infrastructure.rate_limiter import (
    get_rate_limiter, get_client_ip, get_rate_limit_category
)
from ...domain.rbac import PermissionChecker
from ...domain.entities import AuthenticationError


# Configure security logger
security_logger = logging.getLogger('security')


class RateLimitMiddleware:
    """
    Middleware to enforce rate limiting on all endpoints.
    
    Implements both IP-based (for anonymous users) and user-based
    (for authenticated users) rate limiting with graceful 429 responses.
    
    Rate limits are configurable via environment variables.
    """
    
    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]):
        self.get_response = get_response
        self.rate_limiter = get_rate_limiter()
    
    def __call__(self, request: HttpRequest) -> HttpResponse:
        # Get client identifier (IP for anonymous, user_id for authenticated)
        client_ip = get_client_ip(request)
        user_id = getattr(request, 'user_id', None)
        
        # Use user_id if authenticated, otherwise IP
        identifier = f"user:{user_id}" if user_id else f"ip:{client_ip}"
        
        # Get rate limit category for this endpoint
        category = get_rate_limit_category(request.path, request.method)
        
        # Check rate limit
        is_limited, retry_after, headers = self.rate_limiter.is_rate_limited(
            identifier, category
        )
        
        if is_limited:
            # Log rate limit violation for security monitoring
            security_logger.warning(
                f"Rate limit exceeded: identifier={identifier}, "
                f"path={request.path}, category={category}, "
                f"retry_after={retry_after}"
            )
            
            # Return 429 Too Many Requests with proper headers
            response = JsonResponse({
                'error': {
                    'code': 'RATE_LIMIT_EXCEEDED',
                    'message': 'Too many requests. Please try again later.',
                    'retry_after': retry_after
                }
            }, status=429)
            
            # Add rate limit headers
            for header, value in headers.items():
                response[header] = value
            
            return response
        
        # Process request
        response = self.get_response(request)
        
        # Add rate limit headers to successful responses
        if headers:
            for header, value in headers.items():
                response[header] = value
        
        return response


class SecurityHeadersMiddleware:
    """
    Middleware to add security headers to all responses.
    
    Implements OWASP recommended security headers:
    - Content-Security-Policy
    - X-Content-Type-Options
    - X-Frame-Options
    - X-XSS-Protection
    - Referrer-Policy
    - Strict-Transport-Security (for HTTPS)
    - Cache-Control for sensitive responses
    """
    
    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]):
        self.get_response = get_response
    
    def __call__(self, request: HttpRequest) -> HttpResponse:
        response = self.get_response(request)
        
        # Prevent MIME type sniffing
        response['X-Content-Type-Options'] = 'nosniff'
        
        # Prevent clickjacking
        response['X-Frame-Options'] = 'DENY'
        
        # XSS protection (legacy but still useful)
        response['X-XSS-Protection'] = '1; mode=block'
        
        # Referrer policy - don't leak URLs
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Content Security Policy for API responses
        response['Content-Security-Policy'] = "default-src 'none'; frame-ancestors 'none'"
        
        # Permissions Policy - disable unnecessary browser features
        response['Permissions-Policy'] = (
            "accelerometer=(), camera=(), geolocation=(), gyroscope=(), "
            "magnetometer=(), microphone=(), payment=(), usb=()"
        )
        
        # For HTTPS deployments, add HSTS
        # Note: Only enable in production with proper HTTPS setup
        # response['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        
        # Prevent caching of sensitive API responses
        if request.path.startswith('/api/auth/') or request.path.startswith('/api/users/'):
            response['Cache-Control'] = 'no-store, no-cache, must-revalidate, private'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
        
        return response


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


class RequestLoggingMiddleware:
    """
    Middleware for security audit logging.
    
    Logs:
    - All authentication attempts
    - Failed authentication
    - Suspicious activity patterns
    - API access for audit trail
    
    OWASP: Logging and monitoring is critical for security incident detection.
    """
    
    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]):
        self.get_response = get_response
    
    def __call__(self, request: HttpRequest) -> HttpResponse:
        start_time = time.time()
        
        # Process request
        response = self.get_response(request)
        
        # Calculate response time
        duration_ms = (time.time() - start_time) * 1000
        
        # Log security-relevant requests
        if self._should_log(request, response):
            client_ip = get_client_ip(request)
            user_id = getattr(request, 'user_id', 'anonymous')
            
            log_data = {
                'ip': client_ip,
                'user_id': user_id,
                'method': request.method,
                'path': request.path,
                'status': response.status_code,
                'duration_ms': round(duration_ms, 2),
                'user_agent': request.META.get('HTTP_USER_AGENT', '')[:200]
            }
            
            # Log level based on response status
            if response.status_code >= 500:
                security_logger.error(f"Server error: {log_data}")
            elif response.status_code in (401, 403, 429):
                security_logger.warning(f"Security event: {log_data}")
            elif request.path.startswith('/api/auth/'):
                security_logger.info(f"Auth request: {log_data}")
        
        return response
    
    def _should_log(self, request: HttpRequest, response: HttpResponse) -> bool:
        """Determine if request should be logged."""
        # Always log auth endpoints
        if request.path.startswith('/api/auth/'):
            return True
        
        # Log errors
        if response.status_code >= 400:
            return True
        
        # Log admin actions
        if request.path.startswith('/admin/'):
            return True
        
        return False

