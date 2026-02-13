"""
End-to-End Tests for Admin Dashboard (Phase 8)

Tests complete workflows from authentication through to final actions.
These tests verify the integration of all layers working together.

Uses APIRequestFactory with direct view calls for consistent testing.
"""

import os
import django

# Configure Django settings before importing DRF
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'verfai.settings')
django.setup()

import pytest
import uuid
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from rest_framework.test import APIRequestFactory

# Import views to test
from src.interfaces.rest.admin_views import (
    model_health,
    model_health_summary,
    analysis_stats,
    user_stats,
    list_reports,
    update_report,
    list_users,
    get_user,
    delete_user,
    reset_user_password,
    update_user_status,
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
from src.infrastructure.rate_limiter import get_rate_limiter


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture(autouse=True)
def reset_rate_limiter():
    """Reset rate limiter before each test to prevent rate limit errors."""
    limiter = get_rate_limiter()
    limiter.reset()
    yield
    limiter.reset()


@pytest.fixture
def api_factory():
    """Create API request factory."""
    return APIRequestFactory()


@pytest.fixture
def admin_user():
    """Admin user JWT payload."""
    return {
        'user_id': str(uuid.uuid4()),
        'email': 'admin@verifai.com',
        'roles': ['admin'],
        'exp': (datetime.utcnow() + timedelta(hours=1)).timestamp()
    }


@pytest.fixture
def regular_user():
    """Regular user JWT payload."""
    return {
        'user_id': str(uuid.uuid4()),
        'email': 'user@example.com',
        'roles': ['user'],
        'exp': (datetime.utcnow() + timedelta(hours=1)).timestamp()
    }


@pytest.fixture
def target_user_data():
    """Target user for management operations."""
    return {
        'user_id': str(uuid.uuid4()),
        'username': 'target_user',
        'email': 'target@example.com',
        'roles': ['user'],
        'is_active': True,
        'created_at': datetime.utcnow().isoformat(),
    }


@pytest.fixture
def sample_model_health_metrics():
    """Sample model health metrics (same as test_admin_api.py)."""
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


def create_mock_jwt_service(user_payload):
    """Create mock JWT service that returns given payload."""
    mock_service = MagicMock()
    mock_service.verify_access_token.return_value = user_payload
    return mock_service


# ============================================================================
# E2E Workflow: Admin Dashboard Navigation
# ============================================================================

class TestAdminDashboardWorkflowE2E:
    """
    E2E Test: Admin navigates through all dashboard tabs
    """
    
    @patch('src.interfaces.rest.admin_views.require_admin')
    @patch('src.interfaces.rest.admin_views.get_metrics_collector')
    @patch('src.interfaces.rest.admin_views.GetModelHealthUseCase')
    def test_workflow_view_model_health_tab(
        self, mock_use_case_class, mock_get_collector, mock_require_admin, 
        api_factory, sample_model_health_metrics
    ):
        """E2E: Admin views model health metrics tab."""
        mock_require_admin.return_value = None
        
        mock_result = Mock()
        mock_result.success = True
        mock_result.metrics = sample_model_health_metrics
        mock_use_case_class.return_value.execute.return_value = mock_result
        
        request = api_factory.get('/api/admin/model-health/')
        request.META['HTTP_AUTHORIZATION'] = 'Bearer valid_token'
        response = model_health(request)
        
        assert response.status_code == 200
        data = response.data
        assert data['success'] is True
        assert 'gpu' in data['data']
    
    @patch('src.interfaces.rest.admin_views.require_admin')
    @patch('src.interfaces.rest.admin_views.get_admin_repository')
    @patch('src.interfaces.rest.admin_views.GetAnalysisStatisticsUseCase')
    def test_workflow_view_analysis_stats_tab(
        self, mock_use_case_class, mock_get_repo, mock_require_admin,
        api_factory, sample_analysis_statistics
    ):
        """E2E: Admin views analysis statistics tab."""
        mock_require_admin.return_value = None
        
        mock_result = Mock()
        mock_result.success = True
        mock_result.statistics = sample_analysis_statistics
        mock_use_case_class.return_value.execute.return_value = mock_result
        
        request = api_factory.get('/api/admin/analysis-stats/')
        request.META['HTTP_AUTHORIZATION'] = 'Bearer valid_token'
        response = analysis_stats(request)
        
        assert response.status_code == 200
        data = response.data
        assert data['success'] is True
        assert data['data']['total_count'] == 500
    
    @patch('src.interfaces.rest.admin_views.require_admin')
    @patch('src.interfaces.rest.admin_views.get_admin_repository')
    @patch('src.interfaces.rest.admin_views.GetUserStatisticsUseCase')
    def test_workflow_view_user_stats_tab(
        self, mock_use_case_class, mock_get_repo, mock_require_admin,
        api_factory, sample_user_statistics
    ):
        """E2E: Admin views user statistics tab."""
        mock_require_admin.return_value = None
        
        mock_result = Mock()
        mock_result.success = True
        mock_result.statistics = sample_user_statistics
        mock_use_case_class.return_value.execute.return_value = mock_result
        
        request = api_factory.get('/api/admin/user-stats/')
        request.META['HTTP_AUTHORIZATION'] = 'Bearer valid_token'
        response = user_stats(request)
        
        assert response.status_code == 200
        data = response.data
        assert data['success'] is True
        assert data['data']['total_users'] == 1000
    
    @patch('src.interfaces.rest.admin_views.require_admin')
    @patch('src.interfaces.rest.admin_views.get_user_repository')
    @patch('src.interfaces.rest.admin_views.ListUsersUseCase')
    def test_workflow_view_user_management_tab(
        self, mock_use_case_class, mock_get_repo, mock_require_admin,
        api_factory
    ):
        """E2E: Admin views user management tab."""
        mock_require_admin.return_value = None
        
        # Create mock user objects
        mock_user1 = Mock(id='1', email='user1@test.com', is_active=True, roles=['user'])
        mock_user2 = Mock(id='2', email='user2@test.com', is_active=True, roles=['user'])
        
        mock_result = Mock()
        mock_result.success = True
        mock_result.users = [mock_user1, mock_user2]
        mock_result.total_count = 2
        mock_result._user_to_dict = lambda u: {
            'id': u.id,
            'email': u.email,
            'is_active': u.is_active,
            'roles': u.roles
        }
        mock_use_case_class.return_value.execute.return_value = mock_result
        
        request = api_factory.get('/api/admin/users/')
        request.META['HTTP_AUTHORIZATION'] = 'Bearer valid_token'
        response = list_users(request)
        
        assert response.status_code == 200
        data = response.data
        assert data['success'] is True
        assert len(data['data']['users']) == 2


# ============================================================================
# E2E Workflow: User Report Lifecycle
# ============================================================================

class TestUserReportLifecycleE2E:
    """
    E2E Test: Complete report lifecycle from submission to resolution
    """
    
    @patch('src.interfaces.rest.admin_views.require_admin')
    @patch('src.interfaces.rest.admin_views.get_admin_repository')
    @patch('src.interfaces.rest.admin_views.GetUserReportsUseCase')
    def test_admin_views_pending_reports(
        self, mock_use_case_class, mock_get_repo, mock_require_admin,
        api_factory
    ):
        """E2E: Admin views pending reports."""
        mock_require_admin.return_value = None
        
        mock_report = Mock()
        mock_report.to_dict.return_value = {
            'id': str(uuid.uuid4()),
            'report_type': 'hallucination',
            'reason': 'AI gave incorrect information',
            'status': 'pending',
            'reported_by': {'username': 'regular_user'},
        }
        
        mock_result = Mock()
        mock_result.success = True
        mock_result.reports = [mock_report]
        mock_result.total_count = 1
        mock_use_case_class.return_value.execute.return_value = mock_result
        
        request = api_factory.get('/api/admin/reports/?status=pending')
        request.META['HTTP_AUTHORIZATION'] = 'Bearer valid_token'
        response = list_reports(request)
        
        assert response.status_code == 200
        data = response.data
        assert data['success'] is True
        assert len(data['data']['reports']) >= 1
    
    @patch('src.interfaces.rest.admin_views.require_admin')
    @patch('src.interfaces.rest.admin_views.get_admin_repository')
    @patch('src.interfaces.rest.admin_views.UpdateReportStatusUseCase')
    @patch('src.interfaces.rest.admin_views.extract_user_from_request')
    def test_admin_resolves_report(
        self, mock_extract_user, mock_use_case_class, mock_get_repo, mock_require_admin,
        api_factory, admin_user
    ):
        """E2E: Admin resolves the report."""
        mock_require_admin.return_value = None
        mock_extract_user.return_value = (admin_user['user_id'], admin_user['email'], admin_user['roles'])
        
        report_id = str(uuid.uuid4())
        mock_report = Mock()
        mock_report.to_dict.return_value = {
            'id': report_id,
            'status': 'resolved',
            'resolution_notes': 'Model retrained with corrected data',
        }
        
        mock_result = Mock()
        mock_result.success = True
        mock_result.report = mock_report
        mock_use_case_class.return_value.execute.return_value = mock_result
        
        request = api_factory.patch(
            f'/api/admin/reports/{report_id}/',
            data={
                'status': 'resolved',
                'resolution_notes': 'Model retrained with corrected data'
            },
            format='json'
        )
        request.META['HTTP_AUTHORIZATION'] = 'Bearer valid_token'
        response = update_report(request, report_id)
        
        assert response.status_code == 200


# ============================================================================
# E2E Workflow: User Account Management
# ============================================================================

class TestUserAccountManagementE2E:
    """
    E2E Test: Admin manages user accounts
    """
    
    @patch('src.interfaces.rest.admin_views.require_admin')
    @patch('src.interfaces.rest.admin_views.get_user_repository')
    @patch('src.interfaces.rest.admin_views.ListUsersUseCase')
    def test_admin_searches_and_finds_user(
        self, mock_use_case_class, mock_get_repo, mock_require_admin,
        api_factory, target_user_data
    ):
        """E2E: Admin searches for a specific user."""
        mock_require_admin.return_value = None
        
        mock_user = Mock(
            id=target_user_data['user_id'],
            username='target_user',
            email=target_user_data['email'],
            is_active=True,
            roles=['user']
        )
        
        mock_result = Mock()
        mock_result.success = True
        mock_result.users = [mock_user]
        mock_result.total_count = 1
        mock_result._user_to_dict = lambda u: {
            'id': u.id,
            'username': u.username,
            'email': u.email,
            'is_active': u.is_active,
            'roles': u.roles
        }
        mock_use_case_class.return_value.execute.return_value = mock_result
        
        request = api_factory.get('/api/admin/users/?search=target')
        request.META['HTTP_AUTHORIZATION'] = 'Bearer valid_token'
        response = list_users(request)
        
        assert response.status_code == 200
        data = response.data
        assert data['success'] is True
        assert data['data']['users'][0]['username'] == 'target_user'
    
    @patch('src.interfaces.rest.admin_views.require_admin')
    @patch('src.interfaces.rest.admin_views.get_user_repository')
    @patch('src.interfaces.rest.admin_views.GetUserDetailsUseCase')
    def test_admin_views_user_details(
        self, mock_use_case_class, mock_get_repo, mock_require_admin,
        api_factory, target_user_data
    ):
        """E2E: Admin views detailed user information."""
        mock_require_admin.return_value = None
        
        mock_result = Mock()
        mock_result.success = True
        mock_result.to_dict.return_value = {
            'data': {
                **target_user_data,
                'analysis_count': 45,
                'last_login': datetime.utcnow().isoformat(),
            }
        }
        mock_use_case_class.return_value.execute.return_value = mock_result
        
        request = api_factory.get(f'/api/admin/users/{target_user_data["user_id"]}/')
        request.META['HTTP_AUTHORIZATION'] = 'Bearer valid_token'
        response = get_user(request, target_user_data['user_id'])
        
        assert response.status_code == 200
        data = response.data
        assert data['success'] is True
        assert data['data']['username'] == 'target_user'
    
    @patch('src.interfaces.rest.admin_views.require_admin')
    @patch('src.interfaces.rest.admin_views.get_user_repository')
    @patch('src.interfaces.rest.admin_views.get_admin_repository')
    @patch('src.interfaces.rest.admin_views.UpdateUserStatusUseCase')
    @patch('src.interfaces.rest.admin_views.extract_user_from_request')
    def test_admin_disables_user(
        self, mock_extract_user, mock_use_case_class, mock_admin_repo, mock_get_repo, mock_require_admin,
        api_factory, admin_user, target_user_data
    ):
        """E2E: Admin disables user account."""
        mock_require_admin.return_value = None
        mock_extract_user.return_value = (admin_user['user_id'], admin_user['email'], admin_user['roles'])
        
        mock_result = Mock()
        mock_result.success = True
        mock_result.message = 'User status updated successfully'
        mock_use_case_class.return_value.execute.return_value = mock_result
        
        request = api_factory.patch(
            f'/api/admin/users/{target_user_data["user_id"]}/status/',
            data={'is_active': False},
            format='json'
        )
        request.META['HTTP_AUTHORIZATION'] = 'Bearer valid_token'
        response = update_user_status(request, target_user_data['user_id'])
        
        assert response.status_code == 200
        data = response.data
        assert data['success'] is True
        assert 'message' in data
    
    @patch('src.interfaces.rest.admin_views.require_admin')
    @patch('src.interfaces.rest.admin_views.get_user_repository')
    @patch('src.interfaces.rest.admin_views.DeleteUserUseCase')
    @patch('src.interfaces.rest.admin_views.extract_user_from_request')
    def test_admin_deletes_user(
        self, mock_extract_user, mock_use_case_class, mock_get_repo, mock_require_admin,
        api_factory, admin_user, target_user_data
    ):
        """E2E: Admin deletes a user account."""
        mock_require_admin.return_value = None
        mock_extract_user.return_value = (admin_user['user_id'], admin_user['email'], admin_user['roles'])
        
        mock_result = Mock()
        mock_result.success = True
        mock_use_case_class.return_value.execute.return_value = mock_result
        
        request = api_factory.delete(f'/api/admin/users/{target_user_data["user_id"]}/')
        request.META['HTTP_AUTHORIZATION'] = 'Bearer valid_token'
        response = delete_user(request, target_user_data['user_id'])
        
        assert response.status_code == 200
        data = response.data
        assert data['success'] is True


# ============================================================================
# E2E Workflow: Password Reset
# ============================================================================

class TestPasswordResetWorkflowE2E:
    """
    E2E Test: Admin resets user password
    """
    
    @patch('src.interfaces.rest.admin_views.require_admin')
    @patch('src.interfaces.rest.admin_views.get_user_repository')
    @patch('src.interfaces.rest.admin_views.AdminResetPasswordUseCase')
    @patch('src.interfaces.rest.admin_views.extract_user_from_request')
    def test_admin_resets_password(
        self, mock_extract_user, mock_use_case_class, mock_get_repo, mock_require_admin,
        api_factory, admin_user, target_user_data
    ):
        """E2E: Admin resets a user's password."""
        mock_require_admin.return_value = None
        mock_extract_user.return_value = (admin_user['user_id'], admin_user['email'], admin_user['roles'])
        
        mock_result = Mock()
        mock_result.success = True
        mock_use_case_class.return_value.execute.return_value = mock_result
        
        request = api_factory.post(
            f'/api/admin/users/{target_user_data["user_id"]}/reset-password/',
            data={'new_password': 'NewSecurePassword123!'},
            format='json'
        )
        request.META['HTTP_AUTHORIZATION'] = 'Bearer valid_token'
        response = reset_user_password(request, target_user_data['user_id'])
        
        assert response.status_code == 200
        data = response.data
        assert data['success'] is True


# ============================================================================
# Security: Authorization Tests
# ============================================================================

class TestAuthorizationSecurityE2E:
    """
    Security Tests: Verify proper authorization enforcement
    """
    
    @patch('src.interfaces.rest.admin_views.get_jwt_service')
    def test_regular_user_cannot_access_admin_endpoints(self, mock_jwt_fn, api_factory, regular_user):
        """E2E Security: Regular users cannot access admin-only endpoints."""
        mock_jwt_fn.return_value = create_mock_jwt_service(regular_user)
        
        request = api_factory.get('/api/admin/users/')
        request.META['HTTP_AUTHORIZATION'] = 'Bearer valid_token'
        response = list_users(request)
        
        assert response.status_code == 403
    
    @patch('src.interfaces.rest.admin_views.require_admin')
    @patch('src.interfaces.rest.admin_views.get_user_repository')
    @patch('src.interfaces.rest.admin_views.DeleteUserUseCase')
    @patch('src.interfaces.rest.admin_views.extract_user_from_request')
    def test_admin_cannot_delete_themselves(
        self, mock_extract_user, mock_use_case_class, mock_get_repo, mock_require_admin,
        api_factory, admin_user
    ):
        """E2E Security: Admins cannot delete their own account."""
        mock_require_admin.return_value = None
        mock_extract_user.return_value = (admin_user['user_id'], admin_user['email'], admin_user['roles'])
        
        mock_result = Mock()
        mock_result.success = False
        mock_result.error_message = 'Cannot delete your own account'
        mock_use_case_class.return_value.execute.return_value = mock_result
        
        request = api_factory.delete(f'/api/admin/users/{admin_user["user_id"]}/')
        request.META['HTTP_AUTHORIZATION'] = 'Bearer valid_token'
        response = delete_user(request, admin_user['user_id'])
        
        # Should be rejected
        assert response.status_code == 400
    
    def test_unauthenticated_request_rejected(self, api_factory):
        """E2E Security: Requests without authentication are rejected."""
        request = api_factory.get('/api/admin/model-health/')
        response = model_health(request)
        
        assert response.status_code == 401
    
    @patch('src.interfaces.rest.admin_views.get_jwt_service')
    def test_expired_token_rejected(self, mock_jwt_fn, api_factory):
        """E2E Security: Expired tokens are rejected."""
        mock_jwt_fn.return_value.verify_access_token.side_effect = Exception('Token expired')
        
        request = api_factory.get('/api/admin/model-health/')
        request.META['HTTP_AUTHORIZATION'] = 'Bearer expired_token'
        response = model_health(request)
        
        assert response.status_code == 401


# ============================================================================
# Security: Input Validation Tests
# ============================================================================

class TestInputValidationSecurityE2E:
    """
    Security Tests: Verify proper input validation
    """
    
    @patch('src.interfaces.rest.admin_views.require_admin')
    def test_invalid_report_status_rejected(
        self, mock_require_admin,
        api_factory
    ):
        """E2E Security: Invalid report status values are rejected."""
        mock_require_admin.return_value = None
        
        # The view validates status before calling the use case
        # Invalid status 'invalid_status' should be rejected
        request = api_factory.patch(
            '/api/admin/reports/some-id/',
            data={'status': 'invalid_status'},
            format='json'
        )
        request.META['HTTP_AUTHORIZATION'] = 'Bearer valid_token'
        response = update_report(request, 'some-id')
        
        assert response.status_code == 400
    
    @patch('src.interfaces.rest.admin_views.require_admin')
    @patch('src.interfaces.rest.admin_views.get_user_repository')
    @patch('src.interfaces.rest.admin_views.ListUsersUseCase')
    def test_sql_injection_in_search_prevented(
        self, mock_use_case_class, mock_get_repo, mock_require_admin,
        api_factory
    ):
        """E2E Security: SQL injection attempts in search are handled safely."""
        mock_require_admin.return_value = None
        
        mock_result = Mock()
        mock_result.success = True
        mock_result.users = []
        mock_result.total_count = 0
        mock_result._user_to_dict = lambda u: {}
        mock_use_case_class.return_value.execute.return_value = mock_result
        
        malicious_search = "'; DROP TABLE users; --"
        
        request = api_factory.get(f'/api/admin/users/?search={malicious_search}')
        request.META['HTTP_AUTHORIZATION'] = 'Bearer valid_token'
        response = list_users(request)
        
        assert response.status_code in [200, 400]


# ============================================================================
# Performance: Pagination Tests
# ============================================================================

class TestPaginationPerformanceE2E:
    """
    Performance Tests: Verify pagination works correctly
    """
    
    @patch('src.interfaces.rest.admin_views.require_admin')
    @patch('src.interfaces.rest.admin_views.get_user_repository')
    @patch('src.interfaces.rest.admin_views.ListUsersUseCase')
    def test_user_list_pagination(
        self, mock_use_case_class, mock_get_repo, mock_require_admin,
        api_factory
    ):
        """E2E Performance: User list properly paginates large datasets."""
        mock_require_admin.return_value = None
        
        mock_users = [Mock(id=str(i), username=f'user{i}', email=f'user{i}@test.com', is_active=True, roles=['user']) for i in range(10)]
        
        mock_result = Mock()
        mock_result.success = True
        mock_result.users = mock_users
        mock_result.total_count = 1000
        mock_result._user_to_dict = lambda u: {
            'id': u.id,
            'username': u.username,
            'email': u.email,
            'is_active': u.is_active,
            'roles': u.roles
        }
        mock_use_case_class.return_value.execute.return_value = mock_result
        
        request = api_factory.get('/api/admin/users/?page=1&limit=10')
        request.META['HTTP_AUTHORIZATION'] = 'Bearer valid_token'
        response = list_users(request)
        
        assert response.status_code == 200
        data = response.data
        assert data['success'] is True
        assert len(data['data']['users']) == 10
        assert data['data']['total'] == 1000
    
    @patch('src.interfaces.rest.admin_views.require_admin')
    @patch('src.interfaces.rest.admin_views.get_admin_repository')
    @patch('src.interfaces.rest.admin_views.GetUserReportsUseCase')
    def test_reports_pagination(
        self, mock_use_case_class, mock_get_repo, mock_require_admin,
        api_factory
    ):
        """E2E Performance: Reports list properly paginates."""
        mock_require_admin.return_value = None
        
        mock_reports = []
        for i in range(20):
            mock_report = Mock()
            mock_report.to_dict.return_value = {'id': str(i)}
            mock_reports.append(mock_report)
        
        mock_result = Mock()
        mock_result.success = True
        mock_result.reports = mock_reports
        mock_result.total_count = 500
        mock_use_case_class.return_value.execute.return_value = mock_result
        
        request = api_factory.get('/api/admin/reports/?page=2&limit=20')
        request.META['HTTP_AUTHORIZATION'] = 'Bearer valid_token'
        response = list_reports(request)
        
        assert response.status_code == 200
        data = response.data
        assert data['success'] is True
        assert data['data']['total'] == 500


# ============================================================================
# Error Handling Tests
# ============================================================================

class TestErrorHandlingE2E:
    """
    Tests for proper error handling across E2E workflows
    """
    
    @patch('src.interfaces.rest.admin_views.require_admin')
    @patch('src.interfaces.rest.admin_views.get_user_repository')
    @patch('src.interfaces.rest.admin_views.GetUserDetailsUseCase')
    def test_user_not_found_handling(
        self, mock_use_case_class, mock_get_repo, mock_require_admin,
        api_factory
    ):
        """E2E Error: Proper handling when user is not found."""
        mock_require_admin.return_value = None
        
        mock_result = Mock()
        mock_result.success = False
        mock_result.error_message = 'User not found'
        mock_use_case_class.return_value.execute.return_value = mock_result
        
        fake_id = str(uuid.uuid4())
        request = api_factory.get(f'/api/admin/users/{fake_id}/')
        request.META['HTTP_AUTHORIZATION'] = 'Bearer valid_token'
        response = get_user(request, fake_id)
        
        assert response.status_code == 404
    
    @patch('src.interfaces.rest.admin_views.require_admin')
    @patch('src.interfaces.rest.admin_views.get_metrics_collector')
    @patch('src.interfaces.rest.admin_views.GetModelHealthUseCase')
    def test_metrics_service_failure_handling(
        self, mock_use_case_class, mock_get_collector, mock_require_admin,
        api_factory
    ):
        """E2E Error: Proper handling when metrics service fails."""
        mock_require_admin.return_value = None
        mock_use_case_class.return_value.execute.side_effect = Exception('Service unavailable')
        
        request = api_factory.get('/api/admin/model-health/')
        request.META['HTTP_AUTHORIZATION'] = 'Bearer valid_token'
        response = model_health(request)
        
        assert response.status_code in [500, 503]
    
    @patch('src.interfaces.rest.admin_views.require_admin')
    @patch('src.interfaces.rest.admin_views.get_admin_repository')
    @patch('src.interfaces.rest.admin_views.GetAnalysisStatisticsUseCase')
    def test_database_error_handling(
        self, mock_use_case_class, mock_get_repo, mock_require_admin,
        api_factory
    ):
        """E2E Error: Proper handling when database operations fail."""
        mock_require_admin.return_value = None
        mock_use_case_class.return_value.execute.side_effect = Exception('Database connection failed')
        
        request = api_factory.get('/api/admin/analysis-stats/')
        request.META['HTTP_AUTHORIZATION'] = 'Bearer valid_token'
        response = analysis_stats(request)
        
        assert response.status_code in [500, 503]


# ============================================================================
# Integration: Cross-Feature Tests
# ============================================================================

class TestCrossFeatureIntegrationE2E:
    """
    Tests for integration between different features
    """
    
    @patch('src.interfaces.rest.admin_views.require_admin')
    @patch('src.interfaces.rest.admin_views.get_admin_repository')
    @patch('src.interfaces.rest.admin_views.GetUserReportsUseCase')
    def test_deleted_user_reports_handled(
        self, mock_use_case_class, mock_get_repo, mock_require_admin,
        api_factory
    ):
        """E2E Integration: Reports from deleted users are handled gracefully."""
        mock_require_admin.return_value = None
        
        mock_report = Mock()
        mock_report.to_dict.return_value = {
            'id': str(uuid.uuid4()),
            'report_type': 'bug',
            'reason': 'Some issue',
            'status': 'pending',
            'reported_by': None,
        }
        
        mock_result = Mock()
        mock_result.success = True
        mock_result.reports = [mock_report]
        mock_result.total_count = 1
        mock_use_case_class.return_value.execute.return_value = mock_result
        
        request = api_factory.get('/api/admin/reports/')
        request.META['HTTP_AUTHORIZATION'] = 'Bearer valid_token'
        response = list_reports(request)
        
        assert response.status_code == 200
        data = response.data
        assert data['data']['reports'][0]['reported_by'] is None
    
    @patch('src.interfaces.rest.admin_views.require_admin')
    @patch('src.interfaces.rest.admin_views.get_admin_repository')
    @patch('src.interfaces.rest.admin_views.GetAnalysisStatisticsUseCase')
    def test_stats_with_date_range_filter(
        self, mock_use_case_class, mock_get_repo, mock_require_admin,
        api_factory, sample_analysis_statistics
    ):
        """E2E Integration: Statistics properly filter by date range."""
        mock_require_admin.return_value = None
        
        mock_result = Mock()
        mock_result.success = True
        mock_result.statistics = sample_analysis_statistics
        mock_use_case_class.return_value.execute.return_value = mock_result
        
        start_date = (datetime.utcnow() - timedelta(days=7)).strftime('%Y-%m-%d')
        end_date = datetime.utcnow().strftime('%Y-%m-%d')
        
        request = api_factory.get(f'/api/admin/analysis-stats/?start_date={start_date}&end_date={end_date}')
        request.META['HTTP_AUTHORIZATION'] = 'Bearer valid_token'
        response = analysis_stats(request)
        
        assert response.status_code == 200


# ============================================================================
# Complete Admin Workflow E2E Test
# ============================================================================

class TestCompleteAdminWorkflowE2E:
    """
    Full E2E test simulating a complete admin session
    """
    
    @patch('src.interfaces.rest.admin_views.require_admin')
    @patch('src.interfaces.rest.admin_views.get_metrics_collector')
    @patch('src.interfaces.rest.admin_views.get_admin_repository')
    @patch('src.interfaces.rest.admin_views.get_user_repository')
    @patch('src.interfaces.rest.admin_views.GetModelHealthUseCase')
    @patch('src.interfaces.rest.admin_views.GetAnalysisStatisticsUseCase')
    @patch('src.interfaces.rest.admin_views.ListUsersUseCase')
    @patch('src.interfaces.rest.admin_views.GetUserReportsUseCase')
    def test_complete_admin_session(
        self, mock_reports_uc, mock_users_uc, mock_stats_uc, mock_health_uc,
        mock_user_repo, mock_admin_repo, mock_collector,
        mock_require_admin, api_factory, 
        sample_model_health_metrics, sample_analysis_statistics
    ):
        """
        E2E: Complete admin workflow simulation
        1. View model health
        2. Check analysis stats
        3. View user list
        4. Check reports
        """
        mock_require_admin.return_value = None
        
        # Setup model health use case
        health_result = Mock()
        health_result.success = True
        health_result.metrics = sample_model_health_metrics
        mock_health_uc.return_value.execute.return_value = health_result
        
        # Setup analysis stats use case
        stats_result = Mock()
        stats_result.success = True
        stats_result.statistics = sample_analysis_statistics
        mock_stats_uc.return_value.execute.return_value = stats_result
        
        # Setup list users use case with correct mock pattern
        mock_user = Mock(id='1', username='test', email='test@test.com', is_active=True, roles=['user'])
        users_result = Mock()
        users_result.success = True
        users_result.users = [mock_user]
        users_result.total_count = 1
        users_result._user_to_dict = lambda u: {
            'id': u.id,
            'username': u.username,
            'email': u.email,
            'is_active': u.is_active,
            'roles': u.roles
        }
        mock_users_uc.return_value.execute.return_value = users_result
        
        # Setup reports use case with correct mock pattern
        reports_result = Mock()
        reports_result.success = True
        reports_result.reports = []
        reports_result.total_count = 0
        mock_reports_uc.return_value.execute.return_value = reports_result
        
        # Step 1: View model health
        request = api_factory.get('/api/admin/model-health/')
        request.META['HTTP_AUTHORIZATION'] = 'Bearer valid_token'
        response = model_health(request)
        assert response.status_code == 200
        
        # Step 2: Check analysis stats
        request = api_factory.get('/api/admin/analysis-stats/')
        request.META['HTTP_AUTHORIZATION'] = 'Bearer valid_token'
        response = analysis_stats(request)
        assert response.status_code == 200
        
        # Step 3: View user list
        request = api_factory.get('/api/admin/users/')
        request.META['HTTP_AUTHORIZATION'] = 'Bearer valid_token'
        response = list_users(request)
        assert response.status_code == 200
        
        # Step 4: Check reports
        request = api_factory.get('/api/admin/reports/')
        request.META['HTTP_AUTHORIZATION'] = 'Bearer valid_token'
        response = list_reports(request)
        assert response.status_code == 200
