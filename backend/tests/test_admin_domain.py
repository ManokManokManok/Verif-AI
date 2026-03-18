"""
Tests for Admin Domain Entities

Unit tests for the admin domain layer entities to ensure they are
framework-agnostic and contain correct business logic.
"""

import pytest
from datetime import datetime, timedelta
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
    AdminPermissions,
    UserDeletionError,
    ReportNotFoundError,
    InvalidReportStatusError,
    MetricsCollectionError,
)


class TestModelHealthMetrics:
    """Tests for ModelHealthMetrics entity."""
    
    def test_model_health_metrics_creation(self):
        """Test basic creation of ModelHealthMetrics."""
        metrics = ModelHealthMetrics(
            gpu_usage_percent=75.5,
            gpu_memory_used_mb=4096.0,
            gpu_memory_total_mb=8192.0,
            cpu_usage_percent=45.2,
            cpu_count=8,
            memory_used_mb=8000.0,
            memory_total_mb=16000.0,
            memory_usage_percent=50.0,
            model_name="verif-ai-bert",
            token_count_today=1500,
            token_count_total=50000,
            avg_processing_speed_ms=150.5,
            requests_today=100,
            requests_total=5000,
            uptime_seconds=86400,
        )
        
        assert metrics.gpu_usage_percent == 75.5
        assert metrics.gpu_memory_used_mb == 4096.0
        assert metrics.cpu_usage_percent == 45.2
        assert metrics.memory_usage_percent == 50.0
        assert metrics.model_name == "verif-ai-bert"
        assert metrics.token_count_today == 1500
        assert metrics.uptime_seconds == 86400
    
    def test_gpu_memory_usage_percent_calculation(self):
        """Test GPU memory usage percentage calculation."""
        metrics = ModelHealthMetrics(
            gpu_usage_percent=50.0,
            gpu_memory_used_mb=2048.0,
            gpu_memory_total_mb=8192.0,
            cpu_usage_percent=30.0,
            memory_used_mb=4000.0,
            memory_total_mb=8000.0,
            memory_usage_percent=50.0,
        )
        
        assert metrics.gpu_memory_usage_percent == 25.0  # 2048 / 8192 * 100
    
    def test_gpu_memory_usage_percent_zero_total(self):
        """Test GPU memory usage when total is zero (no GPU)."""
        metrics = ModelHealthMetrics(
            gpu_usage_percent=0.0,
            gpu_memory_used_mb=0.0,
            gpu_memory_total_mb=0.0,
            cpu_usage_percent=30.0,
            memory_used_mb=4000.0,
            memory_total_mb=8000.0,
            memory_usage_percent=50.0,
        )
        
        assert metrics.gpu_memory_usage_percent == 0.0
        assert metrics.is_gpu_available is False
    
    def test_is_gpu_available(self):
        """Test GPU availability check."""
        metrics_with_gpu = ModelHealthMetrics(
            gpu_usage_percent=50.0,
            gpu_memory_used_mb=2048.0,
            gpu_memory_total_mb=8192.0,
            cpu_usage_percent=30.0,
            memory_used_mb=4000.0,
            memory_total_mb=8000.0,
            memory_usage_percent=50.0,
        )
        
        metrics_without_gpu = ModelHealthMetrics(
            gpu_usage_percent=0.0,
            gpu_memory_used_mb=0.0,
            gpu_memory_total_mb=0.0,
            cpu_usage_percent=30.0,
            memory_used_mb=4000.0,
            memory_total_mb=8000.0,
            memory_usage_percent=50.0,
        )
        
        assert metrics_with_gpu.is_gpu_available is True
        assert metrics_without_gpu.is_gpu_available is False
    
    def test_uptime_formatted(self):
        """Test uptime formatting."""
        # Test 1 day, 2 hours, 30 minutes, 45 seconds
        metrics = ModelHealthMetrics(
            gpu_usage_percent=0.0,
            gpu_memory_used_mb=0.0,
            gpu_memory_total_mb=0.0,
            cpu_usage_percent=30.0,
            memory_used_mb=4000.0,
            memory_total_mb=8000.0,
            memory_usage_percent=50.0,
            uptime_seconds=95445,  # 1d 2h 30m 45s
        )
        
        assert "1d" in metrics.uptime_formatted
        assert "2h" in metrics.uptime_formatted
        assert "30m" in metrics.uptime_formatted
        assert "45s" in metrics.uptime_formatted
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        metrics = ModelHealthMetrics(
            gpu_usage_percent=75.5,
            gpu_memory_used_mb=4096.0,
            gpu_memory_total_mb=8192.0,
            cpu_usage_percent=45.2,
            cpu_count=8,
            memory_used_mb=8000.0,
            memory_total_mb=16000.0,
            memory_usage_percent=50.0,
            model_name="verif-ai-bert",
            token_count_today=1500,
            uptime_seconds=3600,
        )
        
        data = metrics.to_dict()
        
        assert "gpu" in data
        assert "cpu" in data
        assert "memory" in data
        assert "model" in data
        assert "system" in data
        assert data["gpu"]["usage_percent"] == 75.5
        assert data["cpu"]["count"] == 8
        assert data["model"]["name"] == "verif-ai-bert"


class TestAnalysisStatistics:
    """Tests for AnalysisStatistics entity."""
    
    def test_analysis_statistics_creation(self):
        """Test basic creation of AnalysisStatistics."""
        stats = AnalysisStatistics(
            total_count=1000,
            high_risk_count=300,
            medium_risk_count=200,
            low_risk_count=100,
            legitimate_count=400,
            period=StatisticsPeriod.MONTH,
        )
        
        assert stats.total_count == 1000
        assert stats.high_risk_count == 300
        assert stats.medium_risk_count == 200
        assert stats.low_risk_count == 100
        assert stats.legitimate_count == 400
        assert stats.period == StatisticsPeriod.MONTH
    
    def test_scam_count_calculation(self):
        """Test total scam count calculation."""
        stats = AnalysisStatistics(
            total_count=1000,
            high_risk_count=300,
            medium_risk_count=200,
            low_risk_count=100,
            legitimate_count=400,
        )
        
        assert stats.scam_count == 500  # 300 + 200
    
    def test_scam_rate_percent_calculation(self):
        """Test scam rate percentage calculation."""
        stats = AnalysisStatistics(
            total_count=1000,
            high_risk_count=300,
            medium_risk_count=200,
            low_risk_count=100,
            legitimate_count=400,
        )
        
        assert stats.scam_rate_percent == 50.0  # 500 / 1000 * 100
    
    def test_scam_rate_percent_zero_total(self):
        """Test scam rate when total is zero."""
        stats = AnalysisStatistics(
            total_count=0,
            high_risk_count=0,
            medium_risk_count=0,
            low_risk_count=0,
            legitimate_count=0,
        )
        
        assert stats.scam_rate_percent == 0.0
    
    def test_top_scam_category(self):
        """Test top scam category determination."""
        categories = [
            ScamCategoryBreakdown(category="Phishing", count=150, percentage=30.0),
            ScamCategoryBreakdown(category="Financial", count=200, percentage=40.0),
            ScamCategoryBreakdown(category="Romance", count=100, percentage=20.0),
        ]
        
        stats = AnalysisStatistics(
            total_count=500,
            high_risk_count=250,
            medium_risk_count=150,
            low_risk_count=50,
            legitimate_count=50,
            scam_categories_breakdown=categories,
        )
        
        assert stats.top_scam_category == "Financial"
    
    def test_top_scam_category_empty(self):
        """Test top scam category when no categories exist."""
        stats = AnalysisStatistics(
            total_count=100,
            high_risk_count=50,
            medium_risk_count=30,
            low_risk_count=10,
            legitimate_count=10,
        )
        
        assert stats.top_scam_category is None
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        categories = [
            ScamCategoryBreakdown(category="Phishing", count=100, percentage=50.0),
        ]
        
        stats = AnalysisStatistics(
            total_count=200,
            high_risk_count=100,
            medium_risk_count=50,
            low_risk_count=25,
            legitimate_count=25,
            scam_categories_breakdown=categories,
            period=StatisticsPeriod.WEEK,
        )
        
        data = stats.to_dict()
        
        assert data["total_count"] == 200
        assert data["scam_count"] == 150
        assert data["scam_rate_percent"] == 75.0
        assert data["period"] == "week"
        assert len(data["scam_categories_breakdown"]) == 1


class TestUserStatistics:
    """Tests for UserStatistics entity."""
    
    def test_user_statistics_creation(self):
        """Test basic creation of UserStatistics."""
        stats = UserStatistics(
            total_users=500,
            new_users_count=50,
            active_users_count=200,
            verified_users_count=400,
            unverified_users_count=100,
            website_visits=10000,
            unique_visitors=2000,
            period=StatisticsPeriod.MONTH,
        )
        
        assert stats.total_users == 500
        assert stats.new_users_count == 50
        assert stats.active_users_count == 200
        assert stats.website_visits == 10000
    
    def test_user_growth_rate_calculation(self):
        """Test user growth rate calculation."""
        stats = UserStatistics(
            total_users=500,
            new_users_count=50,
            active_users_count=200,
            verified_users_count=400,
            unverified_users_count=100,
        )
        
        assert stats.user_growth_rate == 10.0  # 50 / 500 * 100
    
    def test_user_growth_rate_zero_users(self):
        """Test user growth rate when total is zero."""
        stats = UserStatistics(
            total_users=0,
            new_users_count=0,
            active_users_count=0,
            verified_users_count=0,
            unverified_users_count=0,
        )
        
        assert stats.user_growth_rate == 0.0
    
    def test_verification_rate_calculation(self):
        """Test verification rate calculation."""
        stats = UserStatistics(
            total_users=500,
            new_users_count=50,
            active_users_count=200,
            verified_users_count=400,
            unverified_users_count=100,
        )
        
        assert stats.verification_rate == 80.0  # 400 / 500 * 100
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        stats = UserStatistics(
            total_users=500,
            new_users_count=50,
            active_users_count=200,
            verified_users_count=400,
            unverified_users_count=100,
            website_visits=10000,
            top_power_user={
                "user_id": "user-1",
                "username": "top_user",
                "email": "top@example.com",
                "total_detections": 77,
            },
            period=StatisticsPeriod.WEEK,
        )
        
        data = stats.to_dict()
        
        assert data["total_users"] == 500
        assert data["user_growth_rate"] == 10.0
        assert data["verification_rate"] == 80.0
        assert data["period"] == "week"
        assert data["top_power_user"]["username"] == "top_user"


class TestUserReport:
    """Tests for UserReport entity."""
    
    def test_user_report_creation(self):
        """Test basic creation of UserReport."""
        report = UserReport(
            user_id="user123",
            user_email="user@example.com",
            report_type=ReportType.HALLUCINATION,
            title="Model gave incorrect response",
            description="The model said X but it should be Y",
        )
        
        assert report.user_id == "user123"
        assert report.user_email == "user@example.com"
        assert report.report_type == ReportType.HALLUCINATION
        assert report.status == ReportStatus.PENDING
        assert report.is_open is True
        assert report.is_resolved is False
    
    def test_user_report_auto_id_generation(self):
        """Test that report_id is auto-generated."""
        report = UserReport(
            user_id="user123",
            report_type=ReportType.BUG,
            title="Bug Report",
            description="Something broke",
        )
        
        assert report.report_id is not None
        assert len(report.report_id) > 0
        assert report.id == report.report_id
    
    def test_user_report_resolve(self):
        """Test resolving a report."""
        report = UserReport(
            user_id="user123",
            report_type=ReportType.FALSE_POSITIVE,
            title="False Positive",
            description="Message was legitimate",
        )
        
        assert report.status == ReportStatus.PENDING
        
        report.resolve(notes="Verified and updated model")
        
        assert report.status == ReportStatus.RESOLVED
        assert report.resolution_notes == "Verified and updated model"
        assert report.resolved_at is not None
        assert report.is_resolved is True
        assert report.is_open is False
    
    def test_user_report_dismiss(self):
        """Test dismissing a report."""
        report = UserReport(
            user_id="user123",
            report_type=ReportType.OTHER,
            title="Other Issue",
            description="Some issue",
        )
        
        report.dismiss(notes="Not actionable")
        
        assert report.status == ReportStatus.DISMISSED
        assert report.resolution_notes == "Not actionable"
        assert report.is_resolved is True
    
    def test_user_report_assign(self):
        """Test assigning a report to an admin."""
        report = UserReport(
            user_id="user123",
            report_type=ReportType.HALLUCINATION,
            title="Hallucination Report",
            description="Model hallucinated",
        )
        
        report.assign("admin456")
        
        assert report.assigned_to == "admin456"
        assert report.status == ReportStatus.IN_PROGRESS
        assert report.is_open is True
    
    def test_user_report_to_dict(self):
        """Test conversion to dictionary."""
        report = UserReport(
            user_id="user123",
            user_email="user@example.com",
            report_type=ReportType.HALLUCINATION,
            title="Test Report",
            description="Test description",
            analysis_id="analysis789",
        )
        
        data = report.to_dict()
        
        assert data["user_id"] == "user123"
        assert data["user_email"] == "user@example.com"
        assert data["report_type"] == "hallucination"
        assert data["status"] == "pending"
        assert data["analysis_id"] == "analysis789"
        assert data["is_open"] is True
    
    def test_user_report_from_dict(self):
        """Test creating report from dictionary."""
        data = {
            "id": "report123",
            "report_id": "report123",
            "user_id": "user456",
            "user_email": "test@example.com",
            "report_type": "bug",
            "title": "Bug Report",
            "description": "Something is wrong",
            "status": "in_progress",
            "assigned_to": "admin789",
        }
        
        report = UserReport.from_dict(data)
        
        assert report.id == "report123"
        assert report.user_id == "user456"
        assert report.report_type == ReportType.BUG
        assert report.status == ReportStatus.IN_PROGRESS
        assert report.assigned_to == "admin789"


class TestAdminActivityLog:
    """Tests for AdminActivityLog entity."""
    
    def test_admin_activity_log_creation(self):
        """Test basic creation of AdminActivityLog."""
        log = AdminActivityLog(
            admin_user_id="admin123",
            admin_email="admin@example.com",
            action="delete_user",
            resource_type="user",
            resource_id="user456",
            details={"reason": "Requested by user"},
            ip_address="192.168.1.1",
        )
        
        assert log.admin_user_id == "admin123"
        assert log.action == "delete_user"
        assert log.resource_type == "user"
        assert log.resource_id == "user456"
        assert log.details["reason"] == "Requested by user"
    
    def test_admin_activity_log_auto_id(self):
        """Test that log_id is auto-generated."""
        log = AdminActivityLog(
            admin_user_id="admin123",
            action="reset_password",
            resource_type="user",
        )
        
        assert log.log_id is not None
        assert len(log.log_id) > 0
    
    def test_admin_activity_log_to_dict(self):
        """Test conversion to dictionary."""
        log = AdminActivityLog(
            admin_user_id="admin123",
            admin_email="admin@example.com",
            action="resolve_report",
            resource_type="report",
            resource_id="report789",
            ip_address="10.0.0.1",
        )
        
        data = log.to_dict()
        
        assert data["admin_user_id"] == "admin123"
        assert data["action"] == "resolve_report"
        assert data["resource_type"] == "report"
        assert data["ip_address"] == "10.0.0.1"
        assert "created_at" in data


class TestScamCategoryBreakdown:
    """Tests for ScamCategoryBreakdown entity."""
    
    def test_scam_category_breakdown_creation(self):
        """Test basic creation of ScamCategoryBreakdown."""
        breakdown = ScamCategoryBreakdown(
            category="Phishing",
            count=150,
            percentage=30.5,
        )
        
        assert breakdown.category == "Phishing"
        assert breakdown.count == 150
        assert breakdown.percentage == 30.5
        assert breakdown.avg_risk_percent == 0.0
    
    def test_scam_category_breakdown_to_dict(self):
        """Test conversion to dictionary."""
        breakdown = ScamCategoryBreakdown(
            category="Financial Fraud",
            count=200,
            percentage=40.123,
        )
        
        data = breakdown.to_dict()
        
        assert data["category"] == "Financial Fraud"
        assert data["count"] == 200
        assert data["percentage"] == 40.12  # Rounded to 2 decimal places
        assert data["avg_risk_percent"] == 0.0


class TestEnums:
    """Tests for enum classes."""
    
    def test_report_status_values(self):
        """Test ReportStatus enum values."""
        assert ReportStatus.PENDING.value == "pending"
        assert ReportStatus.IN_PROGRESS.value == "in_progress"
        assert ReportStatus.RESOLVED.value == "resolved"
        assert ReportStatus.DISMISSED.value == "dismissed"
    
    def test_report_type_values(self):
        """Test ReportType enum values."""
        assert ReportType.HALLUCINATION.value == "hallucination"
        assert ReportType.FALSE_POSITIVE.value == "false_positive"
        assert ReportType.FALSE_NEGATIVE.value == "false_negative"
        assert ReportType.BUG.value == "bug"
        assert ReportType.FEEDBACK.value == "feedback"
        assert ReportType.OTHER.value == "other"
    
    def test_statistics_period_values(self):
        """Test StatisticsPeriod enum values."""
        assert StatisticsPeriod.DAY.value == "day"
        assert StatisticsPeriod.WEEK.value == "week"
        assert StatisticsPeriod.MONTH.value == "month"
        assert StatisticsPeriod.YEAR.value == "year"
        assert StatisticsPeriod.ALL_TIME.value == "all_time"


class TestAdminPermissions:
    """Tests for AdminPermissions constants."""
    
    def test_admin_permissions_defined(self):
        """Test that all admin permissions are defined."""
        assert AdminPermissions.VIEW_MODEL_HEALTH == "view_model_health"
        assert AdminPermissions.VIEW_ANALYSIS_STATS == "view_analysis_stats"
        assert AdminPermissions.VIEW_USER_STATS == "view_user_stats"
        assert AdminPermissions.MANAGE_USER_REPORTS == "manage_user_reports"
        assert AdminPermissions.DELETE_USER == "delete_user"
        assert AdminPermissions.RESET_USER_PASSWORD == "reset_user_password"
        assert AdminPermissions.VIEW_SYSTEM_LOGS == "view_system_logs"
    
    def test_all_permissions_list(self):
        """Test getting all admin permissions."""
        all_perms = AdminPermissions.all_permissions()
        
        assert len(all_perms) == 9
        assert "view_model_health" in all_perms
        assert "manage_user_reports" in all_perms
        assert "view_system_logs" in all_perms


class TestExceptions:
    """Tests for custom exceptions."""
    
    def test_user_deletion_error(self):
        """Test UserDeletionError exception."""
        with pytest.raises(UserDeletionError) as exc_info:
            raise UserDeletionError("Cannot delete admin user")
        
        assert "Cannot delete admin user" in str(exc_info.value)
    
    def test_report_not_found_error(self):
        """Test ReportNotFoundError exception."""
        with pytest.raises(ReportNotFoundError) as exc_info:
            raise ReportNotFoundError("Report ID not found")
        
        assert "Report ID not found" in str(exc_info.value)
    
    def test_invalid_report_status_error(self):
        """Test InvalidReportStatusError exception."""
        with pytest.raises(InvalidReportStatusError) as exc_info:
            raise InvalidReportStatusError("Cannot transition from resolved to pending")
        
        assert "Cannot transition" in str(exc_info.value)
    
    def test_metrics_collection_error(self):
        """Test MetricsCollectionError exception."""
        with pytest.raises(MetricsCollectionError) as exc_info:
            raise MetricsCollectionError("Failed to collect GPU metrics")
        
        assert "GPU metrics" in str(exc_info.value)


# Integration test for checking permissions with RBAC
class TestAdminPermissionsIntegration:
    """Integration tests for admin permissions with RBAC."""
    
    def test_admin_role_has_all_permissions(self):
        """Test that admin permissions are a subset of what should be in admin role."""
        admin_perms = AdminPermissions.all_permissions()
        
        # These should match what's defined in seed_roles.py for admin
        expected_admin_perms = [
            "view_model_health",
            "view_analysis_stats",
            "view_user_stats",
            "manage_user_reports",
            "delete_user",  # Maps to delete_users in seed
            "reset_user_password",
            "view_system_logs",
            "manage_users",
            "view_all_users",
        ]
        
        for perm in admin_perms:
            # Each permission should map to something in the expected list
            assert perm in expected_admin_perms, f"Permission {perm} not found"
