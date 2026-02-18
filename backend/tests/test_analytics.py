"""
Analytics Tests

Unit and integration tests for website analytics middleware and repository.
"""

import os
import sys
import json

# Django setup must happen before imports
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'verfai.settings')

import django
django.setup()

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, patch, PropertyMock
from django.http import HttpRequest, HttpResponse
from django.test import RequestFactory
from rest_framework.test import APIRequestFactory

# Now import the modules to test
from src.infrastructure.middleware.analytics_middleware import (
    VisitData,
    _get_client_ip,
    _anonymize_ip,
    _get_user_agent,
    _is_bot,
    _should_track_path,
    _detect_device_type,
    AnalyticsMiddleware,
)
from src.infrastructure.middleware.analytics_repository import (
    AnalyticsRepository,
    VisitStatistics,
    PageVisitStats,
    DeviceBreakdown,
    TimeSeriesPoint,
)


# ==================== Fixtures ====================

@pytest.fixture
def request_factory():
    """Django request factory."""
    return RequestFactory()


@pytest.fixture
def api_factory():
    """DRF API request factory."""
    return APIRequestFactory()


@pytest.fixture
def mock_mongo_client():
    """Mock MongoDB client."""
    client = MagicMock()
    db = MagicMock()
    client.__getitem__ = Mock(return_value=db)
    
    # Mock collections
    db.website_visits = MagicMock()
    db.analytics_events = MagicMock()
    
    return client


@pytest.fixture
def analytics_repo(mock_mongo_client):
    """Analytics repository with mocked MongoDB."""
    return AnalyticsRepository(mock_mongo_client, 'test_db')


# ==================== VisitData Tests ====================

class TestVisitData:
    """Tests for VisitData class."""
    
    def test_create_visit_data(self):
        """Test creating VisitData object."""
        visit = VisitData(
            path='/api/test',
            method='GET',
            timestamp=datetime.now(),
            anonymous_ip='abc123',
            user_agent='Mozilla/5.0',
            user_id='user123',
            referrer='https://google.com',
            response_status=200,
            response_time_ms=50.5,
            is_authenticated=True,
            device_type='desktop',
            session_id='sess123'
        )
        
        assert visit.path == '/api/test'
        assert visit.method == 'GET'
        assert visit.user_id == 'user123'
        assert visit.is_authenticated == True
        assert visit.device_type == 'desktop'
    
    def test_visit_data_to_dict(self):
        """Test VisitData serialization."""
        timestamp = datetime.now()
        visit = VisitData(
            path='/test',
            method='POST',
            timestamp=timestamp,
            anonymous_ip='xyz789',
            user_agent='Test Agent',
        )
        
        data = visit.to_dict()
        
        assert data['path'] == '/test'
        assert data['method'] == 'POST'
        assert data['timestamp'] == timestamp
        assert data['anonymous_ip'] == 'xyz789'
        assert data['user_agent'] == 'Test Agent'
        assert data['user_id'] is None
    
    def test_visit_data_defaults(self):
        """Test VisitData default values."""
        visit = VisitData(
            path='/',
            method='GET',
            timestamp=datetime.now(),
            anonymous_ip='test',
            user_agent='test'
        )
        
        assert visit.user_id is None
        assert visit.referrer is None
        assert visit.response_status == 200
        assert visit.response_time_ms is None
        assert visit.is_authenticated == False
        assert visit.device_type == 'unknown'


# ==================== Helper Function Tests ====================

class TestHelperFunctions:
    """Tests for analytics helper functions."""
    
    def test_get_client_ip_direct(self, request_factory):
        """Test getting client IP from REMOTE_ADDR."""
        request = request_factory.get('/')
        request.META['REMOTE_ADDR'] = '192.168.1.1'
        
        ip = _get_client_ip(request)
        assert ip == '192.168.1.1'
    
    def test_get_client_ip_forwarded(self, request_factory):
        """Test getting client IP from X-Forwarded-For."""
        request = request_factory.get('/')
        request.META['HTTP_X_FORWARDED_FOR'] = '10.0.0.1, 192.168.1.1'
        
        ip = _get_client_ip(request)
        assert ip == '10.0.0.1'
    
    def test_anonymize_ip(self):
        """Test IP anonymization."""
        ip1 = _anonymize_ip('192.168.1.1')
        ip2 = _anonymize_ip('192.168.1.1')
        ip3 = _anonymize_ip('192.168.1.2')
        
        # Same IP should produce same hash
        assert ip1 == ip2
        # Different IP should produce different hash
        assert ip1 != ip3
        # Hash should be 16 characters
        assert len(ip1) == 16
    
    def test_get_user_agent(self, request_factory):
        """Test getting user agent from request."""
        request = request_factory.get('/')
        request.META['HTTP_USER_AGENT'] = 'Test Browser 1.0'
        
        ua = _get_user_agent(request)
        assert ua == 'Test Browser 1.0'
    
    def test_get_user_agent_truncates_long(self, request_factory):
        """Test that long user agents are truncated."""
        request = request_factory.get('/')
        long_ua = 'A' * 1000
        request.META['HTTP_USER_AGENT'] = long_ua
        
        ua = _get_user_agent(request)
        assert len(ua) <= 500
    
    def test_is_bot_detects_googlebot(self):
        """Test bot detection for Googlebot."""
        ua = 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)'
        assert _is_bot(ua) == True
    
    def test_is_bot_detects_curl(self):
        """Test bot detection for curl."""
        assert _is_bot('curl/7.68.0') == True
    
    def test_is_bot_allows_normal_browser(self):
        """Test that normal browsers are not detected as bots."""
        ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        assert _is_bot(ua) == False
    
    def test_should_track_path_api(self):
        """Test that API paths are tracked."""
        assert _should_track_path('/api/analysis') == True
    
    def test_should_track_path_skip_static(self):
        """Test that static paths are skipped."""
        assert _should_track_path('/static/js/app.js') == False
    
    def test_should_track_path_skip_admin(self):
        """Test that admin API paths are skipped."""
        assert _should_track_path('/api/admin/users') == False
    
    def test_should_track_path_skip_health(self):
        """Test that health check paths are skipped."""
        assert _should_track_path('/api/health') == False
    
    def test_detect_device_type_desktop(self):
        """Test desktop device detection."""
        ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0'
        assert _detect_device_type(ua) == 'desktop'
    
    def test_detect_device_type_mobile(self):
        """Test mobile device detection."""
        ua = 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6) AppleWebKit/605.1'
        assert _detect_device_type(ua) == 'mobile'
    
    def test_detect_device_type_tablet(self):
        """Test tablet device detection."""
        ua = 'Mozilla/5.0 (iPad; CPU OS 14_6) AppleWebKit/605.1'
        assert _detect_device_type(ua) == 'tablet'


# ==================== Analytics Repository Tests ====================

class TestAnalyticsRepository:
    """Tests for AnalyticsRepository."""
    
    def test_track_visit(self, analytics_repo):
        """Test recording a single visit."""
        analytics_repo.visits_collection.insert_one.return_value = Mock(
            inserted_id='visit123'
        )
        
        result = analytics_repo.track_visit({
            'path': '/test',
            'timestamp': datetime.now()
        })
        
        assert result == 'visit123'
        analytics_repo.visits_collection.insert_one.assert_called_once()
    
    def test_bulk_insert_visits(self, analytics_repo):
        """Test bulk inserting visits."""
        analytics_repo.visits_collection.insert_many.return_value = Mock(
            inserted_ids=['v1', 'v2', 'v3']
        )
        
        visits = [
            {'path': '/a', 'timestamp': datetime.now()},
            {'path': '/b', 'timestamp': datetime.now()},
            {'path': '/c', 'timestamp': datetime.now()},
        ]
        
        result = analytics_repo.bulk_insert_visits(visits)
        
        assert result == 3
        analytics_repo.visits_collection.insert_many.assert_called_once()
    
    def test_bulk_insert_empty_list(self, analytics_repo):
        """Test bulk insert with empty list."""
        result = analytics_repo.bulk_insert_visits([])
        assert result == 0
        analytics_repo.visits_collection.insert_many.assert_not_called()
    
    def test_get_visit_count(self, analytics_repo):
        """Test getting visit count."""
        analytics_repo.visits_collection.count_documents.return_value = 42
        
        count = analytics_repo.get_visit_count()
        
        assert count == 42
    
    def test_get_visit_count_with_dates(self, analytics_repo):
        """Test getting visit count with date range."""
        analytics_repo.visits_collection.count_documents.return_value = 10
        
        start = datetime.now() - timedelta(days=7)
        end = datetime.now()
        
        count = analytics_repo.get_visit_count(start, end)
        
        assert count == 10
        # Verify date filter was applied
        call_args = analytics_repo.visits_collection.count_documents.call_args[0][0]
        assert 'timestamp' in call_args
    
    def test_get_unique_visitors(self, analytics_repo):
        """Test getting unique visitor count."""
        analytics_repo.visits_collection.aggregate.return_value = iter([
            {'unique_visitors': 25}
        ])
        
        count = analytics_repo.get_unique_visitors()
        
        assert count == 25
    
    def test_get_unique_visitors_empty(self, analytics_repo):
        """Test getting unique visitors when none exist."""
        analytics_repo.visits_collection.aggregate.return_value = iter([])
        
        count = analytics_repo.get_unique_visitors()
        
        assert count == 0


class TestVisitStatistics:
    """Tests for VisitStatistics dataclass."""
    
    def test_visit_statistics_creation(self):
        """Test creating VisitStatistics."""
        stats = VisitStatistics(
            total_visits=100,
            unique_visitors=50,
            authenticated_visits=30,
            anonymous_visits=70,
            period_start=datetime.now() - timedelta(days=7),
            period_end=datetime.now()
        )
        
        assert stats.total_visits == 100
        assert stats.unique_visitors == 50
        assert stats.authenticated_visits == 30
        assert stats.anonymous_visits == 70
    
    def test_visit_statistics_to_dict(self):
        """Test VisitStatistics serialization."""
        start = datetime(2024, 1, 1)
        end = datetime(2024, 1, 31)
        
        stats = VisitStatistics(
            total_visits=100,
            unique_visitors=50,
            authenticated_visits=30,
            anonymous_visits=70,
            period_start=start,
            period_end=end
        )
        
        data = stats.to_dict()
        
        assert data['total_visits'] == 100
        assert data['unique_visitors'] == 50
        assert data['period_start'] == start.isoformat()
        assert data['period_end'] == end.isoformat()


class TestPageVisitStats:
    """Tests for PageVisitStats dataclass."""
    
    def test_page_stats_creation(self):
        """Test creating PageVisitStats."""
        stats = PageVisitStats(
            path='/api/analysis',
            visit_count=500,
            unique_visitors=200,
            avg_response_time_ms=45.678
        )
        
        assert stats.path == '/api/analysis'
        assert stats.visit_count == 500
    
    def test_page_stats_to_dict(self):
        """Test PageVisitStats serialization."""
        stats = PageVisitStats(
            path='/test',
            visit_count=100,
            unique_visitors=50,
            avg_response_time_ms=123.456789
        )
        
        data = stats.to_dict()
        
        assert data['path'] == '/test'
        assert data['avg_response_time_ms'] == 123.46  # Rounded


class TestDeviceBreakdown:
    """Tests for DeviceBreakdown dataclass."""
    
    def test_device_breakdown_creation(self):
        """Test creating DeviceBreakdown."""
        breakdown = DeviceBreakdown(
            desktop=60,
            mobile=30,
            tablet=8,
            unknown=2
        )
        
        assert breakdown.desktop == 60
        assert breakdown.mobile == 30
    
    def test_device_breakdown_to_dict(self):
        """Test DeviceBreakdown serialization with percentages."""
        breakdown = DeviceBreakdown(
            desktop=60,
            mobile=30,
            tablet=10,
            unknown=0
        )
        
        data = breakdown.to_dict()
        
        assert data['desktop'] == 60
        assert data['total'] == 100
        assert data['percentages']['desktop'] == 60.0
        assert data['percentages']['mobile'] == 30.0
        assert data['percentages']['tablet'] == 10.0
    
    def test_device_breakdown_zero_total(self):
        """Test DeviceBreakdown with zero visits."""
        breakdown = DeviceBreakdown(
            desktop=0,
            mobile=0,
            tablet=0,
            unknown=0
        )
        
        data = breakdown.to_dict()
        
        assert data['total'] == 0
        assert data['percentages']['desktop'] == 0


class TestTimeSeriesPoint:
    """Tests for TimeSeriesPoint dataclass."""
    
    def test_time_series_point_creation(self):
        """Test creating TimeSeriesPoint."""
        date = datetime(2024, 1, 15)
        point = TimeSeriesPoint(date=date, count=42)
        
        assert point.date == date
        assert point.count == 42
    
    def test_time_series_point_to_dict(self):
        """Test TimeSeriesPoint serialization."""
        date = datetime(2024, 1, 15, 10, 30, 0)
        point = TimeSeriesPoint(date=date, count=100)
        
        data = point.to_dict()
        
        assert data['date'] == date.isoformat()
        assert data['count'] == 100


# ==================== Analytics Middleware Tests ====================

class TestAnalyticsMiddleware:
    """Tests for AnalyticsMiddleware."""
    
    def test_middleware_passes_through_disabled(self, request_factory):
        """Test middleware passes through when disabled."""
        def mock_response(request):
            return HttpResponse('OK')
        
        with patch.object(AnalyticsMiddleware, '__init__', lambda x, y: None):
            middleware = AnalyticsMiddleware.__new__(AnalyticsMiddleware)
            middleware.get_response = mock_response
            middleware.enabled = False
            
            request = request_factory.get('/api/test')
            response = middleware(request)
            
            assert response.content == b'OK'
    
    def test_middleware_skips_bots(self, request_factory):
        """Test middleware skips bot requests."""
        def mock_response(request):
            return HttpResponse('OK')
        
        with patch.object(AnalyticsMiddleware, '__init__', lambda x, y: None):
            middleware = AnalyticsMiddleware.__new__(AnalyticsMiddleware)
            middleware.get_response = mock_response
            middleware.enabled = True
            
            request = request_factory.get('/api/test')
            request.META['HTTP_USER_AGENT'] = 'Googlebot/2.1'
            
            # Should not track but still return response
            response = middleware(request)
            assert response.content == b'OK'
    
    def test_middleware_skips_static_paths(self, request_factory):
        """Test middleware skips static file paths."""
        def mock_response(request):
            return HttpResponse('OK')
        
        with patch.object(AnalyticsMiddleware, '__init__', lambda x, y: None):
            middleware = AnalyticsMiddleware.__new__(AnalyticsMiddleware)
            middleware.get_response = mock_response
            middleware.enabled = True
            
            request = request_factory.get('/static/js/app.js')
            request.META['HTTP_USER_AGENT'] = 'Mozilla/5.0'
            
            response = middleware(request)
            assert response.content == b'OK'


# ==================== Analytics API Tests ====================

class TestAnalyticsAPI:
    """Tests for Analytics API endpoints."""
    
    def test_visit_statistics_requires_auth(self, api_factory):
        """Test that visit statistics endpoint requires authentication."""
        from src.interfaces.rest.analytics_views import get_visit_statistics
        
        request = api_factory.get('/api/analytics/visits/')
        request.META['HTTP_AUTHORIZATION'] = ''
        
        response = get_visit_statistics(request)
        
        assert response.status_code == 401
    
    def test_visit_statistics_requires_admin(self, api_factory):
        """Test that visit statistics endpoint requires admin role."""
        from src.interfaces.rest.analytics_views import get_visit_statistics
        
        # Mock JWT with non-admin role
        with patch('src.interfaces.rest.analytics_views.get_jwt_service') as mock_get_jwt:
            mock_jwt = Mock()
            mock_jwt.verify_access_token.return_value = {
                'user_id': 'user123',
                'role': 'user'
            }
            mock_get_jwt.return_value = mock_jwt
            
            request = api_factory.get('/api/analytics/visits/')
            request.META['HTTP_AUTHORIZATION'] = 'Bearer valid_token'
            
            response = get_visit_statistics(request)
            
            assert response.status_code == 403
    
    @patch('src.interfaces.rest.analytics_views.get_analytics_repository')
    def test_visit_statistics_success(self, mock_get_repo, api_factory):
        """Test successful visit statistics retrieval."""
        from src.interfaces.rest.analytics_views import get_visit_statistics
        
        # Mock repository
        mock_repo = Mock()
        mock_repo.get_visit_statistics.return_value = VisitStatistics(
            total_visits=100,
            unique_visitors=50,
            authenticated_visits=30,
            anonymous_visits=70
        )
        mock_get_repo.return_value = mock_repo
        
        # Mock JWT with admin role
        with patch('src.interfaces.rest.analytics_views.get_jwt_service') as mock_get_jwt:
            mock_jwt = Mock()
            mock_jwt.verify_access_token.return_value = {
                'user_id': 'admin123',
                'role': 'admin'
            }
            mock_get_jwt.return_value = mock_jwt
            
            request = api_factory.get('/api/analytics/visits/')
            request.META['HTTP_AUTHORIZATION'] = 'Bearer valid_token'
            
            response = get_visit_statistics(request)
            
            assert response.status_code == 200
            data = json.loads(response.content)
            assert data['success'] == True
            assert data['data']['total_visits'] == 100
    
    @patch('src.interfaces.rest.analytics_views.get_analytics_repository')
    def test_page_analytics_success(self, mock_get_repo, api_factory):
        """Test successful page analytics retrieval."""
        from src.interfaces.rest.analytics_views import get_page_analytics
        
        # Mock repository
        mock_repo = Mock()
        mock_repo.get_visits_by_page.return_value = [
            PageVisitStats('/api/analysis', 500, 200, 45.5),
            PageVisitStats('/api/chat', 300, 150, 30.2),
        ]
        mock_get_repo.return_value = mock_repo
        
        with patch('src.interfaces.rest.analytics_views.get_jwt_service') as mock_get_jwt:
            mock_jwt = Mock()
            mock_jwt.verify_access_token.return_value = {
                'user_id': 'admin123',
                'role': 'admin'
            }
            mock_get_jwt.return_value = mock_jwt
            
            request = api_factory.get('/api/analytics/pages/')
            request.META['HTTP_AUTHORIZATION'] = 'Bearer valid_token'
            
            response = get_page_analytics(request)
            
            assert response.status_code == 200
            data = json.loads(response.content)
            assert data['success'] == True
            assert len(data['data']) == 2
    
    @patch('src.interfaces.rest.analytics_views.get_analytics_repository')
    def test_device_breakdown_success(self, mock_get_repo, api_factory):
        """Test successful device breakdown retrieval."""
        from src.interfaces.rest.analytics_views import get_device_breakdown
        
        mock_repo = Mock()
        mock_repo.get_device_breakdown.return_value = DeviceBreakdown(
            desktop=60, mobile=30, tablet=10, unknown=0
        )
        mock_get_repo.return_value = mock_repo
        
        with patch('src.interfaces.rest.analytics_views.get_jwt_service') as mock_get_jwt:
            mock_jwt = Mock()
            mock_jwt.verify_access_token.return_value = {
                'user_id': 'admin123',
                'role': 'admin'
            }
            mock_get_jwt.return_value = mock_jwt
            
            request = api_factory.get('/api/analytics/devices/')
            request.META['HTTP_AUTHORIZATION'] = 'Bearer valid_token'
            
            response = get_device_breakdown(request)
            
            assert response.status_code == 200
            data = json.loads(response.content)
            assert data['success'] == True
            assert data['data']['desktop'] == 60
    
    @patch('src.interfaces.rest.analytics_views.get_analytics_repository')
    def test_analytics_summary_success(self, mock_get_repo, api_factory):
        """Test successful analytics summary retrieval."""
        from src.interfaces.rest.analytics_views import get_analytics_summary
        
        mock_repo = Mock()
        mock_repo.get_visit_statistics.return_value = VisitStatistics(
            total_visits=100, unique_visitors=50,
            authenticated_visits=30, anonymous_visits=70
        )
        mock_repo.get_device_breakdown.return_value = DeviceBreakdown(
            desktop=60, mobile=30, tablet=10, unknown=0
        )
        mock_repo.get_visits_by_page.return_value = [
            PageVisitStats('/api/analysis', 500, 200, 45.5),
        ]
        mock_repo.get_hourly_traffic_pattern.return_value = {i: 0 for i in range(24)}
        mock_get_repo.return_value = mock_repo
        
        with patch('src.interfaces.rest.analytics_views.get_jwt_service') as mock_get_jwt:
            mock_jwt = Mock()
            mock_jwt.verify_access_token.return_value = {
                'user_id': 'admin123',
                'role': 'admin'
            }
            mock_get_jwt.return_value = mock_jwt
            
            request = api_factory.get('/api/analytics/summary/?period=week')
            request.META['HTTP_AUTHORIZATION'] = 'Bearer valid_token'
            
            response = get_analytics_summary(request)
            
            assert response.status_code == 200
            data = json.loads(response.content)
            assert data['success'] == True
            assert 'visits' in data['data']
            assert 'devices' in data['data']
            assert 'top_pages' in data['data']
    
    def test_analytics_service_unavailable(self, api_factory):
        """Test handling when analytics service is unavailable."""
        from src.interfaces.rest.analytics_views import get_visit_statistics
        
        with patch('src.interfaces.rest.analytics_views.get_analytics_repository') as mock_get_repo:
            mock_get_repo.return_value = None
            
            with patch('src.interfaces.rest.analytics_views.get_jwt_service') as mock_get_jwt:
                mock_jwt = Mock()
                mock_jwt.verify_access_token.return_value = {
                    'user_id': 'admin123',
                    'role': 'admin'
                }
                mock_get_jwt.return_value = mock_jwt
                
                request = api_factory.get('/api/analytics/visits/')
                request.META['HTTP_AUTHORIZATION'] = 'Bearer valid_token'
                
                response = get_visit_statistics(request)
                
                assert response.status_code == 503


# ==================== Integration Tests ====================

class TestAnalyticsIntegration:
    """Integration tests for analytics system."""
    
    def test_repository_date_query_builder(self, analytics_repo):
        """Test date query building."""
        start = datetime(2024, 1, 1)
        end = datetime(2024, 1, 31)
        
        query = analytics_repo._build_date_query(start, end)
        
        assert 'timestamp' in query
        assert query['timestamp']['$gte'] == start
        assert query['timestamp']['$lte'] == end
    
    def test_repository_date_query_empty(self, analytics_repo):
        """Test date query with no dates."""
        query = analytics_repo._build_date_query(None, None)
        assert query == {}
    
    def test_cleanup_old_visits(self, analytics_repo):
        """Test cleanup of old visit records."""
        analytics_repo.visits_collection.delete_many.return_value = Mock(
            deleted_count=100
        )
        
        deleted = analytics_repo.cleanup_old_visits(days_to_keep=30)
        
        assert deleted == 100
        analytics_repo.visits_collection.delete_many.assert_called_once()


# ==================== Error Handling Tests ====================

class TestErrorHandling:
    """Tests for error handling in analytics."""
    
    def test_track_custom_event(self, analytics_repo):
        """Test tracking custom events."""
        analytics_repo.events_collection.insert_one.return_value = Mock(
            inserted_id='event123'
        )
        
        result = analytics_repo.track_custom_event(
            event_name='user_signup',
            timestamp=datetime.now(),
            metadata={'source': 'organic'}
        )
        
        assert result == 'event123'
    
    @patch('src.interfaces.rest.analytics_views.get_analytics_repository')
    def test_api_handles_repository_error(self, mock_get_repo, api_factory):
        """Test API handles repository errors gracefully."""
        from src.interfaces.rest.analytics_views import get_visit_statistics
        
        mock_repo = Mock()
        mock_repo.get_visit_statistics.side_effect = Exception("DB Error")
        mock_get_repo.return_value = mock_repo
        
        with patch('src.interfaces.rest.analytics_views.get_jwt_service') as mock_get_jwt:
            mock_jwt = Mock()
            mock_jwt.verify_access_token.return_value = {
                'user_id': 'admin123',
                'role': 'admin'
            }
            mock_get_jwt.return_value = mock_jwt
            
            request = api_factory.get('/api/analytics/visits/')
            request.META['HTTP_AUTHORIZATION'] = 'Bearer valid_token'
            
            response = get_visit_statistics(request)
            
            assert response.status_code == 500
            data = json.loads(response.content)
            assert 'error' in data
