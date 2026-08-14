"""
User Statistics Use Cases

Use cases for retrieving user statistics, managing user reports,
and handling website visit analytics.
"""

from typing import Protocol, Optional, List, Tuple
from dataclasses import dataclass
from datetime import datetime
import uuid

from ...domain.admin_entities import (
    UserStatistics,
    UserReport,
    ReportStatus,
    ReportType,
    StatisticsPeriod,
    ReportNotFoundError,
    InvalidReportDataError,
)


class AdminRepository(Protocol):
    """Protocol for admin data repository."""
    def get_user_statistics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        period: StatisticsPeriod = StatisticsPeriod.ALL_TIME
    ) -> UserStatistics: ...
    
    def create_report(self, report: UserReport) -> UserReport: ...
    
    def get_reports(
        self,
        status: Optional[ReportStatus] = None,
        user_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Tuple[List[UserReport], int]: ...
    
    def get_report_by_id(self, report_id: str) -> Optional[UserReport]: ...
    
    def update_report_status(
        self,
        report_id: str,
        status: ReportStatus,
        resolution_notes: Optional[str] = None,
        assigned_to: Optional[str] = None
    ) -> UserReport: ...
    
    def log_admin_activity(self, log) -> None: ...


@dataclass
class UserStatisticsResult:
    """Result object for user statistics use case."""
    statistics: Optional[UserStatistics]
    success: bool
    error_message: Optional[str] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary for API response."""
        result = {"success": self.success}
        if self.success and self.statistics:
            result["data"] = self.statistics.to_dict()
        else:
            result["error"] = self.error_message
        return result


@dataclass
class UserReportsResult:
    """Result object for user reports use case."""
    reports: List[UserReport]
    total_count: int
    success: bool
    error_message: Optional[str] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary for API response."""
        result = {"success": self.success}
        if self.success:
            result["data"] = {
                "reports": [r.to_dict() for r in self.reports],
                "total": self.total_count,
            }
        else:
            result["error"] = self.error_message
        return result


@dataclass
class ReportResult:
    """Result object for single report operations."""
    report: Optional[UserReport]
    success: bool
    error_message: Optional[str] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary for API response."""
        result = {"success": self.success}
        if self.success and self.report:
            result["data"] = self.report.to_dict()
        else:
            result["error"] = self.error_message
        return result


class GetUserStatisticsUseCase:
    """
    Use case for retrieving user statistics.
    
    Retrieves aggregated user metrics including:
    - Total users count
    - New users in period
    - Active users count
    - Website visits and unique visitors
    - User signups trend
    
    This use case is read-only and performs aggregation queries.
    """
    
    def __init__(self, admin_repository: AdminRepository):
        """
        Initialize the use case.
        
        Args:
            admin_repository: Repository for admin data aggregations
        """
        self._admin_repository = admin_repository
    
    def execute(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        period: StatisticsPeriod = StatisticsPeriod.ALL_TIME
    ) -> UserStatisticsResult:
        """
        Execute the use case to retrieve user statistics.
        
        Args:
            start_date: Start of date range
            end_date: End of date range
            period: Time period for grouping
            
        Returns:
            UserStatisticsResult containing statistics or error
        """
        try:
            # Validate date range
            if start_date and end_date and start_date > end_date:
                return UserStatisticsResult(
                    statistics=None,
                    success=False,
                    error_message="Start date must be before end date"
                )
            
            statistics = self._admin_repository.get_user_statistics(
                start_date=start_date,
                end_date=end_date,
                period=period
            )
            
            return UserStatisticsResult(
                statistics=statistics,
                success=True
            )
        except Exception as e:
            return UserStatisticsResult(
                statistics=None,
                success=False,
                error_message=f"Failed to retrieve user statistics: {str(e)}"
            )
    
    def get_summary(self) -> dict:
        """
        Get a simplified summary of user statistics.
        
        Returns:
            Dict with key user metrics
        """
        result = self.execute()
        
        if not result.success:
            return {"error": result.error_message}
        
        stats = result.statistics
        
        return {
            "total_users": stats.total_users,
            "new_users": stats.new_users_count,
            "active_users": stats.active_users_count,
            "verified_users": stats.verified_users_count,
            "unverified_users": stats.unverified_users_count,
            "website_visits": stats.website_visits,
            "unique_visitors": stats.unique_visitors,
            "engagement_rate": round(
                (stats.active_users_count / stats.total_users * 100) if stats.total_users > 0 else 0, 1
            ),
            "verification_rate": round(
                (stats.verified_users_count / stats.total_users * 100) if stats.total_users > 0 else 0, 1
            ),
        }


class GetUserReportsUseCase:
    """
    Use case for retrieving user reports.
    
    Returns paginated list of reports (hallucination reports, bugs, feedback, etc.)
    with optional status filtering.
    """
    
    def __init__(self, admin_repository: AdminRepository):
        """
        Initialize the use case.
        
        Args:
            admin_repository: Repository for admin data operations
        """
        self._admin_repository = admin_repository
    
    def execute(
        self,
        status: Optional[ReportStatus] = None,
        user_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> UserReportsResult:
        """
        Execute the use case to retrieve user reports.
        
        Args:
            status: Filter by report status
            user_id: Filter by user ID (admin can see all, users only their own)
            limit: Maximum reports to return
            offset: Number to skip for pagination
            
        Returns:
            UserReportsResult containing reports or error
        """
        try:
            # Validate pagination
            if limit < 1:
                limit = 1
            elif limit > 100:
                limit = 100
            
            if offset < 0:
                offset = 0
            
            reports, total = self._admin_repository.get_reports(
                status=status,
                user_id=user_id,
                limit=limit,
                offset=offset
            )
            
            return UserReportsResult(
                reports=reports,
                total_count=total,
                success=True
            )
        except Exception as e:
            return UserReportsResult(
                reports=[],
                total_count=0,
                success=False,
                error_message=f"Failed to retrieve reports: {str(e)}"
            )
    
    def get_pending_count(self) -> int:
        """
        Get count of pending reports.
        
        Returns:
            Number of pending reports
        """
        result = self.execute(status=ReportStatus.PENDING, limit=1)
        return result.total_count if result.success else 0


class GetReportByIdUseCase:
    """
    Use case for retrieving a single report by ID.
    
    Returns detailed report information for the admin detail view.
    """
    
    def __init__(self, admin_repository: AdminRepository):
        """
        Initialize the use case.
        
        Args:
            admin_repository: Repository for admin data operations
        """
        self._admin_repository = admin_repository
    
    def execute(self, report_id: str) -> ReportResult:
        """
        Execute the use case to retrieve a report by ID.
        
        Args:
            report_id: ID of the report to retrieve
            
        Returns:
            ReportResult containing the report or error
        """
        try:
            if not report_id:
                return ReportResult(
                    report=None,
                    success=False,
                    error_message="Report ID is required"
                )
            
            report = self._admin_repository.get_report_by_id(report_id)
            
            if not report:
                return ReportResult(
                    report=None,
                    success=False,
                    error_message=f"Report not found: {report_id}"
                )
            
            return ReportResult(
                report=report,
                success=True
            )
        except Exception as e:
            return ReportResult(
                report=None,
                success=False,
                error_message=f"Failed to retrieve report: {str(e)}"
            )


class SubmitUserReportUseCase:
    """
    Use case for users to submit reports.
    
    Allows users to submit reports about issues such as:
    - Hallucinations (false AI outputs)
    - False positives/negatives
    - Bugs
    - General feedback
    """
    
    def __init__(self, admin_repository: AdminRepository):
        """
        Initialize the use case.
        
        Args:
            admin_repository: Repository for admin data operations
        """
        self._admin_repository = admin_repository
    
    def execute(
        self,
        user_id: str,
        user_email: str,
        report_type: ReportType,
        title: str,
        description: str,
        analysis_id: Optional[str] = None,
        analysis_ref_id: Optional[str] = None
    ) -> ReportResult:
        """
        Execute the use case to submit a new report.
        
        Args:
            user_id: ID of the user submitting the report
            user_email: Email of the user
            report_type: Type of report
            title: Report title/subject
            description: Detailed description
            analysis_id: Optional related analysis ID
            analysis_ref_id: Optional public analysis reference ID
            
        Returns:
            ReportResult containing the created report or error
        """
        try:
            # Validate required fields
            if not user_id:
                raise InvalidReportDataError("User ID is required")
            
            if not title or len(title.strip()) < 3:
                raise InvalidReportDataError("Title must be at least 3 characters")
            
            if not description or len(description.strip()) < 10:
                raise InvalidReportDataError("Description must be at least 10 characters")
            
            # Create report entity
            report = UserReport(
                report_id=str(uuid.uuid4()),
                user_id=user_id,
                user_email=user_email,
                report_type=report_type,
                title=title.strip(),
                description=description.strip(),
                analysis_id=analysis_id,
                analysis_ref_id=analysis_ref_id,
                status=ReportStatus.PENDING,
                created_at=datetime.utcnow(),
            )
            
            # Save to repository
            created_report = self._admin_repository.create_report(report)
            
            return ReportResult(
                report=created_report,
                success=True
            )
        except InvalidReportDataError as e:
            return ReportResult(
                report=None,
                success=False,
                error_message=str(e)
            )
        except Exception as e:
            return ReportResult(
                report=None,
                success=False,
                error_message=f"Failed to submit report: {str(e)}"
            )


class UpdateReportStatusUseCase:
    """
    Use case for admins to update report status.
    
    Allows administrators to:
    - Mark reports as in progress
    - Resolve reports
    - Dismiss reports
    - Add resolution notes
    """
    
    def __init__(self, admin_repository: AdminRepository):
        """
        Initialize the use case.
        
        Args:
            admin_repository: Repository for admin data operations
        """
        self._admin_repository = admin_repository
    
    def execute(
        self,
        report_id: str,
        status: ReportStatus,
        admin_user_id: str,
        resolution_notes: Optional[str] = None
    ) -> ReportResult:
        """
        Execute the use case to update a report's status.
        
        Args:
            report_id: ID of the report to update
            status: New status
            admin_user_id: ID of the admin making the update
            resolution_notes: Optional notes about resolution
            
        Returns:
            ReportResult containing the updated report or error
        """
        try:
            # Validate report_id
            if not report_id:
                raise InvalidReportDataError("Report ID is required")
            
            # Update the report
            updated_report = self._admin_repository.update_report_status(
                report_id=report_id,
                status=status,
                resolution_notes=resolution_notes,
                assigned_to=admin_user_id
            )
            
            return ReportResult(
                report=updated_report,
                success=True
            )
        except ReportNotFoundError as e:
            return ReportResult(
                report=None,
                success=False,
                error_message=str(e)
            )
        except InvalidReportDataError as e:
            return ReportResult(
                report=None,
                success=False,
                error_message=str(e)
            )
        except Exception as e:
            return ReportResult(
                report=None,
                success=False,
                error_message=f"Failed to update report: {str(e)}"
            )
