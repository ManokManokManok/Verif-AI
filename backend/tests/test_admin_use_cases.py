"""
Tests for Admin Use Cases (Phase 3)

Unit tests for admin use cases following Clean Architecture principles.
All dependencies are mocked to test use case logic in isolation.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, timedelta
from typing import List, Optional

from src.domain.entities import User, UserNotFoundError
from src.domain.admin_entities import (
    ModelHealthMetrics,
    AnalysisStatistics,
    UserStatistics,
    UserReport,
    AdminActivityLog,
    ScamCategoryBreakdown,
    ReportStatus,
    ReportType,
    StatisticsPeriod,
    MetricsCollectionError,
    ReportNotFoundError,
    InvalidReportDataError,
    UserDeletionError,
    AdminOperationError,
)
from src.use_cases.admin.model_health import (
    GetModelHealthUseCase,
    ModelHealthResult,
)
from src.use_cases.admin.analysis_stats import (
    GetAnalysisStatisticsUseCase,
    GetTopScamCategoriesUseCase,
    AnalysisStatisticsResult,
    TopCategoriesResult,
)
from src.use_cases.admin.user_stats import (
    GetUserStatisticsUseCase,
    GetUserReportsUseCase,
    SubmitUserReportUseCase,
    UpdateReportStatusUseCase,
    UserStatisticsResult,
    UserReportsResult,
    ReportResult,
)
from src.use_cases.admin.user_management import (
    ListUsersUseCase,
    GetUserDetailsUseCase,
    DeleteUserUseCase,
    AdminResetPasswordUseCase,
    UpdateUserStatusUseCase,
    UpdateUserRolesUseCase,
    ListUsersResult,
    UserDetailsResult,
    OperationResult,
)


# ============== Fixtures ==============

@pytest.fixture
def mock_metrics_collector():
    """Create a mock metrics collector."""
    collector = Mock()
    collector.collect_metrics.return_value = ModelHealthMetrics(
        gpu_usage_percent=45.0,
        gpu_memory_used_mb=4096.0,
        gpu_memory_total_mb=8192.0,
        cpu_usage_percent=35.0,
        memory_used_mb=8192.0,
        memory_total_mb=16384.0,
        memory_usage_percent=50.0,
        gpu_temperature_celsius=65.0,
        cpu_count=8,
        model_name="verif-ai-bert",
        token_count_today=10000,
        token_count_total=500000,
        avg_processing_speed_ms=150.0,
        requests_today=100,
        requests_total=5000,
        uptime_seconds=86400,
    )
    return collector


@pytest.fixture
def mock_admin_repository():
    """Create a mock admin repository."""
    repo = Mock()
    
    # Analysis statistics
    repo.get_analysis_statistics.return_value = AnalysisStatistics(
        total_count=1000,
        high_risk_count=200,
        medium_risk_count=300,
        low_risk_count=100,
        legitimate_count=400,
        scam_categories_breakdown=[],
        period=StatisticsPeriod.ALL_TIME,
    )
    
    # User statistics
    repo.get_user_statistics.return_value = UserStatistics(
        total_users=500,
        new_users_count=50,
        active_users_count=200,
        verified_users_count=400,
        unverified_users_count=100,
        website_visits=10000,
        unique_visitors=2000,
        period=StatisticsPeriod.ALL_TIME,
    )
    
    # Top categories
    repo.get_top_scam_categories.return_value = [
        ScamCategoryBreakdown(category="Phishing", count=150, percentage=30.0),
        ScamCategoryBreakdown(category="Investment Scam", count=100, percentage=20.0),
        ScamCategoryBreakdown(category="Romance Scam", count=80, percentage=16.0),
    ]
    
    # Reports
    repo.get_reports.return_value = ([], 0)
    repo.create_report.side_effect = lambda r: r
    repo.get_report_by_id.return_value = None
    repo.update_report_status.side_effect = lambda report_id, status, **kwargs: UserReport(
        report_id=report_id,
        user_id="user123",
        report_type=ReportType.HALLUCINATION,
        title="Test Report",
        description="Test description",
        status=status,
    )
    
    # Activity logging
    repo.log_admin_activity.side_effect = lambda log: log
    
    return repo


@pytest.fixture
def mock_user_repository():
    """Create a mock user repository."""
    repo = Mock()
    
    # Default user
    test_user = User(
        id="user123",
        email="test@example.com",
        username="testuser",
        password_hash="hashed",
        roles=["user"],
        is_active=True,
        is_verified=True,
        created_at=datetime.utcnow(),
    )
    
    repo.get_by_id.return_value = test_user
    repo.get_all_users.return_value = ([test_user], 1)
    repo.delete_user.return_value = True
    repo.admin_reset_password.return_value = True
    repo.update_user_status.return_value = True
    repo.update_user_roles.return_value = True
    repo.get_user_activity_summary.return_value = {
        "analysis_count": 25,
        "last_analysis_date": datetime.utcnow(),
    }
    
    return repo


@pytest.fixture
def mock_password_hasher():
    """Create a mock password hasher."""
    hasher = Mock()
    hasher.hash_password.return_value = "new_hashed_password"
    return hasher


# ============== Model Health Use Case Tests ==============

class TestGetModelHealthUseCase:
    """Tests for GetModelHealthUseCase."""
    
    def test_execute_returns_metrics_successfully(self, mock_metrics_collector):
        """Test successful metrics retrieval."""
        use_case = GetModelHealthUseCase(mock_metrics_collector)
        
        result = use_case.execute()
        
        assert result.success is True
        assert result.metrics is not None
        assert result.metrics.cpu_usage_percent == 35.0
        assert result.metrics.gpu_usage_percent == 45.0
        assert result.error_message is None
    
    def test_execute_handles_collection_error(self, mock_metrics_collector):
        """Test handling of metrics collection error."""
        mock_metrics_collector.collect_metrics.side_effect = MetricsCollectionError("GPU not available")
        use_case = GetModelHealthUseCase(mock_metrics_collector)
        
        result = use_case.execute()
        
        assert result.success is False
        assert result.metrics is None
        assert "GPU not available" in result.error_message
    
    def test_execute_handles_unexpected_error(self, mock_metrics_collector):
        """Test handling of unexpected errors."""
        mock_metrics_collector.collect_metrics.side_effect = RuntimeError("Unknown error")
        use_case = GetModelHealthUseCase(mock_metrics_collector)
        
        result = use_case.execute()
        
        assert result.success is False
        assert "Unexpected error" in result.error_message
    
    def test_get_metrics_summary_returns_health_status(self, mock_metrics_collector):
        """Test metrics summary method."""
        use_case = GetModelHealthUseCase(mock_metrics_collector)
        
        summary = use_case.get_metrics_summary()
        
        assert summary["status"] == "healthy"
        assert summary["cpu_percent"] == 35.0
        assert summary["gpu_available"] is True
        assert "uptime" in summary
    
    def test_get_metrics_summary_warns_on_high_cpu(self, mock_metrics_collector):
        """Test warning on high CPU usage."""
        mock_metrics_collector.collect_metrics.return_value = ModelHealthMetrics(
            gpu_usage_percent=30.0,
            gpu_memory_used_mb=4096.0,
            gpu_memory_total_mb=8192.0,
            cpu_usage_percent=95.0,  # High CPU
            memory_used_mb=8192.0,
            memory_total_mb=16384.0,
            memory_usage_percent=50.0,
        )
        use_case = GetModelHealthUseCase(mock_metrics_collector)
        
        summary = use_case.get_metrics_summary()
        
        assert summary["status"] == "warning"
        assert "High CPU usage" in summary["warnings"]
    
    def test_result_to_dict_on_success(self, mock_metrics_collector):
        """Test result conversion to dict on success."""
        use_case = GetModelHealthUseCase(mock_metrics_collector)
        result = use_case.execute()
        
        result_dict = result.to_dict()
        
        assert result_dict["success"] is True
        assert "data" in result_dict
        assert "gpu" in result_dict["data"]
        assert "cpu" in result_dict["data"]
    
    def test_result_to_dict_on_failure(self, mock_metrics_collector):
        """Test result conversion to dict on failure."""
        mock_metrics_collector.collect_metrics.side_effect = MetricsCollectionError("Error")
        use_case = GetModelHealthUseCase(mock_metrics_collector)
        result = use_case.execute()
        
        result_dict = result.to_dict()
        
        assert result_dict["success"] is False
        assert "error" in result_dict


# ============== Analysis Statistics Use Case Tests ==============

class TestGetAnalysisStatisticsUseCase:
    """Tests for GetAnalysisStatisticsUseCase."""
    
    def test_execute_returns_statistics_successfully(self, mock_admin_repository):
        """Test successful statistics retrieval."""
        use_case = GetAnalysisStatisticsUseCase(mock_admin_repository)
        
        result = use_case.execute()
        
        assert result.success is True
        assert result.statistics is not None
        assert result.statistics.total_count == 1000
        assert result.statistics.high_risk_count == 200
    
    def test_execute_with_date_range(self, mock_admin_repository):
        """Test statistics with date range filtering."""
        use_case = GetAnalysisStatisticsUseCase(mock_admin_repository)
        start = datetime.utcnow() - timedelta(days=7)
        end = datetime.utcnow()
        
        result = use_case.execute(start_date=start, end_date=end)
        
        assert result.success is True
        mock_admin_repository.get_analysis_statistics.assert_called_once_with(
            start_date=start,
            end_date=end,
            period=StatisticsPeriod.ALL_TIME
        )
    
    def test_execute_validates_date_range(self, mock_admin_repository):
        """Test validation of invalid date range."""
        use_case = GetAnalysisStatisticsUseCase(mock_admin_repository)
        start = datetime.utcnow()
        end = datetime.utcnow() - timedelta(days=7)  # End before start
        
        result = use_case.execute(start_date=start, end_date=end)
        
        assert result.success is False
        assert "Start date must be before end date" in result.error_message
    
    def test_execute_handles_repository_error(self, mock_admin_repository):
        """Test handling of repository errors."""
        mock_admin_repository.get_analysis_statistics.side_effect = Exception("DB Error")
        use_case = GetAnalysisStatisticsUseCase(mock_admin_repository)
        
        result = use_case.execute()
        
        assert result.success is False
        assert "Failed to retrieve" in result.error_message
    
    def test_get_summary_returns_percentages(self, mock_admin_repository):
        """Test summary calculation with percentages."""
        use_case = GetAnalysisStatisticsUseCase(mock_admin_repository)
        
        summary = use_case.get_summary()
        
        assert summary["total_analyses"] == 1000
        assert summary["high_risk_percent"] == 20.0  # 200/1000 * 100
        assert "scam_detection_rate" in summary


class TestGetTopScamCategoriesUseCase:
    """Tests for GetTopScamCategoriesUseCase."""
    
    def test_execute_returns_categories_successfully(self, mock_admin_repository):
        """Test successful categories retrieval."""
        use_case = GetTopScamCategoriesUseCase(mock_admin_repository)
        
        result = use_case.execute()
        
        assert result.success is True
        assert len(result.categories) == 3
        assert result.categories[0].category == "Phishing"
    
    def test_execute_limits_results(self, mock_admin_repository):
        """Test limit parameter validation."""
        use_case = GetTopScamCategoriesUseCase(mock_admin_repository)
        
        result = use_case.execute(limit=5)
        
        mock_admin_repository.get_top_scam_categories.assert_called_once()
        call_args = mock_admin_repository.get_top_scam_categories.call_args
        assert call_args[1]["limit"] == 5
    
    def test_execute_clamps_limit_to_max(self, mock_admin_repository):
        """Test that limit is clamped to maximum value."""
        use_case = GetTopScamCategoriesUseCase(mock_admin_repository)
        
        result = use_case.execute(limit=100)  # Over max
        
        call_args = mock_admin_repository.get_top_scam_categories.call_args
        assert call_args[1]["limit"] == 50  # Clamped to 50
    
    def test_result_to_dict_format(self, mock_admin_repository):
        """Test result dict format."""
        use_case = GetTopScamCategoriesUseCase(mock_admin_repository)
        result = use_case.execute()
        
        result_dict = result.to_dict()
        
        assert result_dict["success"] is True
        assert "data" in result_dict
        assert len(result_dict["data"]) == 3


# ============== User Statistics Use Case Tests ==============

class TestGetUserStatisticsUseCase:
    """Tests for GetUserStatisticsUseCase."""
    
    def test_execute_returns_statistics_successfully(self, mock_admin_repository):
        """Test successful user statistics retrieval."""
        use_case = GetUserStatisticsUseCase(mock_admin_repository)
        
        result = use_case.execute()
        
        assert result.success is True
        assert result.statistics.total_users == 500
        assert result.statistics.new_users_count == 50
    
    def test_execute_validates_date_range(self, mock_admin_repository):
        """Test date range validation."""
        use_case = GetUserStatisticsUseCase(mock_admin_repository)
        start = datetime.utcnow()
        end = datetime.utcnow() - timedelta(days=1)
        
        result = use_case.execute(start_date=start, end_date=end)
        
        assert result.success is False
        assert "Start date must be before end date" in result.error_message
    
    def test_get_summary_calculates_rates(self, mock_admin_repository):
        """Test summary rate calculations."""
        use_case = GetUserStatisticsUseCase(mock_admin_repository)
        
        summary = use_case.get_summary()
        
        assert summary["total_users"] == 500
        assert summary["engagement_rate"] == 40.0  # 200/500 * 100
        assert summary["verification_rate"] == 80.0  # 400/500 * 100


class TestGetUserReportsUseCase:
    """Tests for GetUserReportsUseCase."""
    
    def test_execute_returns_reports_successfully(self, mock_admin_repository):
        """Test successful reports retrieval."""
        reports = [
            UserReport(
                report_id="r1",
                user_id="u1",
                report_type=ReportType.HALLUCINATION,
                title="Report 1",
                description="Description 1",
                status=ReportStatus.PENDING,
            )
        ]
        mock_admin_repository.get_reports.return_value = (reports, 1)
        use_case = GetUserReportsUseCase(mock_admin_repository)
        
        result = use_case.execute()
        
        assert result.success is True
        assert len(result.reports) == 1
        assert result.total_count == 1
    
    def test_execute_filters_by_status(self, mock_admin_repository):
        """Test status filtering."""
        use_case = GetUserReportsUseCase(mock_admin_repository)
        
        result = use_case.execute(status=ReportStatus.PENDING)
        
        call_args = mock_admin_repository.get_reports.call_args
        assert call_args[1]["status"] == ReportStatus.PENDING
    
    def test_execute_validates_pagination(self, mock_admin_repository):
        """Test pagination validation."""
        use_case = GetUserReportsUseCase(mock_admin_repository)
        
        result = use_case.execute(limit=-5, offset=-10)
        
        call_args = mock_admin_repository.get_reports.call_args
        assert call_args[1]["limit"] == 1  # Minimum
        assert call_args[1]["offset"] == 0  # Minimum
    
    def test_get_pending_count(self, mock_admin_repository):
        """Test pending count method."""
        mock_admin_repository.get_reports.return_value = ([], 15)
        use_case = GetUserReportsUseCase(mock_admin_repository)
        
        count = use_case.get_pending_count()
        
        assert count == 15


class TestSubmitUserReportUseCase:
    """Tests for SubmitUserReportUseCase."""
    
    def test_execute_creates_report_successfully(self, mock_admin_repository):
        """Test successful report submission."""
        use_case = SubmitUserReportUseCase(mock_admin_repository)
        
        result = use_case.execute(
            user_id="user123",
            user_email="user@example.com",
            report_type=ReportType.HALLUCINATION,
            title="AI gave wrong answer",
            description="The AI classified a legitimate email as a scam incorrectly."
        )
        
        assert result.success is True
        assert result.report is not None
        assert result.report.status == ReportStatus.PENDING
    
    def test_execute_validates_title_length(self, mock_admin_repository):
        """Test title validation."""
        use_case = SubmitUserReportUseCase(mock_admin_repository)
        
        result = use_case.execute(
            user_id="user123",
            user_email="user@example.com",
            report_type=ReportType.BUG,
            title="Hi",  # Too short
            description="This is a valid description that is long enough."
        )
        
        assert result.success is False
        assert "Title must be at least 3 characters" in result.error_message
    
    def test_execute_validates_description_length(self, mock_admin_repository):
        """Test description validation."""
        use_case = SubmitUserReportUseCase(mock_admin_repository)
        
        result = use_case.execute(
            user_id="user123",
            user_email="user@example.com",
            report_type=ReportType.BUG,
            title="Valid Title",
            description="Short"  # Too short
        )
        
        assert result.success is False
        assert "Description must be at least 10 characters" in result.error_message
    
    def test_execute_validates_user_id(self, mock_admin_repository):
        """Test user_id validation."""
        use_case = SubmitUserReportUseCase(mock_admin_repository)
        
        result = use_case.execute(
            user_id="",  # Empty
            user_email="user@example.com",
            report_type=ReportType.BUG,
            title="Valid Title",
            description="Valid description that is long enough."
        )
        
        assert result.success is False
        assert "User ID is required" in result.error_message


class TestUpdateReportStatusUseCase:
    """Tests for UpdateReportStatusUseCase."""
    
    def test_execute_updates_status_successfully(self, mock_admin_repository):
        """Test successful status update."""
        use_case = UpdateReportStatusUseCase(mock_admin_repository)
        
        result = use_case.execute(
            report_id="report123",
            status=ReportStatus.RESOLVED,
            admin_user_id="admin1",
            resolution_notes="Issue fixed in update."
        )
        
        assert result.success is True
        assert result.report is not None
        assert result.report.status == ReportStatus.RESOLVED
    
    def test_execute_handles_report_not_found(self, mock_admin_repository):
        """Test handling of missing report."""
        mock_admin_repository.update_report_status.side_effect = ReportNotFoundError("Not found")
        use_case = UpdateReportStatusUseCase(mock_admin_repository)
        
        result = use_case.execute(
            report_id="nonexistent",
            status=ReportStatus.RESOLVED,
            admin_user_id="admin1"
        )
        
        assert result.success is False
        assert "Not found" in result.error_message
    
    def test_execute_validates_report_id(self, mock_admin_repository):
        """Test report_id validation."""
        use_case = UpdateReportStatusUseCase(mock_admin_repository)
        
        result = use_case.execute(
            report_id="",  # Empty
            status=ReportStatus.RESOLVED,
            admin_user_id="admin1"
        )
        
        assert result.success is False
        assert "Report ID is required" in result.error_message


# ============== User Management Use Case Tests ==============

class TestListUsersUseCase:
    """Tests for ListUsersUseCase."""
    
    def test_execute_returns_users_successfully(self, mock_user_repository):
        """Test successful user listing."""
        use_case = ListUsersUseCase(mock_user_repository)
        
        result = use_case.execute()
        
        assert result.success is True
        assert len(result.users) == 1
        assert result.total_count == 1
    
    def test_execute_with_search_filter(self, mock_user_repository):
        """Test search filtering."""
        use_case = ListUsersUseCase(mock_user_repository)
        
        result = use_case.execute(search="test")
        
        call_args = mock_user_repository.get_all_users.call_args
        assert call_args[1]["search"] == "test"
    
    def test_execute_with_pagination(self, mock_user_repository):
        """Test pagination parameters."""
        use_case = ListUsersUseCase(mock_user_repository)
        
        result = use_case.execute(page=2, page_size=25)
        
        call_args = mock_user_repository.get_all_users.call_args
        assert call_args[1]["offset"] == 25  # (2-1) * 25
        assert call_args[1]["limit"] == 25
    
    def test_execute_validates_pagination_limits(self, mock_user_repository):
        """Test pagination limit validation."""
        use_case = ListUsersUseCase(mock_user_repository)
        
        result = use_case.execute(page=-1, page_size=200)
        
        call_args = mock_user_repository.get_all_users.call_args
        assert call_args[1]["offset"] == 0  # (1-1) * 100
        assert call_args[1]["limit"] == 100  # Clamped to max
    
    def test_result_excludes_sensitive_data(self, mock_user_repository):
        """Test that result excludes password hash."""
        use_case = ListUsersUseCase(mock_user_repository)
        result = use_case.execute()
        
        result_dict = result.to_dict()
        
        user_data = result_dict["data"]["users"][0]
        assert "password_hash" not in user_data
        assert "email" in user_data


class TestGetUserDetailsUseCase:
    """Tests for GetUserDetailsUseCase."""
    
    def test_execute_returns_user_details(self, mock_user_repository):
        """Test successful user details retrieval."""
        use_case = GetUserDetailsUseCase(mock_user_repository)
        
        result = use_case.execute("user123")
        
        assert result.success is True
        assert result.user is not None
        assert result.user.email == "test@example.com"
        assert result.activity_summary is not None
    
    def test_execute_handles_user_not_found(self, mock_user_repository):
        """Test handling of missing user."""
        mock_user_repository.get_by_id.return_value = None
        use_case = GetUserDetailsUseCase(mock_user_repository)
        
        result = use_case.execute("nonexistent")
        
        assert result.success is False
        assert "not found" in result.error_message
    
    def test_execute_validates_user_id(self, mock_user_repository):
        """Test user_id validation."""
        use_case = GetUserDetailsUseCase(mock_user_repository)
        
        result = use_case.execute("")
        
        assert result.success is False
        assert "User ID is required" in result.error_message


class TestDeleteUserUseCase:
    """Tests for DeleteUserUseCase."""
    
    def test_execute_soft_deletes_user_successfully(self, mock_user_repository, mock_admin_repository):
        """Test successful soft delete."""
        use_case = DeleteUserUseCase(mock_user_repository, mock_admin_repository)
        
        result = use_case.execute(
            user_id="user123",
            admin_user_id="admin1",
            hard_delete=False
        )
        
        assert result.success is True
        assert "deactivated" in result.message
        mock_user_repository.delete_user.assert_called_once_with("user123", hard_delete=False)
    
    def test_execute_hard_deletes_user_successfully(self, mock_user_repository, mock_admin_repository):
        """Test successful hard delete."""
        use_case = DeleteUserUseCase(mock_user_repository, mock_admin_repository)
        
        result = use_case.execute(
            user_id="user123",
            admin_user_id="admin1",
            hard_delete=True
        )
        
        assert result.success is True
        assert "permanently deleted" in result.message
    
    def test_execute_prevents_self_deletion(self, mock_user_repository):
        """Test prevention of self-deletion."""
        use_case = DeleteUserUseCase(mock_user_repository)
        
        result = use_case.execute(
            user_id="admin1",
            admin_user_id="admin1",  # Same as user_id
            hard_delete=False
        )
        
        assert result.success is False
        assert "Cannot delete your own account" in result.error_message
    
    def test_execute_prevents_super_admin_deletion(self, mock_user_repository):
        """Test prevention of super admin deletion."""
        super_admin = User(
            id="superadmin1",
            email="superadmin@example.com",
            username="superadmin",
            password_hash="hash",
            roles=["super_admin"],
            is_active=True,
        )
        mock_user_repository.get_by_id.return_value = super_admin
        use_case = DeleteUserUseCase(mock_user_repository)
        
        result = use_case.execute(
            user_id="superadmin1",
            admin_user_id="admin1",
            hard_delete=False
        )
        
        assert result.success is False
        assert "super admin" in result.error_message.lower()
    
    def test_execute_handles_user_not_found(self, mock_user_repository):
        """Test handling of missing user."""
        mock_user_repository.get_by_id.return_value = None
        use_case = DeleteUserUseCase(mock_user_repository)
        
        result = use_case.execute(
            user_id="nonexistent",
            admin_user_id="admin1",
            hard_delete=False
        )
        
        assert result.success is False
        assert "not found" in result.error_message
    
    def test_execute_logs_admin_activity(self, mock_user_repository, mock_admin_repository):
        """Test that admin activity is logged."""
        use_case = DeleteUserUseCase(mock_user_repository, mock_admin_repository)
        
        use_case.execute(
            user_id="user123",
            admin_user_id="admin1",
            hard_delete=False
        )
        
        mock_admin_repository.log_admin_activity.assert_called_once()


class TestAdminResetPasswordUseCase:
    """Tests for AdminResetPasswordUseCase."""
    
    def test_execute_resets_password_successfully(
        self, mock_user_repository, mock_password_hasher, mock_admin_repository
    ):
        """Test successful password reset."""
        use_case = AdminResetPasswordUseCase(
            mock_user_repository, mock_password_hasher, mock_admin_repository
        )
        
        result = use_case.execute(
            user_id="user123",
            new_password="newpassword123",
            admin_user_id="admin1"
        )
        
        assert result.success is True
        assert "Password reset" in result.message
        mock_password_hasher.hash_password.assert_called_once_with("newpassword123")
        mock_user_repository.admin_reset_password.assert_called_once()
    
    def test_execute_validates_password_length(
        self, mock_user_repository, mock_password_hasher
    ):
        """Test password length validation."""
        use_case = AdminResetPasswordUseCase(mock_user_repository, mock_password_hasher)
        
        result = use_case.execute(
            user_id="user123",
            new_password="short",  # Less than 8 chars
            admin_user_id="admin1"
        )
        
        assert result.success is False
        assert "at least 8 characters" in result.error_message
    
    def test_execute_handles_user_not_found(
        self, mock_user_repository, mock_password_hasher
    ):
        """Test handling of missing user."""
        mock_user_repository.get_by_id.return_value = None
        use_case = AdminResetPasswordUseCase(mock_user_repository, mock_password_hasher)
        
        result = use_case.execute(
            user_id="nonexistent",
            new_password="newpassword123",
            admin_user_id="admin1"
        )
        
        assert result.success is False
        assert "not found" in result.error_message


class TestUpdateUserStatusUseCase:
    """Tests for UpdateUserStatusUseCase."""
    
    def test_execute_activates_user_successfully(self, mock_user_repository, mock_admin_repository):
        """Test successful user activation."""
        use_case = UpdateUserStatusUseCase(mock_user_repository, mock_admin_repository)
        
        result = use_case.execute(
            user_id="user123",
            is_active=True,
            admin_user_id="admin1"
        )
        
        assert result.success is True
        assert "activated" in result.message
    
    def test_execute_deactivates_user_successfully(self, mock_user_repository, mock_admin_repository):
        """Test successful user deactivation."""
        use_case = UpdateUserStatusUseCase(mock_user_repository, mock_admin_repository)
        
        result = use_case.execute(
            user_id="user123",
            is_active=False,
            admin_user_id="admin1"
        )
        
        assert result.success is True
        assert "deactivated" in result.message
    
    def test_execute_prevents_self_deactivation(self, mock_user_repository):
        """Test prevention of self-deactivation."""
        use_case = UpdateUserStatusUseCase(mock_user_repository)
        
        result = use_case.execute(
            user_id="admin1",
            is_active=False,
            admin_user_id="admin1"  # Same as user_id
        )
        
        assert result.success is False
        assert "Cannot deactivate your own account" in result.error_message
    
    def test_execute_prevents_super_admin_deactivation(self, mock_user_repository):
        """Test prevention of super admin deactivation."""
        super_admin = User(
            id="superadmin1",
            email="superadmin@example.com",
            username="superadmin",
            password_hash="hash",
            roles=["super_admin"],
            is_active=True,
        )
        mock_user_repository.get_by_id.return_value = super_admin
        use_case = UpdateUserStatusUseCase(mock_user_repository)
        
        result = use_case.execute(
            user_id="superadmin1",
            is_active=False,
            admin_user_id="admin1"
        )
        
        assert result.success is False
        assert "super admin" in result.error_message.lower()


class TestUpdateUserRolesUseCase:
    """Tests for UpdateUserRolesUseCase."""
    
    def test_execute_updates_roles_successfully(self, mock_user_repository, mock_admin_repository):
        """Test successful role update."""
        use_case = UpdateUserRolesUseCase(mock_user_repository, mock_admin_repository)
        
        result = use_case.execute(
            user_id="user123",
            roles=["user", "moderator"],
            admin_user_id="admin1",
            admin_roles=["admin"]
        )
        
        assert result.success is True
        assert "Roles updated" in result.message
    
    def test_execute_validates_empty_roles(self, mock_user_repository):
        """Test validation of empty roles."""
        use_case = UpdateUserRolesUseCase(mock_user_repository)
        
        result = use_case.execute(
            user_id="user123",
            roles=[],
            admin_user_id="admin1",
            admin_roles=["admin"]
        )
        
        assert result.success is False
        assert "At least one role is required" in result.error_message
    
    def test_execute_validates_invalid_roles(self, mock_user_repository):
        """Test validation of invalid roles."""
        use_case = UpdateUserRolesUseCase(mock_user_repository)
        
        result = use_case.execute(
            user_id="user123",
            roles=["user", "invalid_role"],
            admin_user_id="admin1",
            admin_roles=["admin"]
        )
        
        assert result.success is False
        assert "Invalid roles" in result.error_message
    
    def test_execute_restricts_super_admin_role_assignment(self, mock_user_repository):
        """Test that only super_admin can assign super_admin role."""
        use_case = UpdateUserRolesUseCase(mock_user_repository)
        
        result = use_case.execute(
            user_id="user123",
            roles=["user", "super_admin"],
            admin_user_id="admin1",
            admin_roles=["admin"]  # Not super_admin
        )
        
        assert result.success is False
        assert "Only super admins can assign super admin role" in result.error_message
    
    def test_execute_allows_super_admin_to_assign_super_admin(self, mock_user_repository):
        """Test that super_admin can assign super_admin role."""
        use_case = UpdateUserRolesUseCase(mock_user_repository)
        
        result = use_case.execute(
            user_id="user123",
            roles=["user", "super_admin"],
            admin_user_id="admin1",
            admin_roles=["super_admin"]  # Is super_admin
        )
        
        assert result.success is True
    
    def test_execute_prevents_removing_own_admin_role(self, mock_user_repository):
        """Test prevention of removing admin role from self."""
        admin_user = User(
            id="admin1",
            email="admin@example.com",
            username="admin",
            password_hash="hash",
            roles=["admin"],
            is_active=True,
        )
        mock_user_repository.get_by_id.return_value = admin_user
        use_case = UpdateUserRolesUseCase(mock_user_repository)
        
        result = use_case.execute(
            user_id="admin1",
            roles=["user"],  # Removing admin role
            admin_user_id="admin1",
            admin_roles=["admin"]
        )
        
        assert result.success is False
        assert "Cannot remove admin role from yourself" in result.error_message
    
    def test_execute_logs_role_changes(self, mock_user_repository, mock_admin_repository):
        """Test that role changes are logged."""
        use_case = UpdateUserRolesUseCase(mock_user_repository, mock_admin_repository)
        
        use_case.execute(
            user_id="user123",
            roles=["user", "moderator"],
            admin_user_id="admin1",
            admin_roles=["admin"]
        )
        
        mock_admin_repository.log_admin_activity.assert_called_once()
        log_call = mock_admin_repository.log_admin_activity.call_args[0][0]
        assert log_call.action == "update_user_roles"
        assert "old_roles" in log_call.details
        assert "new_roles" in log_call.details


# ============== Integration Pattern Tests ==============

class TestUseCaseIntegration:
    """Test use case integration patterns."""
    
    def test_use_cases_are_framework_agnostic(self):
        """Verify use cases don't import Django or other frameworks."""
        import inspect
        from src.use_cases.admin import model_health, analysis_stats, user_stats, user_management
        
        modules = [model_health, analysis_stats, user_stats, user_management]
        
        for module in modules:
            source = inspect.getsource(module)
            assert "django" not in source.lower(), f"{module.__name__} imports Django"
            assert "from rest_framework" not in source, f"{module.__name__} imports DRF"
    
    def test_use_cases_use_protocol_dependencies(self):
        """Verify use cases depend on protocols, not concrete implementations."""
        from src.use_cases.admin.model_health import GetModelHealthUseCase
        from src.use_cases.admin.analysis_stats import GetAnalysisStatisticsUseCase
        from src.use_cases.admin.user_management import ListUsersUseCase
        
        # Check that __init__ accepts any object implementing the protocol
        mock_collector = Mock()
        mock_collector.collect_metrics.return_value = Mock()
        
        # Should not raise - accepts any object with collect_metrics method
        use_case = GetModelHealthUseCase(mock_collector)
        assert use_case is not None
    
    def test_result_objects_are_serializable(self, mock_metrics_collector, mock_admin_repository):
        """Verify result objects can be serialized to dict."""
        model_health_uc = GetModelHealthUseCase(mock_metrics_collector)
        analysis_stats_uc = GetAnalysisStatisticsUseCase(mock_admin_repository)
        
        # All results should have to_dict method
        model_result = model_health_uc.execute()
        analysis_result = analysis_stats_uc.execute()
        
        assert callable(getattr(model_result, 'to_dict', None))
        assert callable(getattr(analysis_result, 'to_dict', None))
        
        # to_dict should return dict
        assert isinstance(model_result.to_dict(), dict)
        assert isinstance(analysis_result.to_dict(), dict)
