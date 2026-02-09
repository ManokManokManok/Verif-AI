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
from typing import Optional
import logging

from ...infrastructure.rate_limiter import rate_limit
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
        limit = min(int(request.query_params.get('limit', 10)), 50)
        
        admin_repo = get_admin_repository()
        use_case = GetTopScamCategoriesUseCase(admin_repo)
        result = use_case.execute(
            start_date=start_date,
            end_date=end_date,
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
            return Response({
                'success': True,
                'data': {
                    'reports': [r.to_dict() for r in result.reports],
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
            return Response({
                'success': True,
                'data': result.report.to_dict()
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
    Enable or disable a user account.
    
    Body:
        - is_active: New active status (boolean)
    
    Requires: admin role + manage_users permission
    """
    auth_error = require_admin(request)
    if auth_error:
        return auth_error
    
    try:
        admin_user_id, _, _ = extract_user_from_request(request)
        
        is_active = request.data.get('is_active')
        if is_active is None:
            return Response({
                'success': False,
                'error': {
                    'code': 'INVALID_INPUT',
                    'message': 'is_active is required'
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        user_repo = get_user_repository()
        admin_repo = get_admin_repository()
        use_case = UpdateUserStatusUseCase(user_repo, admin_repo)
        result = use_case.execute(
            user_id=user_id,
            is_active=bool(is_active),
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
