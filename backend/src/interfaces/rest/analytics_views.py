"""
Analytics API Views

REST API endpoints for website analytics data.
Provides access to visit statistics, page analytics, and traffic patterns.
"""

import json
import logging
from collections import defaultdict
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


def _safe_percent(part: float, total: float) -> float:
    if not total:
        return 0.0
    return round((part / total) * 100, 1)


def _extract_user_id_from_request(request: HttpRequest) -> Optional[str]:
    user = extract_user_from_request(request)
    if not user:
        return None
    return str(user.get('user_id') or user.get('id') or user.get('sub'))


def _get_analysis_collection():
    from ...infrastructure.mongodb.connection import get_mongo_client, get_database_name
    client = get_mongo_client()
    db_name = get_database_name()
    return client[db_name]['analysis_results']


def _build_trend_points(docs):
    buckets = defaultdict(int)
    for doc in docs:
        created_at = doc.get('created_at')
        if not created_at:
            continue
        if isinstance(created_at, str):
            try:
                created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            except ValueError:
                continue
        month_key = created_at.strftime('%Y-%m')
        buckets[month_key] += 1
    ordered = [
        {'label': label, 'count': count}
        for label, count in sorted(buckets.items())
    ]
    return ordered[-6:]


def _build_top_types(docs, limit: int = 4):
    counts = defaultdict(int)
    scam_docs = [doc for doc in docs if doc.get('is_scam') and (doc.get('scam_type') or '').lower() != 'not scam']
    for doc in scam_docs:
        scam_type = doc.get('scam_type') or 'Unknown'
        if scam_type:
            counts[scam_type] += 1
    ranked = [
        {'type': name, 'count': count, 'share': _safe_percent(count, len(scam_docs) or 1)}
        for name, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    ]
    return ranked[:limit]


def _build_type_insights(docs, limit: int = 4):
    """Return category counts with a plain-language pattern description."""
    descriptions = {
        'Banking Access & Payment': 'Requests for passwords, one-time codes, card details, or urgent transfers.',
        'Financial and Investment': 'Promises of guaranteed profits, loans, or pressure to invest quickly.',
        'Impersonation and Authority': 'Messages pretending to be a trusted person, company, or official organization.',
        'Job, Business, and Work-from-Home': 'Offers that ask for fees, personal documents, or banking details before work begins.',
        'Shopping and E-Commerce': 'Fake stores, unbelievable discounts, delivery notices, or payment links.',
        'Tech and Online Account': 'Claims that an account or device is at risk and needs a code or remote access.',
    }
    insights = []
    for item in _build_top_types(docs, limit):
        insights.append({
            **item,
            'description': descriptions.get(
                item['type'],
                'A message pattern that uses urgency, authority, or an attractive offer to prompt quick action.'
            ),
        })
    return insights


def _build_recent_submissions(docs, limit: int = 8):
    """Expose safe analysis metadata, never the submitted message content."""
    submissions = []
    for doc in docs[:limit]:
        created_at = doc.get('created_at')
        if hasattr(created_at, 'isoformat'):
            created_at = created_at.isoformat()
        submissions.append({
            'ref_id': str(doc.get('ref_id') or doc.get('_id') or ''),
            'created_at': created_at,
            'type': doc.get('scam_type') or 'Unknown',
            'is_scam': bool(doc.get('is_scam')),
            'scam_score': doc.get('scam_score') if isinstance(doc.get('scam_score'), (int, float)) else None,
            'risk_level': (
                'High risk'
                if doc.get('is_scam') and isinstance(doc.get('scam_score'), (int, float)) and doc.get('scam_score') >= 70
                else 'Review carefully' if doc.get('is_scam') else 'Low risk'
            ),
        })
    return submissions


def _build_activity_insight(docs, high_risk_count: int):
    if len(docs) < 2:
        return 'Keep checking messages here to reveal how your risk pattern changes over time.'
    recent_docs = docs[:min(5, len(docs))]
    recent_high_risk = sum(
        1 for doc in recent_docs
        if doc.get('is_scam') and isinstance(doc.get('scam_score'), (int, float)) and doc.get('scam_score') >= 70
    )
    recent_rate = _safe_percent(recent_high_risk, len(recent_docs))
    overall_rate = _safe_percent(high_risk_count, len(docs))
    if recent_rate > overall_rate + 10:
        return f'Your latest checks are more concerning than your overall history: {recent_rate}% high risk recently versus {overall_rate}% overall.'
    if recent_rate < overall_rate - 10:
        return f'Your latest checks look safer than your overall history: {recent_rate}% high risk recently versus {overall_rate}% overall.'
    return f'Your recent checks are broadly in line with your overall pattern at about {overall_rate}% high risk.'


def _build_scam_trend_points(docs):
    """Count only confirmed scam analyses by month for the community chart."""
    scam_docs = [doc for doc in docs if doc.get('is_scam') and (doc.get('scam_type') or '').lower() != 'not scam']
    return _build_trend_points(scam_docs)


def _build_global_trend_insight(docs):
    """Describe a meaningful month-over-month change without guessing from sparse data."""
    now = datetime.utcnow()
    current_key = now.strftime('%Y-%m')
    previous_month = (now.replace(day=1) - timedelta(days=1)).strftime('%Y-%m')
    current_counts = defaultdict(int)
    previous_counts = defaultdict(int)

    for doc in docs:
        if not doc.get('is_scam') or (doc.get('scam_type') or '').lower() == 'not scam':
            continue
        created_at = doc.get('created_at')
        if isinstance(created_at, str):
            try:
                created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00')).replace(tzinfo=None)
            except ValueError:
                continue
        if not created_at:
            continue
        scam_type = doc.get('scam_type') or 'Unknown'
        if created_at.strftime('%Y-%m') == current_key:
            current_counts[scam_type] += 1
        elif created_at.strftime('%Y-%m') == previous_month:
            previous_counts[scam_type] += 1

    changes = []
    for scam_type, current_count in current_counts.items():
        previous_count = previous_counts.get(scam_type, 0)
        if current_count > previous_count and current_count >= 2:
            increase = 100 if previous_count == 0 else round(((current_count - previous_count) / previous_count) * 100)
            changes.append((increase, scam_type, current_count, previous_count))

    if not changes:
        return None

    increase, scam_type, current_count, previous_count = max(changes)
    if previous_count == 0:
        return f'{scam_type} has appeared {current_count} times this month and was not seen last month.'
    return f'{scam_type} checks increased by {increase}% this month compared with last month.'


def _build_seasonal_insight():
    month = datetime.utcnow().month
    seasonal_messages = {
        11: 'Holiday shopping and delivery scams often increase this time of year. Be careful with urgent payment links, fake discounts, and delivery messages.',
        12: 'Holiday shopping, delivery, prize, and charity scams often increase this time of year. Be careful with urgent payment links and surprising requests.',
        1: 'Be careful with messages offering quick financial opportunities or asking for urgent payments after the holidays.',
        4: 'Tax and government impersonation scams often become more common around tax deadlines. Verify requests through official websites.',
    }
    return seasonal_messages.get(month)


def _user_risk_summary_text(high_risk_count: int, recent_high_risk: int, total_checks: int):
    if total_checks == 0:
        return 'You have not checked any messages yet. Try a message to see your safety summary.'
    if recent_high_risk >= max(2, total_checks * 0.4):
        return 'You are seeing a lot of high-risk messages lately, so it is a good idea to stay extra careful.'
    if high_risk_count >= max(1, total_checks * 0.25):
        return 'Your checks show a moderate risk pattern. Please pause before acting on urgent or unexpected requests.'
    return 'Your recent checks look fairly safe overall, but it is still wise to be cautious with urgent payment or prize messages.'


def _global_risk_summary_text(global_high_risk: int, global_total: int):
    if global_total == 0:
        return 'There are not enough checks yet to show a platform trend.'
    if global_high_risk / global_total >= 0.5:
        return 'A large share of checks are coming back as high-risk right now. Users should stay alert.'
    if global_high_risk / global_total >= 0.3:
        return 'The overall pattern is moderately risky. Urgent payment and impersonation scams are showing up often.'
    return 'The platform is mostly seeing lower-risk checks overall, but fraud patterns still appear in a few scam categories.'


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


@csrf_exempt
@require_http_methods(["GET"])
@rate_limit('api_read')
def get_user_safety_summary(request: HttpRequest) -> JsonResponse:
    """Provide a simple safety overview for the logged-in user."""
    user_id = _extract_user_id_from_request(request)
    if not user_id:
        return JsonResponse({'error': 'Authentication required'}, status=401)

    collection = _get_analysis_collection()
    docs = list(collection.find({
        'user_id': user_id,
        'user_deleted': {'$ne': True},
    }).sort('created_at', -1))

    if not docs:
        return JsonResponse({
            'success': True,
            'data': {
                'total_checks': 0,
                'high_risk_count': 0,
                'high_risk_rate': 0,
                'recent_high_risk_count': 0,
                'most_common_type': None,
                'risk_level': 'No data yet',
                'summary': 'You have not checked any messages yet. Try a message to see your safety summary.',
                'trend': [],
                'top_types': [],
                'type_insights': [],
                'recent_submissions': [],
                'activity_insight': 'Keep checking messages here to reveal how your risk pattern changes over time.',
                'analytics_scope_note': 'Based only on your authenticated Verif-AI checks. Message content is not shown here.',
            }
        })

    high_risk_count = 0
    recent_high_risk_count = 0
    scam_total = 0
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    for doc in docs:
        created_at = doc.get('created_at')
        if isinstance(created_at, str):
            try:
                created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            except ValueError:
                created_at = None
        if doc.get('is_scam'):
            scam_total += 1
        score = doc.get('scam_score')
        if isinstance(score, (int, float)) and doc.get('is_scam') and score >= 70:
            high_risk_count += 1
        if created_at and created_at >= thirty_days_ago and doc.get('is_scam') and isinstance(score, (int, float)) and score >= 70:
            recent_high_risk_count += 1

    top_types = _build_top_types(docs, limit=4)
    type_insights = _build_type_insights(docs, limit=4)
    trend = _build_trend_points(docs)
    most_common = top_types[0] if top_types else None
    summary = _user_risk_summary_text(high_risk_count, recent_high_risk_count, len(docs))

    risk_level = 'Low risk'
    if high_risk_count >= max(2, len(docs) * 0.3):
        risk_level = 'High risk'
    elif high_risk_count >= max(1, len(docs) * 0.15):
        risk_level = 'Medium risk'

    return JsonResponse({
        'success': True,
        'data': {
            'total_checks': len(docs),
            'high_risk_count': high_risk_count,
            'high_risk_rate': _safe_percent(high_risk_count, len(docs)),
            'recent_high_risk_count': recent_high_risk_count,
            'total_scam_checks': scam_total,
            'most_common_type': most_common['type'] if most_common else None,
            'risk_level': risk_level,
            'summary': summary,
            'trend': trend,
            'top_types': top_types,
            'type_insights': type_insights,
            'recent_submissions': _build_recent_submissions(docs),
            'activity_insight': _build_activity_insight(docs, high_risk_count),
            'analytics_scope_note': 'Based only on your authenticated Verif-AI checks. Message content is not shown here.',
        }
    })


@csrf_exempt
@require_http_methods(["GET"])
@rate_limit('api_read')
def get_global_safety_summary(request: HttpRequest) -> JsonResponse:
    """Provide a simple platform-wide trend summary for all users."""
    user = extract_user_from_request(request)
    if not user:
        return JsonResponse({'error': 'Authentication required'}, status=401)

    collection = _get_analysis_collection()
    docs = list(collection.find({
        'user_id': {'$nin': [None, '']},
        'user_deleted': {'$ne': True},
    }).sort('created_at', -1))

    if not docs:
        return JsonResponse({
            'success': True,
            'data': {
                'total_checks': 0,
                'scam_rate': 0,
                'most_common_type': None,
                'summary': 'There are not enough checks yet to show a platform trend.',
                'trend': [],
                'trend_insight': None,
                'seasonal_insight': _build_seasonal_insight(),
                'top_types': [],
            }
        })

    scam_total = sum(1 for doc in docs if doc.get('is_scam'))
    high_risk_total = sum(
        1 for doc in docs
        if doc.get('is_scam') and isinstance(doc.get('scam_score'), (int, float)) and doc.get('scam_score') >= 70
    )
    top_types = _build_top_types(docs, limit=4)
    trend = _build_scam_trend_points(docs)
    most_common = top_types[0] if top_types else None
    summary = _global_risk_summary_text(high_risk_total, len(docs))

    return JsonResponse({
        'success': True,
        'data': {
            'total_checks': len(docs),
            'scam_rate': _safe_percent(scam_total, len(docs)),
            'high_risk_total': high_risk_total,
            'most_common_type': most_common['type'] if most_common else None,
            'summary': summary,
            'trend': trend,
            'trend_insight': _build_global_trend_insight(docs),
            'seasonal_insight': _build_seasonal_insight(),
            'top_types': top_types,
        }
    })


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
