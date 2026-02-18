"""
User Reports URL Configuration.

Public endpoints for users to submit and view their own reports.
"""

from django.urls import path
from src.interfaces.rest import reports_views

app_name = 'reports'

urlpatterns = [
    # Submit a new report (authenticated users)
    path('', reports_views.submit_report, name='submit_report'),
    
    # Get current user's reports (authenticated users)
    path('my/', reports_views.get_my_reports, name='my_reports'),
    
    # Get available report types (public)
    path('types/', reports_views.get_report_types, name='report_types'),
]
