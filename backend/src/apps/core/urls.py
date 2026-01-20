from django.urls import path
from . import views

urlpatterns = [
    path('health/', views.health, name='health'),
    path('models/status/', views.models_status, name='models_status'),
    path('detect/', views.detect_scam, name='detect_scam'),
]
