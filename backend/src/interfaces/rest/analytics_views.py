"""
Analytics API Views

REST API endpoints for website analytics data.
Provides access to visit statistics, page analytics, and traffic patterns.
"""

import json
import logging
from datetime import datetime, timedelta
from functools import wraps
from typing import Optional, Dict, Any

from django.http import JsonResponse, HttpRequest
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt

from ...infrastructure.rate_limiter import rate_limit
from ...infrastructure.jwt_service import JWTService
from ...infrastructure.middleware.analytics_repository import (
    get_analytics_repository,
    AnalyticsRepository,
)

logger = logging.getLogger(__name__)


def get_jwt_service():
    """Get JWT service instance."""
    import os
    secret_key = os.getenv('JWT_SECRET_KEY', 'dev-secret-key')
    access_lifetime = int(os.getenv('JWT_ACCESS_TOKEN_LIFETIME', '900'))
    refresh_lifetime = int(os.getenv('JWT_REFRESH_TOKEN_LIFETIME', '604800'))
    return JWTService(secret_key, access_lifetime, refresh_lifetime)


# ==================== Authentication Helpers ====================

def extract_user_from_request(request: HttpRequest) -> Optional[Dict[str, Any]]:
    """Extract user info from JWT token in request."""
    auth_header = request.META.get('HTTP_AUTHORIZATION', '')
    if not auth_header.startswith('Bearer '):
        return None
    
    try:
        token = auth_header.split(' ')[1]
        jwt_service = get_jwt_service()
        payload = jwt_service.verify_access_token(token)
        return payload
    except Exception as e:
        logger.warning(f"Token verification failed: {e}")
        return None


def require_admin(view_func):
    """Decorator requiring admin role."""
    @wraps(view_func)
    def wrapper(request: HttpRequest, *args, **kwargs):
        user = extract_user_from_request(request)
        if not user:
            return JsonResponse({'error': 'Authentication required'}, status=401)
        
        # JWT payload uses 'roles' as a list, not 'role' as a string
        user_roles = user.get('roles', [])
        if not any(role in ['admin', 'moderator', 'super_admin'] for role in user_roles):
            return JsonResponse({'error': 'Admin access required'}, status=403)
        
        request.user_info = user
        return view_func(request, *args, **kwargs)
    return wrapper


def parse_date_params(request: HttpRequest) -> tuple[Optional[datetime], Optional[datetime]]:
    """Parse start_date and end_date from query params."""
    start_date = None
    end_date = None
    
    start_str = request.GET.get('start_date')
    end_str = request.GET.get('end_date')
    
    if start_str:
        try:
            start_date = datetime.fromisoformat(start_str.replace('Z', '+00:00'))
        except ValueError:
            try:
                start_date = datetime.strptime(start_str, '%Y-%m-%d')
            except ValueError:
                pass
    
    if end_str:
        try:
            end_date = datetime.fromisoformat(end_str.replace('Z', '+00:00'))
        except ValueError:
            try:
                end_date = datetime.strptime(end_str, '%Y-%m-%d')
                # Set to end of day
                end_date = end_date.replace(hour=23, minute=59, second=59)
            except ValueError:
                pass
    
    return start_date, end_date


# ==================== API Endpoints ====================

@csrf_exempt
@require_http_methods(["GET"])
@rate_limit('api_read')
@require_admin
def get_visit_statistics(request: HttpRequest) -> JsonResponse:
    """
    Get overall visit statistics.
    
    GET /api/analytics/visits/
    
    Query params:
        - start_date: ISO date string (optional)
        - end_date: ISO date string (optional)
        
    Returns:
        - total_visits: Total number of visits
        - unique_visitors: Number of unique visitors
        - authenticated_visits: Visits from logged-in users
        - anonymous_visits: Visits from anonymous users
    """
    repo = get_analytics_repository()
    if not repo:
        return JsonResponse({'error': 'Analytics service unavailable'}, status=503)
    
    start_date, end_date = parse_date_params(request)
    
    try:
        stats = repo.get_visit_statistics(start_date, end_date)
        return JsonResponse({
            'success': True,
            'data': stats.to_dict()
        })
    except Exception as e:
        logger.error(f"Error getting visit statistics: {e}")
        return JsonResponse({'error': 'Failed to retrieve statistics'}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
@rate_limit('api_read')
@require_admin
def get_page_analytics(request: HttpRequest) -> JsonResponse:
    """
    Get visit statistics by page/path.
    
    GET /api/analytics/pages/
    
    Query params:
        - start_date: ISO date string (optional)
        - end_date: ISO date string (optional)
        - limit: Number of pages to return (default 10, max 50)
        
    Returns:
        List of page statistics sorted by visit count
    """
    repo = get_analytics_repository()
    if not repo:
        return JsonResponse({'error': 'Analytics service unavailable'}, status=503)
    
    start_date, end_date = parse_date_params(request)
    
    try:
        limit = min(int(request.GET.get('limit', 10)), 50)
    except ValueError:
        limit = 10
    
    try:
        pages = repo.get_visits_by_page(start_date, end_date, limit)
        return JsonResponse({
            'success': True,
            'data': [p.to_dict() for p in pages]
        })
    except Exception as e:
        logger.error(f"Error getting page analytics: {e}")
        return JsonResponse({'error': 'Failed to retrieve page analytics'}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
@rate_limit('api_read')
@require_admin
def get_device_breakdown(request: HttpRequest) -> JsonResponse:
    """
    Get breakdown of visits by device type.
    
    GET /api/analytics/devices/
    
    Query params:
        - start_date: ISO date string (optional)
        - end_date: ISO date string (optional)
        
    Returns:
        Device breakdown with counts and percentages
    """
    repo = get_analytics_repository()
    if not repo:
        return JsonResponse({'error': 'Analytics service unavailable'}, status=503)
    
    start_date, end_date = parse_date_params(request)
    
    try:
        breakdown = repo.get_device_breakdown(start_date, end_date)
        return JsonResponse({
            'success': True,
            'data': breakdown.to_dict()
        })
    except Exception as e:
        logger.error(f"Error getting device breakdown: {e}")
        return JsonResponse({'error': 'Failed to retrieve device breakdown'}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
@rate_limit('api_read')
@require_admin
def get_visits_time_series(request: HttpRequest) -> JsonResponse:
    """
    Get visit counts over time for graphing.
    
    GET /api/analytics/time-series/
    
    Query params:
        - start_date: ISO date string (required)
        - end_date: ISO date string (required)
        - granularity: 'hour', 'day', 'week', 'month' (default 'day')
        
    Returns:
        List of time series points with date and count
    """
    repo = get_analytics_repository()
    if not repo:
        return JsonResponse({'error': 'Analytics service unavailable'}, status=503)
    
    start_date, end_date = parse_date_params(request)
    
    if not start_date:
        start_date = datetime.utcnow() - timedelta(days=30)
    if not end_date:
        end_date = datetime.utcnow()
    
    granularity = request.GET.get('granularity', 'day')
    if granularity not in ['hour', 'day', 'week', 'month']:
        granularity = 'day'
    
    try:
        time_series = repo.get_visits_time_series(start_date, end_date, granularity)
        return JsonResponse({
            'success': True,
            'data': [p.to_dict() for p in time_series],
            'granularity': granularity,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat()
        })
    except Exception as e:
        logger.error(f"Error getting time series: {e}")
        return JsonResponse({'error': 'Failed to retrieve time series'}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
@rate_limit('api_read')
@require_admin
def get_hourly_pattern(request: HttpRequest) -> JsonResponse:
    """
    Get traffic patterns by hour of day.
    
    GET /api/analytics/hourly/
    
    Query params:
        - start_date: ISO date string (optional)
        - end_date: ISO date string (optional)
        
    Returns:
        Object mapping hour (0-23) to visit count
    """
    repo = get_analytics_repository()
    if not repo:
        return JsonResponse({'error': 'Analytics service unavailable'}, status=503)
    
    start_date, end_date = parse_date_params(request)
    
    try:
        hourly = repo.get_hourly_traffic_pattern(start_date, end_date)
        return JsonResponse({
            'success': True,
            'data': hourly
        })
    except Exception as e:
        logger.error(f"Error getting hourly pattern: {e}")
        return JsonResponse({'error': 'Failed to retrieve hourly pattern'}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
@rate_limit('api_read')
@require_admin
def get_referrer_stats(request: HttpRequest) -> JsonResponse:
    """
    Get top referrers.
    
    GET /api/analytics/referrers/
    
    Query params:
        - start_date: ISO date string (optional)
        - end_date: ISO date string (optional)
        - limit: Number of referrers to return (default 10, max 50)
        
    Returns:
        List of referrer statistics
    """
    repo = get_analytics_repository()
    if not repo:
        return JsonResponse({'error': 'Analytics service unavailable'}, status=503)
    
    start_date, end_date = parse_date_params(request)
    
    try:
        limit = min(int(request.GET.get('limit', 10)), 50)
    except ValueError:
        limit = 10
    
    try:
        referrers = repo.get_referrer_stats(start_date, end_date, limit)
        return JsonResponse({
            'success': True,
            'data': referrers
        })
    except Exception as e:
        logger.error(f"Error getting referrer stats: {e}")
        return JsonResponse({'error': 'Failed to retrieve referrer stats'}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
@rate_limit('api_read')
@require_admin
def get_recent_visits(request: HttpRequest) -> JsonResponse:
    """
    Get most recent visits for live monitoring.
    
    GET /api/analytics/recent/
    
    Query params:
        - limit: Number of visits to return (default 50, max 100)
        - path: Optional path filter
        
    Returns:
        List of recent visit records
    """
    repo = get_analytics_repository()
    if not repo:
        return JsonResponse({'error': 'Analytics service unavailable'}, status=503)
    
    try:
        limit = min(int(request.GET.get('limit', 50)), 100)
    except ValueError:
        limit = 50
    
    path_filter = request.GET.get('path')
    
    try:
        visits = repo.get_recent_visits(limit, path_filter)
        # Convert datetime objects to ISO strings
        for visit in visits:
            if 'timestamp' in visit and isinstance(visit['timestamp'], datetime):
                visit['timestamp'] = visit['timestamp'].isoformat()
        
        return JsonResponse({
            'success': True,
            'data': visits
        })
    except Exception as e:
        logger.error(f"Error getting recent visits: {e}")
        return JsonResponse({'error': 'Failed to retrieve recent visits'}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
@rate_limit('api_read')
@require_admin
def get_analytics_summary(request: HttpRequest) -> JsonResponse:
    """
    Get comprehensive analytics summary for dashboard.
    
    GET /api/analytics/summary/
    
    Query params:
        - period: 'today', 'week', 'month', 'year' (default 'week')
        
    Returns:
        Comprehensive summary including visits, devices, top pages
    """
    repo = get_analytics_repository()
    if not repo:
        return JsonResponse({'error': 'Analytics service unavailable'}, status=503)
    
    period = request.GET.get('period', 'week')
    
    now = datetime.utcnow()
    if period == 'today':
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == 'week':
        start_date = now - timedelta(days=7)
    elif period == 'month':
        start_date = now - timedelta(days=30)
    elif period == 'year':
        start_date = now - timedelta(days=365)
    else:
        start_date = now - timedelta(days=7)
    
    try:
        # Get various statistics
        visit_stats = repo.get_visit_statistics(start_date, now)
        device_breakdown = repo.get_device_breakdown(start_date, now)
        top_pages = repo.get_visits_by_page(start_date, now, limit=5)
        hourly_pattern = repo.get_hourly_traffic_pattern(start_date, now)
        
        # Calculate comparison with previous period
        period_length = (now - start_date).days
        prev_start = start_date - timedelta(days=period_length)
        prev_stats = repo.get_visit_statistics(prev_start, start_date)
        
        # Calculate growth
        visits_growth = 0
        if prev_stats.total_visits > 0:
            visits_growth = round(
                (visit_stats.total_visits - prev_stats.total_visits) / prev_stats.total_visits * 100, 
                1
            )
        
        return JsonResponse({
            'success': True,
            'data': {
                'period': period,
                'start_date': start_date.isoformat(),
                'end_date': now.isoformat(),
                'visits': visit_stats.to_dict(),
                'visits_growth_percent': visits_growth,
                'previous_period_visits': prev_stats.total_visits,
                'devices': device_breakdown.to_dict(),
                'top_pages': [p.to_dict() for p in top_pages],
                'hourly_pattern': hourly_pattern,
            }
        })
    except Exception as e:
        logger.error(f"Error getting analytics summary: {e}")
        return JsonResponse({'error': 'Failed to retrieve analytics summary'}, status=500)
