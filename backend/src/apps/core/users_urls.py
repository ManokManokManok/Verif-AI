from django.urls import path
from src.interfaces.rest import views

urlpatterns = [
    path('profile/', views.profile, name='user_profile'),
    path('check-permission/', views.check_permission, name='check_permission'),
]
