"""
Tests for Admin Infrastructure Layer

Tests for metrics collector, admin repository, and user management extensions.
Includes unit tests with mocks and integration tests with MongoDB.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import time

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
)
from src.infrastructure.system.metrics_collector import (
    SystemMetricsCollector,
    get_metrics_collector,
    get_current_metrics,
    record_inference,
    _model_metrics,
)


class TestSystemMetricsCollector:
    """Tests for SystemMetricsCollector."""
    
    def test_collector_initialization(self):
        """Test that collector initializes correctly."""
        collector = SystemMetricsCollector(model_name="test-model")
        assert collector.model_name == "test-model"
    
    def test_collect_metrics_returns_model_health_metrics(self):
        """Test that collect_metrics returns ModelHealthMetrics entity."""
        collector = SystemMetricsCollector()
        metrics = collector.collect_metrics()
        
        assert isinstance(metrics, ModelHealthMetrics)
        assert metrics.collected_at is not None
        assert metrics.model_name == "verif-ai-bert"
    
    def test_collect_cpu_metrics_with_psutil(self):
        """Test CPU metrics collection with psutil available."""
        collector = SystemMetricsCollector()
        cpu_percent, cpu_count = collector._collect_cpu_metrics()
        
        # Should return valid values
        assert isinstance(cpu_percent, float)
        assert cpu_percent >= 0
        assert isinstance(cpu_count, int)
        assert cpu_count >= 1
    
    def test_collect_memory_metrics_with_psutil(self):
        """Test memory metrics collection with psutil available."""
        collector = SystemMetricsCollector()
        mem_used, mem_total, mem_percent = collector._collect_memory_metrics()
        
        # Should return valid values (may be 0 if psutil not available)
        assert isinstance(mem_used, float)
        assert isinstance(mem_total, float)
        assert isinstance(mem_percent, float)
        assert mem_percent >= 0
    
    def test_collect_gpu_metrics_without_gpu(self):
        """Test GPU metrics when no GPU is available."""
        collector = SystemMetricsCollector()
        # Force no GPU
        collector._pynvml = None
        collector._gpu_handle = None
        
        gpu_percent, gpu_mem_used, gpu_mem_total, gpu_temp = collector._collect_gpu_metrics()
        
        assert gpu_percent == 0.0
        assert gpu_mem_used == 0.0
        assert gpu_mem_total == 0.0
        assert gpu_temp is None
    
    def test_record_model_inference(self):
        """Test recording model inference metrics."""
        collector = SystemMetricsCollector()
        
        # Record some inferences
        collector.record_model_inference(token_count=100, processing_time_ms=50.5)
        collector.record_model_inference(token_count=200, processing_time_ms=75.0)
        
        model_metrics = collector._get_model_metrics()
        
        assert model_metrics["token_count_today"] >= 300
        assert model_metrics["requests_today"] >= 2
        assert model_metrics["avg_processing_speed_ms"] > 0
    
    def test_record_inference_convenience_function(self):
        """Test the convenience function for recording inference."""
        initial_metrics = get_current_metrics()
        initial_requests = initial_metrics.requests_total
        
        record_inference(token_count=50, processing_time_ms=25.0)
        
        new_metrics = get_current_metrics()
        assert new_metrics.requests_total >= initial_requests + 1
    
    def test_uptime_calculation(self):
        """Test that uptime is calculated correctly."""
        collector = SystemMetricsCollector()
        metrics = collector.collect_metrics()
        
        # Uptime should be at least 0 seconds
        assert metrics.uptime_seconds >= 0
    
    def test_metrics_to_dict_structure(self):
        """Test that metrics can be converted to dict properly."""
        collector = SystemMetricsCollector()
        metrics = collector.collect_metrics()
        data = metrics.to_dict()
        
        assert "gpu" in data
        assert "cpu" in data
        assert "memory" in data
        assert "model" in data
        assert "system" in data
        assert "collected_at" in data
    
    @patch('src.infrastructure.system.metrics_collector._try_import_psutil')
    def test_fallback_when_psutil_unavailable(self, mock_psutil):
        """Test fallback behavior when psutil is not available."""
        mock_psutil.return_value = None
        
        collector = SystemMetricsCollector()
        collector._psutil = None
        
        cpu_percent, cpu_count = collector._collect_cpu_metrics()
        
        # Should use fallback values
        assert cpu_percent == 0.0
        assert cpu_count >= 1


class TestAdminRepository:
    """Tests for AdminRepository."""
    
    @pytest.fixture
    def mock_mongo_client(self):
        """Create a mock MongoDB client."""
        client = MagicMock()
        db = MagicMock()
        client.__getitem__ = Mock(return_value=db)
        
        # Mock collections
        db.analysis_results = MagicMock()
        db.users = MagicMock()
        db.user_reports = MagicMock()
        db.admin_activity_logs = MagicMock()
        db.website_visits = MagicMock()
        
        return client
    
    def test_repository_initialization(self, mock_mongo_client):
        """Test repository initializes correctly."""
        from src.infrastructure.mongodb.admin_repository import AdminRepository
        
        repo = AdminRepository(mock_mongo_client, "test_db")
        
        assert repo.db is not None
        assert repo.analysis_collection is not None
        assert repo.users_collection is not None
        assert repo.reports_collection is not None
    
    def test_get_analysis_statistics_empty_db(self, mock_mongo_client):
        """Test getting analysis statistics with empty database."""
        from src.infrastructure.mongodb.admin_repository import AdminRepository
        
        # Mock empty aggregation result
        mock_mongo_client["test_db"].analysis_results.aggregate.return_value = iter([])
        
        repo = AdminRepository(mock_mongo_client, "test_db")
        stats = repo.get_analysis_statistics()
        
        assert isinstance(stats, AnalysisStatistics)
        assert stats.total_count == 0
        assert stats.high_risk_count == 0
    
    def test_get_analysis_statistics_with_data(self, mock_mongo_client):
        """Test getting analysis statistics with data."""
        from src.infrastructure.mongodb.admin_repository import AdminRepository
        
        # Mock aggregation result
        mock_result = [{
            "total_count": 100,
            "scam_count": 60,
            "legitimate_count": 40,
            "high_risk_count": 30,
            "medium_risk_count": 20,
        }]
        mock_mongo_client["test_db"].analysis_results.aggregate.return_value = iter(mock_result)
        
        repo = AdminRepository(mock_mongo_client, "test_db")
        stats = repo.get_analysis_statistics()
        
        assert stats.total_count == 100
        assert stats.high_risk_count == 30
        assert stats.medium_risk_count == 20
        assert stats.legitimate_count == 40
    
    def test_get_top_scam_categories(self, mock_mongo_client):
        """Test getting top scam categories."""
        from src.infrastructure.mongodb.admin_repository import AdminRepository
        
        # Mock aggregation result
        mock_result = [
            {"_id": "Phishing", "count": 50},
            {"_id": "Financial Fraud", "count": 30},
            {"_id": "Romance Scam", "count": 20},
        ]
        mock_mongo_client["test_db"].analysis_results.aggregate.return_value = iter(mock_result)
        
        repo = AdminRepository(mock_mongo_client, "test_db")
        categories = repo.get_top_scam_categories()
        
        assert len(categories) == 3
        assert categories[0].category == "Phishing"
        assert categories[0].count == 50
        assert categories[0].percentage == 50.0  # 50/100 * 100
    
    def test_create_report(self, mock_mongo_client):
        """Test creating a user report."""
        from src.infrastructure.mongodb.admin_repository import AdminRepository
        
        # Mock insert result
        mock_insert = MagicMock()
        mock_insert.inserted_id = "mock_id_123"
        mock_mongo_client["test_db"].user_reports.insert_one.return_value = mock_insert
        
        repo = AdminRepository(mock_mongo_client, "test_db")
        
        report = UserReport(
            user_id="user123",
            report_type=ReportType.HALLUCINATION,
            title="Test Report",
            description="Test description"
        )
        
        created_report = repo.create_report(report)
        
        assert created_report.id == "mock_id_123"
        mock_mongo_client["test_db"].user_reports.insert_one.assert_called_once()
    
    def test_get_reports_with_status_filter(self, mock_mongo_client):
        """Test getting reports with status filter."""
        from src.infrastructure.mongodb.admin_repository import AdminRepository
        
        # Mock find result
        mock_docs = [
            {
                "_id": "id1",
                "report_id": "report1",
                "user_id": "user1",
                "report_type": "hallucination",
                "title": "Report 1",
                "description": "Desc 1",
                "status": "pending",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            }
        ]
        mock_cursor = MagicMock()
        mock_cursor.sort.return_value = mock_cursor
        mock_cursor.skip.return_value = mock_cursor
        mock_cursor.limit.return_value = iter(mock_docs)
        mock_mongo_client["test_db"].user_reports.find.return_value = mock_cursor
        mock_mongo_client["test_db"].user_reports.count_documents.return_value = 1
        
        repo = AdminRepository(mock_mongo_client, "test_db")
        reports, total = repo.get_reports(status=ReportStatus.PENDING)
        
        assert total == 1
        assert len(reports) == 1
        assert reports[0].status == ReportStatus.PENDING
    
    def test_update_report_status(self, mock_mongo_client):
        """Test updating report status."""
        from src.infrastructure.mongodb.admin_repository import AdminRepository
        
        # Mock find_one_and_update result
        mock_doc = {
            "_id": "id1",
            "report_id": "report1",
            "user_id": "user1",
            "report_type": "hallucination",
            "title": "Report 1",
            "description": "Desc 1",
            "status": "resolved",
            "resolution_notes": "Fixed",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "resolved_at": datetime.utcnow(),
        }
        mock_mongo_client["test_db"].user_reports.find_one_and_update.return_value = mock_doc
        
        repo = AdminRepository(mock_mongo_client, "test_db")
        updated = repo.update_report_status(
            "report1",
            ReportStatus.RESOLVED,
            resolution_notes="Fixed"
        )
        
        assert updated.status == ReportStatus.RESOLVED
        assert updated.resolution_notes == "Fixed"
        assert updated.resolved_at is not None
    
    def test_update_report_status_not_found(self, mock_mongo_client):
        """Test updating report that doesn't exist."""
        from src.infrastructure.mongodb.admin_repository import AdminRepository
        
        mock_mongo_client["test_db"].user_reports.find_one_and_update.return_value = None
        
        repo = AdminRepository(mock_mongo_client, "test_db")
        
        with pytest.raises(ReportNotFoundError):
            repo.update_report_status("nonexistent", ReportStatus.RESOLVED)
    
    def test_log_admin_activity(self, mock_mongo_client):
        """Test logging admin activity."""
        from src.infrastructure.mongodb.admin_repository import AdminRepository
        
        # Mock insert result
        mock_insert = MagicMock()
        mock_insert.inserted_id = "log_id_123"
        mock_mongo_client["test_db"].admin_activity_logs.insert_one.return_value = mock_insert
        
        repo = AdminRepository(mock_mongo_client, "test_db")
        
        log = AdminActivityLog(
            admin_user_id="admin123",
            action="delete_user",
            resource_type="user",
            resource_id="user456"
        )
        
        created_log = repo.log_admin_activity(log)
        
        assert created_log.id == "log_id_123"
        mock_mongo_client["test_db"].admin_activity_logs.insert_one.assert_called_once()
    
    def test_get_user_statistics(self, mock_mongo_client):
        """Test getting user statistics."""
        from src.infrastructure.mongodb.admin_repository import AdminRepository
        
        # Mock count_documents
        mock_mongo_client["test_db"].users.count_documents.side_effect = [
            100,  # total_users
            80,   # verified_users
            10,   # new_users (with date filter)
        ]
        
        # Mock aggregate for active users
        mock_mongo_client["test_db"].analysis_results.aggregate.return_value = iter([
            {"active_users": 50}
        ])
        
        # Mock visits
        mock_mongo_client["test_db"].website_visits.count_documents.return_value = 1000
        
        repo = AdminRepository(mock_mongo_client, "test_db")
        stats = repo.get_user_statistics()
        
        assert isinstance(stats, UserStatistics)
        assert stats.total_users == 100
        assert stats.verified_users_count == 80
        assert stats.unverified_users_count == 20


class TestUserRepositoryAdminExtensions:
    """Tests for admin extensions in MongoDBUserRepository."""
    
    @pytest.fixture
    def mock_mongo_client(self):
        """Create a mock MongoDB client."""
        client = MagicMock()
        db = MagicMock()
        client.__getitem__ = Mock(return_value=db)
        
        db.users = MagicMock()
        db.roles = MagicMock()
        db.analysis_results = MagicMock()
        
        return client
    
    def test_get_all_users_no_filters(self, mock_mongo_client):
        """Test getting all users without filters."""
        from src.infrastructure.mongodb.repositories import MongoDBUserRepository
        
        # Mock user documents
        mock_docs = [
            {
                "_id": "id1",
                "email": "user1@test.com",
                "username": "user1",
                "password_hash": "hash1",
                "roles": ["user"],
                "is_active": True,
                "is_verified": True,
            }
        ]
        mock_cursor = MagicMock()
        mock_cursor.sort.return_value = mock_cursor
        mock_cursor.skip.return_value = mock_cursor
        mock_cursor.limit.return_value = iter(mock_docs)
        mock_mongo_client["test_db"].users.find.return_value = mock_cursor
        mock_mongo_client["test_db"].users.count_documents.return_value = 1
        
        repo = MongoDBUserRepository(mock_mongo_client, "test_db")
        users, total = repo.get_all_users()
        
        assert total == 1
        assert len(users) == 1
        assert users[0].email == "user1@test.com"
    
    def test_get_all_users_with_search(self, mock_mongo_client):
        """Test getting users with search filter."""
        from src.infrastructure.mongodb.repositories import MongoDBUserRepository
        
        mock_cursor = MagicMock()
        mock_cursor.sort.return_value = mock_cursor
        mock_cursor.skip.return_value = mock_cursor
        mock_cursor.limit.return_value = iter([])
        mock_mongo_client["test_db"].users.find.return_value = mock_cursor
        mock_mongo_client["test_db"].users.count_documents.return_value = 0
        
        repo = MongoDBUserRepository(mock_mongo_client, "test_db")
        users, total = repo.get_all_users(search="test@email.com")
        
        # Verify find was called with $or for search
        call_args = mock_mongo_client["test_db"].users.find.call_args[0][0]
        assert "$or" in call_args
    
    def test_delete_user_soft_delete(self, mock_mongo_client):
        """Test soft deleting a user."""
        from src.infrastructure.mongodb.repositories import MongoDBUserRepository
        from bson import ObjectId
        
        # Mock finding the user
        mock_mongo_client["test_db"].users.find_one.return_value = {
            "_id": ObjectId("507f1f77bcf86cd799439011"),
            "email": "user@test.com"
        }
        
        # Mock update result
        mock_result = MagicMock()
        mock_result.modified_count = 1
        mock_mongo_client["test_db"].users.update_one.return_value = mock_result
        
        repo = MongoDBUserRepository(mock_mongo_client, "test_db")
        result = repo.delete_user("507f1f77bcf86cd799439011", hard_delete=False)
        
        assert result is True
        mock_mongo_client["test_db"].users.update_one.assert_called_once()
    
    def test_delete_user_hard_delete(self, mock_mongo_client):
        """Test hard deleting a user."""
        from src.infrastructure.mongodb.repositories import MongoDBUserRepository
        from bson import ObjectId
        
        # Mock finding the user
        mock_mongo_client["test_db"].users.find_one.return_value = {
            "_id": ObjectId("507f1f77bcf86cd799439011"),
            "email": "user@test.com"
        }
        
        # Mock delete result
        mock_result = MagicMock()
        mock_result.deleted_count = 1
        mock_mongo_client["test_db"].users.delete_one.return_value = mock_result
        
        repo = MongoDBUserRepository(mock_mongo_client, "test_db")
        result = repo.delete_user("507f1f77bcf86cd799439011", hard_delete=True)
        
        assert result is True
        mock_mongo_client["test_db"].users.delete_one.assert_called_once()
    
    def test_delete_user_not_found(self, mock_mongo_client):
        """Test deleting a user that doesn't exist."""
        from src.infrastructure.mongodb.repositories import MongoDBUserRepository
        from src.domain.entities import UserNotFoundError
        from bson import ObjectId
        
        mock_mongo_client["test_db"].users.find_one.return_value = None
        
        repo = MongoDBUserRepository(mock_mongo_client, "test_db")
        
        # Use a valid ObjectId format
        with pytest.raises(UserNotFoundError):
            repo.delete_user("507f1f77bcf86cd799439011")
    
    def test_admin_reset_password(self, mock_mongo_client):
        """Test admin resetting a user's password."""
        from src.infrastructure.mongodb.repositories import MongoDBUserRepository
        from bson import ObjectId
        
        # Mock finding the user
        mock_mongo_client["test_db"].users.find_one.return_value = {
            "_id": ObjectId("507f1f77bcf86cd799439011"),
            "email": "user@test.com"
        }
        
        # Mock update result
        mock_result = MagicMock()
        mock_result.modified_count = 1
        mock_mongo_client["test_db"].users.update_one.return_value = mock_result
        
        repo = MongoDBUserRepository(mock_mongo_client, "test_db")
        result = repo.admin_reset_password("507f1f77bcf86cd799439011", "new_hash")
        
        assert result is True
        
        # Verify update was called with correct fields
        call_args = mock_mongo_client["test_db"].users.update_one.call_args[0][1]["$set"]
        assert call_args["password_hash"] == "new_hash"
        assert call_args["password_reset_by_admin"] is True
    
    def test_update_user_status(self, mock_mongo_client):
        """Test updating user active status."""
        from src.infrastructure.mongodb.repositories import MongoDBUserRepository
        from bson import ObjectId
        
        # Mock finding the user
        mock_mongo_client["test_db"].users.find_one.return_value = {
            "_id": ObjectId("507f1f77bcf86cd799439011"),
            "email": "user@test.com"
        }
        
        # Mock update result
        mock_result = MagicMock()
        mock_result.modified_count = 1
        mock_mongo_client["test_db"].users.update_one.return_value = mock_result
        
        repo = MongoDBUserRepository(mock_mongo_client, "test_db")
        result = repo.update_user_status("507f1f77bcf86cd799439011", is_active=False)
        
        assert result is True
        
        # Verify update was called with is_active=False
        call_args = mock_mongo_client["test_db"].users.update_one.call_args[0][1]["$set"]
        assert call_args["is_active"] is False
    
    def test_update_user_roles(self, mock_mongo_client):
        """Test updating user roles."""
        from src.infrastructure.mongodb.repositories import MongoDBUserRepository
        from bson import ObjectId
        
        # Mock finding the user
        mock_mongo_client["test_db"].users.find_one.return_value = {
            "_id": ObjectId("507f1f77bcf86cd799439011"),
            "email": "user@test.com"
        }
        
        # Mock update result
        mock_result = MagicMock()
        mock_result.modified_count = 1
        mock_mongo_client["test_db"].users.update_one.return_value = mock_result
        
        repo = MongoDBUserRepository(mock_mongo_client, "test_db")
        result = repo.update_user_roles("507f1f77bcf86cd799439011", ["user", "moderator"])
        
        assert result is True
        
        # Verify update was called with new roles
        call_args = mock_mongo_client["test_db"].users.update_one.call_args[0][1]["$set"]
        assert call_args["roles"] == ["user", "moderator"]


class TestMetricsIntegration:
    """Integration tests for metrics that require actual system calls."""
    
    def test_get_current_metrics_integration(self):
        """Test getting current metrics in integration setting."""
        metrics = get_current_metrics()
        
        # Should return valid ModelHealthMetrics
        assert isinstance(metrics, ModelHealthMetrics)
        assert metrics.cpu_count >= 1
        assert metrics.uptime_seconds >= 0
    
    def test_record_and_retrieve_metrics(self):
        """Test recording inferences and retrieving updated metrics."""
        # Record some inferences
        for i in range(5):
            record_inference(token_count=100 + i * 10, processing_time_ms=50 + i * 5)
        
        metrics = get_current_metrics()
        
        # Metrics should reflect recorded data
        assert metrics.requests_total >= 5
        assert metrics.token_count_total >= 500
        assert metrics.avg_processing_speed_ms > 0


class TestStatisticsPeriodFiltering:
    """Tests for date range filtering in statistics."""
    
    @pytest.fixture
    def mock_mongo_client(self):
        """Create a mock MongoDB client."""
        client = MagicMock()
        db = MagicMock()
        client.__getitem__ = Mock(return_value=db)
        
        db.analysis_results = MagicMock()
        db.users = MagicMock()
        db.user_reports = MagicMock()
        db.admin_activity_logs = MagicMock()
        db.website_visits = MagicMock()
        
        return client
    
    def test_analysis_stats_with_date_range(self, mock_mongo_client):
        """Test analysis statistics with date range filter."""
        from src.infrastructure.mongodb.admin_repository import AdminRepository
        
        mock_mongo_client["test_db"].analysis_results.aggregate.return_value = iter([])
        
        repo = AdminRepository(mock_mongo_client, "test_db")
        
        start = datetime.utcnow() - timedelta(days=7)
        end = datetime.utcnow()
        
        stats = repo.get_analysis_statistics(
            start_date=start,
            end_date=end,
            period=StatisticsPeriod.WEEK
        )
        
        assert stats.period == StatisticsPeriod.WEEK
        assert stats.start_date == start
        assert stats.end_date == end
    
    def test_user_stats_with_date_range(self, mock_mongo_client):
        """Test user statistics with date range filter."""
        from src.infrastructure.mongodb.admin_repository import AdminRepository
        
        # Setup mocks
        mock_mongo_client["test_db"].users.count_documents.return_value = 0
        mock_mongo_client["test_db"].analysis_results.aggregate.return_value = iter([])
        mock_mongo_client["test_db"].analysis_results.count_documents.return_value = 0
        mock_mongo_client["test_db"].website_visits.count_documents.return_value = 0
        mock_mongo_client["test_db"].website_visits.aggregate.return_value = iter([])
        mock_mongo_client["test_db"].users.aggregate.return_value = iter([])
        
        repo = AdminRepository(mock_mongo_client, "test_db")
        
        start = datetime.utcnow() - timedelta(days=30)
        end = datetime.utcnow()
        
        stats = repo.get_user_statistics(
            start_date=start,
            end_date=end,
            period=StatisticsPeriod.MONTH
        )
        
        assert stats.period == StatisticsPeriod.MONTH
        assert stats.start_date == start
        assert stats.end_date == end
