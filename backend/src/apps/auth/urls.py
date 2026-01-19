from django.urls import path
from . import views

app_name = 'auth'

urlpatterns = [
    path('register/', views.signup, name='signup'),
    path('login/', views.login, name='login'),
    path('profile/', views.profile, name='profile'),
    path('check-permission/', views.check_permission, name='check_permission'),
    path('send-verification/', views.send_verification_email, name='send_verification_email'),
    path('verify-email/', views.verify_email, name='verify_email'),
    path('request-reset/', views.request_password_reset, name='request_password_reset'),
    path('reset-password/', views.reset_password, name='reset_password'),
    path('logout/', views.logout, name='logout'),
    path('refresh/', views.refresh_token, name='refresh_token'),
]
