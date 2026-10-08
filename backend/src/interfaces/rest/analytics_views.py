"""
Analytics API Views

REST API endpoints for website analytics data.
Provides access to visit statistics, page analytics, and traffic patterns.
"""

import json
import logging
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from functools import wraps
from typing import Optional, Dict, Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

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


def _get_activity_timezone(timezone_name: str):
    try:
        return ZoneInfo(timezone_name)
    except (ZoneInfoNotFoundError, TypeError, ValueError):
        return timezone.utc


def _parse_activity_datetime(value, local_timezone):
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value.replace('Z', '+00:00'))
        except ValueError:
            return None
    if not isinstance(value, datetime):
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(local_timezone)


def _build_activity_data(docs, timezone_name: str = 'UTC', now=None) -> Dict[str, Any]:
    local_timezone = _get_activity_timezone(timezone_name)
    current_time = now or datetime.now(local_timezone)
    if current_time.tzinfo is None:
        current_time = current_time.replace(tzinfo=local_timezone)
    else:
        current_time = current_time.astimezone(local_timezone)

    risk_mix = {'not_scam': 0, 'suspicious': 0, 'high_risk': 0}
    monthly = defaultdict(lambda: {'not_scam': 0, 'suspicious': 0, 'high_risk': 0, 'total': 0})
    weekdays = [
        {'weekday': label, 'scam_count': 0, 'total_count': 0}
        for label in ('Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun')
    ]
    daily = defaultdict(lambda: {'count': 0, 'high_risk_count': 0, 'groups': defaultdict(int)})
    recent = {'total_checks': 0, 'high_risk_count': 0}
    previous = {'total_checks': 0, 'high_risk_count': 0}
    last_high_risk = None
    recent_start = current_time - timedelta(days=30)
    previous_start = current_time - timedelta(days=60)
    first_calendar_day = current_time.date() - timedelta(days=current_time.date().weekday() + 77)
    current_month = current_time.strftime('%Y-%m')

    for doc in docs:
        created_at = _parse_activity_datetime(doc.get('created_at'), local_timezone)
        if not created_at:
            continue

        is_scam = bool(doc.get('is_scam'))
        score = doc.get('scam_score')
        high_risk = is_scam and isinstance(score, (int, float)) and score >= 70
        bucket = 'high_risk' if high_risk else 'suspicious' if is_scam else 'not_scam'
        risk_mix[bucket] += 1

        month_key = created_at.strftime('%Y-%m')
        monthly[month_key][bucket] += 1
        monthly[month_key]['total'] += 1

        weekdays[created_at.weekday()]['total_count'] += 1
        if is_scam:
            weekdays[created_at.weekday()]['scam_count'] += 1

        if first_calendar_day <= created_at.date() <= current_time.date():
            day_bucket = daily[created_at.date().isoformat()]
            day_bucket['count'] += 1
            day_bucket['groups'][str(doc.get('scam_type') or 'Unknown')] += 1
            if high_risk:
                day_bucket['high_risk_count'] += 1

        if recent_start <= created_at <= current_time:
            recent['total_checks'] += 1
            if high_risk:
                recent['high_risk_count'] += 1
        elif previous_start <= created_at < recent_start:
            previous['total_checks'] += 1
            if high_risk:
                previous['high_risk_count'] += 1

        if high_risk and (last_high_risk is None or created_at > last_high_risk):
            last_high_risk = created_at

    active_months = sorted(monthly.items())[-6:]
    monthly_risk = [
        {
            'month': month,
            'label': datetime.strptime(month, '%Y-%m').strftime('%b %Y'),
            'is_current_month': month == current_month,
            **values,
        }
        for month, values in active_months
    ]
    calendar_days = [
        {
            'date': (first_calendar_day + timedelta(days=offset)).isoformat(),
            'count': daily[(first_calendar_day + timedelta(days=offset)).isoformat()]['count'],
            'high_risk_count': daily[(first_calendar_day + timedelta(days=offset)).isoformat()]['high_risk_count'],
            'groups': [
                {'type': category, 'count': count}
                for category, count in sorted(
                    daily[(first_calendar_day + timedelta(days=offset)).isoformat()]['groups'].items(),
                    key=lambda entry: (-entry[1], entry[0]),
                )
            ],
        }
        for offset in range(84)
    ]

    return {
        'as_of_date': current_time.date().isoformat(),
        'risk_mix': risk_mix,
        'monthly_risk': monthly_risk,
        'calendar_days': calendar_days,
        'weekday_activity': weekdays,
        'checks_this_month': monthly[current_month]['total'],
        'recent_30_days': {
            **recent,
            'high_risk_rate': _safe_percent(recent['high_risk_count'], recent['total_checks'])
            if recent['total_checks'] else None,
        },
        'previous_30_days': {
            **previous,
            'high_risk_rate': _safe_percent(previous['high_risk_count'], previous['total_checks'])
            if previous['total_checks'] else None,
        },
        'last_high_risk_at': last_high_risk.isoformat() if last_high_risk else None,
        'days_since_last_high_risk': (current_time.date() - last_high_risk.date()).days if last_high_risk else None,
    }


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


def _safe_red_flag_label(marker: str) -> str:
    marker_text = marker.lower()
    if any(term in marker_text for term in ('urgent', 'immediate', 'deadline', 'act now', 'pressure')):
        return 'Urgency or pressure'
    if any(term in marker_text for term in ('link', 'url', 'website', 'contact method', 'phone number')):
        return 'Suspicious link or contact method'
    if any(term in marker_text for term in ('password', 'verification code', 'personal information', 'account details', 'bank detail')):
        return 'Request for sensitive information'
    if any(term in marker_text for term in ('payment', 'transfer', 'fee', 'gift card', 'money')):
        return 'Unusual payment request'
    if any(term in marker_text for term in ('impersonat', 'pretend', 'authority', 'official')):
        return 'Impersonation or false authority'
    if any(term in marker_text for term in ('threat', 'suspend', 'legal action', 'penalty')):
        return 'Threat or consequence'
    if any(term in marker_text for term in ('guaranteed', 'prize', 'winner', 'too good', 'unrealistic')):
        return 'Unrealistic offer or promise'
    return 'Other repeated warning sign'


def _build_type_insights(docs, limit: int = 4, timezone_name: str = 'UTC'):
    """Return category metrics that can support a user-facing insight."""
    descriptions = {
        'Banking Access & Payment': 'Requests for passwords, one-time codes, card details, or urgent transfers.',
        'Financial and Investment': 'Promises of guaranteed profits, loans, or pressure to invest quickly.',
        'Impersonation and Authority': 'Messages pretending to be a trusted person, company, or official organization.',
        'Job, Business, and Work-from-Home': 'Offers that ask for fees, personal documents, or banking details before work begins.',
        'Shopping and E-Commerce': 'Fake stores, unbelievable discounts, delivery notices, or payment links.',
        'Tech and Online Account': 'Claims that an account or device is at risk and needs a code or remote access.',
    }
    scam_docs = [
        doc for doc in docs
        if doc.get('is_scam') and (doc.get('scam_type') or '').lower() != 'not scam'
    ]
    try:
        local_timezone = ZoneInfo(timezone_name)
    except (ZoneInfoNotFoundError, TypeError, ValueError):
        local_timezone = timezone.utc
    local_now = datetime.now(local_timezone)
    now = datetime.utcnow()
    recent_start = now - timedelta(days=30)
    previous_start = now - timedelta(days=60)
    current_month_index = local_now.year * 12 + local_now.month - 1
    month_points = []
    for offset in range(5, -1, -1):
        year, month_index = divmod(current_month_index - offset, 12)
        month = month_index + 1
        month_points.append({
            'month': f'{year:04d}-{month:02d}',
            'label': datetime(year, month, 1).strftime('%b'),
        })

    def as_datetime(value):
        if isinstance(value, str):
            try:
                value = datetime.fromisoformat(value.replace('Z', '+00:00'))
            except ValueError:
                return None
        if value and getattr(value, 'tzinfo', None):
            return value.astimezone(timezone.utc).replace(tzinfo=None)
        return value

    insights = []
    for item in _build_top_types(docs, limit):
        matching = [doc for doc in scam_docs if (doc.get('scam_type') or 'Unknown') == item['type']]
        monthly_counts = {point['month']: 0 for point in month_points}
        marker_counts = defaultdict(int)
        scores = [
            float(doc['scam_score']) for doc in matching
            if isinstance(doc.get('scam_score'), (int, float))
        ]
        high_risk_count = sum(1 for score in scores if score >= 70)
        recent_count = 0
        previous_count = 0
        for doc in matching:
            created_at = as_datetime(doc.get('created_at'))
            if created_at and created_at >= recent_start:
                recent_count += 1
            elif created_at and created_at >= previous_start:
                previous_count += 1

            monthly_value = doc.get('created_at')
            if isinstance(monthly_value, str):
                try:
                    monthly_value = datetime.fromisoformat(monthly_value.replace('Z', '+00:00'))
                except ValueError:
                    monthly_value = None
            if isinstance(monthly_value, datetime):
                if monthly_value.tzinfo is None:
                    monthly_value = monthly_value.replace(tzinfo=timezone.utc)
                month_key = monthly_value.astimezone(local_timezone).strftime('%Y-%m')
                if month_key in monthly_counts:
                    monthly_counts[month_key] += 1

            markers = doc.get('key_markers')
            if isinstance(markers, list):
                for marker in {str(value).strip() for value in markers if value}:
                    if marker and len(marker) <= 100:
                        marker_counts[_safe_red_flag_label(marker)] += 1

        if recent_count > previous_count:
            trend_direction = 'increasing'
        elif recent_count < previous_count:
            trend_direction = 'decreasing'
        else:
            trend_direction = 'stable'

        sample_note = (
            'Early signal: fewer than five checks for this pattern in one or both 30-day comparison windows.'
            if recent_count < 5 or previous_count < 5
            else None
        )

        insights.append({
            **item,
            'description': descriptions.get(
                item['type'],
                'A message pattern that uses urgency, authority, or an attractive offer to prompt quick action.'
            ),
            'average_scam_score': round(sum(scores) / len(scores), 1) if scores else None,
            'high_risk_count': high_risk_count,
            'high_risk_rate': _safe_percent(high_risk_count, len(matching)),
            'average_type_confidence': round(
                sum(float(doc['type_confidence']) for doc in matching if isinstance(doc.get('type_confidence'), (int, float)))
                / len([doc for doc in matching if isinstance(doc.get('type_confidence'), (int, float))]),
                1,
            ) if any(isinstance(doc.get('type_confidence'), (int, float)) for doc in matching) else None,
            'recent_count': recent_count,
            'previous_count': previous_count,
            'trend_direction': trend_direction,
            'sample_note': sample_note,
            'monthly_counts': [
                {**point, 'count': monthly_counts[point['month']]}
                for point in month_points
            ],
            'common_red_flags': [
                {'marker': marker, 'count': count}
                for marker, count in sorted(marker_counts.items(), key=lambda entry: (-entry[1], entry[0]))[:5]
            ],
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


def _compute_user_safety_summary(user_id: str, timezone_name: str = 'UTC') -> Dict[str, Any]:
    """Build the personal safety summary dict for a user (shared by both endpoints)."""
    collection = _get_analysis_collection()
    docs = list(collection.find({
        'user_id': user_id,
        'user_deleted': {'$ne': True},
    }).sort('created_at', -1))

    if not docs:
        return {
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
            'activity': _build_activity_data([], timezone_name),
            'analytics_scope_note': 'Based only on your authenticated Verif-AI checks. Message content is not shown here.',
        }

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
    type_insights = _build_type_insights(docs, limit=20, timezone_name=timezone_name)
    trend = _build_trend_points(docs)
    most_common = top_types[0] if top_types else None
    summary = _user_risk_summary_text(high_risk_count, recent_high_risk_count, len(docs))

    risk_level = 'Low risk'
    if high_risk_count >= max(2, len(docs) * 0.3):
        risk_level = 'High risk'
    elif high_risk_count >= max(1, len(docs) * 0.15):
        risk_level = 'Medium risk'

    return {
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
        'activity': _build_activity_data(docs, timezone_name),
        'analytics_scope_note': 'Based only on your authenticated Verif-AI checks. Message content is not shown here.',
    }


@csrf_exempt
@require_http_methods(["GET"])
@rate_limit('api_read')
def get_user_safety_summary(request: HttpRequest) -> JsonResponse:
    """Provide a simple safety overview for the logged-in user."""
    user_id = _extract_user_id_from_request(request)
    if not user_id:
        return JsonResponse({'error': 'Authentication required'}, status=401)

    timezone_name = request.GET.get('timezone', 'UTC')
    return JsonResponse({'success': True, 'data': _compute_user_safety_summary(user_id, timezone_name)})


def _get_ai_summary_repository():
    from ...infrastructure.mongodb.connection import get_mongo_client, get_database_name
    from ...infrastructure.mongodb.ai_summary_repository import AIAnalyticsSummaryRepository
    client = get_mongo_client()
    db_name = get_database_name()
    return AIAnalyticsSummaryRepository(client, db_name)


@csrf_exempt
@require_http_methods(["GET"])
@rate_limit('api_read')
def get_user_ai_summary(request: HttpRequest) -> JsonResponse:
    """Provide an AI-generated, plain-language explanation of the user's safety summary.

    Cooled down and persisted per-user (see AnalyticsPlainLanguageSummaryUseCase) so
    repeated page loads never trigger repeated Gemini calls.
    """
    from ...infrastructure.ai.genai_provider import get_genai_provider
    from ...use_cases.ai.analytics_summary import AnalyticsPlainLanguageSummaryUseCase

    user_id = _extract_user_id_from_request(request)
    if not user_id:
        return JsonResponse({'error': 'Authentication required'}, status=401)

    personal_summary = _compute_user_safety_summary(user_id)
    community_summary = _compute_global_safety_summary()
    use_case = AnalyticsPlainLanguageSummaryUseCase(get_genai_provider(), _get_ai_summary_repository())
    result = use_case.get_summary(user_id, personal_summary, community_summary)

    return JsonResponse({'success': True, 'data': result})


@csrf_exempt
@require_http_methods(["GET"])
@rate_limit('api_read')
def get_user_ai_summary_cached(request: HttpRequest) -> JsonResponse:
    """Return a previously generated AI summary, if one exists, without calling Gemini.

    Used on page load so a returning user immediately sees their last summary
    instead of being asked to press the button again every visit.
    """
    from ...use_cases.ai.analytics_summary import AnalyticsPlainLanguageSummaryUseCase

    user_id = _extract_user_id_from_request(request)
    if not user_id:
        return JsonResponse({'error': 'Authentication required'}, status=401)

    use_case = AnalyticsPlainLanguageSummaryUseCase(None, _get_ai_summary_repository())
    result = use_case.get_cached_summary(user_id)

    return JsonResponse({'success': True, 'data': result})


def _build_community_analytics(docs, timezone_name: str = 'UTC', now=None, minimum_users: int = 5) -> Dict[str, Any]:
    local_timezone = _get_activity_timezone(timezone_name)
    current_time = now or datetime.now(local_timezone)
    if current_time.tzinfo is None:
        current_time = current_time.replace(tzinfo=local_timezone)
    else:
        current_time = current_time.astimezone(local_timezone)

    month_index = current_time.year * 12 + current_time.month - 1
    current_month_start = current_time.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    previous_month_end = current_month_start - timedelta(days=1)
    previous_month_start = previous_month_end.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    previous_period_days = min(current_time.day, previous_month_end.day)
    previous_period_end = previous_month_start + timedelta(days=previous_period_days)
    months = []
    for offset in range(11, -1, -1):
        year, index = divmod(month_index - offset, 12)
        month = index + 1
        month_key = f'{year:04d}-{month:02d}'
        months.append({'month': month_key, 'label': datetime(year, month, 1).strftime('%b %Y')})

    distinct_users = set()
    scam_docs = []
    all_month_counts = defaultdict(int)
    all_month_users = defaultdict(set)
    category_counts = defaultdict(int)
    category_users = defaultdict(set)
    category_month_counts = defaultdict(int)
    category_month_users = defaultdict(set)
    current_period_counts = defaultdict(int)
    current_period_users = defaultdict(set)
    previous_period_counts = defaultdict(int)
    previous_period_users = defaultdict(set)

    for doc in docs:
        user_id = str(doc.get('user_id') or '').strip()
        if not user_id:
            continue
        distinct_users.add(user_id)
        if not doc.get('is_scam') or (doc.get('scam_type') or '').lower() == 'not scam':
            continue

        category = str(doc.get('scam_type') or 'Unknown').strip() or 'Unknown'
        scam_docs.append(doc)
        category_counts[category] += 1
        category_users[category].add(user_id)
        created_at = _parse_activity_datetime(doc.get('created_at'), local_timezone)
        if not created_at:
            continue
        if current_month_start <= created_at <= current_time:
            current_period_counts[category] += 1
            current_period_users[category].add(user_id)
        if previous_month_start <= created_at < previous_period_end:
            previous_period_counts[category] += 1
            previous_period_users[category].add(user_id)
        month_key = created_at.strftime('%Y-%m')
        if month_key not in {month['month'] for month in months}:
            continue

        all_month_counts[month_key] += 1
        all_month_users[month_key].add(user_id)
        category_month_counts[(category, month_key)] += 1
        category_month_users[(category, month_key)].add(user_id)

    month_series = []
    for month in months:
        user_count = len(all_month_users[month['month']])
        enough_data = user_count >= minimum_users
        month_series.append({
            **month,
            'count': all_month_counts[month['month']] if enough_data else None,
            'distinct_users': user_count if enough_data else None,
            'not_enough_data': not enough_data,
        })

    def ranked_types(counts, month_key=None):
        denominator = sum(counts.values())
        eligible = [
            (category, count)
            for category, count in counts.items()
            if len(category_month_users[(category, month_key)]) >= minimum_users
            if month_key is not None
        ] if month_key is not None else [
            (category, count)
            for category, count in counts.items()
            if len(category_users[category]) >= minimum_users
        ]
        result = []
        for category, count in sorted(eligible, key=lambda item: (-item[1], item[0]))[:5]:
            monthly_counts = []
            for month in months:
                month_user_count = len(category_month_users[(category, month['month'])])
                enough_data = month_user_count >= minimum_users
                monthly_counts.append({
                    **month,
                    'count': category_month_counts[(category, month['month'])] if enough_data else None,
                    'distinct_users': month_user_count if enough_data else None,
                    'not_enough_data': not enough_data,
                })
            result.append({
                'type': category,
                'count': count,
                'share': _safe_percent(count, denominator),
                'distinct_users': len(category_month_users[(category, month_key)]) if month_key is not None else len(category_users[category]),
                'monthly_counts': monthly_counts,
            })
        return result

    all_time_counts = {category: count for category, count in category_counts.items()}
    category_monthly_series = [
        {
            'type': category,
            'count': category_counts[category],
            'share': _safe_percent(category_counts[category], len(scam_docs)),
            'distinct_users': len(category_users[category]),
            'monthly_counts': [
                {
                    **month,
                    'count': category_month_counts[(category, month['month'])]
                    if len(category_month_users[(category, month['month'])]) >= minimum_users else None,
                    'distinct_users': len(category_month_users[(category, month['month'])])
                    if len(category_month_users[(category, month['month'])]) >= minimum_users else None,
                    'not_enough_data': len(category_month_users[(category, month['month'])]) < minimum_users,
                }
                for month in months
            ],
        }
        for category in sorted(category_counts)
        if len(category_users[category]) >= minimum_users
    ]
    this_month = current_time.strftime('%Y-%m')
    current_counts = {
        category: category_month_counts[(category, this_month)]
        for category in category_counts
        if category_month_counts[(category, this_month)]
    }
    rising_scams = []
    for category in category_counts:
        current_users = len(current_period_users[category])
        previous_users = len(previous_period_users[category])
        current_count = current_period_counts[category]
        previous_count = previous_period_counts[category]
        if current_users < minimum_users or (previous_count and previous_users < minimum_users):
            continue
        rising_scams.append({
            'type': category,
            'current_count': current_count,
            'previous_count': previous_count,
            'change_percent': round(((current_count - previous_count) / previous_count) * 100, 1) if previous_count else None,
            'is_new': previous_count == 0,
            'current_distinct_users': current_users,
            'previous_distinct_users': previous_users if previous_users >= minimum_users else None,
            'monthly_counts': [
                {
                    **month,
                    'count': category_month_counts[(category, month['month'])] if len(category_month_users[(category, month['month'])]) >= minimum_users else None,
                    'not_enough_data': len(category_month_users[(category, month['month'])]) < minimum_users,
                }
                for month in months[-6:]
            ],
        })
    rising_scams.sort(key=lambda item: (-(item['change_percent'] if item['change_percent'] is not None else 0), item['type']))

    return {
        'distinct_users': len(distinct_users),
        'minimum_users': minimum_users,
        'total_scam_checks': len(scam_docs),
        'has_demo_data': any(bool(doc.get('analytics_demo_batch')) for doc in docs),
        'top_types_all_time': ranked_types(all_time_counts),
        'top_types_this_month': ranked_types(current_counts, this_month),
        'category_monthly_series': category_monthly_series,
        'rising_scams': rising_scams[:5],
        'monthly_confirmed_scams': month_series,
    }


def _compute_global_safety_summary(timezone_name: str = 'UTC') -> Dict[str, Any]:
    """Build the platform-wide trend summary dict (shared by both endpoints)."""
    collection = _get_analysis_collection()
    docs = list(collection.find({
        'user_id': {'$nin': [None, '']},
        'user_deleted': {'$ne': True},
    }).sort('created_at', -1))

    if not docs:
        return {
            'total_checks': 0,
            'scam_rate': 0,
            'most_common_type': None,
            'summary': 'There are not enough checks yet to show a platform trend.',
            'trend': [],
            'trend_insight': None,
            'seasonal_insight': _build_seasonal_insight(),
            'top_types': [],
            'community_analytics': _build_community_analytics([], timezone_name),
        }

    scam_total = sum(1 for doc in docs if doc.get('is_scam'))
    high_risk_total = sum(
        1 for doc in docs
        if doc.get('is_scam') and isinstance(doc.get('scam_score'), (int, float)) and doc.get('scam_score') >= 70
    )
    top_types = _build_top_types(docs, limit=4)
    community_analytics = _build_community_analytics(docs, timezone_name)
    trend = _build_scam_trend_points(docs)
    most_common = top_types[0] if top_types else None
    summary = _global_risk_summary_text(high_risk_total, len(docs))

    return {
        'total_checks': len(docs),
        'scam_rate': _safe_percent(scam_total, len(docs)),
        'high_risk_total': high_risk_total,
        'most_common_type': most_common['type'] if most_common else None,
        'summary': summary,
        'trend': trend,
        'trend_insight': _build_global_trend_insight(docs),
        'seasonal_insight': _build_seasonal_insight(),
        'top_types': top_types,
        'community_analytics': community_analytics,
    }


@csrf_exempt
@require_http_methods(["GET"])
@rate_limit('api_read')
def get_global_safety_summary(request: HttpRequest) -> JsonResponse:
    """Provide a simple platform-wide trend summary for all users."""
    user = extract_user_from_request(request)
    if not user:
        return JsonResponse({'error': 'Authentication required'}, status=401)

    timezone_name = request.GET.get('timezone', 'UTC')
    return JsonResponse({'success': True, 'data': _compute_global_safety_summary(timezone_name)})


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
