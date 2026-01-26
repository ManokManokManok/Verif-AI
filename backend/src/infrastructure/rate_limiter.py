"""
Rate Limiting Service for API Endpoints

Implements IP-based and user-based rate limiting following OWASP best practices:
- Sliding window rate limiting algorithm
- Configurable limits per endpoint category
- Graceful 429 responses with Retry-After headers
- Support for both anonymous (IP) and authenticated (user) rate limits

OWASP Reference: https://cheatsheetseries.owasp.org/cheatsheets/Denial_of_Service_Cheat_Sheet.html
"""

import time
import hashlib
from collections import defaultdict
from dataclasses import dataclass
from typing import Optional, Dict, Tuple
from threading import Lock
import os


@dataclass
class RateLimitConfig:
    """
    Configuration for rate limiting rules.
    
    Attributes:
        requests: Maximum number of requests allowed
        window_seconds: Time window in seconds
        block_duration_seconds: How long to block after limit exceeded
    """
    requests: int
    window_seconds: int
    block_duration_seconds: int = 60


# Sensible default rate limits per endpoint category (OWASP recommended)
# These can be overridden via environment variables
DEFAULT_RATE_LIMITS = {
    # Authentication endpoints - more restrictive to prevent brute force
    'auth_login': RateLimitConfig(
        requests=int(os.getenv('RATE_LIMIT_AUTH_LOGIN_REQUESTS', '5')),
        window_seconds=int(os.getenv('RATE_LIMIT_AUTH_LOGIN_WINDOW', '300')),  # 5 requests per 5 minutes
        block_duration_seconds=int(os.getenv('RATE_LIMIT_AUTH_LOGIN_BLOCK', '900'))  # 15 min block
    ),
    'auth_register': RateLimitConfig(
        requests=int(os.getenv('RATE_LIMIT_AUTH_REGISTER_REQUESTS', '3')),
        window_seconds=int(os.getenv('RATE_LIMIT_AUTH_REGISTER_WINDOW', '3600')),  # 3 per hour
        block_duration_seconds=int(os.getenv('RATE_LIMIT_AUTH_REGISTER_BLOCK', '3600'))
    ),
    'password_reset': RateLimitConfig(
        requests=int(os.getenv('RATE_LIMIT_PASSWORD_RESET_REQUESTS', '3')),
        window_seconds=int(os.getenv('RATE_LIMIT_PASSWORD_RESET_WINDOW', '3600')),  # 3 per hour
        block_duration_seconds=int(os.getenv('RATE_LIMIT_PASSWORD_RESET_BLOCK', '3600'))
    ),
    'email_verification': RateLimitConfig(
        requests=int(os.getenv('RATE_LIMIT_EMAIL_VERIFICATION_REQUESTS', '5')),
        window_seconds=int(os.getenv('RATE_LIMIT_EMAIL_VERIFICATION_WINDOW', '3600')),  # 5 per hour
        block_duration_seconds=int(os.getenv('RATE_LIMIT_EMAIL_VERIFICATION_BLOCK', '1800'))
    ),
    # General API endpoints - less restrictive
    'api_read': RateLimitConfig(
        requests=int(os.getenv('RATE_LIMIT_API_READ_REQUESTS', '100')),
        window_seconds=int(os.getenv('RATE_LIMIT_API_READ_WINDOW', '60')),  # 100 per minute
        block_duration_seconds=int(os.getenv('RATE_LIMIT_API_READ_BLOCK', '60'))
    ),
    'api_write': RateLimitConfig(
        requests=int(os.getenv('RATE_LIMIT_API_WRITE_REQUESTS', '30')),
        window_seconds=int(os.getenv('RATE_LIMIT_API_WRITE_WINDOW', '60')),  # 30 per minute
        block_duration_seconds=int(os.getenv('RATE_LIMIT_API_WRITE_BLOCK', '120'))
    ),
    # Token refresh - moderate limit
    'token_refresh': RateLimitConfig(
        requests=int(os.getenv('RATE_LIMIT_TOKEN_REFRESH_REQUESTS', '10')),
        window_seconds=int(os.getenv('RATE_LIMIT_TOKEN_REFRESH_WINDOW', '60')),  # 10 per minute
        block_duration_seconds=int(os.getenv('RATE_LIMIT_TOKEN_REFRESH_BLOCK', '300'))
    ),
    # Blockchain endpoints - restrictive for write, moderate for read
    'blockchain_write': RateLimitConfig(
        requests=int(os.getenv('RATE_LIMIT_BLOCKCHAIN_WRITE_REQUESTS', '10')),
        window_seconds=int(os.getenv('RATE_LIMIT_BLOCKCHAIN_WRITE_WINDOW', '60')),  # 10 per minute
        block_duration_seconds=int(os.getenv('RATE_LIMIT_BLOCKCHAIN_WRITE_BLOCK', '300'))  # 5 min block
    ),
    'blockchain_read': RateLimitConfig(
        requests=int(os.getenv('RATE_LIMIT_BLOCKCHAIN_READ_REQUESTS', '30')),
        window_seconds=int(os.getenv('RATE_LIMIT_BLOCKCHAIN_READ_WINDOW', '60')),  # 30 per minute
        block_duration_seconds=int(os.getenv('RATE_LIMIT_BLOCKCHAIN_READ_BLOCK', '120'))
    ),
    # Default fallback
    'default': RateLimitConfig(
        requests=int(os.getenv('RATE_LIMIT_DEFAULT_REQUESTS', '60')),
        window_seconds=int(os.getenv('RATE_LIMIT_DEFAULT_WINDOW', '60')),  # 60 per minute
        block_duration_seconds=int(os.getenv('RATE_LIMIT_DEFAULT_BLOCK', '60'))
    ),
}


class SlidingWindowRateLimiter:
    """
    Thread-safe sliding window rate limiter implementation.
    
    Uses in-memory storage by default. For production with multiple
    workers/servers, replace with Redis-based implementation.
    
    Security considerations:
    - Uses hashed identifiers to prevent key enumeration
    - Implements both IP and user-based limiting
    - Provides Retry-After header support
    """
    
    def __init__(self):
        # Storage: {hashed_key: [(timestamp, count), ...]}
        self._requests: Dict[str, list] = defaultdict(list)
        # Blocked keys: {hashed_key: unblock_timestamp}
        self._blocked: Dict[str, float] = {}
        self._lock = Lock()
    
    def _hash_key(self, identifier: str, endpoint: str) -> str:
        """
        Create a hashed key for rate limiting storage.
        
        Hashing prevents potential enumeration attacks and 
        ensures consistent key lengths.
        """
        raw = f"{identifier}:{endpoint}"
        return hashlib.sha256(raw.encode()).hexdigest()[:32]
    
    def _clean_old_requests(self, key: str, window_seconds: int) -> None:
        """Remove requests outside the current time window."""
        cutoff = time.time() - window_seconds
        self._requests[key] = [
            req for req in self._requests[key] 
            if req[0] > cutoff
        ]
    
    def _clean_expired_blocks(self) -> None:
        """Remove expired blocks (called periodically)."""
        current_time = time.time()
        expired = [
            key for key, unblock_time in self._blocked.items() 
            if current_time > unblock_time
        ]
        for key in expired:
            del self._blocked[key]
    
    def is_rate_limited(
        self,
        identifier: str,
        endpoint_category: str,
        config: Optional[RateLimitConfig] = None
    ) -> Tuple[bool, Optional[int], Optional[Dict]]:
        """
        Check if a request should be rate limited.
        
        Args:
            identifier: IP address or user ID
            endpoint_category: Category of the endpoint (e.g., 'auth_login')
            config: Optional custom rate limit configuration
        
        Returns:
            Tuple of (is_limited, retry_after_seconds, headers_dict)
            - is_limited: True if request should be blocked
            - retry_after_seconds: Seconds until rate limit resets (if limited)
            - headers_dict: Rate limit headers to include in response
        """
        if config is None:
            config = DEFAULT_RATE_LIMITS.get(
                endpoint_category, 
                DEFAULT_RATE_LIMITS['default']
            )
        
        key = self._hash_key(identifier, endpoint_category)
        current_time = time.time()
        
        with self._lock:
            # Clean up periodically
            if len(self._blocked) > 1000:
                self._clean_expired_blocks()
            
            # Check if currently blocked
            if key in self._blocked:
                unblock_time = self._blocked[key]
                if current_time < unblock_time:
                    retry_after = int(unblock_time - current_time) + 1
                    return True, retry_after, {
                        'X-RateLimit-Limit': str(config.requests),
                        'X-RateLimit-Remaining': '0',
                        'X-RateLimit-Reset': str(int(unblock_time)),
                        'Retry-After': str(retry_after)
                    }
                else:
                    # Block expired
                    del self._blocked[key]
            
            # Clean old requests and count current
            self._clean_old_requests(key, config.window_seconds)
            request_count = len(self._requests[key])
            
            # Calculate remaining and reset time
            remaining = max(0, config.requests - request_count - 1)
            window_reset = current_time + config.window_seconds
            
            headers = {
                'X-RateLimit-Limit': str(config.requests),
                'X-RateLimit-Remaining': str(remaining),
                'X-RateLimit-Reset': str(int(window_reset))
            }
            
            # Check if limit exceeded
            if request_count >= config.requests:
                # Block the identifier
                unblock_time = current_time + config.block_duration_seconds
                self._blocked[key] = unblock_time
                retry_after = config.block_duration_seconds
                
                headers['X-RateLimit-Remaining'] = '0'
                headers['Retry-After'] = str(retry_after)
                
                return True, retry_after, headers
            
            # Record this request
            self._requests[key].append((current_time, 1))
            
            return False, None, headers
    
    def reset(self, identifier: str, endpoint_category: str) -> None:
        """
        Reset rate limit for an identifier (useful for testing or admin actions).
        
        Args:
            identifier: IP address or user ID
            endpoint_category: Category of the endpoint
        """
        key = self._hash_key(identifier, endpoint_category)
        with self._lock:
            if key in self._requests:
                del self._requests[key]
            if key in self._blocked:
                del self._blocked[key]


# Global rate limiter instance (singleton pattern)
_rate_limiter_instance: Optional[SlidingWindowRateLimiter] = None


def get_rate_limiter() -> SlidingWindowRateLimiter:
    """
    Get the global rate limiter instance.
    
    Returns:
        SlidingWindowRateLimiter instance
    """
    global _rate_limiter_instance
    if _rate_limiter_instance is None:
        _rate_limiter_instance = SlidingWindowRateLimiter()
    return _rate_limiter_instance


def get_client_ip(request) -> str:
    """
    Extract client IP address from request, handling proxies.
    
    Checks X-Forwarded-For header first (for reverse proxy setups),
    falls back to REMOTE_ADDR.
    
    Security note: X-Forwarded-For can be spoofed if not properly
    configured at the proxy level. Ensure your proxy strips/overwrites
    this header.
    """
    # Check for X-Forwarded-For header (common with reverse proxies)
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        # Take the first IP (client IP) from the chain
        # Format: "client, proxy1, proxy2, ..."
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR', '0.0.0.0')
    
    return ip


# Endpoint to rate limit category mapping
ENDPOINT_RATE_LIMIT_MAP = {
    # Authentication endpoints
    '/api/auth/login/': 'auth_login',
    '/api/auth/register/': 'auth_register',
    '/api/auth/request-reset/': 'password_reset',
    '/api/auth/reset-password/': 'password_reset',
    '/api/auth/send-verification/': 'email_verification',
    '/api/auth/verify-email/': 'email_verification',
    '/api/auth/refresh/': 'token_refresh',
    '/api/auth/logout/': 'api_write',
    # User endpoints
    '/api/users/profile/': 'api_read',
    '/api/users/check-permission/': 'api_read',
    # Health check (more lenient)
    '/api/health/': 'api_read',
}


def get_rate_limit_category(path: str, method: str = 'GET') -> str:
    """
    Get the rate limit category for a given endpoint.
    
    Args:
        path: Request path
        method: HTTP method
    
    Returns:
        Rate limit category string
    """
    # Check explicit mapping first
    if path in ENDPOINT_RATE_LIMIT_MAP:
        return ENDPOINT_RATE_LIMIT_MAP[path]
    
    # Fall back to method-based categorization
    if method in ('GET', 'HEAD', 'OPTIONS'):
        return 'api_read'
    else:
        return 'api_write'
