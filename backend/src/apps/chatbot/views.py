"""
Chatbot API Views

REST API endpoints for chatbot interactions.
"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
import logging

from ...use_cases.chatbot import GeneralChatbotUseCase
from ...infrastructure.mongodb.connection import get_mongo_client, get_database_name
from ...infrastructure.mongodb.conversation_repository import ConversationRepository
from ...infrastructure.ai.genai_provider import get_genai_provider
from ...infrastructure.rate_limiter import rate_limit
from ...infrastructure.validators import sanitize_for_logging


logger = logging.getLogger(__name__)
security_logger = logging.getLogger('security')

# In-memory storage for anonymous user conversations (session-based)
# Format: {session_id: [{"role": "user", "content": "..."}, ...]}
_anonymous_conversations = {}


def get_conversation_repository():
    """Get conversation repository instance."""
    client = get_mongo_client()
    db_name = get_database_name()
    return ConversationRepository(client, db_name)


def get_chatbot_use_case():
    """Get general chatbot use case instance."""
    conversation_repo = get_conversation_repository()
    return GeneralChatbotUseCase(get_genai_provider(), conversation_repo)


def _get_session_id(request: Request) -> str:
    """
    Get or create a session ID for anonymous users.
    Uses custom header or creates a simple identifier.
    """
    # Check for custom session header
    session_id = request.headers.get('X-Session-ID')
    
    if not session_id:
        # Fallback: use IP address as session identifier
        # In production, you might want to use Django sessions or cookies
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR', 'unknown')
        session_id = f"anon_{ip}"
    
    return session_id


def _handle_anonymous_chat(request: Request, message: str) -> dict:
    """
    Handle chat for anonymous (non-authenticated) users.
    Uses in-memory storage that doesn't persist.
    """
    from ...use_cases.chatbot.general_chatbot import GENERAL_CHATBOT_SYSTEM_PROMPT
    
    session_id = _get_session_id(request)
    logger.info(f"[CHATBOT] Anonymous session: {session_id}")
    
    # Get or create conversation history for this session
    if session_id not in _anonymous_conversations:
        _anonymous_conversations[session_id] = []
        logger.info(f"[CHATBOT] Created new anonymous conversation for {session_id}")
    
    conversation_history = _anonymous_conversations[session_id]
    
    # Add user message
    conversation_history.append({
        "role": "user",
        "content": message
    })
    
    # Build messages for LLM
    llm_messages = [
        {"role": "system", "content": GENERAL_CHATBOT_SYSTEM_PROMPT}
    ] + conversation_history
    
    # Limit conversation length for anonymous users (prevent memory bloat)
    MAX_ANONYMOUS_MESSAGES = 20
    if len(conversation_history) > MAX_ANONYMOUS_MESSAGES:
        # Keep only recent messages
        conversation_history = conversation_history[-MAX_ANONYMOUS_MESSAGES:]
        _anonymous_conversations[session_id] = conversation_history
        logger.info(f"[CHATBOT] Trimmed anonymous conversation to {MAX_ANONYMOUS_MESSAGES} messages")
    
    try:
        # Generate response through Gemini, with lazy Gemma fallback.
        response = get_genai_provider().create_chat_completion(
            messages=llm_messages,
            max_tokens=500,
            temperature=0.7,
            stop=["<|im_start|>", "<|end|>", "<end>"]
        )
        
        assistant_reply = response["choices"][0]["message"]["content"].strip()
        
        # Clean up stop tokens
        for token in ["<|im_start|>", "<|end|>", "<end>", "end|", "<|end", "<end|"]:
            assistant_reply = assistant_reply.replace(token, "").strip()
        
        # Fallback if empty
        if not assistant_reply or len(assistant_reply) < 10:
            assistant_reply = (
                "I'm here to help you stay safe from scams! "
                "Feel free to ask me about common scam types, red flags to watch for, "
                "or what to do if you suspect you've encountered a scam."
            )
        
        logger.info(f"[CHATBOT] Anonymous response: {assistant_reply[:100]}...")
        
    except Exception as e:
        logger.error(f"[CHATBOT] Error generating anonymous response: {str(e)}", exc_info=True)
        assistant_reply = (
            "I apologize, but I'm having trouble processing your message right now. "
            "Please try again in a moment."
        )
    
    # Add assistant reply to history
    conversation_history.append({
        "role": "assistant",
        "content": assistant_reply
    })
    
    return {
        "response": assistant_reply,
        "message_count": len(conversation_history),
        "session_id": session_id  # Return session_id so client can maintain it
    }


@api_view(['POST'])
@permission_classes([AllowAny])  # Allow both authenticated and anonymous users
@rate_limit('api_write')
def send_message(request: Request) -> Response:
    """
    Send a message to the general chatbot.
    
    POST /api/chat/message
    
    Request body:
    {
        "message": "How do I spot a phishing email?"
    }
    
    Response (Authenticated):
    {
        "response": "Great question! Here are key signs...",
        "conversation_id": "mongodb_id",
        "message_count": 4,
        "is_authenticated": true
    }
    
    Response (Anonymous):
    {
        "response": "Great question! Here are key signs...",
        "message_count": 2,
        "is_authenticated": false,
        "disclaimer": "Thank you for trying out our guidance mode! Since you are not logged in, this conversation will not be saved and may be limited, but still feel free to continue conversing."
    }
    
    Security:
    - Works for both authenticated and anonymous users
    - Rate limited (api_write: 30 requests per minute)
    - Input validation and length limits
    - Anonymous conversations are NOT saved to database
    """
    try:
        # Extract user_id from JWT (optional)
        user_id = None
        is_authenticated = False
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ', 1)[1]
            try:
                from ...infrastructure.jwt_service import JWTService
                import os
                secret_key = os.getenv('JWT_SECRET_KEY')
                jwt_service = JWTService(secret_key, 900, 604800, None)
                payload = jwt_service.verify_access_token(token)
                user_id = payload.get('user_id')
                is_authenticated = True
                logger.info(f"[CHATBOT] Authenticated user: {user_id}")
            except Exception as jwt_error:
                logger.warning(f"[CHATBOT] Invalid/expired token: {jwt_error}")
        
        if not is_authenticated:
            logger.info("[CHATBOT] Anonymous user detected")
        
        # Validate message
        message = request.data.get('message', '').strip()
        
        if not message:
            return Response({
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': 'Message is required',
                    'details': {'message': 'This field is required'}
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if len(message) > 2000:
            return Response({
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': 'Message is too long',
                    'details': {'message': 'Maximum 2000 characters allowed'}
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Log sanitized message
        user_label = user_id if user_id else "anonymous"
        logger.info(f"[CHATBOT] User {user_label} message: {sanitize_for_logging(message, 100)}")
        
        # For anonymous users: Use in-memory conversation (not saved to DB)
        if not is_authenticated:
            result = _handle_anonymous_chat(request, message)
            # Add disclaimer to first message
            if result.get('message_count', 0) <= 2:  # First exchange
                result['disclaimer'] = (
                    "Thank you for trying out our guidance mode! Since you are not logged in, "
                    "this conversation will not be saved and may be limited, but still feel free "
                    "to continue conversing."
                )
            result['is_authenticated'] = False
            return Response(result, status=status.HTTP_200_OK)
        
        # For authenticated users: Save to database
        # Get optional conversation_id to continue existing conversation
        conversation_id = request.data.get('conversation_id')
        
        chatbot = get_chatbot_use_case()
        result = chatbot.send_message(user_id, message, conversation_id)
        result['is_authenticated'] = True
        
        return Response(result, status=status.HTTP_200_OK)
        
    except RuntimeError as e:
        # LLM not loaded
        logger.error(f"[CHATBOT] LLM not available: {str(e)}")
        return Response({
            'error': {
                'code': 'SERVICE_UNAVAILABLE',
                'message': 'Chatbot is currently unavailable. Please try again later.'
            }
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    
    except Exception as e:
        logger.error(f"[CHATBOT] Error processing message: {str(e)}", exc_info=True)
        return Response({
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'An unexpected error occurred'
            }
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
@rate_limit('api_read')
def get_history(request: Request) -> Response:
    """
    Get a specific conversation's history or the most recent one.
    
    GET /api/chat/history?conversation_id=mongodb_id
    
    Query Parameters:
        conversation_id (optional): Specific conversation ID to retrieve
    
    Response (Authenticated):
    {
        "conversation_id": "mongodb_id",
        "title": "How do I spot phishing...",
        "messages": [...],
        "created_at": "2026-02-01T15:00:00Z",
        "updated_at": "2026-02-02T10:30:05Z",
        "is_authenticated": true
    }
    
    Response (Anonymous):
    {
        "messages": [...],
        "is_authenticated": false,
        "note": "Anonymous conversations are not saved"
    }
    
    Security:
    - Works for both authenticated and anonymous users
    - Rate limited (api_read category)
    - Anonymous users get session-based history only
    """
    try:
        # Extract user_id from JWT (optional)
        user_id = None
        is_authenticated = False
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ', 1)[1]
            try:
                from ...infrastructure.jwt_service import JWTService
                import os
                secret_key = os.getenv('JWT_SECRET_KEY')
                jwt_service = JWTService(secret_key, 900, 604800, None)
                payload = jwt_service.verify_access_token(token)
                user_id = payload.get('user_id')
                is_authenticated = True
            except Exception as jwt_error:
                logger.warning(f"[CHATBOT] Invalid/expired token: {jwt_error}")
        
        # For anonymous users: Return session-based history
        if not is_authenticated:
            session_id = _get_session_id(request)
            conversation_history = _anonymous_conversations.get(session_id, [])
            
            return Response({
                'messages': conversation_history,
                'is_authenticated': False,
                'note': 'Anonymous conversations are not saved'
            }, status=status.HTTP_200_OK)
        
        # For authenticated users: Get saved conversation
        conversation_id = request.query_params.get('conversation_id')
        
        chatbot = get_chatbot_use_case()
        history = chatbot.get_conversation_history(user_id, conversation_id)
        history['is_authenticated'] = True
        
        return Response(history, status=status.HTTP_200_OK)
        
    except RuntimeError as e:
        logger.error(f"[CHATBOT] LLM not available: {str(e)}")
        return Response({
            'error': {
                'code': 'SERVICE_UNAVAILABLE',
                'message': 'Chatbot is currently unavailable'
            }
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    
    except Exception as e:
        logger.error(f"[CHATBOT] Error fetching history: {str(e)}", exc_info=True)
        return Response({
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'An unexpected error occurred'
            }
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
@permission_classes([AllowAny])
@rate_limit('api_write')
def clear_history(request: Request) -> Response:
    """
    Clear user's general chatbot conversation (start fresh).
    
    DELETE /api/chat/history
    
    Response:
    {
        "message": "Conversation cleared successfully"
    }
    
    Security:
    - Works for both authenticated and anonymous users
    - Rate limited
    """
    try:
        # Extract user_id from JWT (optional)
        user_id = None
        is_authenticated = False
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ', 1)[1]
            try:
                from ...infrastructure.jwt_service import JWTService
                import os
                secret_key = os.getenv('JWT_SECRET_KEY')
                jwt_service = JWTService(secret_key, 900, 604800, None)
                payload = jwt_service.verify_access_token(token)
                user_id = payload.get('user_id')
                is_authenticated = True
            except Exception as jwt_error:
                logger.warning(f"[CHATBOT] Invalid/expired token: {jwt_error}")
        
        # For anonymous users: Clear session-based history
        if not is_authenticated:
            session_id = _get_session_id(request)
            if session_id in _anonymous_conversations:
                del _anonymous_conversations[session_id]
                logger.info(f"[CHATBOT] Cleared anonymous conversation for {session_id}")
            
            return Response({
                'message': 'Conversation cleared successfully'
            }, status=status.HTTP_200_OK)
        
        # Clear conversation
        chatbot = get_chatbot_use_case()
        success = chatbot.clear_conversation(user_id)
        
        if success:
            return Response({
                'message': 'Conversation cleared successfully'
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'message': 'No conversation to clear'
            }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"[CHATBOT] Error clearing history: {str(e)}", exc_info=True)
        return Response({
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'An unexpected error occurred'
            }
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



def _extract_user_id_from_jwt(request: Request):
    """
    Helper function to extract user_id from JWT token.
    
    Returns:
        tuple: (user_id, is_authenticated) - user_id is None if not authenticated
    """
    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith('Bearer '):
        token = auth_header.split(' ', 1)[1]
        try:
            from ...infrastructure.jwt_service import JWTService
            import os
            secret_key = os.getenv('JWT_SECRET_KEY')
            jwt_service = JWTService(secret_key, 900, 604800, None)
            payload = jwt_service.verify_access_token(token)
            user_id = payload.get('user_id')
            return user_id, True
        except Exception as jwt_error:
            logger.warning(f"[CHATBOT] Invalid/expired token: {jwt_error}")
    return None, False


@api_view(['GET'])
@permission_classes([AllowAny])
@rate_limit('api_read')
def get_conversations(request: Request) -> Response:
    """
    Get list of all conversations for the authenticated user.
    
    GET /api/chat/conversations
    
    Query Parameters:
        limit (optional): Maximum number of conversations to return (default: 50)
    
    Response (Authenticated):
    {
        "conversations": [
            {
                "id": "mongodb_id",
                "title": "How do I spot phishing...",
                "conversation_type": "general",
                "message_count": 4,
                "created_at": "2026-02-01T15:00:00Z",
                "updated_at": "2026-02-02T10:30:05Z"
            },
            ...
        ],
        "total": 5,
        "is_authenticated": true
    }
    
    Response (Anonymous):
    {
        "conversations": [],
        "is_authenticated": false,
        "note": "Login to save and view conversation history"
    }
    """
    try:
        user_id, is_authenticated = _extract_user_id_from_jwt(request)
        
        if not is_authenticated:
            return Response({
                'conversations': [],
                'is_authenticated': False,
                'note': 'Login to save and view conversation history'
            }, status=status.HTTP_200_OK)
        
        limit = int(request.query_params.get('limit', 50))
        limit = min(limit, 100)  # Cap at 100
        
        chatbot = get_chatbot_use_case()
        conversations = chatbot.get_user_conversations(user_id, limit)
        
        return Response({
            'conversations': conversations,
            'total': len(conversations),
            'is_authenticated': True
        }, status=status.HTTP_200_OK)
        
    except RuntimeError as e:
        logger.error(f"[CHATBOT] Service not available: {str(e)}")
        return Response({
            'error': {
                'code': 'SERVICE_UNAVAILABLE',
                'message': 'Service is currently unavailable'
            }
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    
    except Exception as e:
        logger.error(f"[CHATBOT] Error fetching conversations: {str(e)}", exc_info=True)
        return Response({
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'An unexpected error occurred'
            }
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
@permission_classes([AllowAny])
@rate_limit('api_write')
def delete_conversation(request: Request, conversation_id: str) -> Response:
    """
    Delete a specific conversation.
    
    DELETE /api/chat/conversations/<conversation_id>
    
    Response:
    {
        "message": "Conversation deleted successfully"
    }
    
    Security:
    - Requires authentication
    - Only the owner can delete their conversation
    """
    try:
        user_id, is_authenticated = _extract_user_id_from_jwt(request)
        
        if not is_authenticated:
            return Response({
                'error': {
                    'code': 'UNAUTHORIZED',
                    'message': 'Authentication required'
                }
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        chatbot = get_chatbot_use_case()
        success = chatbot.delete_conversation(user_id, conversation_id)
        
        if success:
            logger.info(f"[CHATBOT] User {user_id} deleted conversation {conversation_id}")
            return Response({
                'message': 'Conversation deleted successfully'
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'error': {
                    'code': 'NOT_FOUND',
                    'message': 'Conversation not found or unauthorized'
                }
            }, status=status.HTTP_404_NOT_FOUND)
        
    except Exception as e:
        logger.error(f"[CHATBOT] Error deleting conversation: {str(e)}", exc_info=True)
        return Response({
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'An unexpected error occurred'
            }
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ============================================================
# ANALYSIS-GUIDED CHATBOT ENDPOINTS
# ============================================================

def get_analysis_guided_use_case():
    """Get analysis-guided chatbot use case instance."""
    from ...use_cases.chatbot.analysis_guided_chatbot import AnalysisGuidedChatbotUseCase
    from ...infrastructure.mongodb.analysis_repository import AnalysisResultRepository
    from ...infrastructure.ai.genai_provider import get_genai_provider
    
    client = get_mongo_client()
    db_name = get_database_name()
    conversation_repo = ConversationRepository(client, db_name)
    analysis_repo = AnalysisResultRepository(client, db_name)
    
    return AnalysisGuidedChatbotUseCase(get_genai_provider(), conversation_repo, analysis_repo)


@api_view(['GET'])
@permission_classes([AllowAny])
@rate_limit('api_read')
def get_analysis_conversation(request: Request, analysis_ref_id: str) -> Response:
    """
    Get or create conversation for a specific analysis.
    
    GET /api/chatbot/analysis-guided/<analysis_ref_id>/
    
    Response:
    {
        "conversation_id": "mongodb_id",
        "title": "Guidance: Banking Phishing Scam",
        "is_new": false,
        "analysis_context": {
            "ref_id": "uuid",
            "is_scam": true,
            "scam_type": "Banking Access Payment Scam",
            "scam_score": 95.3,
            ...
        },
        "messages": [...]
    }
    
    Security:
    - Requires authentication
    - Rate limited (api_read: 60 requests per minute)
    """
    try:
        # Extract user_id from JWT
        user_id = None
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ', 1)[1]
            try:
                from ...infrastructure.jwt_service import JWTService
                import os
                secret_key = os.getenv('JWT_SECRET_KEY')
                jwt_service = JWTService(secret_key, 900, 604800, None)
                payload = jwt_service.verify_access_token(token)
                user_id = payload.get('user_id')
            except Exception as jwt_error:
                logger.warning(f"[GUIDED CHATBOT] Invalid/expired token: {jwt_error}")
                return Response({
                    'error': {
                        'code': 'UNAUTHORIZED',
                        'message': 'Authentication required'
                    }
                }, status=status.HTTP_401_UNAUTHORIZED)
        
        if not user_id:
            return Response({
                'error': {
                    'code': 'UNAUTHORIZED',
                    'message': 'Authentication required'
                }
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        logger.info(f"[GUIDED CHATBOT] Getting conversation for analysis {analysis_ref_id}")
        
        chatbot = get_analysis_guided_use_case()
        result = chatbot.get_or_create_conversation(user_id, analysis_ref_id)
        
        return Response(result, status=status.HTTP_200_OK)
        
    except ValueError as e:
        logger.error(f"[GUIDED CHATBOT] Validation error: {str(e)}")
        return Response({
            'error': {
                'code': 'VALIDATION_ERROR',
                'message': str(e)
            }
        }, status=status.HTTP_400_BAD_REQUEST)
    
    except RuntimeError as e:
        logger.error(f"[GUIDED CHATBOT] LLM not available: {str(e)}")
        return Response({
            'error': {
                'code': 'SERVICE_UNAVAILABLE',
                'message': 'Chatbot is currently unavailable. Please try again later.'
            }
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    
    except Exception as e:
        logger.error(f"[GUIDED CHATBOT] Error getting conversation: {str(e)}", exc_info=True)
        return Response({
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'An unexpected error occurred'
            }
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
@rate_limit('api_write')
def send_analysis_guided_message(request: Request) -> Response:
    """
    Send a message in an analysis-guided conversation.
    
    POST /api/chatbot/analysis-guided/message
    
    Request body:
    {
        "conversation_id": "mongodb_id",
        "message": "What should I do next?"
    }
    
    Response:
    {
        "response": "Based on the analysis showing this is a banking scam...",
        "conversation_id": "mongodb_id",
        "title": "Guidance: Banking Phishing Scam",
        "message_count": 4
    }
    
    Security:
    - Requires authentication
    - Rate limited (api_write: 30 requests per minute)
    - Input validation and length limits
    """
    try:
        # Extract user_id from JWT
        user_id = None
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ', 1)[1]
            try:
                from ...infrastructure.jwt_service import JWTService
                import os
                secret_key = os.getenv('JWT_SECRET_KEY')
                jwt_service = JWTService(secret_key, 900, 604800, None)
                payload = jwt_service.verify_access_token(token)
                user_id = payload.get('user_id')
            except Exception as jwt_error:
                logger.warning(f"[GUIDED CHATBOT] Invalid/expired token: {jwt_error}")
                return Response({
                    'error': {
                        'code': 'UNAUTHORIZED',
                        'message': 'Authentication required'
                    }
                }, status=status.HTTP_401_UNAUTHORIZED)
        
        if not user_id:
            return Response({
                'error': {
                    'code': 'UNAUTHORIZED',
                    'message': 'Authentication required'
                }
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        # Validate request data
        conversation_id = request.data.get('conversation_id', '').strip()
        message = request.data.get('message', '').strip()
        
        if not conversation_id:
            return Response({
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': 'Conversation ID is required',
                    'details': {'conversation_id': 'This field is required'}
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not message:
            return Response({
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': 'Message is required',
                    'details': {'message': 'This field is required'}
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if len(message) > 2000:
            return Response({
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': 'Message is too long',
                    'details': {'message': 'Maximum 2000 characters allowed'}
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        logger.info(f"[GUIDED CHATBOT] User {user_id} sending message in conversation {conversation_id}")
        
        chatbot = get_analysis_guided_use_case()
        result = chatbot.send_message(user_id, conversation_id, message)
        
        return Response(result, status=status.HTTP_200_OK)
        
    except ValueError as e:
        logger.error(f"[GUIDED CHATBOT] Validation error: {str(e)}")
        return Response({
            'error': {
                'code': 'VALIDATION_ERROR',
                'message': str(e)
            }
        }, status=status.HTTP_400_BAD_REQUEST)
    
    except RuntimeError as e:
        logger.error(f"[GUIDED CHATBOT] LLM not available: {str(e)}")
        return Response({
            'error': {
                'code': 'SERVICE_UNAVAILABLE',
                'message': 'Chatbot is currently unavailable. Please try again later.'
            }
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    
    except Exception as e:
        logger.error(f"[GUIDED CHATBOT] Error processing message: {str(e)}", exc_info=True)
        return Response({
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'An unexpected error occurred'
            }
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
@rate_limit('api_read')
def get_analysis_guided_history(request: Request, conversation_id: str) -> Response:
    """
    Get full history of an analysis-guided conversation.
    
    GET /api/chatbot/analysis-guided/history/<conversation_id>/
    
    Response:
    {
        "conversation_id": "mongodb_id",
        "title": "Guidance: Banking Phishing Scam",
        "conversation_type": "analysis_guided",
        "analysis_ref_id": "uuid",
        "analysis_context": {...},
        "messages": [...],
        "created_at": "...",
        "updated_at": "..."
    }
    
    Security:
    - Requires authentication
    - Rate limited (api_read: 60 requests per minute)
    """
    try:
        # Extract user_id from JWT
        user_id = None
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ', 1)[1]
            try:
                from ...infrastructure.jwt_service import JWTService
                import os
                secret_key = os.getenv('JWT_SECRET_KEY')
                jwt_service = JWTService(secret_key, 900, 604800, None)
                payload = jwt_service.verify_access_token(token)
                user_id = payload.get('user_id')
            except Exception as jwt_error:
                logger.warning(f"[GUIDED CHATBOT] Invalid/expired token: {jwt_error}")
                return Response({
                    'error': {
                        'code': 'UNAUTHORIZED',
                        'message': 'Authentication required'
                    }
                }, status=status.HTTP_401_UNAUTHORIZED)
        
        if not user_id:
            return Response({
                'error': {
                    'code': 'UNAUTHORIZED',
                    'message': 'Authentication required'
                }
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        logger.info(f"[GUIDED CHATBOT] Getting history for conversation {conversation_id}")
        
        chatbot = get_analysis_guided_use_case()
        result = chatbot.get_conversation_history(user_id, conversation_id)
        
        return Response(result, status=status.HTTP_200_OK)
        
    except ValueError as e:
        logger.error(f"[GUIDED CHATBOT] Validation error: {str(e)}")
        return Response({
            'error': {
                'code': 'NOT_FOUND',
                'message': 'Conversation not found'
            }
        }, status=status.HTTP_404_NOT_FOUND)
    
    except RuntimeError as e:
        logger.error(f"[GUIDED CHATBOT] LLM not available: {str(e)}")
        return Response({
            'error': {
                'code': 'SERVICE_UNAVAILABLE',
                'message': 'Chatbot is currently unavailable. Please try again later.'
            }
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    
    except Exception as e:
        logger.error(f"[GUIDED CHATBOT] Error getting history: {str(e)}", exc_info=True)
        return Response({
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'An unexpected error occurred'
            }
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


