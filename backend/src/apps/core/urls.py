from django.urls import path
from . import views

from src.interfaces.rest.views import (
    history,
    history_detail,
    delete_history,
    delete_history_detail,
    extract_text_from_image,
)

urlpatterns = [
    path('health/', views.health, name='health'),
    path('models/status/', views.models_status, name='models_status'),
    path('detect/', views.detect_scam, name='detect_scam'),
    path('extract-text/', extract_text_from_image, name='extract_text'),
    path('history/', history, name='history'),
    path('history/<str:analysis_id>/', history_detail, name='history_detail'),
    path('history/delete/', delete_history, name='delete_history'),
    path('history/<str:analysis_id>/delete/', delete_history_detail, name='delete_history_detail'),
]
