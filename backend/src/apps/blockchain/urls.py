"""
Blockchain API URL Configuration

URL patterns for blockchain anchoring and verification endpoints.
"""

from django.urls import path
from . import views

app_name = 'blockchain'

urlpatterns = [
    # Public status endpoint
    path('status/', views.blockchain_status, name='status'),
    
    # Analysis list endpoint
    path('analyses/', views.list_analyses, name='list_analyses'),
    
    # Create analysis (for testing)
    path('analyses/create/', views.create_analysis, name='create_analysis'),
    
    # Analysis detail endpoint (must be before anchor/verify to avoid conflicts)
    path('analysis/<str:ref_id>/', views.get_analysis, name='get_analysis'),
    
    # Anchor endpoint (admin only)
    path('analysis/<str:ref_id>/anchor/', views.anchor_analysis, name='anchor'),
    
    # Verify endpoint (authenticated)
    path('analysis/<str:ref_id>/verify/', views.verify_analysis, name='verify'),
]