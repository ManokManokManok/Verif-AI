"""
Tests for Admin API Endpoints (Phase 4)

Tests the REST API layer including:
- Model Health endpoints
- Analysis Statistics endpoints
- User Statistics endpoints
- User Reports endpoints
- User Management endpoints

Tests cover authentication, authorization, request validation,
and response formatting.
"""

import os
import django

# Configure Django settings before importing DRF
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'verfai.settings')
django.setup()

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from rest_framework.test import APIRequestFactory
from rest_framework import status
import json

# Import views to test
from src.interfaces.rest.admin_views import (
    model_health,
    model_health_summary,
    analysis_stats,
    top_scam_categories,
    export_analysis_stats,
    user_stats,
    list_reports,
    update_report,
    list_users,
    get_user,
    delete_user,
    reset_user_password,
    update_user_status,
    update_user_roles,
    extract_user_from_request,
    require_admin,
    parse_date_param,
    parse_period_param,
)
from src.domain.admin_entities import (
    ModelHealthMetrics,
    AnalysisStatistics,
    UserStatistics,
    UserReport,
    ScamCategoryBreakdown,
    ReportStatus,
    StatisticsPeriod,
)
from src.domain.entities import User


@pytest.fixture
def api_factory():
    """Create API request factory."""
    return APIRequestFactory()


@pytest.fixture
def admin_token_payload():
    """Valid admin JWT payload."""
    return {
        'user_id': 'admin-123',
        'email': 'admin@test.com',
        'roles': ['admin'],
        'exp': (datetime.utcnow() + timedelta(hours=1)).timestamp()
    }


@pytest.fixture
def non_admin_token_payload():
    """Non-admin user JWT payload."""
    return {
        'user_id': 'user-123',
        'email': 'user@test.com',
        'roles': ['user'],
        'exp': (datetime.utcnow() + timedelta(hours=1)).timestamp()
    }


@pytest.fixture
def super_admin_token_payload():
    """Super admin JWT payload."""
    return {
        'user_id': 'superadmin-123',
        'email': 'superadmin@test.com',
        'roles': ['super_admin'],
        'exp': (datetime.utcnow() + timedelta(hours=1)).timestamp()
    }


@pytest.fixture
def sample_model_health_metrics():
    """Sample model health metrics."""
    return ModelHealthMetrics(
        gpu_usage_percent=45.5,
        gpu_memory_used_mb=4000.0,
        gpu_memory_total_mb=8000.0,
        cpu_usage_percent=30.2,
        memory_used_mb=8000.0,
        memory_total_mb=16000.0,
        memory_usage_percent=50.0,
        model_name="verif-ai-bert",
        token_count_today=10000,
        token_count_total=1000000,
        avg_processing_speed_ms=150.5,
    )


@pytest.fixture
def sample_analysis_statistics():
    """Sample analysis statistics."""
    return AnalysisStatistics(
        total_count=500,
        high_risk_count=100,
        medium_risk_count=150,
        low_risk_count=100,
        legitimate_count=150,
        period=StatisticsPeriod.MONTH,
        start_date=datetime.utcnow() - timedelta(days=30),
        end_date=datetime.utcnow(),
        scam_categories_breakdown=[
            ScamCategoryBreakdown(category="phishing", count=80, percentage=32.0),
            ScamCategoryBreakdown(category="fraud", count=60, percentage=24.0),
        ]
    )


@pytest.fixture
def sample_user_statistics():
    """Sample user statistics."""
    return UserStatistics(
        total_users=1000,
        new_users_count=150,
        active_users_count=500,
        verified_users_count=800,
        unverified_users_count=200,
        website_visits=5000,
        unique_visitors=2000,
        period=StatisticsPeriod.MONTH,
        start_date=datetime.utcnow() - timedelta(days=30),
        end_date=datetime.utcnow(),
    )


@pytest.fixture
def sample_user_report():
    """Sample user report."""
    from src.domain.admin_entities import ReportType
    return UserReport(
        report_id="report-123",
        user_id="user-456",
        report_type=ReportType.BUG,
        title="Bug Report",
        description="Suspicious activity",
        status=ReportStatus.PENDING,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )


@pytest.fixture
def sample_scam_categories():
    """Sample scam categories."""
    return [
        ScamCategoryBreakdown(
            category="phishing",
            count=100,
            percentage=40.0,
        ),
        ScamCategoryBreakdown(
            category="fraud",
            count=75,
            percentage=30.0,
        ),
    ]


@pytest.fixture
def sample_user():
    """Sample user entity."""
    return User(
        id="user-123",
        email="test@example.com",
        username="testuser",
        password_hash="hashed",
        created_at=datetime.utcnow(),
        is_active=True,
        is_verified=True,
        roles=['user']
    )


# ==================== Helper Function Tests ====================

class TestHelperFunctions:
    """Tests for helper functions."""
    
    def test_parse_date_param_valid_date(self):
        """Should parse valid date string."""
        result = parse_date_param('2024-01-15')
        assert result is not None
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15
    
    def test_parse_date_param_with_time(self):
        """Should parse date with time."""
        result = parse_date_param('2024-01-15T10:30:00')
        assert result is not None
        assert result.hour == 10
        assert result.minute == 30
    
    def test_parse_date_param_with_z_suffix(self):
        """Should parse ISO date with Z suffix."""
        result = parse_date_param('2024-01-15T10:30:00Z')
        assert result is not None
    
    def test_parse_date_param_invalid(self):
        """Should return None for invalid date."""
        assert parse_date_param('invalid') is None
        assert parse_date_param('') is None
        assert parse_date_param(None) is None
    
    def test_parse_period_param_valid(self):
        """Should parse valid period strings."""
        assert parse_period_param('day') == StatisticsPeriod.DAY
        assert parse_period_param('week') == StatisticsPeriod.WEEK
        assert parse_period_param('month') == StatisticsPeriod.MONTH
        assert parse_period_param('year') == StatisticsPeriod.YEAR
        assert parse_period_param('all') == StatisticsPeriod.ALL_TIME
        assert parse_period_param('all_time') == StatisticsPeriod.ALL_TIME
    
    def test_parse_period_param_case_insensitive(self):
        """Should be case insensitive."""
        assert parse_period_param('DAY') == StatisticsPeriod.DAY
        assert parse_period_param('Month') == StatisticsPeriod.MONTH
    
    def test_parse_period_param_invalid(self):
        """Should default to ALL_TIME for invalid input."""
        assert parse_period_param('invalid') == StatisticsPeriod.ALL_TIME
        assert parse_period_param('') == StatisticsPeriod.ALL_TIME
        assert parse_period_param(None) == StatisticsPeriod.ALL_TIME


class TestExtractUserFromRequest:
    """Tests for extract_user_from_request function."""
    
    def test_no_auth_header(self, api_factory):
        """Should return empty tuple with no auth header."""
        request = api_factory.get('/test/')
        user_id, email, roles = extract_user_from_request(request)
        assert user_id is None
        assert email is None
        assert roles == []
    
    def test_invalid_auth_header_format(self, api_factory):
        """Should return empty tuple with wrong format."""
        request = api_factory.get('/test/', HTTP_AUTHORIZATION='Basic token123')
        user_id, email, roles = extract_user_from_request(request)
        assert user_id is None
    
    @patch('src.interfaces.rest.admin_views.get_jwt_service')
    def test_valid_token(self, mock_get_jwt, api_factory, admin_token_payload):
        """Should extract user from valid token."""
        mock_jwt = Mock()
        mock_jwt.verify_access_token.return_value = admin_token_payload
        mock_get_jwt.return_value = mock_jwt
        
        request = api_factory.get('/test/', HTTP_AUTHORIZATION='Bearer validtoken')
        user_id, email, roles = extract_user_from_request(request)
        
        assert user_id == 'admin-123'
        assert email == 'admin@test.com'
        assert 'admin' in roles
    
    @patch('src.interfaces.rest.admin_views.get_jwt_service')
    def test_invalid_token(self, mock_get_jwt, api_factory):
        """Should return empty tuple for invalid token."""
        mock_jwt = Mock()
        mock_jwt.verify_access_token.side_effect = Exception("Invalid token")
        mock_get_jwt.return_value = mock_jwt
        
        request = api_factory.get('/test/', HTTP_AUTHORIZATION='Bearer invalidtoken')
        user_id, email, roles = extract_user_from_request(request)
        
        assert user_id is None


class TestRequireAdmin:
    """Tests for require_admin function."""
    
    def test_no_authentication(self, api_factory):
        """Should return 401 when not authenticated."""
        request = api_factory.get('/test/')
        response = require_admin(request)
        
        assert response is not None
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.data['error']['code'] == 'AUTHENTICATION_REQUIRED'
    
    @patch('src.interfaces.rest.admin_views.extract_user_from_request')
    def test_non_admin_user(self, mock_extract, api_factory):
        """Should return 403 when user is not admin."""
        mock_extract.return_value = ('user-123', 'user@test.com', ['user'])
        
        request = api_factory.get('/test/', HTTP_AUTHORIZATION='Bearer token')
        response = require_admin(request)
        
        assert response is not None
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data['error']['code'] == 'PERMISSION_DENIED'
    
    @patch('src.interfaces.rest.admin_views.extract_user_from_request')
    def test_admin_user(self, mock_extract, api_factory):
        """Should return None when user is admin."""
        mock_extract.return_value = ('admin-123', 'admin@test.com', ['admin'])
        
        request = api_factory.get('/test/', HTTP_AUTHORIZATION='Bearer token')
        response = require_admin(request)
        
        assert response is None
    
    @patch('src.interfaces.rest.admin_views.extract_user_from_request')
    def test_super_admin_user(self, mock_extract, api_factory):
        """Should return None when user is super_admin."""
        mock_extract.return_value = ('superadmin-123', 'super@test.com', ['super_admin'])
        
        request = api_factory.get('/test/', HTTP_AUTHORIZATION='Bearer token')
        response = require_admin(request)
        
        assert response is None


# ==================== Model Health Endpoint Tests ====================

class TestModelHealthEndpoint:
    """Tests for model health endpoints."""
    
    @patch('src.interfaces.rest.admin_views.require_admin')
    @patch('src.interfaces.rest.admin_views.get_metrics_collector')
    @patch('src.interfaces.rest.admin_views.GetModelHealthUseCase')
    def test_model_health_success(self, mock_use_case_class, mock_get_collector, 
                                   mock_require_admin, api_factory, sample_model_health_metrics):
        """Should return model health metrics successfully."""
        mock_require_admin.return_value = None
        
        # Setup use case mock
        mock_result = Mock()
        mock_result.success = True
        mock_result.metrics = sample_model_health_metrics
        
        mock_use_case = Mock()
        mock_use_case.execute.return_value = mock_result
        mock_use_case_class.return_value = mock_use_case
        
        request = api_factory.get('/api/admin/model-health/', 
                                   HTTP_AUTHORIZATION='Bearer token')
        response = model_health(request)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert 'gpu' in response.data['data']
        assert 'usage_percent' in response.data['data']['gpu']
    
    @patch('src.interfaces.rest.admin_views.require_admin')
    def test_model_health_unauthorized(self, mock_require_admin, api_factory):
        """Should return 401 when not authenticated."""
        from rest_framework.response import Response as DRFResponse
        mock_require_admin.return_value = DRFResponse(
            data={'error': {'code': 'AUTHENTICATION_REQUIRED', 'message': 'Auth required'}},
            status=401
        )
        
        request = api_factory.get('/api/admin/model-health/')
        response = model_health(request)
        
        assert response.status_code == 401
    
    @patch('src.interfaces.rest.admin_views.require_admin')
    @patch('src.interfaces.rest.admin_views.get_metrics_collector')
    @patch('src.interfaces.rest.admin_views.GetModelHealthUseCase')
    def test_model_health_error(self, mock_use_case_class, mock_get_collector,
                                 mock_require_admin, api_factory):
        """Should handle use case errors."""
        mock_require_admin.return_value = None
        
        mock_result = Mock()
        mock_result.success = False
        mock_result.error_message = "GPU unavailable"
        
        mock_use_case = Mock()
        mock_use_case.execute.return_value = mock_result
        mock_use_case_class.return_value = mock_use_case
        
        request = api_factory.get('/api/admin/model-health/',
                                   HTTP_AUTHORIZATION='Bearer token')
        response = model_health(request)
        
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response.data['success'] is False

    @patch('src.interfaces.rest.admin_views.require_admin')
    @patch('src.interfaces.rest.admin_views.get_metrics_collector')
    @patch('src.interfaces.rest.admin_views.GetModelHealthUseCase')
    def test_model_health_summary_success(self, mock_use_case_class, mock_get_collector,
                                           mock_require_admin, api_factory):
        """Should return health summary successfully."""
        mock_require_admin.return_value = None
        
        mock_use_case = Mock()
        mock_use_case.get_metrics_summary.return_value = {
            'overall_status': 'healthy',
            'gpu_status': 'normal',
            'cpu_status': 'normal',
            'memory_status': 'normal'
        }
        mock_use_case_class.return_value = mock_use_case
        
        request = api_factory.get('/api/admin/model-health/summary/',
                                   HTTP_AUTHORIZATION='Bearer token')
        response = model_health_summary(request)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert 'overall_status' in response.data['data']


# ==================== Analysis Statistics Endpoint Tests ====================

class TestAnalysisStatsEndpoint:
    """Tests for analysis statistics endpoints."""
    
    @patch('src.interfaces.rest.admin_views.require_admin')
    @patch('src.interfaces.rest.admin_views.get_admin_repository')
    @patch('src.interfaces.rest.admin_views.GetAnalysisStatisticsUseCase')
    def test_analysis_stats_success(self, mock_use_case_class, mock_get_repo,
                                     mock_require_admin, api_factory, 
                                     sample_analysis_statistics):
        """Should return analysis statistics successfully."""
        mock_require_admin.return_value = None
        
        mock_result = Mock()
        mock_result.success = True
        mock_result.statistics = sample_analysis_statistics
        
        mock_use_case = Mock()
        mock_use_case.execute.return_value = mock_result
        mock_use_case_class.return_value = mock_use_case
        
        request = api_factory.get('/api/admin/analysis-stats/',
                                   HTTP_AUTHORIZATION='Bearer token')
        response = analysis_stats(request)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert response.data['data']['total_count'] == 500
    
    @patch('src.interfaces.rest.admin_views.require_admin')
    @patch('src.interfaces.rest.admin_views.get_admin_repository')
    @patch('src.interfaces.rest.admin_views.GetAnalysisStatisticsUseCase')
    def test_analysis_stats_with_date_filter(self, mock_use_case_class, mock_get_repo,
                                              mock_require_admin, api_factory,
                                              sample_analysis_statistics):
        """Should pass date filters to use case."""
        mock_require_admin.return_value = None
        
        mock_result = Mock()
        mock_result.success = True
        mock_result.statistics = sample_analysis_statistics
        
        mock_use_case = Mock()
        mock_use_case.execute.return_value = mock_result
        mock_use_case_class.return_value = mock_use_case
        
        request = api_factory.get(
            '/api/admin/analysis-stats/?start_date=2024-01-01&end_date=2024-01-31&period=month',
            HTTP_AUTHORIZATION='Bearer token'
        )
        response = analysis_stats(request)
        
        assert response.status_code == status.HTTP_200_OK
        # Verify use case was called with parsed dates
        call_args = mock_use_case.execute.call_args
        assert call_args.kwargs['period'] == StatisticsPeriod.MONTH
    
    @patch('src.interfaces.rest.admin_views.require_admin')
    @patch('src.interfaces.rest.admin_views.get_admin_repository')
    @patch('src.interfaces.rest.admin_views.GetTopScamCategoriesUseCase')
    def test_top_scam_categories_success(self, mock_use_case_class, mock_get_repo,
                                          mock_require_admin, api_factory,
                                          sample_scam_categories):
        """Should return top scam categories successfully."""
        mock_require_admin.return_value = None
        
        mock_result = Mock()
        mock_result.success = True
        mock_result.categories = sample_scam_categories
        
        mock_use_case = Mock()
        mock_use_case.execute.return_value = mock_result
        mock_use_case_class.return_value = mock_use_case
        
        request = api_factory.get('/api/admin/analysis-stats/top-categories/',
                                   HTTP_AUTHORIZATION='Bearer token')
        response = top_scam_categories(request)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert len(response.data['data']) == 2
        assert response.data['data'][0]['category'] == 'phishing'
    
    @patch('src.interfaces.rest.admin_views.require_admin')
    @patch('src.interfaces.rest.admin_views.get_admin_repository')
    @patch('src.interfaces.rest.admin_views.GetTopScamCategoriesUseCase')
    def test_top_scam_categories_with_limit(self, mock_use_case_class, mock_get_repo,
                                             mock_require_admin, api_factory,
                                             sample_scam_categories):
        """Should respect limit parameter."""
        mock_require_admin.return_value = None
        
        mock_result = Mock()
        mock_result.success = True
        mock_result.categories = sample_scam_categories[:1]  # Just one
        
        mock_use_case = Mock()
        mock_use_case.execute.return_value = mock_result
        mock_use_case_class.return_value = mock_use_case
        
        request = api_factory.get('/api/admin/analysis-stats/top-categories/?limit=1',
                                   HTTP_AUTHORIZATION='Bearer token')
        response = top_scam_categories(request)
        
        assert response.status_code == status.HTTP_200_OK
        call_args = mock_use_case.execute.call_args
        assert call_args.kwargs['limit'] == 1
    
    @patch('src.interfaces.rest.admin_views.require_admin')
    def test_top_scam_categories_invalid_limit(self, mock_require_admin, api_factory):
        """Should handle invalid limit parameter."""
        mock_require_admin.return_value = None
        
        request = api_factory.get('/api/admin/analysis-stats/top-categories/?limit=invalid',
                                   HTTP_AUTHORIZATION='Bearer token')
        response = top_scam_categories(request)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['error']['code'] == 'INVALID_INPUT'

    @patch('src.interfaces.rest.admin_views.require_admin')
    @patch('src.interfaces.rest.admin_views.get_admin_repository')
    @patch('src.interfaces.rest.admin_views.GetTopScamCategoriesUseCase')
    @patch('src.interfaces.rest.admin_views.GetAnalysisStatisticsUseCase')
    def test_export_analysis_stats_success(
        self,
        mock_stats_use_case_class,
        mock_categories_use_case_class,
        mock_get_repo,
        mock_require_admin,
        api_factory,
        sample_analysis_statistics,
        sample_scam_categories,
    ):
        """Should export analysis stats as downloadable CSV."""
        mock_require_admin.return_value = None

        stats_result = Mock(success=True, statistics=sample_analysis_statistics)
        stats_use_case = Mock()
        stats_use_case.execute.return_value = stats_result
        mock_stats_use_case_class.return_value = stats_use_case

        categories_result = Mock(success=True, categories=sample_scam_categories)
        categories_use_case = Mock()
        categories_use_case.execute.return_value = categories_result
        mock_categories_use_case_class.return_value = categories_use_case

        request = api_factory.get('/api/admin/analysis-stats/export/?period=month&format=csv',
                                   HTTP_AUTHORIZATION='Bearer token')
        response = export_analysis_stats(request)

        assert response.status_code == status.HTTP_200_OK
        assert 'text/csv' in response['Content-Type']
        assert 'attachment; filename=' in response['Content-Disposition']
        body = response.content.decode('utf-8')
        assert 'Summary Metric,Value' in body
        assert 'Top Scam Categories' in body

    @patch('src.interfaces.rest.admin_views.require_admin')
    def test_export_analysis_stats_invalid_format(self, mock_require_admin, api_factory):
        """Should reject unsupported export formats."""
        mock_require_admin.return_value = None

        request = api_factory.get('/api/admin/analysis-stats/export/?format=pdf',
                                   HTTP_AUTHORIZATION='Bearer token')
        response = export_analysis_stats(request)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['error']['code'] == 'INVALID_INPUT'


# ==================== User Statistics Endpoint Tests ====================

class TestUserStatsEndpoint:
    """Tests for user statistics endpoint."""
    
    @patch('src.interfaces.rest.admin_views.require_admin')
    @patch('src.interfaces.rest.admin_views.get_admin_repository')
    @patch('src.interfaces.rest.admin_views.GetUserStatisticsUseCase')
    def test_user_stats_success(self, mock_use_case_class, mock_get_repo,
                                 mock_require_admin, api_factory,
                                 sample_user_statistics):
        """Should return user statistics successfully."""
        mock_require_admin.return_value = None
        
        mock_result = Mock()
        mock_result.success = True
        mock_result.statistics = sample_user_statistics
        
        mock_use_case = Mock()
        mock_use_case.execute.return_value = mock_result
        mock_use_case_class.return_value = mock_use_case
        
        request = api_factory.get('/api/admin/user-stats/',
                                   HTTP_AUTHORIZATION='Bearer token')
        response = user_stats(request)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert response.data['data']['total_users'] == 1000
        assert response.data['data']['new_users_count'] == 150


# ==================== User Reports Endpoint Tests ====================

class TestUserReportsEndpoint:
    """Tests for user reports endpoints."""
    
    @patch('src.interfaces.rest.admin_views.require_admin')
    @patch('src.interfaces.rest.admin_views.get_admin_repository')
    @patch('src.interfaces.rest.admin_views.GetUserReportsUseCase')
    def test_list_reports_success(self, mock_use_case_class, mock_get_repo,
                                   mock_require_admin, api_factory,
                                   sample_user_report):
        """Should list reports with pagination."""
        mock_require_admin.return_value = None
        
        mock_result = Mock()
        mock_result.success = True
        mock_result.reports = [sample_user_report]
        mock_result.total_count = 1
        
        mock_use_case = Mock()
        mock_use_case.execute.return_value = mock_result
        mock_use_case_class.return_value = mock_use_case
        
        request = api_factory.get('/api/admin/reports/',
                                   HTTP_AUTHORIZATION='Bearer token')
        response = list_reports(request)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert len(response.data['data']['reports']) == 1
        assert response.data['data']['total'] == 1
        assert response.data['data']['page'] == 1
    
    @patch('src.interfaces.rest.admin_views.require_admin')
    @patch('src.interfaces.rest.admin_views.get_admin_repository')
    @patch('src.interfaces.rest.admin_views.GetUserReportsUseCase')
    def test_list_reports_with_status_filter(self, mock_use_case_class, mock_get_repo,
                                              mock_require_admin, api_factory,
                                              sample_user_report):
        """Should filter reports by status."""
        mock_require_admin.return_value = None
        
        mock_result = Mock()
        mock_result.success = True
        mock_result.reports = [sample_user_report]
        mock_result.total_count = 1
        
        mock_use_case = Mock()
        mock_use_case.execute.return_value = mock_result
        mock_use_case_class.return_value = mock_use_case
        
        request = api_factory.get('/api/admin/reports/?status=pending',
                                   HTTP_AUTHORIZATION='Bearer token')
        response = list_reports(request)
        
        assert response.status_code == status.HTTP_200_OK
        call_args = mock_use_case.execute.call_args
        assert call_args.kwargs['status'] == ReportStatus.PENDING
    
    @patch('src.interfaces.rest.admin_views.require_admin')
    @patch('src.interfaces.rest.admin_views.get_admin_repository')
    @patch('src.interfaces.rest.admin_views.GetUserReportsUseCase')
    def test_list_reports_pagination(self, mock_use_case_class, mock_get_repo,
                                      mock_require_admin, api_factory,
                                      sample_user_report):
        """Should handle pagination parameters."""
        mock_require_admin.return_value = None
        
        mock_result = Mock()
        mock_result.success = True
        mock_result.reports = []
        mock_result.total_count = 150
        
        mock_use_case = Mock()
        mock_use_case.execute.return_value = mock_result
        mock_use_case_class.return_value = mock_use_case
        
        request = api_factory.get('/api/admin/reports/?page=3&limit=25',
                                   HTTP_AUTHORIZATION='Bearer token')
        response = list_reports(request)
        
        assert response.status_code == status.HTTP_200_OK
        call_args = mock_use_case.execute.call_args
        assert call_args.kwargs['limit'] == 25
        assert call_args.kwargs['offset'] == 50  # (3-1) * 25
        assert response.data['data']['total_pages'] == 6
    
    @patch('src.interfaces.rest.admin_views.require_admin')
    @patch('src.interfaces.rest.admin_views.extract_user_from_request')
    @patch('src.interfaces.rest.admin_views.get_admin_repository')
    @patch('src.interfaces.rest.admin_views.UpdateReportStatusUseCase')
    def test_update_report_success(self, mock_use_case_class, mock_get_repo,
                                    mock_extract, mock_require_admin, api_factory,
                                    sample_user_report):
        """Should update report status successfully."""
        mock_require_admin.return_value = None
        mock_extract.return_value = ('admin-123', 'admin@test.com', ['admin'])
        
        from src.domain.admin_entities import ReportType
        updated_report = UserReport(
            report_id=sample_user_report.report_id,
            user_id=sample_user_report.user_id,
            report_type=sample_user_report.report_type,
            title=sample_user_report.title,
            description=sample_user_report.description,
            status=ReportStatus.RESOLVED,
            created_at=sample_user_report.created_at,
            updated_at=datetime.utcnow(),
            assigned_to='admin-123',
            resolved_at=datetime.utcnow(),
            resolution_notes='Handled'
        )
        
        mock_result = Mock()
        mock_result.success = True
        mock_result.report = updated_report
        
        mock_use_case = Mock()
        mock_use_case.execute.return_value = mock_result
        mock_use_case_class.return_value = mock_use_case
        
        request = api_factory.patch(
            '/api/admin/reports/report-123/',
            {'status': 'resolved', 'resolution_notes': 'Handled'},
            format='json',
            HTTP_AUTHORIZATION='Bearer token'
        )
        response = update_report(request, 'report-123')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
    
    @patch('src.interfaces.rest.admin_views.require_admin')
    def test_update_report_missing_status(self, mock_require_admin, api_factory):
        """Should return error when status is missing."""
        mock_require_admin.return_value = None
        
        request = api_factory.patch(
            '/api/admin/reports/report-123/',
            {},
            format='json',
            HTTP_AUTHORIZATION='Bearer token'
        )
        response = update_report(request, 'report-123')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['error']['code'] == 'INVALID_INPUT'
    
    @patch('src.interfaces.rest.admin_views.require_admin')
    def test_update_report_invalid_status(self, mock_require_admin, api_factory):
        """Should return error for invalid status."""
        mock_require_admin.return_value = None
        
        request = api_factory.patch(
            '/api/admin/reports/report-123/',
            {'status': 'invalid_status'},
            format='json',
            HTTP_AUTHORIZATION='Bearer token'
        )
        response = update_report(request, 'report-123')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST


# ==================== User Management Endpoint Tests ====================

class TestUserManagementEndpoints:
    """Tests for user management endpoints."""
    
    @patch('src.interfaces.rest.admin_views.require_admin')
    @patch('src.interfaces.rest.admin_views.get_user_repository')
    @patch('src.interfaces.rest.admin_views.ListUsersUseCase')
    def test_list_users_success(self, mock_use_case_class, mock_get_repo,
                                 mock_require_admin, api_factory, sample_user):
        """Should list users with pagination."""
        mock_require_admin.return_value = None
        
        mock_result = Mock()
        mock_result.success = True
        mock_result.users = [sample_user]
        mock_result.total_count = 1
        mock_result._user_to_dict = lambda u: {
            'id': u.id,
            'email': u.email,
            'is_active': u.is_active,
            'roles': u.roles
        }
        
        mock_use_case = Mock()
        mock_use_case.execute.return_value = mock_result
        mock_use_case_class.return_value = mock_use_case
        
        request = api_factory.get('/api/admin/users/',
                                   HTTP_AUTHORIZATION='Bearer token')
        response = list_users(request)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert len(response.data['data']['users']) == 1
    
    @patch('src.interfaces.rest.admin_views.require_admin')
    @patch('src.interfaces.rest.admin_views.get_user_repository')
    @patch('src.interfaces.rest.admin_views.ListUsersUseCase')
    def test_list_users_with_filters(self, mock_use_case_class, mock_get_repo,
                                      mock_require_admin, api_factory, sample_user):
        """Should pass filters to use case."""
        mock_require_admin.return_value = None
        
        mock_result = Mock()
        mock_result.success = True
        mock_result.users = [sample_user]
        mock_result.total_count = 1
        mock_result._user_to_dict = lambda u: {'id': u.id}
        
        mock_use_case = Mock()
        mock_use_case.execute.return_value = mock_result
        mock_use_case_class.return_value = mock_use_case
        
        request = api_factory.get(
            '/api/admin/users/?search=test&role=admin&is_active=true&is_verified=false',
            HTTP_AUTHORIZATION='Bearer token'
        )
        response = list_users(request)
        
        assert response.status_code == status.HTTP_200_OK
        call_args = mock_use_case.execute.call_args.kwargs
        assert call_args['search'] == 'test'
        assert call_args['role'] == 'admin'
        assert call_args['is_active'] is True
        assert call_args['is_verified'] is False
    
    @patch('src.interfaces.rest.admin_views.require_admin')
    @patch('src.interfaces.rest.admin_views.get_user_repository')
    @patch('src.interfaces.rest.admin_views.GetUserDetailsUseCase')
    def test_get_user_success(self, mock_use_case_class, mock_get_repo,
                               mock_require_admin, api_factory, sample_user):
        """Should get single user details."""
        mock_require_admin.return_value = None
        
        mock_result = Mock()
        mock_result.success = True
        mock_result.to_dict.return_value = {
            'data': {
                'id': sample_user.id,
                'email': sample_user.email,
                'is_active': sample_user.is_active
            }
        }
        
        mock_use_case = Mock()
        mock_use_case.execute.return_value = mock_result
        mock_use_case_class.return_value = mock_use_case
        
        request = api_factory.get('/api/admin/users/user-123/',
                                   HTTP_AUTHORIZATION='Bearer token')
        response = get_user(request, 'user-123')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
    
    @patch('src.interfaces.rest.admin_views.require_admin')
    @patch('src.interfaces.rest.admin_views.get_user_repository')
    @patch('src.interfaces.rest.admin_views.GetUserDetailsUseCase')
    def test_get_user_not_found(self, mock_use_case_class, mock_get_repo,
                                 mock_require_admin, api_factory):
        """Should return 404 when user not found."""
        mock_require_admin.return_value = None
        
        mock_result = Mock()
        mock_result.success = False
        mock_result.error_message = "User not found"
        
        mock_use_case = Mock()
        mock_use_case.execute.return_value = mock_result
        mock_use_case_class.return_value = mock_use_case
        
        request = api_factory.get('/api/admin/users/nonexistent/',
                                   HTTP_AUTHORIZATION='Bearer token')
        response = get_user(request, 'nonexistent')
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    @patch('src.interfaces.rest.admin_views.require_admin')
    @patch('src.interfaces.rest.admin_views.extract_user_from_request')
    @patch('src.interfaces.rest.admin_views.get_user_repository')
    @patch('src.interfaces.rest.admin_views.get_admin_repository')
    @patch('src.interfaces.rest.admin_views.DeleteUserUseCase')
    def test_delete_user_success(self, mock_use_case_class, mock_get_admin_repo,
                                  mock_get_user_repo, mock_extract,
                                  mock_require_admin, api_factory):
        """Should delete user successfully."""
        mock_require_admin.return_value = None
        mock_extract.return_value = ('admin-123', 'admin@test.com', ['admin'])
        
        mock_result = Mock()
        mock_result.success = True
        mock_result.message = "User soft-deleted successfully"
        
        mock_use_case = Mock()
        mock_use_case.execute.return_value = mock_result
        mock_use_case_class.return_value = mock_use_case
        
        request = api_factory.delete('/api/admin/users/user-123/delete/',
                                      HTTP_AUTHORIZATION='Bearer token')
        response = delete_user(request, 'user-123')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
    
    @patch('src.interfaces.rest.admin_views.require_admin')
    @patch('src.interfaces.rest.admin_views.extract_user_from_request')
    @patch('src.interfaces.rest.admin_views.get_user_repository')
    @patch('src.interfaces.rest.admin_views.get_admin_repository')
    @patch('src.interfaces.rest.admin_views.DeleteUserUseCase')
    def test_delete_user_hard_delete(self, mock_use_case_class, mock_get_admin_repo,
                                      mock_get_user_repo, mock_extract,
                                      mock_require_admin, api_factory):
        """Should support hard delete flag."""
        mock_require_admin.return_value = None
        mock_extract.return_value = ('admin-123', 'admin@test.com', ['admin'])
        
        mock_result = Mock()
        mock_result.success = True
        mock_result.message = "User permanently deleted"
        
        mock_use_case = Mock()
        mock_use_case.execute.return_value = mock_result
        mock_use_case_class.return_value = mock_use_case
        
        request = api_factory.delete('/api/admin/users/user-123/delete/?hard_delete=true',
                                      HTTP_AUTHORIZATION='Bearer token')
        response = delete_user(request, 'user-123')
        
        assert response.status_code == status.HTTP_200_OK
        call_args = mock_use_case.execute.call_args.kwargs
        assert call_args['hard_delete'] is True
    
    @patch('src.interfaces.rest.admin_views.require_admin')
    @patch('src.interfaces.rest.admin_views.extract_user_from_request')
    @patch('src.interfaces.rest.admin_views.get_user_repository')
    @patch('src.interfaces.rest.admin_views.get_admin_repository')
    @patch('src.interfaces.rest.admin_views.BCryptPasswordHasher')
    @patch('src.interfaces.rest.admin_views.AdminResetPasswordUseCase')
    def test_reset_password_success(self, mock_use_case_class, mock_hasher_class,
                                     mock_get_admin_repo, mock_get_user_repo,
                                     mock_extract, mock_require_admin, api_factory):
        """Should reset password successfully."""
        mock_require_admin.return_value = None
        mock_extract.return_value = ('admin-123', 'admin@test.com', ['admin'])
        
        mock_result = Mock()
        mock_result.success = True
        mock_result.message = "Password reset successfully"
        
        mock_use_case = Mock()
        mock_use_case.execute.return_value = mock_result
        mock_use_case_class.return_value = mock_use_case
        
        request = api_factory.post(
            '/api/admin/users/user-123/reset-password/',
            {'new_password': 'NewPassword123!'},
            format='json',
            HTTP_AUTHORIZATION='Bearer token'
        )
        response = reset_user_password(request, 'user-123')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
    
    @patch('src.interfaces.rest.admin_views.require_admin')
    def test_reset_password_missing_password(self, mock_require_admin, api_factory):
        """Should return error when password is missing."""
        mock_require_admin.return_value = None
        
        request = api_factory.post(
            '/api/admin/users/user-123/reset-password/',
            {},
            format='json',
            HTTP_AUTHORIZATION='Bearer token'
        )
        response = reset_user_password(request, 'user-123')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    @patch('src.interfaces.rest.admin_views.require_admin')
    @patch('src.interfaces.rest.admin_views.extract_user_from_request')
    @patch('src.interfaces.rest.admin_views.get_user_repository')
    @patch('src.interfaces.rest.admin_views.get_admin_repository')
    @patch('src.interfaces.rest.admin_views.UpdateUserStatusUseCase')
    def test_update_user_status_success(self, mock_use_case_class, mock_get_admin_repo,
                                         mock_get_user_repo, mock_extract,
                                         mock_require_admin, api_factory):
        """Should update user status successfully."""
        mock_require_admin.return_value = None
        mock_extract.return_value = ('admin-123', 'admin@test.com', ['admin'])
        
        mock_result = Mock()
        mock_result.success = True
        mock_result.message = "User disabled successfully"
        
        mock_use_case = Mock()
        mock_use_case.execute.return_value = mock_result
        mock_use_case_class.return_value = mock_use_case
        
        request = api_factory.patch(
            '/api/admin/users/user-123/status/',
            {'is_active': False},
            format='json',
            HTTP_AUTHORIZATION='Bearer token'
        )
        response = update_user_status(request, 'user-123')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
    
    @patch('src.interfaces.rest.admin_views.require_admin')
    def test_update_user_status_missing_field(self, mock_require_admin, api_factory):
        """Should return error when is_active is missing."""
        mock_require_admin.return_value = None
        
        request = api_factory.patch(
            '/api/admin/users/user-123/status/',
            {},
            format='json',
            HTTP_AUTHORIZATION='Bearer token'
        )
        response = update_user_status(request, 'user-123')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    @patch('src.interfaces.rest.admin_views.require_admin')
    @patch('src.interfaces.rest.admin_views.extract_user_from_request')
    @patch('src.interfaces.rest.admin_views.get_user_repository')
    @patch('src.interfaces.rest.admin_views.get_admin_repository')
    @patch('src.interfaces.rest.admin_views.UpdateUserRolesUseCase')
    def test_update_user_roles_success(self, mock_use_case_class, mock_get_admin_repo,
                                        mock_get_user_repo, mock_extract,
                                        mock_require_admin, api_factory):
        """Should update user roles successfully."""
        mock_require_admin.return_value = None
        mock_extract.return_value = ('admin-123', 'admin@test.com', ['admin'])
        
        mock_result = Mock()
        mock_result.success = True
        mock_result.message = "Roles updated successfully"
        
        mock_use_case = Mock()
        mock_use_case.execute.return_value = mock_result
        mock_use_case_class.return_value = mock_use_case
        
        request = api_factory.patch(
            '/api/admin/users/user-123/roles/',
            {'roles': ['user', 'moderator']},
            format='json',
            HTTP_AUTHORIZATION='Bearer token'
        )
        response = update_user_roles(request, 'user-123')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
    
    @patch('src.interfaces.rest.admin_views.require_admin')
    def test_update_user_roles_missing_roles(self, mock_require_admin, api_factory):
        """Should return error when roles is missing."""
        mock_require_admin.return_value = None
        
        request = api_factory.patch(
            '/api/admin/users/user-123/roles/',
            {},
            format='json',
            HTTP_AUTHORIZATION='Bearer token'
        )
        response = update_user_roles(request, 'user-123')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    @patch('src.interfaces.rest.admin_views.require_admin')
    def test_update_user_roles_invalid_roles(self, mock_require_admin, api_factory):
        """Should return error when roles is not a list."""
        mock_require_admin.return_value = None
        
        request = api_factory.patch(
            '/api/admin/users/user-123/roles/',
            {'roles': 'admin'},  # String instead of list
            format='json',
            HTTP_AUTHORIZATION='Bearer token'
        )
        response = update_user_roles(request, 'user-123')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST


# ==================== Authentication Edge Cases ====================

class TestAuthenticationEdgeCases:
    """Tests for authentication edge cases across all endpoints."""
    
    @pytest.mark.parametrize("view_func", [
        model_health, model_health_summary, analysis_stats, top_scam_categories,
        user_stats, list_reports, list_users
    ])
    @patch('src.interfaces.rest.admin_views.require_admin')
    def test_all_get_endpoints_require_auth(self, mock_require_admin, api_factory, view_func):
        """All GET endpoints should require authentication."""
        from rest_framework.response import Response as DRFResponse
        mock_require_admin.return_value = DRFResponse(
            data={'error': {'code': 'AUTHENTICATION_REQUIRED'}},
            status=401
        )
        
        request = api_factory.get('/test/')
        response = view_func(request)
        
        assert response.status_code == 401
    
    @patch('src.interfaces.rest.admin_views.require_admin')
    @patch('src.interfaces.rest.admin_views.extract_user_from_request')
    def test_moderator_cannot_access_admin_endpoints(self, mock_extract,
                                                       mock_require_admin, api_factory):
        """Moderator should not access admin-only endpoints."""
        from rest_framework.response import Response as DRFResponse
        mock_require_admin.return_value = DRFResponse(
            data={'error': {'code': 'PERMISSION_DENIED'}},
            status=403
        )
        
        request = api_factory.get('/api/admin/model-health/',
                                   HTTP_AUTHORIZATION='Bearer token')
        response = model_health(request)
        
        assert response.status_code == 403


# ==================== Error Handling Tests ====================

class TestErrorHandling:
    """Tests for error handling scenarios."""
    
    @patch('src.interfaces.rest.admin_views.require_admin')
    @patch('src.interfaces.rest.admin_views.get_metrics_collector')
    def test_internal_error_handling(self, mock_get_collector, mock_require_admin, api_factory):
        """Should handle internal errors gracefully."""
        mock_require_admin.return_value = None
        mock_get_collector.side_effect = Exception("Database connection failed")
        
        request = api_factory.get('/api/admin/model-health/',
                                   HTTP_AUTHORIZATION='Bearer token')
        response = model_health(request)
        
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response.data['error']['code'] == 'INTERNAL_ERROR'
    
    @patch('src.interfaces.rest.admin_views.require_admin')
    @patch('src.interfaces.rest.admin_views.get_admin_repository')
    def test_repository_error_handling(self, mock_get_repo, mock_require_admin, api_factory):
        """Should handle repository errors gracefully."""
        mock_require_admin.return_value = None
        mock_get_repo.side_effect = Exception("MongoDB unavailable")
        
        request = api_factory.get('/api/admin/analysis-stats/',
                                   HTTP_AUTHORIZATION='Bearer token')
        response = analysis_stats(request)
        
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


# ==================== Rate Limiting Tests ====================

class TestRateLimiting:
    """Tests that rate limiting decorator is applied."""
    
    def test_model_health_has_rate_limit(self):
        """Model health endpoint should have rate limit decorator."""
        # Check if the view has rate limiting applied
        assert hasattr(model_health, '__wrapped__') or 'rate_limit' in str(model_health)
    
    def test_analysis_stats_has_rate_limit(self):
        """Analysis stats endpoint should have rate limit decorator."""
        assert hasattr(analysis_stats, '__wrapped__') or 'rate_limit' in str(analysis_stats)


# ==================== Response Format Tests ====================

class TestResponseFormat:
    """Tests for consistent response formatting."""
    
    @patch('src.interfaces.rest.admin_views.require_admin')
    @patch('src.interfaces.rest.admin_views.get_metrics_collector')
    @patch('src.interfaces.rest.admin_views.GetModelHealthUseCase')
    def test_success_response_format(self, mock_use_case_class, mock_get_collector,
                                      mock_require_admin, api_factory,
                                      sample_model_health_metrics):
        """Success responses should have consistent format."""
        mock_require_admin.return_value = None
        
        mock_result = Mock()
        mock_result.success = True
        mock_result.metrics = sample_model_health_metrics
        
        mock_use_case = Mock()
        mock_use_case.execute.return_value = mock_result
        mock_use_case_class.return_value = mock_use_case
        
        request = api_factory.get('/api/admin/model-health/',
                                   HTTP_AUTHORIZATION='Bearer token')
        response = model_health(request)
        
        assert 'success' in response.data
        assert 'data' in response.data
        assert response.data['success'] is True
    
    @patch('src.interfaces.rest.admin_views.require_admin')
    def test_error_response_format(self, mock_require_admin, api_factory):
        """Error responses should have consistent format."""
        mock_require_admin.return_value = None
        
        request = api_factory.get('/api/admin/analysis-stats/top-categories/?limit=invalid',
                                   HTTP_AUTHORIZATION='Bearer token')
        response = top_scam_categories(request)
        
        assert 'success' in response.data
        assert 'error' in response.data
        assert 'code' in response.data['error']
        assert 'message' in response.data['error']
        assert response.data['success'] is False
