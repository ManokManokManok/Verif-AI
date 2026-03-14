"""
Admin Domain Entities

Domain entities for admin dashboard features including model health monitoring,
analysis statistics, user statistics, and user management.
These entities are framework-agnostic and contain only business logic.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
import uuid


class ReportStatus(str, Enum):
    """Status values for user reports."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"


class ReportType(str, Enum):
    """Types of user reports."""
    HALLUCINATION = "hallucination"
    FALSE_POSITIVE = "false_positive"
    FALSE_NEGATIVE = "false_negative"
    BUG = "bug"
    FEEDBACK = "feedback"
    OTHER = "other"


class StatisticsPeriod(str, Enum):
    """Time periods for statistics aggregation."""
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    YEAR = "year"
    ALL_TIME = "all_time"


@dataclass
class ModelHealthMetrics:
    """
    Domain entity representing model health and system metrics.
    
    Used for monitoring the AI model's performance and resource utilization.
    """
    # GPU Metrics (required)
    gpu_usage_percent: float  # 0-100
    gpu_memory_used_mb: float
    gpu_memory_total_mb: float
    
    # CPU Metrics (required)
    cpu_usage_percent: float  # 0-100
    
    # Memory Metrics (required)
    memory_used_mb: float
    memory_total_mb: float
    memory_usage_percent: float  # 0-100
    
    # Optional fields with defaults
    gpu_temperature_celsius: Optional[float] = None
    cpu_count: int = 1
    
    # Disk Metrics
    disk_used_mb: float = 0.0
    disk_total_mb: float = 0.0
    disk_usage_percent: float = 0.0
    
    # Active Sessions
    active_sessions: int = 0
    
    # Cache Status
    cache_hit_rate: float = 0.0
    cache_size_mb: float = 0.0
    
    # Model Performance Metrics
    model_name: str = "verif-ai-bert"
    token_count_today: int = 0
    token_count_total: int = 0
    avg_processing_speed_ms: float = 0.0
    requests_today: int = 0
    requests_total: int = 0
    
    # System Uptime
    uptime_seconds: int = 0
    last_model_reload: Optional[datetime] = None

    # System info (collected once at startup)
    platform: str = ''
    python_version: str = ''
    django_version: str = ''
    load_average: Optional[float] = None
    database_connected: bool = True
    cache_connected: bool = True

    # Timestamp
    collected_at: datetime = field(default_factory=datetime.utcnow)
    
    @property
    def gpu_memory_usage_percent(self) -> float:
        """Calculate GPU memory usage percentage."""
        if self.gpu_memory_total_mb == 0:
            return 0.0
        return (self.gpu_memory_used_mb / self.gpu_memory_total_mb) * 100
    
    @property
    def is_gpu_available(self) -> bool:
        """Check if GPU is available."""
        return self.gpu_memory_total_mb > 0
    
    @property
    def uptime_formatted(self) -> str:
        """Format uptime as human-readable string."""
        days, remainder = divmod(self.uptime_seconds, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        parts = []
        if days > 0:
            parts.append(f"{days}d")
        if hours > 0:
            parts.append(f"{hours}h")
        if minutes > 0:
            parts.append(f"{minutes}m")
        parts.append(f"{seconds}s")
        
        return " ".join(parts)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "gpu": {
                "usage_percent": self.gpu_usage_percent,
                "memory_used_mb": self.gpu_memory_used_mb,
                "memory_total_mb": self.gpu_memory_total_mb,
                "memory_usage_percent": self.gpu_memory_usage_percent,
                "temperature_celsius": self.gpu_temperature_celsius,
                "available": self.is_gpu_available,
            },
            "cpu": {
                "usage_percent": self.cpu_usage_percent,
                "count": self.cpu_count,
            },
            "memory": {
                "used_mb": self.memory_used_mb,
                "total_mb": self.memory_total_mb,
                "usage_percent": self.memory_usage_percent,
            },
            "disk": {
                "used_mb": self.disk_used_mb,
                "total_mb": self.disk_total_mb,
                "usage_percent": self.disk_usage_percent,
            },
            "active_sessions": self.active_sessions,
            "cache": {
                "hit_rate": self.cache_hit_rate,
                "size_mb": self.cache_size_mb,
                "connected": self.cache_connected,
            },
            "model": {
                "name": self.model_name,
                "token_count_today": self.token_count_today,
                "token_count_total": self.token_count_total,
                "avg_processing_speed_ms": self.avg_processing_speed_ms,
                "requests_today": self.requests_today,
                "requests_total": self.requests_total,
            },
            "system": {
                "uptime_seconds": self.uptime_seconds,
                "uptime_formatted": self.uptime_formatted,
                "last_model_reload": self.last_model_reload.isoformat() if self.last_model_reload else None,
                "platform": self.platform,
                "python_version": self.python_version,
                "django_version": self.django_version,
                "load_average": self.load_average,
            },
            "database": {
                "connected": self.database_connected,
            },
            "collected_at": self.collected_at.isoformat(),
        }


@dataclass
class ScamCategoryBreakdown:
    """Breakdown of analyses by scam category."""
    category: str
    count: int
    percentage: float  # 0-100
    severity: str = "medium"  # high, medium, low
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category,
            "count": self.count,
            "percentage": round(self.percentage, 2),
            "severity": self.severity,
        }


@dataclass
class AnalysisStatistics:
    """
    Domain entity representing analysis statistics.
    
    Provides aggregated data about scam detection analyses.
    """
    # Total counts
    total_count: int
    high_risk_count: int  # is_scam = True with confidence >= 70%
    medium_risk_count: int  # is_scam = True with confidence 40-69%
    low_risk_count: int  # is_scam = True with confidence < 40% OR is_scam = False
    legitimate_count: int  # is_scam = False
    
    # Scam categories breakdown
    scam_categories_breakdown: List[ScamCategoryBreakdown] = field(default_factory=list)
    
    # Time period
    period: StatisticsPeriod = StatisticsPeriod.ALL_TIME
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    
    # Trends (optional, for time-series data)
    daily_counts: List[Dict[str, Any]] = field(default_factory=list)
    
    # Timestamp
    calculated_at: datetime = field(default_factory=datetime.utcnow)
    
    @property
    def scam_count(self) -> int:
        """Total number of detected scams."""
        return self.high_risk_count + self.medium_risk_count
    
    @property
    def scam_rate_percent(self) -> float:
        """Percentage of analyses that detected scams."""
        if self.total_count == 0:
            return 0.0
        return (self.scam_count / self.total_count) * 100
    
    @property
    def top_scam_category(self) -> Optional[str]:
        """Get the most common scam category."""
        if not self.scam_categories_breakdown:
            return None
        return max(self.scam_categories_breakdown, key=lambda x: x.count).category
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "total_count": self.total_count,
            "high_risk_count": self.high_risk_count,
            "medium_risk_count": self.medium_risk_count,
            "low_risk_count": self.low_risk_count,
            "legitimate_count": self.legitimate_count,
            "scam_count": self.scam_count,
            "scam_rate_percent": round(self.scam_rate_percent, 2),
            "top_scam_category": self.top_scam_category,
            "scam_categories_breakdown": [
                cat.to_dict() for cat in self.scam_categories_breakdown
            ],
            "period": self.period.value,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "daily_counts": self.daily_counts,
            "calculated_at": self.calculated_at.isoformat(),
        }


@dataclass
class UserStatistics:
    """
    Domain entity representing user statistics.
    
    Provides aggregated data about users and website activity.
    """
    # User counts
    total_users: int
    new_users_count: int  # New users in the period
    active_users_count: int  # Users who performed analyses in the period
    verified_users_count: int
    unverified_users_count: int
    
    # Website activity
    website_visits: int = 0
    unique_visitors: int = 0
    
    # User engagement
    total_analyses_by_users: int = 0
    avg_analyses_per_user: float = 0.0
    power_users: int = 0  # Users with >50 analyses
    
    # Time period
    period: StatisticsPeriod = StatisticsPeriod.ALL_TIME
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    
    # Trends (optional, for time-series data)
    daily_signups: List[Dict[str, Any]] = field(default_factory=list)
    daily_visits: List[Dict[str, Any]] = field(default_factory=list)
    
    # Timestamp
    calculated_at: datetime = field(default_factory=datetime.utcnow)
    
    @property
    def user_growth_rate(self) -> float:
        """Calculate user growth rate in the period."""
        if self.total_users == 0:
            return 0.0
        return (self.new_users_count / self.total_users) * 100
    
    @property
    def verification_rate(self) -> float:
        """Calculate email verification rate."""
        if self.total_users == 0:
            return 0.0
        return (self.verified_users_count / self.total_users) * 100
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "total_users": self.total_users,
            "new_users_count": self.new_users_count,
            "active_users_count": self.active_users_count,
            "verified_users_count": self.verified_users_count,
            "unverified_users_count": self.unverified_users_count,
            "user_growth_rate": round(self.user_growth_rate, 2),
            "verification_rate": round(self.verification_rate, 2),
            "website_visits": self.website_visits,
            "unique_visitors": self.unique_visitors,
            "total_analyses_by_users": self.total_analyses_by_users,
            "avg_analyses_per_user": round(self.avg_analyses_per_user, 2),
            "power_users": self.power_users,
            "period": self.period.value,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "daily_signups": self.daily_signups,
            "daily_visits": self.daily_visits,
            "calculated_at": self.calculated_at.isoformat(),
        }


@dataclass
class UserReport:
    """
    Domain entity representing a user-submitted report.
    
    Used for tracking issues reported by users such as model hallucinations,
    false positives/negatives, bugs, or general feedback.
    """
    # Identification
    id: Optional[str] = None
    report_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    # Reporter information
    user_id: str = ""
    user_email: Optional[str] = None
    
    # Report details
    report_type: ReportType = ReportType.OTHER
    title: str = ""
    description: str = ""
    
    # Context (optional - for linking to specific analysis)
    analysis_id: Optional[str] = None
    analysis_ref_id: Optional[str] = None
    
    # Status tracking
    status: ReportStatus = ReportStatus.PENDING
    assigned_to: Optional[str] = None  # Admin user ID
    resolution_notes: Optional[str] = None
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    resolved_at: Optional[datetime] = None
    
    def __post_init__(self):
        if not self.id:
            self.id = self.report_id
    
    @property
    def is_open(self) -> bool:
        """Check if report is still open."""
        return self.status in [ReportStatus.PENDING, ReportStatus.IN_PROGRESS]
    
    @property
    def is_resolved(self) -> bool:
        """Check if report has been resolved or dismissed."""
        return self.status in [ReportStatus.RESOLVED, ReportStatus.DISMISSED]
    
    def resolve(self, notes: Optional[str] = None) -> None:
        """Mark report as resolved."""
        self.status = ReportStatus.RESOLVED
        self.resolution_notes = notes
        self.resolved_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def dismiss(self, notes: Optional[str] = None) -> None:
        """Mark report as dismissed."""
        self.status = ReportStatus.DISMISSED
        self.resolution_notes = notes
        self.resolved_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def assign(self, admin_user_id: str) -> None:
        """Assign report to an admin."""
        self.assigned_to = admin_user_id
        self.status = ReportStatus.IN_PROGRESS
        self.updated_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "id": self.id,
            "report_id": self.report_id,
            "user_id": self.user_id,
            "user_email": self.user_email,
            "report_type": self.report_type.value,
            "title": self.title,
            "description": self.description,
            "analysis_id": self.analysis_id,
            "analysis_ref_id": self.analysis_ref_id,
            "status": self.status.value,
            "assigned_to": self.assigned_to,
            "resolution_notes": self.resolution_notes,
            "is_open": self.is_open,
            "is_resolved": self.is_resolved,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UserReport":
        """Create a UserReport from a dictionary."""
        return cls(
            id=data.get("id") or data.get("_id"),
            report_id=data.get("report_id", str(uuid.uuid4())),
            user_id=data.get("user_id", ""),
            user_email=data.get("user_email"),
            report_type=ReportType(data.get("report_type", "other")),
            title=data.get("title", ""),
            description=data.get("description", ""),
            analysis_id=data.get("analysis_id"),
            analysis_ref_id=data.get("analysis_ref_id"),
            status=ReportStatus(data.get("status", "pending")),
            assigned_to=data.get("assigned_to"),
            resolution_notes=data.get("resolution_notes"),
            created_at=data.get("created_at", datetime.utcnow()),
            updated_at=data.get("updated_at", datetime.utcnow()),
            resolved_at=data.get("resolved_at"),
        )


@dataclass
class AdminActivityLog:
    """
    Domain entity for tracking admin actions for audit purposes.
    """
    id: Optional[str] = None
    log_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    # Admin information
    admin_user_id: str = ""
    admin_email: Optional[str] = None
    
    # Action details
    action: str = ""  # e.g., "delete_user", "reset_password", "resolve_report"
    resource_type: str = ""  # e.g., "user", "report"
    resource_id: Optional[str] = None
    
    # Additional context
    details: Dict[str, Any] = field(default_factory=dict)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    
    # Timestamp
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage/API responses."""
        return {
            "id": self.id or self.log_id,
            "log_id": self.log_id,
            "admin_user_id": self.admin_user_id,
            "admin_email": self.admin_email,
            "action": self.action,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "details": self.details,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "created_at": self.created_at.isoformat(),
        }


# Admin-specific permissions (constants for reference)
class AdminPermissions:
    """Constants for admin-specific permissions."""
    VIEW_MODEL_HEALTH = "view_model_health"
    VIEW_ANALYSIS_STATS = "view_analysis_stats"
    VIEW_USER_STATS = "view_user_stats"
    MANAGE_USER_REPORTS = "manage_user_reports"
    DELETE_USER = "delete_user"
    RESET_USER_PASSWORD = "reset_user_password"
    VIEW_SYSTEM_LOGS = "view_system_logs"
    MANAGE_USERS = "manage_users"
    VIEW_ALL_USERS = "view_all_users"
    
    @classmethod
    def all_permissions(cls) -> List[str]:
        """Get all admin permissions."""
        return [
            cls.VIEW_MODEL_HEALTH,
            cls.VIEW_ANALYSIS_STATS,
            cls.VIEW_USER_STATS,
            cls.MANAGE_USER_REPORTS,
            cls.DELETE_USER,
            cls.RESET_USER_PASSWORD,
            cls.VIEW_SYSTEM_LOGS,
            cls.MANAGE_USERS,
            cls.VIEW_ALL_USERS,
        ]


# Custom exceptions for admin operations
class AdminOperationError(Exception):
    """Base exception for admin operations."""
    pass


class UserDeletionError(AdminOperationError):
    """Exception raised when user deletion fails."""
    pass


class ReportNotFoundError(AdminOperationError):
    """Exception raised when a report is not found."""
    pass


class InvalidReportStatusError(AdminOperationError):
    """Exception raised when an invalid report status transition is attempted."""
    pass


class MetricsCollectionError(AdminOperationError):
    """Exception raised when metrics collection fails."""
    pass


class InvalidReportDataError(AdminOperationError):
    """Exception raised when report data is invalid."""
    pass


class InsufficientPermissionsError(AdminOperationError):
    """Exception raised when user lacks required permissions."""
    pass
