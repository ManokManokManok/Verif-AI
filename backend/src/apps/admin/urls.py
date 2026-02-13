"""
Admin API URL Configuration.

All admin endpoints require authentication with admin role.
"""

from django.urls import path
from . import views

app_name = 'admin'

urlpatterns = [
    # Model Health - Tab 1
    path('model-health/', views.model_health, name='model_health'),
    path('model-health/summary/', views.model_health_summary, name='model_health_summary'),
    
    # Analysis Statistics - Tab 2
    path('analysis-stats/', views.analysis_stats, name='analysis_stats'),
    path('analysis-stats/top-categories/', views.top_scam_categories, name='top_scam_categories'),
    
    # User Statistics - Tab 3
    path('user-stats/', views.user_stats, name='user_stats'),
    path('reports/', views.list_reports, name='list_reports'),
    path('reports/<str:report_id>/', views.update_report, name='update_report'),
    
    # User Management - Tab 4
    path('users/', views.list_users, name='list_users'),
    path('users/<str:user_id>/', views.get_user, name='get_user'),
    path('users/<str:user_id>/delete/', views.delete_user, name='delete_user'),
    path('users/<str:user_id>/reset-password/', views.reset_user_password, name='reset_user_password'),
    path('users/<str:user_id>/status/', views.update_user_status, name='update_user_status'),
    path('users/<str:user_id>/roles/', views.update_user_roles, name='update_user_roles'),
]
