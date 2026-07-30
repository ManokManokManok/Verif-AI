"""
Analytics Middleware

Django middleware for tracking page visits and user analytics.
Captures visit data without impacting performance using async processing.
"""

import logging
import hashlib
import re
from datetime import datetime
from typing import Optional, Dict, Any
from functools import wraps
import threading
import queue

from django.http import HttpRequest, HttpResponse
from django.conf import settings

logger = logging.getLogger(__name__)

# Thread-safe queue for async visit processing
_visit_queue: queue.Queue = queue.Queue(maxsize=10000)
_worker_thread: Optional[threading.Thread] = None
_shutdown_event = threading.Event()


def _get_client_ip(request: HttpRequest) -> str:
    """Extract client IP from request, handling proxies."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR', '0.0.0.0')
    return ip


def _anonymize_ip(ip: str) -> str:
    """Anonymize IP address for GDPR compliance."""
    # Hash the IP to create anonymous but consistent identifier
    return hashlib.sha256(ip.encode()).hexdigest()[:16]


def _get_user_agent(request: HttpRequest) -> str:
    """Get user agent string from request."""
    return request.META.get('HTTP_USER_AGENT', '')[:500]  # Limit length


def _extract_user_id(request: HttpRequest) -> Optional[str]:
    """Extract user ID from JWT token if present."""
    auth_header = request.META.get('HTTP_AUTHORIZATION', '')
    if not auth_header.startswith('Bearer '):
        return None
    
    try:
        import os
        from ..jwt_service import JWTService
        secret_key = os.getenv('JWT_SECRET_KEY', 'dev-secret-key')
        jwt_service = JWTService(secret_key)
        token = auth_header.split(' ')[1]
        payload = jwt_service.verify_access_token(token)
        return payload.get('user_id') if payload else None
    except Exception:
        return None


def _is_bot(user_agent: str) -> bool:
    """Check if request is from a known bot."""
    bot_patterns = [
        r'bot', r'crawler', r'spider', r'scraper',
        r'googlebot', r'bingbot', r'slurp', r'duckduckbot',
        r'baiduspider', r'yandexbot', r'facebookexternalhit',
        r'curl', r'wget', r'python-requests', r'axios'
    ]
    user_agent_lower = user_agent.lower()
    return any(re.search(pattern, user_agent_lower) for pattern in bot_patterns)


def _should_track_path(path: str) -> bool:
    """Determine if this path should be tracked."""
    # Only track specific meaningful interactions (detection or guidance)
    # to prevent counting basic page refreshes as website visits.
    track_patterns = [
        r'^/api/detect/?',               # Scam detection actions
        r'^/api/chat/message/?',         # General chatbot guidance
        r'^/api/chat/analysis-guided/?', # Specific analysis guidance
    ]
    return any(re.match(pattern, path) for pattern in track_patterns)


class VisitData:
    """Data class for visit information."""
    
    def __init__(
        self,
        path: str,
        method: str,
        timestamp: datetime,
        anonymous_ip: str,
        user_agent: str,
        user_id: Optional[str] = None,
        referrer: Optional[str] = None,
        response_status: int = 200,
        response_time_ms: Optional[float] = None,
        is_authenticated: bool = False,
        device_type: str = 'unknown',
        session_id: Optional[str] = None,
    ):
        self.path = path
        self.method = method
        self.timestamp = timestamp
        self.anonymous_ip = anonymous_ip
        self.user_agent = user_agent
        self.user_id = user_id
        self.referrer = referrer
        self.response_status = response_status
        self.response_time_ms = response_time_ms
        self.is_authenticated = is_authenticated
        self.device_type = device_type
        self.session_id = session_id
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for MongoDB storage."""
        return {
            'path': self.path,
            'method': self.method,
            'timestamp': self.timestamp,
            'anonymous_ip': self.anonymous_ip,
            'user_agent': self.user_agent,
            'user_id': self.user_id,
            'referrer': self.referrer,
            'response_status': self.response_status,
            'response_time_ms': self.response_time_ms,
            'is_authenticated': self.is_authenticated,
            'device_type': self.device_type,
            'session_id': self.session_id,
        }


def _detect_device_type(user_agent: str) -> str:
    """Detect device type from user agent."""
    ua_lower = user_agent.lower()
    if any(mobile in ua_lower for mobile in ['mobile', 'android', 'iphone', 'ipad']):
        if 'tablet' in ua_lower or 'ipad' in ua_lower:
            return 'tablet'
        return 'mobile'
    return 'desktop'


def _process_visits_worker():
    """Background worker to process visit queue."""
    from .analytics_repository import get_analytics_repository
    
    batch = []
    batch_size = 50
    flush_interval = 5.0  # seconds
    last_flush = datetime.utcnow()
    
    while not _shutdown_event.is_set():
        try:
            # Get visit with timeout
            try:
                visit_data = _visit_queue.get(timeout=1.0)
                batch.append(visit_data.to_dict())
                _visit_queue.task_done()
            except queue.Empty:
                pass
            
            # Flush batch if size reached or interval elapsed
            now = datetime.utcnow()
            should_flush = (
                len(batch) >= batch_size or
                (len(batch) > 0 and (now - last_flush).total_seconds() >= flush_interval)
            )
            
            if should_flush and batch:
                try:
                    repo = get_analytics_repository()
                    if repo:
                        repo.bulk_insert_visits(batch)
                except Exception as e:
                    logger.error(f"Failed to flush visit batch: {e}")
                batch = []
                last_flush = now
                
        except Exception as e:
            logger.error(f"Error in visit processing worker: {e}")
    
    # Final flush on shutdown
    if batch:
        try:
            repo = get_analytics_repository()
            if repo:
                repo.bulk_insert_visits(batch)
        except Exception as e:
            logger.error(f"Failed to flush final visit batch: {e}")


def _ensure_worker_running():
    """Ensure background worker thread is running."""
    global _worker_thread
    if _worker_thread is None or not _worker_thread.is_alive():
        _shutdown_event.clear()
        _worker_thread = threading.Thread(target=_process_visits_worker, daemon=True)
        _worker_thread.start()


def shutdown_analytics():
    """Shutdown analytics worker gracefully."""
    _shutdown_event.set()
    if _worker_thread:
        _worker_thread.join(timeout=10.0)


class AnalyticsMiddleware:
    """
    Django middleware for tracking page visits.
    
    Features:
    - Async processing to avoid blocking requests
    - GDPR compliant (IP anonymization)
    - Bot detection and filtering
    - Configurable path filtering
    - Device type detection
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.enabled = getattr(settings, 'ANALYTICS_ENABLED', True)
        _ensure_worker_running()
    
    def __call__(self, request: HttpRequest) -> HttpResponse:
        if not self.enabled:
            return self.get_response(request)
        
        # Skip if path shouldn't be tracked
        if not _should_track_path(request.path):
            return self.get_response(request)
        
        # Skip bots
        user_agent = _get_user_agent(request)
        if _is_bot(user_agent):
            return self.get_response(request)
        
        # Record start time
        start_time = datetime.utcnow()
        
        # Process request
        response = self.get_response(request)
        
        # Calculate response time
        response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        # Create visit data
        try:
            visit_data = VisitData(
                path=request.path,
                method=request.method,
                timestamp=start_time,
                anonymous_ip=_anonymize_ip(_get_client_ip(request)),
                user_agent=user_agent,
                user_id=_extract_user_id(request),
                referrer=request.META.get('HTTP_REFERER', '')[:500],
                response_status=response.status_code,
                response_time_ms=round(response_time, 2),
                is_authenticated=bool(_extract_user_id(request)),
                device_type=_detect_device_type(user_agent),
                session_id=request.session.session_key if hasattr(request, 'session') else None,
            )
            
            # Queue for async processing
            try:
                _visit_queue.put_nowait(visit_data)
            except queue.Full:
                logger.warning("Visit queue full, dropping visit data")
                
        except Exception as e:
            logger.error(f"Error creating visit data: {e}")
        
        return response


# Decorator for tracking specific function calls
def track_event(event_name: str, metadata: Optional[Dict[str, Any]] = None):
    """Decorator to track custom events."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                from .analytics_repository import get_analytics_repository
                repo = get_analytics_repository()
                if repo:
                    repo.track_custom_event(
                        event_name=event_name,
                        timestamp=datetime.utcnow(),
                        metadata=metadata or {}
                    )
            except Exception as e:
                logger.error(f"Error tracking event {event_name}: {e}")
            return func(*args, **kwargs)
        return wrapper
    return decorator
