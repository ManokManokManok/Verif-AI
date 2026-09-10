"""
General Chatbot Use Case

Business logic for general scam prevention chatbot.
Uses the configured generative AI provider to provide friendly, professional guidance.
"""

import logging
from typing import Dict, Any, Optional, List

from ...domain.chat_entities import ChatConversation, MessageRole
from ...infrastructure.prompt_sanitizer import PromptSanitizer


logger = logging.getLogger(__name__)


# System prompt for general chatbot
GENERAL_CHATBOT_SYSTEM_PROMPT = """You are Verif-AI, a friendly and professional scam prevention assistant. Your mission is to help people stay safe from scams, phishing, and fraud.

**Your Core Responsibilities:**

1. **Educate & Guide**: Provide clear, actionable advice on recognizing and avoiding scams. Use simple language and be patient.

2. **Be Supportive**: Users may feel anxious or embarrassed about potential scams. Be reassuring and never judgmental.

3. **Direct to Analysis**: If a user mentions a specific suspicious message, email, or text they received, encourage them to use our Analysis feature for detailed detection:
   - Say something like: "I'd be happy to help! For the most accurate analysis, you can paste that message into our Analysis tab. Our AI will examine it in detail and provide specific guidance."
   - Don't try to analyze specific messages yourself - that's what the Analysis feature is for.

4. **General Guidance Only**: Provide general scam prevention tips, common red flags, and safety practices. Examples:
   - Common scam types (phishing, romance scams, tech support scams)
   - Red flags to watch for (urgency, poor grammar, suspicious links)
   - What to do if they suspect a scam
   - How to report scams to authorities

5. **Stay on Topic**: Keep conversations focused on scam prevention and online safety. If users try to chat about unrelated topics, politely redirect them.

**Tone & Style:**
- Friendly but professional
- Clear and concise (avoid jargon)
- Empowering (help users feel capable of protecting themselves)
- Warm and approachable (like a knowledgeable friend)

**Things to Avoid:**
- Don't analyze specific messages yourself
- Don't provide legal or financial advice
- Don't guarantee outcomes
- Don't use fear tactics

Remember: You're here to educate, support, and guide users to the right tools!
"""


class GeneralChatbotUseCase:
    """
    Use case for general chatbot interactions.
    Manages conversation flow and LLM communication.
    """
    
    def __init__(self, llm_model, conversation_repository):
        """
        Initialize the chatbot use case.
        
        Args:
            llm_model: Provider exposing create_chat_completion()
            conversation_repository: ConversationRepository instance
        """
        self.llm = llm_model
        self.conversation_repo = conversation_repository
        self.sanitizer = PromptSanitizer(max_length=4000, log_threats=True)
    
    def send_message(
        self, 
        user_id: str, 
        message: str,
        conversation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process user message and generate response.
        
        Args:
            user_id: User's MongoDB ID
            message: User's message text
            conversation_id: Optional specific conversation ID (creates new if not provided)
            
        Returns:
            Dictionary with:
                - response: Assistant's reply
                - conversation_id: MongoDB ID of conversation
                - title: Conversation title
                - message_count: Total messages in conversation
                - is_new_conversation: True if a new conversation was created
        """
        logger.info(f"[CHATBOT] User {user_id} sent message: {message[:100]}...")
        
        # Sanitize user input to prevent prompt injection
        sanitized = self.sanitizer.sanitize(message, context="chatbot")
        safe_message = sanitized.sanitized_text
        
        if sanitized.threats_detected:
            logger.warning(
                f"[CHATBOT] Prompt injection attempt by user {user_id}: {sanitized.threats_detected}"
            )
        
        is_new_conversation = False
        
        # Get existing conversation or create new one
        if conversation_id:
            conversation = self.conversation_repo.get_by_id_for_user(conversation_id, user_id)
            if not conversation:
                # If specified conversation not found, create new one
                conversation = self.conversation_repo.create_conversation(user_id)
                is_new_conversation = True
        else:
            # No conversation_id provided - create a new conversation
            conversation = self.conversation_repo.create_conversation(user_id)
            is_new_conversation = True
        
        # Add user's SANITIZED message to conversation
        conversation.add_message(MessageRole.USER.value, safe_message)
        
        # Build messages for LLM (system prompt + conversation history)
        llm_messages = [
            {"role": "system", "content": GENERAL_CHATBOT_SYSTEM_PROMPT}
        ] + conversation.get_message_history_for_llm()
        
        try:
            # Generate response from the configured provider.
            response = self.llm.create_chat_completion(
                messages=llm_messages,
                max_tokens=500,
                temperature=0.7,
                stop=["<|im_start|>", "<|end|>", "<end>"]
            )
            
            assistant_reply = response["choices"][0]["message"]["content"].strip()
            
            # Clean up any stop tokens that might have leaked through
            for token in ["<|im_start|>", "<|end|>", "<end>", "end|", "<|end", "<end|"]:
                assistant_reply = assistant_reply.replace(token, "").strip()
            
            # Fallback if response is empty or too short
            if not assistant_reply or len(assistant_reply) < 10:
                assistant_reply = (
                    "I'm here to help you stay safe from scams! "
                    "Feel free to ask me about common scam types, red flags to watch for, "
                    "or what to do if you suspect you've encountered a scam."
                )
            
            logger.info(f"[CHATBOT] Generated response: {assistant_reply[:100]}...")
            
        except Exception as e:
            logger.error(f"[CHATBOT] Error generating response: {str(e)}", exc_info=True)
            assistant_reply = (
                "I apologize, but I'm having trouble processing your message right now. "
                "Please try again in a moment. If you have a suspicious message to analyze, "
                "please use our Analysis feature for the most accurate results."
            )
        
        # Add assistant's reply to conversation
        conversation.add_message(MessageRole.ASSISTANT.value, assistant_reply)
        
        # Save conversation
        self.conversation_repo.save(conversation)
        
        return {
            "response": assistant_reply,
            "conversation_id": conversation.id,
            "title": conversation.title,
            "message_count": len(conversation.messages),
            "is_new_conversation": is_new_conversation
        }
    
    def get_conversation_history(
        self, 
        user_id: str, 
        conversation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get a specific conversation's history.
        
        Args:
            user_id: User's MongoDB ID
            conversation_id: Specific conversation ID (returns latest if not provided)
            
        Returns:
            Dictionary with conversation details and messages
        """
        if conversation_id:
            conversation = self.conversation_repo.get_by_id_for_user(conversation_id, user_id)
        else:
            conversation = self.conversation_repo.get_latest_conversation(user_id)
        
        if not conversation:
            return {
                "conversation_id": None,
                "title": None,
                "messages": [],
                "created_at": None,
                "updated_at": None
            }
        
        return {
            "conversation_id": conversation.id,
            "title": conversation.title,
            "messages": [
                {
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat() if msg.timestamp else None
                }
                for msg in conversation.messages
                if msg.role != MessageRole.SYSTEM.value  # Don't show system prompts to users
            ],
            "created_at": conversation.created_at.isoformat() if conversation.created_at else None,
            "updated_at": conversation.updated_at.isoformat() if conversation.updated_at else None
        }
    
    def get_user_conversations(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get list of all conversations for a user.
        
        Args:
            user_id: User's MongoDB ID
            limit: Maximum number of conversations to return
            
        Returns:
            List of conversation summaries (id, title, message_count, dates)
        """
        conversations = self.conversation_repo.get_user_conversations(user_id, limit)
        
        return [
            conversation.to_summary_dict()
            for conversation in conversations
        ]
    
    def delete_conversation(self, user_id: str, conversation_id: str) -> bool:
        """
        Delete a specific conversation.
        
        Args:
            user_id: User's MongoDB ID
            conversation_id: Conversation ID to delete
            
        Returns:
            True if deleted successfully
        """
        return self.conversation_repo.delete_conversation(conversation_id, user_id)
    
    def clear_conversation(self, user_id: str) -> bool:
        """
        Clear user's most recent general conversation (delete it).
        
        Args:
            user_id: User's MongoDB ID
            
        Returns:
            True if cleared successfully
        """
        conversation = self.conversation_repo.get_latest_conversation(user_id)
        
        if conversation and conversation.id:
            return self.conversation_repo.delete_conversation(
                conversation.id, 
                user_id
            )
        
        return False
