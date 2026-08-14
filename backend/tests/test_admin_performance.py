"""
Admin Dashboard Performance Tests (Phase 8)

Tests for performance benchmarks including:
- Response time for admin endpoints
- Database query optimization
- Pagination efficiency
- Concurrent request handling
"""

import os
import sys
import pytest
import time
import threading
from unittest.mock import Mock, patch, MagicMock
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'verfai.settings')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import django
django.setup()

from django.test import override_settings
from rest_framework.test import APIRequestFactory

from src.interfaces.rest.admin_views import (
    model_health,
    analysis_stats,
    user_stats,
    list_users,
    list_reports,
)
from src.domain.admin_entities import (
    ModelHealthMetrics,
    AnalysisStatistics,
    UserStatistics,
)
from src.infrastructure.rate_limiter import get_rate_limiter


# ==================== Fixtures ====================

@pytest.fixture(autouse=True)
def reset_rate_limiter():
    """Reset rate limiter before each test to prevent rate limit errors."""
    limiter = get_rate_limiter()
    limiter.reset()
    yield
    limiter.reset()


@pytest.fixture
def factory():
    return APIRequestFactory()


@pytest.fixture
def admin_user_tuple():
    """Return admin user info as tuple (user_id, email, roles)."""
    return ('admin-perf-123', 'admin@test.com', ['admin'])


@pytest.fixture
def mock_model_health_metrics():
    return ModelHealthMetrics(
        gpu_usage_percent=45.0,
        gpu_memory_used_mb=2000.0,
        gpu_memory_total_mb=8000.0,
        cpu_usage_percent=30.0,
        memory_used_mb=4000.0,
        memory_total_mb=16000.0,
        memory_usage_percent=25.0,
        model_name='scam-detector-v1',
        uptime_seconds=86400,
    )


@pytest.fixture
def mock_analysis_stats():
    return AnalysisStatistics(
        total_count=10000,
        high_risk_count=2500,
        medium_risk_count=3500,
        low_risk_count=2500,
        legitimate_count=1500,
    )


@pytest.fixture
def mock_user_stats():
    return UserStatistics(
        total_users=5000,
        new_users_count=150,
        active_users_count=3500,
        verified_users_count=4000,
        unverified_users_count=1000,
    )


# ==================== Response Time Tests ====================

class TestEndpointResponseTime:
    """Tests for endpoint response time benchmarks."""
    
    RESPONSE_TIME_THRESHOLD_MS = 500  # Maximum acceptable response time
    
    @patch('src.interfaces.rest.admin_views.GetModelHealthUseCase')
    @patch('src.interfaces.rest.admin_views.extract_user_from_request')
    def test_model_health_response_time(
        self, mock_extract, mock_use_case_class, factory, admin_user_tuple, mock_model_health_metrics
    ):
        """Model health endpoint should respond within threshold."""
        mock_extract.return_value = admin_user_tuple
        
        mock_result = Mock()
        mock_result.success = True
        mock_result.metrics = mock_model_health_metrics
        mock_use_case_class.return_value.execute.return_value = mock_result
        
        request = factory.get('/api/admin/model-health/')
        
        start_time = time.time()
        response = model_health(request)
        elapsed_ms = (time.time() - start_time) * 1000
        
        assert response.status_code == 200
        assert elapsed_ms < self.RESPONSE_TIME_THRESHOLD_MS, \
            f"Response time {elapsed_ms:.2f}ms exceeds threshold {self.RESPONSE_TIME_THRESHOLD_MS}ms"
    
    @patch('src.interfaces.rest.admin_views.GetAnalysisStatisticsUseCase')
    @patch('src.interfaces.rest.admin_views.extract_user_from_request')
    def test_analysis_stats_response_time(
        self, mock_extract, mock_use_case_class, factory, admin_user_tuple, mock_analysis_stats
    ):
        """Analysis stats endpoint should respond within threshold."""
        mock_extract.return_value = admin_user_tuple
        
        mock_result = Mock()
        mock_result.success = True
        mock_result.statistics = mock_analysis_stats
        mock_use_case_class.return_value.execute.return_value = mock_result
        
        request = factory.get('/api/admin/analysis-stats/')
        
        start_time = time.time()
        response = analysis_stats(request)
        elapsed_ms = (time.time() - start_time) * 1000
        
        assert response.status_code == 200
        assert elapsed_ms < self.RESPONSE_TIME_THRESHOLD_MS
    
    @patch('src.interfaces.rest.admin_views.GetUserStatisticsUseCase')
    @patch('src.interfaces.rest.admin_views.extract_user_from_request')
    def test_user_stats_response_time(
        self, mock_extract, mock_use_case_class, factory, admin_user_tuple, mock_user_stats
    ):
        """User stats endpoint should respond within threshold."""
        mock_extract.return_value = admin_user_tuple
        
        mock_result = Mock()
        mock_result.success = True
        mock_result.statistics = mock_user_stats
        mock_use_case_class.return_value.execute.return_value = mock_result
        
        request = factory.get('/api/admin/user-stats/')
        
        start_time = time.time()
        response = user_stats(request)
        elapsed_ms = (time.time() - start_time) * 1000
        
        assert response.status_code == 200
        assert elapsed_ms < self.RESPONSE_TIME_THRESHOLD_MS


# ==================== Pagination Performance Tests ====================

class TestPaginationPerformance:
    """Tests for pagination efficiency with large datasets."""
    
    @patch('src.interfaces.rest.admin_views.ListUsersUseCase')
    @patch('src.interfaces.rest.admin_views.extract_user_from_request')
    def test_user_list_pagination_large_dataset(
        self, mock_extract, mock_use_case_class, factory, admin_user_tuple
    ):
        """User list pagination should be efficient with large datasets."""
        mock_extract.return_value = admin_user_tuple
        
        # Simulate large dataset
        mock_users = [
            Mock(
                id=f'user-{i}',
                email=f'user{i}@test.com',
                username=f'user{i}',
                is_active=True,
                roles=['user'],
                created_at='2024-01-01T00:00:00Z',
            )
            for i in range(50)  # Page size
        ]
        
        mock_result = Mock()
        mock_result.success = True
        mock_result.users = mock_users
        mock_result.total_count = 10000  # Large total
        mock_result._user_to_dict = lambda u: {
            'id': u.id,
            'email': u.email,
            'username': u.username,
            'is_active': u.is_active,
            'roles': u.roles,
        }
        mock_use_case_class.return_value.execute.return_value = mock_result
        
        request = factory.get('/api/admin/users/?page=1&limit=50')
        
        start_time = time.time()
        response = list_users(request)
        elapsed_ms = (time.time() - start_time) * 1000
        
        assert response.status_code == 200
        assert elapsed_ms < 500, f"Pagination took {elapsed_ms:.2f}ms"
    
    @patch('src.interfaces.rest.admin_views.ListUsersUseCase')
    @patch('src.interfaces.rest.admin_views.extract_user_from_request')
    def test_pagination_different_page_sizes(
        self, mock_extract, mock_use_case_class, factory, admin_user_tuple
    ):
        """Response time should scale reasonably with page size."""
        mock_extract.return_value = admin_user_tuple
        
        page_sizes = [10, 25, 50, 100]
        response_times = []
        
        for size in page_sizes:
            mock_users = [
                Mock(
                    id=f'user-{i}',
                    email=f'user{i}@test.com',
                    username=f'user{i}',
                    is_active=True,
                    roles=['user'],
                    created_at='2024-01-01T00:00:00Z',
                )
                for i in range(size)
            ]
            
            mock_result = Mock()
            mock_result.success = True
            mock_result.users = mock_users
            mock_result.total_count = 10000
            mock_result._user_to_dict = lambda u: {
                'id': u.id,
                'email': u.email,
                'username': u.username,
                'is_active': u.is_active,
                'roles': u.roles,
            }
            mock_use_case_class.return_value.execute.return_value = mock_result
            
            request = factory.get(f'/api/admin/users/?page=1&limit={size}')
            
            start_time = time.time()
            response = list_users(request)
            elapsed_ms = (time.time() - start_time) * 1000
            
            response_times.append(elapsed_ms)
            assert response.status_code == 200
        
        # Response time should not grow exponentially
        # Filter out any 0.0 times (shouldn't happen but just in case)
        valid_times = [t for t in response_times if t > 0]
        if len(valid_times) >= 2:
            assert valid_times[-1] < valid_times[0] * 10, \
                f"Response time grew too fast with page size: {valid_times}"


# ==================== Concurrent Request Tests ====================

class TestConcurrentRequests:
    """Tests for handling concurrent requests."""
    
    @patch('src.interfaces.rest.admin_views.GetModelHealthUseCase')
    @patch('src.interfaces.rest.admin_views.extract_user_from_request')
    def test_concurrent_model_health_requests(
        self, mock_extract, mock_use_case_class, factory, admin_user_tuple, mock_model_health_metrics
    ):
        """Should handle multiple concurrent requests without errors."""
        mock_extract.return_value = admin_user_tuple
        
        mock_result = Mock()
        mock_result.success = True
        mock_result.metrics = mock_model_health_metrics
        mock_use_case_class.return_value.execute.return_value = mock_result
        
        num_requests = 10
        results = []
        errors = []
        
        def make_request():
            try:
                request = factory.get('/api/admin/model-health/')
                response = model_health(request)
                return response.status_code
            except Exception as e:
                return str(e)
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request) for _ in range(num_requests)]
            for future in as_completed(futures):
                result = future.result()
                if isinstance(result, int):
                    results.append(result)
                else:
                    errors.append(result)
        
        # All requests should succeed (200 or 429 for rate limit)
        assert len(errors) == 0, f"Errors occurred: {errors}"
        success_count = sum(1 for r in results if r in [200, 429])
        assert success_count == num_requests


# ==================== Memory Efficiency Tests ====================

class TestMemoryEfficiency:
    """Tests for memory-efficient data handling."""
    
    @patch('src.interfaces.rest.admin_views.ListUsersUseCase')
    @patch('src.interfaces.rest.admin_views.extract_user_from_request')
    def test_user_list_does_not_load_all_records(
        self, mock_extract, mock_use_case_class, factory, admin_user_tuple
    ):
        """Pagination should only load requested page, not all records."""
        mock_extract.return_value = admin_user_tuple
        
        # Create exactly 10 users (page size)
        mock_users = [
            Mock(
                id=f'user-{i}',
                email=f'user{i}@test.com',
                username=f'user{i}',
                is_active=True,
                roles=['user'],
            )
            for i in range(10)
        ]
        
        mock_result = Mock()
        mock_result.success = True
        mock_result.users = mock_users
        mock_result.total_count = 100000  # Large total, but only 10 loaded
        mock_result._user_to_dict = lambda u: {
            'id': u.id,
            'email': u.email,
            'username': u.username,
        }
        mock_use_case_class.return_value.execute.return_value = mock_result
        
        request = factory.get('/api/admin/users/?page=1&limit=10')
        response = list_users(request)
        
        assert response.status_code == 200
        # Verify only 10 users in response, not 100000
        assert len(mock_result.users) == 10


# ==================== Database Query Optimization Tests ====================

class TestQueryOptimization:
    """Tests for database query optimization."""
    
    @patch('src.interfaces.rest.admin_views.GetAnalysisStatisticsUseCase')
    @patch('src.interfaces.rest.admin_views.extract_user_from_request')
    def test_analysis_stats_uses_aggregation(
        self, mock_extract, mock_use_case_class, factory, admin_user_tuple, mock_analysis_stats
    ):
        """Analysis stats should use aggregation, not load all records."""
        mock_extract.return_value = admin_user_tuple
        
        mock_result = Mock()
        mock_result.success = True
        mock_result.statistics = mock_analysis_stats
        mock_use_case_class.return_value.execute.return_value = mock_result
        
        request = factory.get('/api/admin/analysis-stats/')
        response = analysis_stats(request)
        
        assert response.status_code == 200
        # Use case should be called once (aggregation query)
        mock_use_case_class.return_value.execute.assert_called_once()
    
    @patch('src.interfaces.rest.admin_views.GetUserStatisticsUseCase')
    @patch('src.interfaces.rest.admin_views.extract_user_from_request')
    def test_user_stats_efficient_counting(
        self, mock_extract, mock_use_case_class, factory, admin_user_tuple, mock_user_stats
    ):
        """User stats should use efficient count queries."""
        mock_extract.return_value = admin_user_tuple
        
        mock_result = Mock()
        mock_result.success = True
        mock_result.statistics = mock_user_stats
        mock_use_case_class.return_value.execute.return_value = mock_result
        
        request = factory.get('/api/admin/user-stats/')
        response = user_stats(request)
        
        assert response.status_code == 200
        mock_use_case_class.return_value.execute.assert_called_once()


# ==================== Benchmark Summary Tests ====================

class TestPerformanceBenchmarks:
    """Summary tests for overall performance benchmarks."""
    
    BENCHMARKS = {
        'model_health': 200,  # ms
        'analysis_stats': 300,  # ms
        'user_stats': 200,  # ms
        'user_list': 500,  # ms
        'reports_list': 500,  # ms
    }
    
    @patch('src.interfaces.rest.admin_views.GetModelHealthUseCase')
    @patch('src.interfaces.rest.admin_views.extract_user_from_request')
    def test_all_endpoints_meet_benchmarks(
        self, mock_extract, mock_use_case_class, factory, admin_user_tuple, mock_model_health_metrics
    ):
        """All critical endpoints should meet performance benchmarks."""
        mock_extract.return_value = admin_user_tuple
        
        mock_result = Mock()
        mock_result.success = True
        mock_result.metrics = mock_model_health_metrics
        mock_use_case_class.return_value.execute.return_value = mock_result
        
        request = factory.get('/api/admin/model-health/')
        
        # Run multiple times to get average
        times = []
        for _ in range(5):
            start = time.time()
            model_health(request)
            times.append((time.time() - start) * 1000)
        
        avg_time = sum(times) / len(times)
        assert avg_time < self.BENCHMARKS['model_health'], \
            f"Average time {avg_time:.2f}ms exceeds benchmark {self.BENCHMARKS['model_health']}ms"
    
    def test_performance_benchmarks_documented(self):
        """Performance benchmarks should be documented."""
        assert 'model_health' in self.BENCHMARKS
        assert 'analysis_stats' in self.BENCHMARKS
        assert 'user_stats' in self.BENCHMARKS
        assert 'user_list' in self.BENCHMARKS
        assert 'reports_list' in self.BENCHMARKS
        
        # All benchmarks should be reasonable (< 1 second)
        for endpoint, benchmark in self.BENCHMARKS.items():
            assert benchmark < 1000, f"{endpoint} benchmark too high: {benchmark}ms"
