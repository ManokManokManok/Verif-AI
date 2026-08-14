"""
Admin REST API Views

REST endpoints for admin dashboard features including model health,
analysis statistics, user statistics, and user management.

All endpoints require admin role authentication.
"""

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.request import Request
from rest_framework.response import Response
from datetime import datetime
from typing import Optional, Dict, Any
from django.http import HttpResponse
import csv
import io
import logging

from ...infrastructure.rate_limiter import rate_limit
from ...infrastructure.rate_limiter import get_client_ip as _get_client_ip
from ...infrastructure.audit_logger import get_audit_logger, AuditEventType
from ...infrastructure.mongodb.connection import get_mongo_client, get_database_name
from ...infrastructure.mongodb.admin_repository import AdminRepository
from ...infrastructure.mongodb.repositories import MongoDBUserRepository
from ...infrastructure.system.metrics_collector import get_metrics_collector
from ...infrastructure.jwt_service import JWTService
from ...use_cases.admin.model_health import GetModelHealthUseCase
from ...use_cases.admin.analysis_stats import (
    GetAnalysisStatisticsUseCase,
    GetTopScamCategoriesUseCase,
)
from ...use_cases.admin.user_stats import (
    GetUserStatisticsUseCase,
    GetUserReportsUseCase,
    GetReportByIdUseCase,
    UpdateReportStatusUseCase,
)
from ...use_cases.admin.user_management import (
    ListUsersUseCase,
    GetUserDetailsUseCase,
    DeleteUserUseCase,
    AdminResetPasswordUseCase,
    UpdateUserStatusUseCase,
    UpdateUserRolesUseCase,
)
from ...domain.admin_entities import ReportStatus, StatisticsPeriod
from ...domain.services import BCryptPasswordHasher
from .middleware import require_role, require_permission

logger = logging.getLogger(__name__)


# ==================== Helper Functions ====================

def get_jwt_service():
    """Get JWT service instance."""
    import os
    secret_key = os.getenv('JWT_SECRET_KEY', 'dev-secret-key')
    access_lifetime = int(os.getenv('JWT_ACCESS_TOKEN_LIFETIME', '900'))
    refresh_lifetime = int(os.getenv('JWT_REFRESH_TOKEN_LIFETIME', '604800'))
    return JWTService(secret_key, access_lifetime, refresh_lifetime)


def get_admin_repository():
    """Get admin repository instance."""
    client = get_mongo_client()
    db_name = get_database_name()
    return AdminRepository(client, db_name)


def get_user_repository():
    """Get user repository instance."""
    client = get_mongo_client()
    db_name = get_database_name()
    return MongoDBUserRepository(client, db_name)


def extract_user_from_request(request: Request) -> tuple:
    """
    Extract user info from JWT token.
    
    Returns:
        Tuple of (user_id, email, roles) or (None, None, []) if not authenticated
    """
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return None, None, []
    
    token = auth_header[7:]
    try:
        jwt_service = get_jwt_service()
        payload = jwt_service.verify_access_token(token)
        return (
            payload.get('user_id'),
            payload.get('email'),
            payload.get('roles', [])
        )
    except Exception as e:
        logger.warning(f"JWT verification failed: {e}")
        return None, None, []


def require_admin(request: Request) -> Optional[Response]:
    """
    Check if request is from an admin user.
    
    Returns:
        Response with error if not admin, None if authorized
    """
    user_id, email, roles = extract_user_from_request(request)
    
    if not user_id:
        return Response({
            'error': {
                'code': 'AUTHENTICATION_REQUIRED',
                'message': 'Authentication required'
            }
        }, status=status.HTTP_401_UNAUTHORIZED)
    
    if 'admin' not in roles and 'super_admin' not in roles:
        return Response({
            'error': {
                'code': 'PERMISSION_DENIED',
                'message': 'Admin role required'
            }
        }, status=status.HTTP_403_FORBIDDEN)
    
    return None


def parse_date_param(date_str: str) -> Optional[datetime]:
    """Parse date string to datetime object."""
    if not date_str:
        return None
    try:
        # Support multiple formats
        for fmt in ['%Y-%m-%d', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%dT%H:%M:%SZ']:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        return None
    except Exception:
        return None


def parse_period_param(period_str: str) -> StatisticsPeriod:
    """Parse period string to StatisticsPeriod enum."""
    period_map = {
        'day': StatisticsPeriod.DAY,
        'week': StatisticsPeriod.WEEK,
        'month': StatisticsPeriod.MONTH,
        'year': StatisticsPeriod.YEAR,
        'all': StatisticsPeriod.ALL_TIME,
        'all_time': StatisticsPeriod.ALL_TIME,
    }
    return period_map.get(period_str.lower(), StatisticsPeriod.ALL_TIME) if period_str else StatisticsPeriod.ALL_TIME


def _resolve_reporter_info(report_data: Dict[str, Any], admin_repo: AdminRepository) -> Dict[str, Optional[str]]:
    """Resolve reporter identity details for a user report payload."""
    user_id = report_data.get('user_id')
    user_email = report_data.get('user_email')

    reporter: Dict[str, Optional[str]] = {
        'user_id': user_id,
        'email': user_email,
        'username': None,
    }

    query_conditions = []
    if user_id:
        query_conditions.extend([
            {'user_id': user_id},
            {'id': user_id},
        ])
    if user_email:
        query_conditions.append({'email': user_email})

    user_doc: Optional[Dict[str, Any]] = None
    if query_conditions:
        lookup_result = admin_repo.users_collection.find_one(
            {'$or': query_conditions},
            {'username': 1, 'email': 1, 'user_id': 1, 'id': 1},
        )
        if isinstance(lookup_result, dict):
            user_doc = lookup_result

    if isinstance(user_doc, dict):
        reporter['username'] = user_doc.get('username') or user_doc.get('email')
        reporter['email'] = reporter['email'] or user_doc.get('email')
        reporter['user_id'] = (
            reporter['user_id']
            or user_doc.get('user_id')
            or user_doc.get('id')
            or (str(user_doc.get('_id')) if user_doc.get('_id') is not None else None)
        )

    if not reporter['username'] and reporter['email']:
        reporter['username'] = str(reporter['email']).split('@')[0]
    if not reporter['username'] and reporter['user_id']:
        reporter['username'] = str(reporter['user_id'])

    return reporter


def _enrich_report_payload(report_data: Dict[str, Any], admin_repo: AdminRepository) -> Dict[str, Any]:
    """Attach computed reporter object to a report payload."""
    enriched = dict(report_data)
    enriched['reported_by'] = _resolve_reporter_info(enriched, admin_repo)
    return enriched


def _format_period_for_filename(period: StatisticsPeriod) -> str:
    return period.value if period else "all_time"


def _build_analysis_stats_export_csv(stats: dict, categories: list, metadata: Optional[dict] = None) -> str:
    """Build CSV content for analysis stats export."""
    output = io.StringIO()
    writer = csv.writer(output)
    metadata = metadata or {}

    total_count = stats.get('total_count', 0) or 0
    previous_total_count = stats.get('previous_total_count', 0) or 0
    scam_count = stats.get('scam_count', 0) or 0
    previous_scam_count = stats.get('previous_scam_count', 0) or 0
    high_risk_count = stats.get('high_risk_count', 0) or 0
    medium_risk_count = stats.get('medium_risk_count', 0) or 0
    low_risk_count = stats.get('low_risk_count', 0) or 0
    legitimate_count = stats.get('legitimate_count', 0) or 0

    def pct(value: int, total: int) -> float:
        if not total:
            return 0.0
        return round((value / total) * 100, 2)

    def change_pct(current: int, previous: int) -> float:
        if not previous:
            return 0.0
        return round(((current - previous) / previous) * 100, 2)

    writer.writerow(["Metadata", "Value"])
    writer.writerow(["Generated By", metadata.get('generated_by', 'unknown')])
    writer.writerow(["Generated At (UTC)", metadata.get('generated_at_utc', datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'))])
    writer.writerow(["Timezone", metadata.get('timezone', 'UTC')])
    writer.writerow(["Filters Applied", metadata.get('filters_applied', '')])
    writer.writerow([])

    writer.writerow(["Summary Metric", "Value"])
    writer.writerow(["Period", stats.get('period') or 'all_time'])
    writer.writerow(["Start Date", stats.get('start_date') or 'N/A'])
    writer.writerow(["End Date", stats.get('end_date') or 'N/A'])
    writer.writerow(["Calculated At", stats.get('calculated_at') or 'N/A'])
    writer.writerow(["Total Analyses", total_count])
    writer.writerow(["Previous Total Analyses", previous_total_count])
    writer.writerow(["Total Analyses Change (%)", change_pct(total_count, previous_total_count)])
    writer.writerow(["Scams Detected", scam_count])
    writer.writerow(["Previous Scams Detected", previous_scam_count])
    writer.writerow(["Scam Detection Change (%)", change_pct(scam_count, previous_scam_count)])
    writer.writerow(["Scam Detection Rate (%)", round(stats.get('scam_rate_percent', 0.0) or 0.0, 2)])
    writer.writerow(["High Risk Count", high_risk_count])
    writer.writerow(["High Risk Rate (%)", pct(high_risk_count, total_count)])
    writer.writerow(["Medium Risk Count", medium_risk_count])
    writer.writerow(["Medium Risk Rate (%)", pct(medium_risk_count, total_count)])
    writer.writerow(["Low Risk Count", low_risk_count])
    writer.writerow(["Low Risk Rate (%)", pct(low_risk_count, total_count)])
    writer.writerow(["Legitimate Count", legitimate_count])
    writer.writerow(["Legitimate Rate (%)", pct(legitimate_count, total_count)])
    writer.writerow(["Top Scam Category", stats.get('top_scam_category') or 'N/A'])

    writer.writerow([])
    writer.writerow(["Confidence Distribution", "Bucket", "Count", "Share (%)"])
    for bucket in stats.get('confidence_distribution', []) or []:
        writer.writerow([
            "Confidence",
            bucket.get('bucket') or '',
            bucket.get('count', 0),
            round(bucket.get('percentage', 0.0) or 0.0, 2),
        ])

    writer.writerow([])
    writer.writerow(["Risk Breakdown", "Count", "Share (%)"])
    writer.writerow(["High Risk", high_risk_count, pct(high_risk_count, total_count)])
    writer.writerow(["Medium Risk", medium_risk_count, pct(medium_risk_count, total_count)])
    writer.writerow(["Low Risk", low_risk_count, pct(low_risk_count, total_count)])
    writer.writerow(["Legitimate", legitimate_count, pct(legitimate_count, total_count)])

    writer.writerow([])
    writer.writerow(["Top Scam Categories", "Rank", "Category", "Detections", "Share (%)", "Severity"])
    for idx, category in enumerate(categories or [], start=1):
        writer.writerow([
            "Category",
            idx,
            category.get('category') or 'Unknown',
            category.get('count', 0),
            round(category.get('percentage', 0.0) or 0.0, 2),
            category.get('severity') or 'unknown',
        ])

    writer.writerow([])
    writer.writerow(["Daily Activity", "Date", "Total", "Scams", "Legitimate", "Detection Rate (%)"])
    for day in stats.get('daily_counts', []) or []:
        total = day.get('total', 0) or 0
        scams = day.get('scams', 0) or 0
        legitimate = day.get('legitimate', 0) or 0
        writer.writerow([
            "Day",
            day.get('date') or '',
            total,
            scams,
            legitimate,
            pct(scams, total),
        ])

    writer.writerow([])
    writer.writerow(["Previous Period Daily Activity", "Date", "Total", "Scams", "Legitimate", "Detection Rate (%)"])
    for day in stats.get('previous_daily_counts', []) or []:
        total = day.get('total', 0) or 0
        scams = day.get('scams', 0) or 0
        legitimate = day.get('legitimate', 0) or 0
        writer.writerow([
            "Previous Day",
            day.get('date') or '',
            total,
            scams,
            legitimate,
            pct(scams, total),
        ])

    return output.getvalue()


# ==================== Model Health Endpoints ====================

@api_view(['GET'])
@rate_limit('api_read')
def model_health(request: Request) -> Response:
    """
    Get current model health metrics.
    
    Returns GPU/CPU usage, memory, token counts, and processing speed.
    
    Requires: admin role + view_model_health permission
    """
    # Check admin authorization
    auth_error = require_admin(request)
    if auth_error:
        return auth_error
    
    try:
        metrics_collector = get_metrics_collector()
        use_case = GetModelHealthUseCase(metrics_collector)
        result = use_case.execute()
        
        if result.success:
            return Response({
                'success': True,
                'data': result.metrics.to_dict()
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'success': False,
                'error': {
                    'code': 'METRICS_ERROR',
                    'message': result.error_message
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        logger.error(f"Model health error: {e}", exc_info=True)
        return Response({
            'success': False,
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'Failed to retrieve model health metrics'
            }
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@rate_limit('api_read')
def model_health_summary(request: Request) -> Response:
    """
    Get simplified model health summary with status indicators.
    
    Requires: admin role
    """
    auth_error = require_admin(request)
    if auth_error:
        return auth_error
    
    try:
        metrics_collector = get_metrics_collector()
        use_case = GetModelHealthUseCase(metrics_collector)
        summary = use_case.get_metrics_summary()
        
        return Response({
            'success': True,
            'data': summary
        }, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Model health summary error: {e}", exc_info=True)
        return Response({
            'success': False,
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'Failed to retrieve health summary'
            }
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==================== Analysis Statistics Endpoints ====================

@api_view(['GET'])
@rate_limit('api_read')
def analysis_stats(request: Request) -> Response:
    """
    Get analysis statistics.
    
    Query params:
        - start_date: Start of date range (YYYY-MM-DD)
        - end_date: End of date range (YYYY-MM-DD)
        - period: Grouping period (day|week|month|year|all_time)
    
    Requires: admin role + view_analysis_stats permission
    """
    auth_error = require_admin(request)
    if auth_error:
        return auth_error
    
    try:
        # Parse query parameters
        start_date = parse_date_param(request.query_params.get('start_date'))
        end_date = parse_date_param(request.query_params.get('end_date'))
        period = parse_period_param(request.query_params.get('period', 'all_time'))
        
        admin_repo = get_admin_repository()
        use_case = GetAnalysisStatisticsUseCase(admin_repo)
        result = use_case.execute(
            start_date=start_date,
            end_date=end_date,
            period=period
        )
        
        if result.success:
            logger.debug("User stats API response payload: %s", result.statistics.to_dict())
            return Response({
                'success': True,
                'data': result.statistics.to_dict()
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'success': False,
                'error': {
                    'code': 'STATS_ERROR',
                    'message': result.error_message
                }
            }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Analysis stats error: {e}", exc_info=True)
        return Response({
            'success': False,
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'Failed to retrieve analysis statistics'
            }
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@rate_limit('api_read')
def top_scam_categories(request: Request) -> Response:
    """
    Get top scam categories by count.
    
    Query params:
        - start_date: Start of date range
        - end_date: End of date range
        - limit: Maximum categories to return (default 10, max 50)
    
    Requires: admin role + view_analysis_stats permission
    """
    auth_error = require_admin(request)
    if auth_error:
        return auth_error
    
    try:
        start_date = parse_date_param(request.query_params.get('start_date'))
        end_date = parse_date_param(request.query_params.get('end_date'))
        period = parse_period_param(request.query_params.get('period', 'all_time'))
        limit = min(int(request.query_params.get('limit', 10)), 50)
        
        admin_repo = get_admin_repository()
        use_case = GetTopScamCategoriesUseCase(admin_repo)
        result = use_case.execute(
            start_date=start_date,
            end_date=end_date,
            period=period,
            limit=limit
        )
        
        if result.success:
            return Response({
                'success': True,
                'data': [cat.to_dict() for cat in result.categories]
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'success': False,
                'error': {
                    'code': 'STATS_ERROR',
                    'message': result.error_message
                }
            }, status=status.HTTP_400_BAD_REQUEST)
    except ValueError:
        return Response({
            'success': False,
            'error': {
                'code': 'INVALID_INPUT',
                'message': 'Invalid limit parameter'
            }
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Top categories error: {e}", exc_info=True)
        return Response({
            'success': False,
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'Failed to retrieve top categories'
            }
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@rate_limit('api_read')
def export_analysis_stats(request: Request) -> HttpResponse:
    """
    Export analysis stats as CSV (or Excel-compatible CSV).

    Query params:
        - start_date: Start of date range (YYYY-MM-DD)
        - end_date: End of date range (YYYY-MM-DD)
        - period: Grouping period (day|week|month|year|all_time)
        - format: csv|excel (excel returns CSV with Excel MIME type)
        - limit: Number of top categories to include (default 10, max 50)

    Requires: admin role + view_analysis_stats permission
    """
    auth_error = require_admin(request)
    if auth_error:
        return auth_error

    try:
        start_date = parse_date_param(request.query_params.get('start_date'))
        end_date = parse_date_param(request.query_params.get('end_date'))
        period = parse_period_param(request.query_params.get('period', 'all_time'))
        export_format = (request.query_params.get('format', 'csv') or 'csv').lower()
        limit = min(int(request.query_params.get('limit', 10)), 50)

        if export_format not in ('csv', 'excel'):
            return Response({
                'success': False,
                'error': {
                    'code': 'INVALID_INPUT',
                    'message': 'format must be one of: csv, excel'
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        admin_repo = get_admin_repository()

        stats_result = GetAnalysisStatisticsUseCase(admin_repo).execute(
            start_date=start_date,
            end_date=end_date,
            period=period,
        )
        if not stats_result.success or not stats_result.statistics:
            return Response({
                'success': False,
                'error': {
                    'code': 'STATS_ERROR',
                    'message': stats_result.error_message or 'Failed to generate statistics export'
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        categories_result = GetTopScamCategoriesUseCase(admin_repo).execute(
            start_date=start_date,
            end_date=end_date,
            period=period,
            limit=limit,
        )
        categories = [c.to_dict() for c in (categories_result.categories if categories_result.success else [])]

        user_id, user_email, _ = extract_user_from_request(request)
        filters_applied = f"period={period.value};start_date={request.query_params.get('start_date') or ''};end_date={request.query_params.get('end_date') or ''};limit={limit};format={export_format}"
        metadata = {
            'generated_by': user_email or user_id or 'admin',
            'generated_at_utc': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
            'timezone': 'UTC',
            'filters_applied': filters_applied,
        }

        csv_content = _build_analysis_stats_export_csv(
            stats=stats_result.statistics.to_dict(),
            categories=categories,
            metadata=metadata,
        )

        date_stamp = datetime.utcnow().strftime('%Y%m%d')
        period_fragment = _format_period_for_filename(period)
        extension = 'xls' if export_format == 'excel' else 'csv'
        filename = f"analysis_stats_{period_fragment}_{date_stamp}.{extension}"
        content_type = 'application/vnd.ms-excel' if export_format == 'excel' else 'text/csv'

        response = HttpResponse(csv_content, content_type=content_type)
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response

    except ValueError:
        return Response({
            'success': False,
            'error': {
                'code': 'INVALID_INPUT',
                'message': 'Invalid limit parameter'
            }
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Analysis stats export error: {e}", exc_info=True)
        return Response({
            'success': False,
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'Failed to export analysis statistics'
            }
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==================== User Statistics Endpoints ====================

@api_view(['GET'])
@rate_limit('api_read')
def user_stats(request: Request) -> Response:
    """
    Get user statistics.
    
    Query params:
        - start_date: Start of date range
        - end_date: End of date range
        - period: Grouping period
    
    Requires: admin role + view_user_stats permission
    """
    auth_error = require_admin(request)
    if auth_error:
        return auth_error
    
    try:
        start_date = parse_date_param(request.query_params.get('start_date'))
        end_date = parse_date_param(request.query_params.get('end_date'))
        period = parse_period_param(request.query_params.get('period', 'all_time'))
        
        admin_repo = get_admin_repository()
        use_case = GetUserStatisticsUseCase(admin_repo)
        result = use_case.execute(
            start_date=start_date,
            end_date=end_date,
            period=period
        )
        
        if result.success:
            return Response({
                'success': True,
                'data': result.statistics.to_dict()
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'success': False,
                'error': {
                    'code': 'STATS_ERROR',
                    'message': result.error_message
                }
            }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"User stats error: {e}", exc_info=True)
        return Response({
            'success': False,
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'Failed to retrieve user statistics'
            }
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==================== User Reports Endpoints ====================

@api_view(['GET'])
@rate_limit('api_read')
def list_reports(request: Request) -> Response:
    """
    Get user reports with optional filtering.
    
    Query params:
        - status: Filter by status (pending|in_progress|resolved|dismissed)
        - page: Page number (default 1)
        - limit: Results per page (default 50, max 100)
    
    Requires: admin role + manage_user_reports permission
    """
    auth_error = require_admin(request)
    if auth_error:
        return auth_error
    
    try:
        # Parse status filter
        status_str = request.query_params.get('status')
        report_status = None
        if status_str:
            status_map = {
                'pending': ReportStatus.PENDING,
                'in_progress': ReportStatus.IN_PROGRESS,
                'resolved': ReportStatus.RESOLVED,
                'dismissed': ReportStatus.DISMISSED,
            }
            report_status = status_map.get(status_str.lower())
        
        # Parse pagination
        page = max(1, int(request.query_params.get('page', 1)))
        limit = min(100, max(1, int(request.query_params.get('limit', 50))))
        offset = (page - 1) * limit
        
        admin_repo = get_admin_repository()
        use_case = GetUserReportsUseCase(admin_repo)
        result = use_case.execute(
            status=report_status,
            limit=limit,
            offset=offset
        )
        
        if result.success:
            report_payloads = [_enrich_report_payload(r.to_dict(), admin_repo) for r in result.reports]
            return Response({
                'success': True,
                'data': {
                    'reports': report_payloads,
                    'total': result.total_count,
                    'page': page,
                    'limit': limit,
                    'total_pages': (result.total_count + limit - 1) // limit
                }
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'success': False,
                'error': {
                    'code': 'REPORTS_ERROR',
                    'message': result.error_message
                }
            }, status=status.HTTP_400_BAD_REQUEST)
    except ValueError:
        return Response({
            'success': False,
            'error': {
                'code': 'INVALID_INPUT',
                'message': 'Invalid pagination parameters'
            }
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"List reports error: {e}", exc_info=True)
        return Response({
            'success': False,
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'Failed to retrieve reports'
            }
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@rate_limit('api_read')
def get_report(request: Request, report_id: str) -> Response:
    """
    Get detailed information for a specific report.
    
    GET /api/admin/reports/<report_id>/
    
    Path Parameters:
        report_id: UUID of the report
    
    Returns:
        200: Report details
        404: Report not found
    
    Requires: admin role
    """
    auth_error = require_admin(request)
    if auth_error:
        return auth_error
    
    try:
        admin_repo = get_admin_repository()
        use_case = GetReportByIdUseCase(admin_repo)
        result = use_case.execute(report_id=report_id)
        
        if result.success:
            report_payload = _enrich_report_payload(result.report.to_dict(), admin_repo)
            return Response({
                'success': True,
                'data': report_payload
            }, status=status.HTTP_200_OK)
        else:
            error_status_code = status.HTTP_404_NOT_FOUND if 'not found' in result.error_message.lower() else status.HTTP_400_BAD_REQUEST
            return Response({
                'success': False,
                'error': {
                    'code': 'REPORT_NOT_FOUND',
                    'message': result.error_message
                }
            }, status=error_status_code)
    except Exception as e:
        logger.error(f"Get report error: {e}", exc_info=True)
        return Response({
            'success': False,
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'Failed to retrieve report details'
            }
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PATCH'])
@rate_limit('api_write')
def update_report(request: Request, report_id: str) -> Response:
    """
    Update a report's status.
    
    Body:
        - status: New status (pending|in_progress|resolved|dismissed)
        - resolution_notes: Optional notes
    
    Requires: admin role + manage_user_reports permission
    """
    auth_error = require_admin(request)
    if auth_error:
        return auth_error
    
    try:
        user_id, _, _ = extract_user_from_request(request)
        
        # Validate request body
        status_str = request.data.get('status')
        if not status_str:
            return Response({
                'success': False,
                'error': {
                    'code': 'INVALID_INPUT',
                    'message': 'Status is required'
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        status_map = {
            'pending': ReportStatus.PENDING,
            'in_progress': ReportStatus.IN_PROGRESS,
            'resolved': ReportStatus.RESOLVED,
            'dismissed': ReportStatus.DISMISSED,
        }
        new_status = status_map.get(status_str.lower())
        if not new_status:
            return Response({
                'success': False,
                'error': {
                    'code': 'INVALID_INPUT',
                    'message': f'Invalid status: {status_str}'
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        resolution_notes = request.data.get('resolution_notes')
        
        admin_repo = get_admin_repository()
        use_case = UpdateReportStatusUseCase(admin_repo)
        result = use_case.execute(
            report_id=report_id,
            status=new_status,
            admin_user_id=user_id,
            resolution_notes=resolution_notes
        )
        
        if result.success:
            report_payload = _enrich_report_payload(result.report.to_dict(), admin_repo)
            return Response({
                'success': True,
                'data': report_payload
            }, status=status.HTTP_200_OK)
        else:
            error_status = status.HTTP_404_NOT_FOUND if 'not found' in result.error_message.lower() else status.HTTP_400_BAD_REQUEST
            return Response({
                'success': False,
                'error': {
                    'code': 'UPDATE_ERROR',
                    'message': result.error_message
                }
            }, status=error_status)
    except Exception as e:
        logger.error(f"Update report error: {e}", exc_info=True)
        return Response({
            'success': False,
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'Failed to update report'
            }
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==================== User Management Endpoints ====================

@api_view(['GET'])
@rate_limit('api_read')
def list_users(request: Request) -> Response:
    """
    Get paginated list of users.
    
    Query params:
        - search: Search by email or username
        - role: Filter by role
        - is_active: Filter by active status (true|false)
        - is_verified: Filter by verification status (true|false)
        - page: Page number (default 1)
        - limit: Results per page (default 50, max 100)
        - sort_by: Sort field (default 'created_at')
        - sort_order: Sort direction (asc|desc, default desc)
    
    Requires: admin role + view_all_users permission
    """
    auth_error = require_admin(request)
    if auth_error:
        return auth_error
    
    try:
        # Parse filters
        search = request.query_params.get('search')
        role = request.query_params.get('role')
        
        is_active_str = request.query_params.get('is_active')
        is_active = None
        if is_active_str:
            is_active = is_active_str.lower() == 'true'
        
        is_verified_str = request.query_params.get('is_verified')
        is_verified = None
        if is_verified_str:
            is_verified = is_verified_str.lower() == 'true'
        
        # Parse pagination
        page = max(1, int(request.query_params.get('page', 1)))
        page_size = min(100, max(1, int(request.query_params.get('limit', 50))))
        sort_by = request.query_params.get('sort_by', 'created_at')
        sort_order = request.query_params.get('sort_order', 'desc')
        
        user_repo = get_user_repository()
        use_case = ListUsersUseCase(user_repo)
        result = use_case.execute(
            search=search,
            role=role,
            is_active=is_active,
            is_verified=is_verified,
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        if result.success:
            return Response({
                'success': True,
                'data': {
                    'users': [result._user_to_dict(u) for u in result.users],
                    'total': result.total_count,
                    'page': page,
                    'limit': page_size,
                    'total_pages': (result.total_count + page_size - 1) // page_size
                }
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'success': False,
                'error': {
                    'code': 'LIST_ERROR',
                    'message': result.error_message
                }
            }, status=status.HTTP_400_BAD_REQUEST)
    except ValueError:
        return Response({
            'success': False,
            'error': {
                'code': 'INVALID_INPUT',
                'message': 'Invalid pagination parameters'
            }
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"List users error: {e}", exc_info=True)
        return Response({
            'success': False,
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'Failed to retrieve users'
            }
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@rate_limit('api_read')
def get_user(request: Request, user_id: str) -> Response:
    """
    Get single user details.
    
    Requires: admin role + view_all_users permission
    """
    auth_error = require_admin(request)
    if auth_error:
        return auth_error
    
    try:
        user_repo = get_user_repository()
        use_case = GetUserDetailsUseCase(user_repo)
        result = use_case.execute(user_id)
        
        if result.success:
            return Response({
                'success': True,
                'data': result.to_dict()['data']
            }, status=status.HTTP_200_OK)
        else:
            error_status = status.HTTP_404_NOT_FOUND if 'not found' in result.error_message.lower() else status.HTTP_400_BAD_REQUEST
            return Response({
                'success': False,
                'error': {
                    'code': 'USER_ERROR',
                    'message': result.error_message
                }
            }, status=error_status)
    except Exception as e:
        logger.error(f"Get user error: {e}", exc_info=True)
        return Response({
            'success': False,
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'Failed to retrieve user'
            }
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
@rate_limit('api_write')
def delete_user(request: Request, user_id: str) -> Response:
    """
    Delete a user account.
    
    Query params:
        - hard_delete: If true, permanently delete (default false)
    
    Requires: admin role + delete_users permission
    """
    auth_error = require_admin(request)
    if auth_error:
        return auth_error
    
    try:
        admin_user_id, _, _ = extract_user_from_request(request)
        hard_delete = request.query_params.get('hard_delete', 'false').lower() == 'true'
        
        user_repo = get_user_repository()
        admin_repo = get_admin_repository()
        use_case = DeleteUserUseCase(user_repo, admin_repo)
        result = use_case.execute(
            user_id=user_id,
            admin_user_id=admin_user_id,
            hard_delete=hard_delete
        )
        
        if result.success:
            # Audit: user deleted
            get_audit_logger().log_event(
                event_type=AuditEventType.USER_DELETED,
                user_id=user_id,
                ip_address=_get_client_ip(request),
                metadata={'admin_user_id': admin_user_id, 'hard_delete': hard_delete},
            )
            return Response({
                'success': True,
                'message': result.message
            }, status=status.HTTP_200_OK)
        else:
            error_status = status.HTTP_404_NOT_FOUND if 'not found' in result.error_message.lower() else status.HTTP_400_BAD_REQUEST
            return Response({
                'success': False,
                'error': {
                    'code': 'DELETE_ERROR',
                    'message': result.error_message
                }
            }, status=error_status)
    except Exception as e:
        logger.error(f"Delete user error: {e}", exc_info=True)
        return Response({
            'success': False,
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'Failed to delete user'
            }
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@rate_limit('api_write')
def reset_user_password(request: Request, user_id: str) -> Response:
    """
    Admin reset user's password.
    
    Body:
        - new_password: New password (min 8 chars)
    
    Requires: admin role + reset_user_password permission
    """
    auth_error = require_admin(request)
    if auth_error:
        return auth_error
    
    try:
        admin_user_id, _, _ = extract_user_from_request(request)
        
        new_password = request.data.get('new_password')
        if not new_password:
            return Response({
                'success': False,
                'error': {
                    'code': 'INVALID_INPUT',
                    'message': 'New password is required'
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        user_repo = get_user_repository()
        admin_repo = get_admin_repository()
        password_hasher = BCryptPasswordHasher()
        use_case = AdminResetPasswordUseCase(user_repo, password_hasher, admin_repo)
        result = use_case.execute(
            user_id=user_id,
            new_password=new_password,
            admin_user_id=admin_user_id
        )
        
        if result.success:
            return Response({
                'success': True,
                'message': result.message
            }, status=status.HTTP_200_OK)
        else:
            error_status = status.HTTP_404_NOT_FOUND if 'not found' in result.error_message.lower() else status.HTTP_400_BAD_REQUEST
            return Response({
                'success': False,
                'error': {
                    'code': 'RESET_ERROR',
                    'message': result.error_message
                }
            }, status=error_status)
    except Exception as e:
        logger.error(f"Reset password error: {e}", exc_info=True)
        return Response({
            'success': False,
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'Failed to reset password'
            }
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PATCH'])
@rate_limit('api_write')
def update_user_status(request: Request, user_id: str) -> Response:
    """
    Update a user account status.
    
    Supports both the new `status` string and legacy `is_active` boolean.
    
    Body:
        - status: New status string ('active', 'inactive', 'suspended') [preferred]
        - is_active: Legacy boolean active status (deprecated, use status)
    
    Requires: admin role + manage_users permission
    """
    auth_error = require_admin(request)
    if auth_error:
        return auth_error
    
    try:
        admin_user_id, _, _ = extract_user_from_request(request)
        
        # Support both new 'status' string and legacy 'is_active' boolean
        status_str = request.data.get('status')
        is_active = request.data.get('is_active')
        
        if status_str is None and is_active is None:
            return Response({
                'success': False,
                'error': {
                    'code': 'INVALID_INPUT',
                    'message': 'Either status or is_active is required'
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate status if provided
        if status_str is not None:
            valid_statuses = ['active', 'inactive', 'suspended']
            if str(status_str).lower() not in valid_statuses:
                return Response({
                    'success': False,
                    'error': {
                        'code': 'INVALID_INPUT',
                        'message': f'Invalid status: {status_str}. Must be one of {valid_statuses}'
                    }
                }, status=status.HTTP_400_BAD_REQUEST)
            status_str = str(status_str).lower()
        
        user_repo = get_user_repository()
        admin_repo = get_admin_repository()
        use_case = UpdateUserStatusUseCase(user_repo, admin_repo)
        result = use_case.execute(
            user_id=user_id,
            admin_user_id=admin_user_id,
            status=status_str,
            is_active=bool(is_active) if is_active is not None and status_str is None else None
        )
        
        if result.success:
            return Response({
                'success': True,
                'message': result.message
            }, status=status.HTTP_200_OK)
        else:
            error_status = status.HTTP_404_NOT_FOUND if 'not found' in result.error_message.lower() else status.HTTP_400_BAD_REQUEST
            return Response({
                'success': False,
                'error': {
                    'code': 'STATUS_ERROR',
                    'message': result.error_message
                }
            }, status=error_status)
    except Exception as e:
        logger.error(f"Update status error: {e}", exc_info=True)
        return Response({
            'success': False,
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'Failed to update user status'
            }
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PATCH'])
@rate_limit('api_write')
def update_user_roles(request: Request, user_id: str) -> Response:
    """
    Update a user's roles.
    
    Body:
        - roles: List of role names
    
    Requires: admin role + manage_users permission
    """
    auth_error = require_admin(request)
    if auth_error:
        return auth_error
    
    try:
        admin_user_id, _, admin_roles = extract_user_from_request(request)
        
        roles = request.data.get('roles')
        if not roles or not isinstance(roles, list):
            return Response({
                'success': False,
                'error': {
                    'code': 'INVALID_INPUT',
                    'message': 'roles must be a non-empty list'
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        user_repo = get_user_repository()
        admin_repo = get_admin_repository()
        use_case = UpdateUserRolesUseCase(user_repo, admin_repo)
        result = use_case.execute(
            user_id=user_id,
            roles=roles,
            admin_user_id=admin_user_id,
            admin_roles=admin_roles
        )
        
        if result.success:
            # Audit: role updated
            get_audit_logger().log_event(
                event_type=AuditEventType.ROLE_ASSIGNED,
                user_id=user_id,
                ip_address=_get_client_ip(request),
                metadata={'admin_user_id': admin_user_id, 'new_roles': roles},
            )
            return Response({
                'success': True,
                'message': result.message
            }, status=status.HTTP_200_OK)
        else:
            error_status = status.HTTP_404_NOT_FOUND if 'not found' in result.error_message.lower() else status.HTTP_400_BAD_REQUEST
            return Response({
                'success': False,
                'error': {
                    'code': 'ROLES_ERROR',
                    'message': result.error_message
                }
            }, status=error_status)
    except Exception as e:
        logger.error(f"Update roles error: {e}", exc_info=True)
        return Response({
            'success': False,
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'Failed to update user roles'
            }
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
