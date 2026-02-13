"""
User Reports API Tests

Tests for the public user reports endpoint.
Run with: python -m pytest tests/test_reports_api.py -v --tb=short
"""

import os
import django

# Configure Django settings before importing anything else
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'verfai.settings')
django.setup()

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from rest_framework.test import APIRequestFactory
from rest_framework import status

from src.interfaces.rest.reports_views import (
    submit_report,
    get_my_reports,
    get_report_types,
    extract_user_from_request,
    require_auth,
)
from src.domain.admin_entities import (
    ReportType,
    ReportStatus,
    UserReport,
)


@pytest.fixture
def api_factory():
    """Create API request factory."""
    return APIRequestFactory()


@pytest.fixture
def user_token_payload():
    """Valid user JWT payload."""
    from datetime import timedelta
    return {
        'user_id': 'user-123',
        'email': 'test@example.com',
        'roles': ['user'],
        'exp': (datetime.utcnow() + timedelta(hours=1)).timestamp()
    }


@pytest.fixture
def sample_report():
    """Sample user report."""
    return UserReport(
        report_id='report-123',
        user_id='user-123',
        user_email='test@example.com',
        report_type=ReportType.BUG,
        title='Bug Report',
        description='This is a detailed bug description.',
        status=ReportStatus.PENDING,
        created_at=datetime.utcnow(),
    )


class TestExtractUserFromRequest:
    """Tests for the extract_user_from_request helper."""

    def test_returns_none_without_auth_header(self, api_factory):
        """Should return None when no Authorization header."""
        request = api_factory.get('/test/')
        
        result = extract_user_from_request(request)
        
        assert result is None

    def test_returns_none_without_bearer_prefix(self, api_factory):
        """Should return None when Authorization doesn't start with Bearer."""
        request = api_factory.get('/test/', HTTP_AUTHORIZATION='Basic some_token')
        
        result = extract_user_from_request(request)
        
        assert result is None

    @patch('src.interfaces.rest.reports_views.JWTService')
    def test_returns_none_for_invalid_token(self, mock_jwt_class, api_factory):
        """Should return None when token is invalid."""
        mock_jwt = Mock()
        mock_jwt.verify_token.return_value = None
        mock_jwt_class.return_value = mock_jwt
        
        request = api_factory.get('/test/', HTTP_AUTHORIZATION='Bearer invalid_token')
        
        result = extract_user_from_request(request)
        
        assert result is None

    @patch('src.interfaces.rest.reports_views.JWTService')
    def test_returns_user_info_for_valid_token(self, mock_jwt_class, api_factory):
        """Should return user info when token is valid."""
        mock_jwt = Mock()
        mock_jwt.verify_token.return_value = {
            'user_id': 'user_123',
            'email': 'test@example.com',
            'roles': ['user'],
        }
        mock_jwt_class.return_value = mock_jwt
        
        request = api_factory.get('/test/', HTTP_AUTHORIZATION='Bearer valid_token')
        
        result = extract_user_from_request(request)
        
        assert result == {
            'user_id': 'user_123',
            'email': 'test@example.com',
            'roles': ['user'],
        }


class TestRequireAuthDecorator:
    """Tests for the require_auth decorator."""

    def test_returns_401_without_auth(self, api_factory):
        """Should return 401 when user is not authenticated."""
        @require_auth
        def my_view(request):
            from django.http import JsonResponse
            return JsonResponse({'success': True})
        
        with patch('src.interfaces.rest.reports_views.extract_user_from_request') as mock_extract:
            mock_extract.return_value = None
            request = api_factory.get('/test/')
            
            response = my_view(request)
            
            assert response.status_code == 401
            data = json.loads(response.content)
            assert data['success'] is False
            assert 'Authentication required' in data['error']

    def test_calls_view_when_authenticated(self, api_factory):
        """Should call the wrapped view when user is authenticated."""
        @require_auth
        def my_view(request):
            from django.http import JsonResponse
            return JsonResponse({'success': True, 'user_id': request.auth_user['user_id']})
        
        with patch('src.interfaces.rest.reports_views.extract_user_from_request') as mock_extract:
            mock_extract.return_value = {'user_id': 'user_123', 'email': 'test@example.com', 'roles': []}
            request = api_factory.get('/test/')
            
            response = my_view(request)
            
            assert response.status_code == 200
            data = json.loads(response.content)
            assert data['success'] is True
            assert data['user_id'] == 'user_123'


class TestGetReportTypes:
    """Tests for the get_report_types endpoint."""

    def test_returns_all_report_types(self, api_factory):
        """Should return all available report types."""
        request = api_factory.get('/api/reports/types/')
        
        response = get_report_types(request)
        
        assert response.status_code == 200
        data = json.loads(response.content)
        assert data['success'] is True
        assert len(data['data']) == 6  # All 6 report types
        
        # Check each type has required fields
        for report_type in data['data']:
            assert 'value' in report_type
            assert 'label' in report_type
            assert 'description' in report_type

    def test_includes_expected_types(self, api_factory):
        """Should include all expected report types."""
        request = api_factory.get('/api/reports/types/')
        
        response = get_report_types(request)
        data = json.loads(response.content)
        
        type_values = [t['value'] for t in data['data']]
        assert 'hallucination' in type_values
        assert 'false_positive' in type_values
        assert 'false_negative' in type_values
        assert 'bug' in type_values
        assert 'feedback' in type_values
        assert 'other' in type_values


class TestSubmitReport:
    """Tests for the submit_report endpoint."""

    @patch('src.interfaces.rest.reports_views.extract_user_from_request')
    def test_rejects_unauthenticated(self, mock_extract, api_factory):
        """Should reject unauthenticated requests."""
        mock_extract.return_value = None
        
        request = api_factory.post(
            '/api/reports/',
            data=json.dumps({
                'report_type': 'bug',
                'title': 'Test Report',
                'description': 'Test description here.',
            }),
            content_type='application/json'
        )
        
        # We can test the auth decorator behavior
        @require_auth
        def mock_submit(r):
            from django.http import JsonResponse
            return JsonResponse({'success': True}, status=201)
        
        response = mock_submit(request)
        
        assert response.status_code == 401


class TestGetMyReports:
    """Tests for the get_my_reports endpoint."""

    @patch('src.interfaces.rest.reports_views.AdminRepository')
    @patch('src.interfaces.rest.reports_views.extract_user_from_request')
    def test_returns_user_reports(self, mock_extract, mock_repo_class, api_factory, sample_report):
        """Should return the authenticated user's reports."""
        mock_extract.return_value = {
            'user_id': 'user-123',
            'email': 'test@example.com',
            'roles': ['user'],
        }
        
        mock_reports = [sample_report]
        
        mock_repo = Mock()
        mock_repo.get_reports.return_value = (mock_reports, 1)
        mock_repo_class.return_value = mock_repo
        
        request = api_factory.get(
            '/api/reports/my/',
            HTTP_AUTHORIZATION='Bearer valid_token'
        )
        
        response = get_my_reports(request)
        
        assert response.status_code == 200
        data = json.loads(response.content)
        assert data['success'] is True
        assert len(data['data']['reports']) == 1
        assert data['data']['total'] == 1
        
        # Verify user_id filter was applied
        mock_repo.get_reports.assert_called_once()
        call_kwargs = mock_repo.get_reports.call_args
        assert call_kwargs[1]['user_id'] == 'user-123'

    @patch('src.interfaces.rest.reports_views.AdminRepository')
    @patch('src.interfaces.rest.reports_views.extract_user_from_request')
    def test_filters_by_status(self, mock_extract, mock_repo_class, api_factory):
        """Should filter reports by status when provided."""
        mock_extract.return_value = {
            'user_id': 'user-123',
            'email': 'test@example.com',
            'roles': ['user'],
        }
        
        mock_repo = Mock()
        mock_repo.get_reports.return_value = ([], 0)
        mock_repo_class.return_value = mock_repo
        
        request = api_factory.get(
            '/api/reports/my/?status=pending',
            HTTP_AUTHORIZATION='Bearer valid_token'
        )
        
        response = get_my_reports(request)
        
        assert response.status_code == 200
        # Verify status filter was applied
        call_kwargs = mock_repo.get_reports.call_args
        assert call_kwargs[1]['status'] == ReportStatus.PENDING

    @patch('src.interfaces.rest.reports_views.AdminRepository')
    @patch('src.interfaces.rest.reports_views.extract_user_from_request')
    def test_pagination(self, mock_extract, mock_repo_class, api_factory):
        """Should handle pagination parameters."""
        mock_extract.return_value = {
            'user_id': 'user-123',
            'email': 'test@example.com',
            'roles': ['user'],
        }
        
        mock_repo = Mock()
        mock_repo.get_reports.return_value = ([], 100)
        mock_repo_class.return_value = mock_repo
        
        request = api_factory.get(
            '/api/reports/my/?page=3&limit=25',
            HTTP_AUTHORIZATION='Bearer valid_token'
        )
        
        response = get_my_reports(request)
        
        assert response.status_code == 200
        data = json.loads(response.content)
        assert data['data']['page'] == 3
        assert data['data']['limit'] == 25
        assert data['data']['total_pages'] == 4  # 100 / 25 = 4

    @patch('src.interfaces.rest.reports_views.extract_user_from_request')
    def test_rejects_unauthenticated(self, mock_extract, api_factory):
        """Should reject unauthenticated requests."""
        mock_extract.return_value = None
        
        request = api_factory.get('/api/reports/my/')
        
        response = get_my_reports(request)
        
        assert response.status_code == 401
        data = json.loads(response.content)
        assert data['success'] is False


class TestReportValidation:
    """Tests for report data validation logic."""

    def test_valid_report_types_returned(self, api_factory):
        """Should have all expected report types returned from endpoint."""
        request = api_factory.get('/api/reports/types/')
        response = get_report_types(request)
        data = json.loads(response.content)
        
        expected_types = ['hallucination', 'false_positive', 'false_negative', 'bug', 'feedback', 'other']
        type_values = [t['value'] for t in data['data']]
        
        for expected in expected_types:
            assert expected in type_values, f"Missing type: {expected}"

    def test_report_type_has_required_fields(self, api_factory):
        """Each report type should have value, label, and description."""
        request = api_factory.get('/api/reports/types/')
        response = get_report_types(request)
        data = json.loads(response.content)
        
        for report_type in data['data']:
            assert 'value' in report_type
            assert 'label' in report_type
            assert 'description' in report_type
            assert len(report_type['value']) > 0
            assert len(report_type['label']) > 0
            assert len(report_type['description']) > 0


class TestIntegration:
    """Integration tests for the reports API flow."""

    @patch('src.interfaces.rest.reports_views.AdminRepository')
    @patch('src.interfaces.rest.reports_views.extract_user_from_request')
    def test_get_types_then_retrieve_reports(self, mock_extract, mock_repo_class, api_factory, sample_report):
        """Should be able to get types and retrieve reports."""
        # First, get report types (public endpoint)
        types_request = api_factory.get('/api/reports/types/')
        types_response = get_report_types(types_request)
        
        assert types_response.status_code == 200
        types_data = json.loads(types_response.content)
        assert len(types_data['data']) > 0
        
        # User authenticates
        mock_extract.return_value = {
            'user_id': 'user-123',
            'email': 'test@example.com',
            'roles': ['user'],
        }
        
        mock_repo = Mock()
        mock_repo.get_reports.return_value = ([sample_report], 1)
        mock_repo_class.return_value = mock_repo
        
        # Get user's reports
        my_reports_request = api_factory.get(
            '/api/reports/my/',
            HTTP_AUTHORIZATION='Bearer valid_token'
        )
        my_reports_response = get_my_reports(my_reports_request)
        
        assert my_reports_response.status_code == 200
        my_reports_data = json.loads(my_reports_response.content)
        assert my_reports_data['success'] is True


class TestErrorHandling:
    """Tests for error handling scenarios."""

    @patch('src.interfaces.rest.reports_views.AdminRepository')
    @patch('src.interfaces.rest.reports_views.extract_user_from_request')
    def test_handles_repository_error(self, mock_extract, mock_repo_class, api_factory):
        """Should handle repository errors gracefully."""
        mock_extract.return_value = {
            'user_id': 'user-123',
            'email': 'test@example.com',
            'roles': ['user'],
        }
        
        mock_repo = Mock()
        mock_repo.get_reports.side_effect = Exception("Database error")
        mock_repo_class.return_value = mock_repo
        
        request = api_factory.get(
            '/api/reports/my/',
            HTTP_AUTHORIZATION='Bearer valid_token'
        )
        
        response = get_my_reports(request)
        
        assert response.status_code == 500
        data = json.loads(response.content)
        assert data['success'] is False

    @patch('src.interfaces.rest.reports_views.JWTService')
    def test_handles_jwt_exception(self, mock_jwt_class, api_factory):
        """Should handle JWT service exceptions."""
        mock_jwt = Mock()
        mock_jwt.verify_token.side_effect = Exception("JWT error")
        mock_jwt_class.return_value = mock_jwt
        
        request = api_factory.get('/test/', HTTP_AUTHORIZATION='Bearer bad_token')
        
        result = extract_user_from_request(request)
        
        # Should return None on exception, not crash
        assert result is None
