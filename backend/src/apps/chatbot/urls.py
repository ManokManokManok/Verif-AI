from django.urls import path
from . import views

urlpatterns = [
    path('message/', views.send_message, name='chatbot_send_message'),
    path('history/', views.get_history, name='chatbot_get_history'),
    path('history/', views.clear_history, name='chatbot_clear_history'),  # DELETE method
]
