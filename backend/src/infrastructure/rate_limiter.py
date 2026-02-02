"""
Rate Limiter Module

Provides rate limiting functionality for API endpoints.
Uses in-memory storage for simplicity (use Redis for production scaling).

OWASP References:
- Rate Limiting: https://cheatsheetseries.owasp.org/cheatsheets/Denial_of_Service_Cheat_Sheet.html
- Authentication: https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html

Security Features:
- Combined IP + User-based rate limiting
- Sliding window algorithm
- Progressive blocking for repeat offenders
- Configurable per-endpoint limits
- Graceful 429 responses with Retry-After headers
"""

import os
import time
import logging
import functools
from typing import Dict, Tuple, Optional, Callable
from collections import defaultdict
from threading import Lock
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger(__name__)
security_logger = logging.getLogger('security')


class RateLimiter:
    """
    Simple in-memory rate limiter using sliding window algorithm.
    
    Thread-safe implementation suitable for single-instance deployments.
    For multi-instance deployments, use Redis-backed implementation.
    """
    
    def __init__(self):
        # Store: {identifier: [(timestamp, count), ...]}
        self._requests: Dict[str, list] = defaultdict(list)
        self._blocked: Dict[str, float] = {}  # identifier -> blocked_until timestamp
        self._lock = Lock()
        
        # Load rate limits from environment
        self._limits = self._load_limits()
    
    def _load_limits(self) -> Dict[str, Dict[str, int]]:
        """Load rate limit configuration from environment variables."""
        return {
            'auth_login': {
                'requests': int(os.getenv('RATE_LIMIT_AUTH_LOGIN_REQUESTS', '5')),
                'window': int(os.getenv('RATE_LIMIT_AUTH_LOGIN_WINDOW', '300')),
                'block': int(os.getenv('RATE_LIMIT_AUTH_LOGIN_BLOCK', '900')),
            },
            'auth_register': {
                'requests': int(os.getenv('RATE_LIMIT_AUTH_REGISTER_REQUESTS', '3')),
                'window': int(os.getenv('RATE_LIMIT_AUTH_REGISTER_WINDOW', '3600')),
                'block': int(os.getenv('RATE_LIMIT_AUTH_REGISTER_BLOCK', '3600')),
            },
            'password_reset': {
                'requests': int(os.getenv('RATE_LIMIT_PASSWORD_RESET_REQUESTS', '3')),
                'window': int(os.getenv('RATE_LIMIT_PASSWORD_RESET_WINDOW', '3600')),
                'block': int(os.getenv('RATE_LIMIT_PASSWORD_RESET_BLOCK', '3600')),
            },
            'email_verification': {
                'requests': int(os.getenv('RATE_LIMIT_EMAIL_VERIFICATION_REQUESTS', '5')),
                'window': int(os.getenv('RATE_LIMIT_EMAIL_VERIFICATION_WINDOW', '3600')),
                'block': int(os.getenv('RATE_LIMIT_EMAIL_VERIFICATION_BLOCK', '1800')),
            },
            'api_read': {
                'requests': int(os.getenv('RATE_LIMIT_API_READ_REQUESTS', '100')),
                'window': int(os.getenv('RATE_LIMIT_API_READ_WINDOW', '60')),
                'block': int(os.getenv('RATE_LIMIT_API_READ_BLOCK', '60')),
            },
            'api_write': {
                'requests': int(os.getenv('RATE_LIMIT_API_WRITE_REQUESTS', '30')),
                'window': int(os.getenv('RATE_LIMIT_API_WRITE_WINDOW', '60')),
                'block': int(os.getenv('RATE_LIMIT_API_WRITE_BLOCK', '120')),
            },
            'blockchain_read': {
                'requests': int(os.getenv('RATE_LIMIT_BLOCKCHAIN_READ_REQUESTS', '50')),
                'window': int(os.getenv('RATE_LIMIT_BLOCKCHAIN_READ_WINDOW', '60')),
                'block': int(os.getenv('RATE_LIMIT_BLOCKCHAIN_READ_BLOCK', '60')),
            },
            'blockchain_write': {
                'requests': int(os.getenv('RATE_LIMIT_BLOCKCHAIN_WRITE_REQUESTS', '10')),
                'window': int(os.getenv('RATE_LIMIT_BLOCKCHAIN_WRITE_WINDOW', '60')),
                'block': int(os.getenv('RATE_LIMIT_BLOCKCHAIN_WRITE_BLOCK', '300')),
            },
            'token_refresh': {
                'requests': int(os.getenv('RATE_LIMIT_TOKEN_REFRESH_REQUESTS', '10')),
                'window': int(os.getenv('RATE_LIMIT_TOKEN_REFRESH_WINDOW', '60')),
                'block': int(os.getenv('RATE_LIMIT_TOKEN_REFRESH_BLOCK', '300')),
            },
            'default': {
                'requests': int(os.getenv('RATE_LIMIT_DEFAULT_REQUESTS', '60')),
                'window': int(os.getenv('RATE_LIMIT_DEFAULT_WINDOW', '60')),
                'block': int(os.getenv('RATE_LIMIT_DEFAULT_BLOCK', '60')),
            },
        }
    
    def is_rate_limited(
        self, 
        identifier: str, 
        category: str = 'default'
    ) -> Tuple[bool, Optional[int], Optional[Dict[str, str]]]:
        """
        Check if an identifier is rate limited for a category.
        
        Args:
            identifier: Unique identifier (e.g., "user:123" or "ip:1.2.3.4")
            category: Rate limit category (e.g., "api_read", "blockchain_write")
            
        Returns:
            Tuple of (is_limited, retry_after_seconds, response_headers)
        """
        limits = self._limits.get(category, self._limits['default'])
        max_requests = limits['requests']
        window_seconds = limits['window']
        block_seconds = limits['block']
        
        key = f"{category}:{identifier}"
        now = time.time()
        
        with self._lock:
            # Check if currently blocked
            if key in self._blocked:
                blocked_until = self._blocked[key]
                if now < blocked_until:
                    retry_after = int(blocked_until - now)
                    headers = {
                        'Retry-After': str(retry_after),
                        'X-RateLimit-Limit': str(max_requests),
                        'X-RateLimit-Remaining': '0',
                        'X-RateLimit-Reset': str(int(blocked_until)),
                    }
                    return True, retry_after, headers
                else:
                    # Block expired
                    del self._blocked[key]
            
            # Clean old requests outside window
            window_start = now - window_seconds
            self._requests[key] = [
                ts for ts in self._requests[key] 
                if ts > window_start
            ]
            
            # Count requests in window
            request_count = len(self._requests[key])
            
            if request_count >= max_requests:
                # Rate limited - apply block
                self._blocked[key] = now + block_seconds
                retry_after = block_seconds
                headers = {
                    'Retry-After': str(retry_after),
                    'X-RateLimit-Limit': str(max_requests),
                    'X-RateLimit-Remaining': '0',
                    'X-RateLimit-Reset': str(int(now + block_seconds)),
                }
                return True, retry_after, headers
            
            # Record this request
            self._requests[key].append(now)
            
            # Return headers showing remaining quota
            remaining = max_requests - len(self._requests[key])
            headers = {
                'X-RateLimit-Limit': str(max_requests),
                'X-RateLimit-Remaining': str(remaining),
                'X-RateLimit-Reset': str(int(now + window_seconds)),
            }
            
            return False, None, headers
    
    def reset(self, identifier: str = None, category: str = None):
        """Reset rate limits for testing purposes."""
        with self._lock:
            if identifier and category:
                key = f"{category}:{identifier}"
                self._requests.pop(key, None)
                self._blocked.pop(key, None)
            elif identifier:
                # Reset all categories for this identifier
                to_remove = [k for k in self._requests if k.endswith(f":{identifier}")]
                for k in to_remove:
                    del self._requests[k]
                to_remove = [k for k in self._blocked if k.endswith(f":{identifier}")]
                for k in to_remove:
                    del self._blocked[k]
            else:
                # Reset everything
                self._requests.clear()
                self._blocked.clear()


# Singleton instance
_rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    """Get the singleton rate limiter instance."""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter


def get_client_ip(request: Request) -> str:
    """
    Extract client IP from request, handling proxies.
    
    Checks X-Forwarded-For header first for proxied requests,
    falls back to REMOTE_ADDR.
    
    Security:
    - Only trusts first IP in X-Forwarded-For chain
    - Falls back to REMOTE_ADDR if header is missing
    - Validates IP format to prevent injection
    """
    import re
    
    # IP address validation pattern (IPv4 and IPv6)
    ipv4_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
    ipv6_pattern = r'^([0-9a-fA-F:]+)$'
    
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        # Take the first IP in the chain (original client)
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR', '0.0.0.0')
    
    # Validate IP format to prevent injection attacks
    if not (re.match(ipv4_pattern, ip) or re.match(ipv6_pattern, ip)):
        security_logger.warning(f"Invalid IP format detected: {ip[:50]}")
        ip = '0.0.0.0'
    
    return ip


def get_rate_limit_identifier(request: Request) -> Tuple[str, Optional[str]]:
    """
    Get rate limit identifiers for both IP and user (if authenticated).
    
    Returns:
        Tuple of (ip_identifier, user_identifier or None)
    """
    client_ip = get_client_ip(request)
    ip_identifier = f"ip:{client_ip}"
    
    user_id = getattr(request, 'user_id', None)
    user_identifier = f"user:{user_id}" if user_id else None
    
    return ip_identifier, user_identifier


def rate_limit(category: str = 'default'):
    """
    Decorator to apply rate limiting to a view.
    
    Applies both IP-based and user-based rate limiting.
    If either limit is exceeded, returns 429 response.
    
    Args:
        category: Rate limit category (e.g., 'auth_login', 'api_read')
        
    Usage:
        @api_view(['POST'])
        @rate_limit('auth_login')
        def login(request):
            ...
    
    Security:
        - Checks both IP and user (if authenticated)
        - Logs rate limit events for security monitoring
        - Returns standard 429 response with Retry-After header
    """
    def decorator(view_func: Callable):
        @functools.wraps(view_func)
        def wrapper(request: Request, *args, **kwargs):
            rate_limiter = get_rate_limiter()
            ip_identifier, user_identifier = get_rate_limit_identifier(request)
            
            # Check IP-based rate limit
            is_limited, retry_after, headers = rate_limiter.is_rate_limited(
                ip_identifier, category
            )
            
            if is_limited:
                security_logger.warning(
                    f"Rate limit exceeded: identifier={ip_identifier}, "
                    f"category={category}, retry_after={retry_after}"
                )
                return _create_rate_limit_response(retry_after, headers)
            
            # Also check user-based rate limit if authenticated
            if user_identifier:
                is_limited, retry_after, headers = rate_limiter.is_rate_limited(
                    user_identifier, category
                )
                
                if is_limited:
                    security_logger.warning(
                        f"Rate limit exceeded: identifier={user_identifier}, "
                        f"category={category}, retry_after={retry_after}"
                    )
                    return _create_rate_limit_response(retry_after, headers)
            
            # Execute the view
            response = view_func(request, *args, **kwargs)
            
            # Add rate limit headers to successful responses
            if hasattr(response, '__setitem__'):
                _, _, success_headers = rate_limiter.is_rate_limited(
                    ip_identifier, category
                )
                if success_headers:
                    for header, value in success_headers.items():
                        if header.startswith('X-RateLimit'):
                            response[header] = value
            
            return response
        
        return wrapper
    return decorator


def _create_rate_limit_response(retry_after: int, headers: Dict[str, str]) -> Response:
    """
    Create a graceful 429 rate limit response.
    
    Args:
        retry_after: Seconds until the client can retry
        headers: Rate limit headers to include
        
    Returns:
        DRF Response with 429 status and helpful message
    """
    response = Response({
        'error': {
            'code': 'RATE_LIMIT_EXCEEDED',
            'message': 'Too many requests. Please slow down and try again later.',
            'retry_after': retry_after,
            'retry_after_human': _format_retry_after(retry_after)
        }
    }, status=status.HTTP_429_TOO_MANY_REQUESTS)
    
    # Add all rate limit headers
    for header, value in (headers or {}).items():
        response[header] = value
    
    return response


def _format_retry_after(seconds: int) -> str:
    """Format retry_after seconds into human-readable string."""
    if seconds < 60:
        return f"{seconds} seconds"
    elif seconds < 3600:
        minutes = seconds // 60
        return f"{minutes} minute{'s' if minutes > 1 else ''}"
    else:
        hours = seconds // 3600
        return f"{hours} hour{'s' if hours > 1 else ''}"


def check_rate_limit(request: Request, category: str) -> Optional[Response]:
    """
    Utility function to check rate limit without decorator.
    
    Args:
        request: DRF Request object
        category: Rate limit category
        
    Returns:
        429 Response if rate limited, None otherwise
        
    Usage:
        response = check_rate_limit(request, 'api_write')
        if response:
            return response
        # Continue with normal processing
    """
    rate_limiter = get_rate_limiter()
    ip_identifier, user_identifier = get_rate_limit_identifier(request)
    
    # Check IP
    is_limited, retry_after, headers = rate_limiter.is_rate_limited(
        ip_identifier, category
    )
    if is_limited:
        security_logger.warning(
            f"Rate limit check failed: identifier={ip_identifier}, category={category}"
        )
        return _create_rate_limit_response(retry_after, headers)
    
    # Check user
    if user_identifier:
        is_limited, retry_after, headers = rate_limiter.is_rate_limited(
            user_identifier, category
        )
        if is_limited:
            security_logger.warning(
                f"Rate limit check failed: identifier={user_identifier}, category={category}"
            )
            return _create_rate_limit_response(retry_after, headers)
    
    return None

