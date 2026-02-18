"""
Domain Layer

This module contains all domain entities and business logic.
Entities are framework-agnostic and contain only pure business rules.
"""

from .entities import (
    User,
    Role,
    Permission,
    AuthTokens,
    AuthResult,
    UserAlreadyExistsError,
    InvalidCredentialsError,
    UserNotFoundError,
    PermissionDeniedError,
    AuthenticationError,
)

from .admin_entities import (
    ModelHealthMetrics,
    AnalysisStatistics,
    UserStatistics,
    UserReport,
    AdminActivityLog,
    ScamCategoryBreakdown,
    ReportStatus,
    ReportType,
    StatisticsPeriod,
    AdminPermissions,
    AdminOperationError,
    UserDeletionError,
    ReportNotFoundError,
    InvalidReportStatusError,
    MetricsCollectionError,
)

__all__ = [
    # User entities
    "User",
    "Role",
    "Permission",
    "AuthTokens",
    "AuthResult",
    # User exceptions
    "UserAlreadyExistsError",
    "InvalidCredentialsError",
    "UserNotFoundError",
    "PermissionDeniedError",
    "AuthenticationError",
    # Admin entities
    "ModelHealthMetrics",
    "AnalysisStatistics",
    "UserStatistics",
    "UserReport",
    "AdminActivityLog",
    "ScamCategoryBreakdown",
    # Admin enums
    "ReportStatus",
    "ReportType",
    "StatisticsPeriod",
    "AdminPermissions",
    # Admin exceptions
    "AdminOperationError",
    "UserDeletionError",
    "ReportNotFoundError",
    "InvalidReportStatusError",
    "MetricsCollectionError",
]
