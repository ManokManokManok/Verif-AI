from django.urls import path
from . import views

from src.interfaces.rest.views import history, history_detail

urlpatterns = [
    path('health/', views.health, name='health'),
    path('models/status/', views.models_status, name='models_status'),
    path('detect/', views.detect_scam, name='detect_scam'),
    path('history/', history, name='history'),
    path('history/<str:analysis_id>/', history_detail, name='history_detail'),
]
