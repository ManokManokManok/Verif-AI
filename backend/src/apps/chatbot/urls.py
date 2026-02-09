from django.urls import path
from . import views

urlpatterns = [
    # Send message to chatbot (creates new or continues existing conversation)
    path('message/', views.send_message, name='chatbot_send_message'),
    
    # Get/clear current conversation history
    path('history/', views.get_history, name='chatbot_get_history'),  # GET - get history
    path('history/', views.clear_history, name='chatbot_clear_history'),  # DELETE - clear latest conversation
    
    # Conversation management (for logged in users)
    path('conversations/', views.get_conversations, name='chatbot_get_conversations'),  # GET - list all conversations
    path('conversations/<str:conversation_id>/', views.delete_conversation, name='chatbot_delete_conversation'),  # DELETE - delete specific conversation
]
