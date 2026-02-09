"""
User Reports REST API Views.

Public endpoints for users to submit reports about issues with the system.
These endpoints require authentication but NOT admin role.
"""

import os
import json
from datetime import datetime
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt

from ...domain.admin_entities import ReportType, ReportStatus
from ...use_cases.admin.user_stats import SubmitUserReportUseCase, GetUserReportsUseCase
from ...infrastructure.mongodb.admin_repository import AdminRepository
from ...infrastructure.mongodb.connection import get_mongo_client, get_database_name
from ...infrastructure.jwt_service import JWTService
from ...infrastructure.rate_limiter import rate_limit


def get_jwt_service():
    """Get JWT service instance with proper configuration."""
    secret_key = os.getenv('JWT_SECRET_KEY', 'dev-secret-key')
    access_lifetime = int(os.getenv('JWT_ACCESS_TOKEN_LIFETIME', '900'))
    refresh_lifetime = int(os.getenv('JWT_REFRESH_TOKEN_LIFETIME', '604800'))
    return JWTService(secret_key, access_lifetime, refresh_lifetime)


def get_admin_repository():
    """Get admin repository instance with proper MongoDB connection."""
    client = get_mongo_client()
    db_name = get_database_name()
    return AdminRepository(client, db_name)


def extract_user_from_request(request):
    """
    Extract user information from JWT token in Authorization header.
    
    Args:
        request: Django HTTP request
        
    Returns:
        dict: User info with 'user_id', 'email', 'roles' or None
    """
    auth_header = request.headers.get('Authorization', '')
    
    if not auth_header.startswith('Bearer '):
        return None
    
    token = auth_header[7:]  # Remove 'Bearer ' prefix
    
    try:
        jwt_service = get_jwt_service()
        payload = jwt_service.verify_token(token)
        
        if not payload:
            return None
        
        return {
            'user_id': payload.get('user_id'),
            'email': payload.get('email'),
            'roles': payload.get('roles', []),
        }
    except Exception:
        # Token verification failed
        return None


def require_auth(view_func):
    """
    Decorator to require authentication (any authenticated user).
    """
    def wrapper(request, *args, **kwargs):
        user = extract_user_from_request(request)
        if not user:
            return JsonResponse({
                'success': False,
                'error': 'Authentication required'
            }, status=401)
        
        request.auth_user = user
        return view_func(request, *args, **kwargs)
    
    return wrapper


@csrf_exempt
@require_http_methods(["POST"])
@rate_limit('api_write')  # Uses 'api_write' category for rate limiting
@require_auth
def submit_report(request):
    """
    Submit a new user report.
    
    POST /api/reports/
    
    Request body:
    {
        "report_type": "hallucination" | "false_positive" | "false_negative" | "bug" | "feedback" | "other",
        "title": "Report title (3+ chars)",
        "description": "Detailed description (10+ chars)",
        "analysis_id": "optional analysis ID",
        "analysis_ref_id": "optional analysis reference ID"
    }
    
    Returns:
        201: Report created successfully
        400: Invalid report data
        401: Authentication required
        429: Rate limit exceeded
    """
    try:
        data = json.loads(request.body.decode('utf-8'))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON in request body'
        }, status=400)
    
    # Validate report type
    report_type_str = data.get('report_type', '').lower()
    try:
        report_type = ReportType(report_type_str)
    except ValueError:
        valid_types = [t.value for t in ReportType]
        return JsonResponse({
            'success': False,
            'error': f'Invalid report_type. Must be one of: {", ".join(valid_types)}'
        }, status=400)
    
    # Get user info from request
    user = request.auth_user
    
    # Initialize repository and use case
    admin_repository = get_admin_repository()
    use_case = SubmitUserReportUseCase(admin_repository)
    
    # Execute use case
    result = use_case.execute(
        user_id=user['user_id'],
        user_email=user['email'],
        report_type=report_type,
        title=data.get('title', ''),
        description=data.get('description', ''),
        analysis_id=data.get('analysis_id'),
        analysis_ref_id=data.get('analysis_ref_id'),
    )
    
    if result.success:
        return JsonResponse({
            'success': True,
            'data': result.report.to_dict(),
            'message': 'Report submitted successfully. Thank you for your feedback!'
        }, status=201)
    else:
        return JsonResponse({
            'success': False,
            'error': result.error_message
        }, status=400)


@csrf_exempt
@require_http_methods(["GET"])
@require_auth
def get_my_reports(request):
    """
    Get the current user's own reports.
    
    GET /api/reports/
    
    Query params:
        status: Filter by status (pending, in_progress, resolved, dismissed)
        page: Page number (default 1)
        limit: Items per page (default 20, max 50)
    
    Returns:
        200: List of user's reports
        401: Authentication required
    """
    user = request.auth_user
    
    # Parse query parameters
    status_param = request.GET.get('status')
    status = None
    if status_param:
        try:
            status = ReportStatus(status_param.lower())
        except ValueError:
            pass  # Ignore invalid status, return all
    
    page = int(request.GET.get('page', 1))
    limit = min(int(request.GET.get('limit', 20)), 50)  # Max 50
    offset = (page - 1) * limit
    
    # Initialize repository and use case
    admin_repository = get_admin_repository()
    use_case = GetUserReportsUseCase(admin_repository)
    
    # Execute use case with user_id filter
    result = use_case.execute(
        status=status,
        user_id=user['user_id'],
        limit=limit,
        offset=offset,
    )
    
    if result.success:
        total_pages = (result.total_count + limit - 1) // limit if limit > 0 else 1
        return JsonResponse({
            'success': True,
            'data': {
                'reports': [r.to_dict() for r in result.reports],
                'total': result.total_count,
                'page': page,
                'limit': limit,
                'total_pages': total_pages,
            }
        })
    else:
        return JsonResponse({
            'success': False,
            'error': result.error_message
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def get_report_types(request):
    """
    Get available report types with descriptions.
    
    GET /api/reports/types/
    
    This endpoint is public (no auth required) so users can see
    available report categories before logging in.
    
    Returns:
        200: List of report types
    """
    report_types = [
        {
            'value': ReportType.HALLUCINATION.value,
            'label': 'AI Hallucination',
            'description': 'The AI provided incorrect or fabricated information',
        },
        {
            'value': ReportType.FALSE_POSITIVE.value,
            'label': 'False Positive',
            'description': 'Legitimate content was incorrectly flagged as a scam',
        },
        {
            'value': ReportType.FALSE_NEGATIVE.value,
            'label': 'False Negative',
            'description': 'A scam was not detected or was marked as legitimate',
        },
        {
            'value': ReportType.BUG.value,
            'label': 'Bug Report',
            'description': 'A technical issue or error in the application',
        },
        {
            'value': ReportType.FEEDBACK.value,
            'label': 'Feedback',
            'description': 'General feedback or suggestions for improvement',
        },
        {
            'value': ReportType.OTHER.value,
            'label': 'Other',
            'description': 'Other issues not covered by the above categories',
        },
    ]
    
    return JsonResponse({
        'success': True,
        'data': report_types
    })
