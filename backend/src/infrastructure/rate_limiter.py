"""
Rate Limiter Module

Provides rate limiting functionality for API endpoints.
Uses in-memory storage for simplicity (use Redis for production scaling).
"""

import os
import time
from typing import Dict, Tuple, Optional
from collections import defaultdict
from threading import Lock
from rest_framework.request import Request


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
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        # Take the first IP in the chain (original client)
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR', '0.0.0.0')
    return ip
