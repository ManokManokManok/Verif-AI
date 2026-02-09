"""
Analytics URL Configuration

Maps analytics API endpoints to views.
"""

from django.urls import path

from ...interfaces.rest.analytics_views import (
    get_visit_statistics,
    get_page_analytics,
    get_device_breakdown,
    get_visits_time_series,
    get_hourly_pattern,
    get_referrer_stats,
    get_recent_visits,
    get_analytics_summary,
)

app_name = 'analytics'

urlpatterns = [
    # Visit statistics
    path('visits/', get_visit_statistics, name='visit_statistics'),
    
    # Page analytics
    path('pages/', get_page_analytics, name='page_analytics'),
    
    # Device breakdown
    path('devices/', get_device_breakdown, name='device_breakdown'),
    
    # Time series data
    path('time-series/', get_visits_time_series, name='time_series'),
    
    # Hourly traffic pattern
    path('hourly/', get_hourly_pattern, name='hourly_pattern'),
    
    # Referrer statistics
    path('referrers/', get_referrer_stats, name='referrer_stats'),
    
    # Recent visits (live monitoring)
    path('recent/', get_recent_visits, name='recent_visits'),
    
    # Comprehensive summary
    path('summary/', get_analytics_summary, name='analytics_summary'),
]
