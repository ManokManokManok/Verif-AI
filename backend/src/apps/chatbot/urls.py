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
    
    # Analysis-guided chatbot endpoints
    # IMPORTANT: More specific paths MUST come before generic paths with parameters
    path('analysis-guided/message/', views.send_analysis_guided_message, name='chatbot_send_analysis_guided_message'),  # POST - send message in analysis conversation
    path('analysis-guided/history/<str:conversation_id>/', views.get_analysis_guided_history, name='chatbot_get_analysis_guided_history'),  # GET - get analysis conversation history
    path('analysis-guided/<str:analysis_ref_id>/', views.get_analysis_conversation, name='chatbot_get_analysis_conversation'),  # GET - get or create analysis conversation
]
