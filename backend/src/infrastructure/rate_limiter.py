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
import re
import time
import logging
import functools
from typing import Dict, Tuple, Optional, Callable
from collections import defaultdict
from threading import Lock
from django.http import JsonResponse
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger(__name__)
security_logger = logging.getLogger('security')


def _use_mongo_backend() -> bool:
    """RATE_LIMIT_BACKEND=mongo shares counters across instances (needed on AWS Lambda)."""
    return os.getenv('RATE_LIMIT_BACKEND', 'memory').strip().lower() == 'mongo'


class RateLimiter:
    """
    Sliding window rate limiter.

    Counters live in memory by default (single instance). Set
    RATE_LIMIT_BACKEND=mongo to store them in MongoDB for multi-instance
    deployments such as AWS Lambda.
    """
    
    def __init__(self):
        self._mongo_collection = None
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
            'data_export': {
                'requests': int(os.getenv('RATE_LIMIT_DATA_EXPORT_REQUESTS', '1')),
                'window': int(os.getenv('RATE_LIMIT_DATA_EXPORT_WINDOW', '10800')),
                'block': int(os.getenv('RATE_LIMIT_DATA_EXPORT_BLOCK', '10800')),
            },
            'token_refresh': {
                'requests': int(os.getenv('RATE_LIMIT_TOKEN_REFRESH_REQUESTS', '10')),
                'window': int(os.getenv('RATE_LIMIT_TOKEN_REFRESH_WINDOW', '60')),
                'block': int(os.getenv('RATE_LIMIT_TOKEN_REFRESH_BLOCK', '300')),
            },
            'mfa_send': {
                'requests': int(os.getenv('RATE_LIMIT_MFA_SEND_REQUESTS', '3')),
                'window': int(os.getenv('RATE_LIMIT_MFA_SEND_WINDOW', '300')),
                'block': int(os.getenv('RATE_LIMIT_MFA_SEND_BLOCK', '600')),
            },
            'mfa_verify': {
                'requests': int(os.getenv('RATE_LIMIT_MFA_VERIFY_REQUESTS', '5')),
                'window': int(os.getenv('RATE_LIMIT_MFA_VERIFY_WINDOW', '300')),
                'block': int(os.getenv('RATE_LIMIT_MFA_VERIFY_BLOCK', '900')),
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
            category: Rate limit category (e.g., "api_read")
            
        Returns:
            Tuple of (is_limited, retry_after_seconds, response_headers)
        """
        if os.getenv('RATE_LIMIT_ENABLED', 'true').strip().lower() in ('false', '0', 'no', 'off'):
            return False, None, {}

        limits = self._limits.get(category, self._limits['default'])
        max_requests = limits['requests']
        window_seconds = limits['window']
        block_seconds = limits['block']
        
        key = f"{category}:{identifier}"
        now = time.time()

        if _use_mongo_backend():
            try:
                return self._is_rate_limited_mongo(key, max_requests, window_seconds, block_seconds, now)
            except Exception as exc:
                # Fail open: a database hiccup must not lock every user out.
                security_logger.error(f"Mongo rate limiter unavailable, allowing request: {type(exc).__name__}")
                return False, None, {}
        
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

    def _get_mongo_collection(self):
        """Shared collection for all instances; a TTL index removes stale counters."""
        if self._mongo_collection is None:
            from .mongodb.connection import get_mongo_client, get_database_name
            collection = get_mongo_client()[get_database_name()]['rate_limits']
            collection.create_index('expires_at', expireAfterSeconds=0)
            self._mongo_collection = collection
        return self._mongo_collection

    def _is_rate_limited_mongo(
        self, key: str, max_requests: int, window_seconds: int, block_seconds: int, now: float
    ) -> Tuple[bool, Optional[int], Optional[Dict[str, str]]]:
        """Sliding window + progressive block, stored in MongoDB so every instance shares it."""
        from datetime import datetime, timezone
        from pymongo import ReturnDocument

        collection = self._get_mongo_collection()
        doc = collection.find_one_and_update(
            {'_id': key},
            {'$pull': {'ts': {'$lte': now - window_seconds}}},
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )

        blocked_until = doc.get('blocked_until') or 0
        if now < blocked_until:
            retry_after = int(blocked_until - now)
            return True, retry_after, {
                'Retry-After': str(retry_after),
                'X-RateLimit-Limit': str(max_requests),
                'X-RateLimit-Remaining': '0',
                'X-RateLimit-Reset': str(int(blocked_until)),
            }

        timestamps = doc.get('ts', [])
        if len(timestamps) >= max_requests:
            blocked_until = now + block_seconds
            collection.update_one({'_id': key}, {'$set': {
                'blocked_until': blocked_until,
                'expires_at': datetime.fromtimestamp(blocked_until + window_seconds, tz=timezone.utc),
            }})
            return True, block_seconds, {
                'Retry-After': str(block_seconds),
                'X-RateLimit-Limit': str(max_requests),
                'X-RateLimit-Remaining': '0',
                'X-RateLimit-Reset': str(int(blocked_until)),
            }

        collection.update_one({'_id': key}, {
            '$push': {'ts': now},
            '$set': {'expires_at': datetime.fromtimestamp(now + max(window_seconds, block_seconds), tz=timezone.utc)},
        })
        return False, None, {
            'X-RateLimit-Limit': str(max_requests),
            'X-RateLimit-Remaining': str(max_requests - len(timestamps) - 1),
            'X-RateLimit-Reset': str(int(now + window_seconds)),
        }
    
    def reset(self, identifier: str = None, category: str = None):
        """Reset rate limits for testing purposes."""
        if _use_mongo_backend():
            collection = self._get_mongo_collection()
            if identifier and category:
                collection.delete_one({'_id': f"{category}:{identifier}"})
            elif identifier:
                collection.delete_many({'_id': {'$regex': f":{re.escape(identifier)}$"}})
            else:
                collection.delete_many({})
            return
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


def _trusted_proxy_hops() -> int:
    """Number of trusted proxies in front of the app (TRUSTED_PROXY_HOPS; 0 = legacy first-entry)."""
    try:
        return max(int(os.getenv('TRUSTED_PROXY_HOPS', '0')), 0)
    except ValueError:
        return 0


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
        hops = _trusted_proxy_hops()
        chain = [part.strip() for part in x_forwarded_for.split(',') if part.strip()]
        if hops > 0 and chain:
            # Each trusted proxy appends the address it saw, so count from the right;
            # anything further left is client-supplied and can be spoofed.
            ip = chain[max(len(chain) - hops, 0)]
        else:
            ip = chain[0] if chain else request.META.get('REMOTE_ADDR', '0.0.0.0')
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
                return _create_rate_limit_response(retry_after, headers, not isinstance(request, Request))
            
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
                    return _create_rate_limit_response(retry_after, headers, not isinstance(request, Request))
            
            # Execute the view
            response = view_func(request, *args, **kwargs)
            
            # Reuse the quota headers from the initial check; checking again would
            # count a successful request twice against the sliding window.
            if hasattr(response, '__setitem__'):
                if headers:
                    for header, value in headers.items():
                        if header.startswith('X-RateLimit'):
                            response[header] = value
            
            return response
        
        return wrapper
    return decorator


def _create_rate_limit_response(retry_after: int, headers: Dict[str, str], as_json: bool = False):
    """
    Create a graceful 429 rate limit response.
    
    Args:
        retry_after: Seconds until the client can retry
        headers: Rate limit headers to include
        
    Returns:
        DRF Response with 429 status and helpful message
    """
    payload = {
        'error': {
            'code': 'RATE_LIMIT_EXCEEDED',
            'message': 'Too many requests. Please slow down and try again later.',
            'retry_after': retry_after,
            'retry_after_human': _format_retry_after(retry_after)
        }
    }
    # Plain Django views have no DRF renderer, so a DRF Response would fail to render.
    if as_json:
        response = JsonResponse(payload, status=status.HTTP_429_TOO_MANY_REQUESTS)
    else:
        response = Response(payload, status=status.HTTP_429_TOO_MANY_REQUESTS)
    
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
        return _create_rate_limit_response(retry_after, headers, not isinstance(request, Request))
    
    # Check user
    if user_identifier:
        is_limited, retry_after, headers = rate_limiter.is_rate_limited(
            user_identifier, category
        )
        if is_limited:
            security_logger.warning(
                f"Rate limit check failed: identifier={user_identifier}, category={category}"
            )
            return _create_rate_limit_response(retry_after, headers, not isinstance(request, Request))
    
    return None
