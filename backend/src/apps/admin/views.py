"""
Admin app views - imports from interfaces layer.
"""

from ...interfaces.rest.admin_views import (
    # Model Health
    model_health,
    model_health_summary,
    # Analysis Statistics
    analysis_stats,
    top_scam_categories,
    # User Statistics
    user_stats,
    # User Reports
    list_reports,
    update_report,
    # User Management
    list_users,
    get_user,
    delete_user,
    reset_user_password,
    update_user_status,
    update_user_roles,
)

__all__ = [
    'model_health',
    'model_health_summary',
    'analysis_stats',
    'top_scam_categories',
    'user_stats',
    'list_reports',
    'update_report',
    'list_users',
    'get_user',
    'delete_user',
    'reset_user_password',
    'update_user_status',
    'update_user_roles',
]
