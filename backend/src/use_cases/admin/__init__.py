"""
Admin Use Cases

Business logic for admin dashboard features including model health monitoring,
analysis statistics, user statistics, and user management.
"""

from .model_health import GetModelHealthUseCase
from .analysis_stats import (
    GetAnalysisStatisticsUseCase,
    GetTopScamCategoriesUseCase,
)
from .user_stats import (
    GetUserStatisticsUseCase,
    GetUserReportsUseCase,
    SubmitUserReportUseCase,
    UpdateReportStatusUseCase,
)
from .user_management import (
    ListUsersUseCase,
    GetUserDetailsUseCase,
    DeleteUserUseCase,
    AdminResetPasswordUseCase,
    UpdateUserStatusUseCase,
    UpdateUserRolesUseCase,
)

__all__ = [
    # Model Health
    "GetModelHealthUseCase",
    # Analysis Statistics
    "GetAnalysisStatisticsUseCase",
    "GetTopScamCategoriesUseCase",
    # User Statistics
    "GetUserStatisticsUseCase",
    "GetUserReportsUseCase",
    "SubmitUserReportUseCase",
    "UpdateReportStatusUseCase",
    # User Management
    "ListUsersUseCase",
    "GetUserDetailsUseCase",
    "DeleteUserUseCase",
    "AdminResetPasswordUseCase",
    "UpdateUserStatusUseCase",
    "UpdateUserRolesUseCase",
]
