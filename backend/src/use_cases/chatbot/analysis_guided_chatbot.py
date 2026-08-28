"""
Analysis Guided Chatbot Use Case

Business logic for analysis-guided scam prevention chatbot.
Uses the configured generative AI provider to provide specific guidance based on analysis results.
"""

import logging
from typing import Dict, Any, Optional

from ...domain.chat_entities import ChatConversation, MessageRole, ConversationType
from ...domain.analysis_entities import AnalysisResult


logger = logging.getLogger(__name__)


# System prompt for analysis-guided chatbot
ANALYSIS_GUIDED_SYSTEM_PROMPT = ANALYSIS_GUIDED_SYSTEM_PROMPT = """You are Verif-AI, a scam analysis advisor. A user just received their analysis results and needs quick, clear guidance.

**Response Structure (always follow this):**
1. One sentence verdict/confirmation based on the analysis
2. 1-3 specific action items (no more)
3. One closing sentence if needed — otherwise stop

**Rules:**
- Always complete your response fully before stopping — never trail off mid-thought
- Keep responses SHORT and DIRECT — a complete response should be 3-6 sentences total
- Lead with the most important action first
- Use 2-3 bullet points max when listing actions
- Do NOT repeat information already visible in the analysis results
- Do NOT pad with reassurances, summaries, or filler the user didn't ask for
- If asked a follow-up, answer it in 2-4 sentences and stop
- Reference their specific scam type, markers, or scores only when it adds value

**If it's a SCAM:** lead with the single most urgent action, then 2 supporting steps
**If it's LEGITIMATE:** one sentence confirming why, one optional verification tip

You MUST finish every response with a complete sentence. Never end mid-word or mid-thought.
"""


class AnalysisGuidedChatbotUseCase:
    """
    Use case for analysis-guided chatbot interactions.
    Provides specialized guidance based on specific analysis results.
    """
    
    def __init__(self, llm_model, conversation_repository, analysis_repository):
        """
        Initialize the analysis-guided chatbot use case.
        
        Args:
            llm_model: Provider exposing create_chat_completion()
            conversation_repository: ConversationRepository instance
            analysis_repository: AnalysisResultRepository instance
        """
        self.llm = llm_model
        self.conversation_repo = conversation_repository
        self.analysis_repo = analysis_repository
    
    def get_or_create_conversation(
        self,
        user_id: str,
        analysis_ref_id: str
    ) -> Dict[str, Any]:
        """
        Get existing conversation for an analysis or create a new one.
        
        Args:
            user_id: User's MongoDB ID
            analysis_ref_id: UUID of the analysis result
            
        Returns:
            Dictionary with:
                - conversation_id: MongoDB ID of conversation
                - title: Conversation title
                - is_new: True if newly created
                - analysis_context: The analysis result data
        """
        logger.info(f"[GUIDED CHATBOT] Get/create conversation for user {user_id}, analysis {analysis_ref_id}")
        
        # Try to find existing conversation for this analysis
        conversation = self.conversation_repo.get_by_analysis_ref_id(analysis_ref_id, user_id)
        
        # Get the analysis result to include context
        analysis = self.analysis_repo.get_by_ref_id(analysis_ref_id)
        if not analysis or analysis.user_id != user_id:
            raise ValueError(f"Analysis {analysis_ref_id} not found")
        
        is_new = False
        if not conversation:
            # Create new analysis-guided conversation
            title = self._generate_title_from_analysis(analysis)
            conversation = self.conversation_repo.create_analysis_guided_conversation(
                user_id=user_id,
                analysis_ref_id=analysis_ref_id,
                title=title
            )
            is_new = True
            logger.info(f"[GUIDED CHATBOT] Created new conversation {conversation.id}")
        else:
            logger.info(f"[GUIDED CHATBOT] Found existing conversation {conversation.id}")
        
        return {
            "conversation_id": conversation.id,
            "title": conversation.title,
            "is_new": is_new,
            "analysis_context": self._format_analysis_for_context(analysis),
            "messages": [msg.to_dict() for msg in conversation.messages]
        }
    
    def send_message(
        self,
        user_id: str,
        conversation_id: str,
        message: str
    ) -> Dict[str, Any]:
        """
        Process user message in analysis-guided conversation.
        
        Args:
            user_id: User's MongoDB ID
            conversation_id: Conversation MongoDB ID
            message: User's message text
            
        Returns:
            Dictionary with:
                - response: Assistant's reply
                - conversation_id: MongoDB ID of conversation
                - title: Conversation title
                - message_count: Total messages in conversation
        """
        logger.info(f"[GUIDED CHATBOT] User {user_id} sent message in conversation {conversation_id}")
        
        # Get conversation
        conversation = self.conversation_repo.get_by_id_for_user(conversation_id, user_id)
        if not conversation:
            raise ValueError(f"Conversation {conversation_id} not found for user {user_id}")
        
        # Verify it's an analysis-guided conversation
        if conversation.conversation_type != ConversationType.ANALYSIS_GUIDED.value:
            raise ValueError("This conversation is not an analysis-guided conversation")
        
        # Get analysis context
        if not conversation.analysis_ref_id:
            raise ValueError("Conversation has no associated analysis")
        
        analysis = self.analysis_repo.get_by_ref_id(conversation.analysis_ref_id)
        if not analysis or analysis.user_id != user_id:
            raise ValueError(f"Analysis {conversation.analysis_ref_id} not found")
        
        # Add user message to conversation
        conversation.add_message(MessageRole.USER.value, message)
        
        # Build context with analysis information
        analysis_context = self._format_analysis_for_llm(analysis)
        
        # Build message history for LLM
        # Keep the active conversation context bounded as it grows.
        message_history = conversation.get_message_history_for_llm()[-12:]
        
        # Generate response with analysis context
        llm_messages = [
            {"role": "system", "content": f"{ANALYSIS_GUIDED_SYSTEM_PROMPT}\n\n{analysis_context}"},
            *message_history
        ]
        
        logger.info(f"[GUIDED CHATBOT] Generating response with {len(message_history)} history messages")
        
        # Call LLM
        try:
            response = self.llm.create_chat_completion(
                messages=llm_messages,
                temperature=0.7,
                max_tokens=300,
                top_p=0.95
            )
            
            assistant_message = response["choices"][0]["message"]["content"]
            logger.info(f"[GUIDED CHATBOT] Generated response: {assistant_message[:100]}...")
            
        except Exception as e:
            logger.error(f"[GUIDED CHATBOT] LLM error: {e}")
            assistant_message = "I apologize, but I'm having trouble generating a response right now. Please try again."
        
        # Add assistant message to conversation
        conversation.add_message(MessageRole.ASSISTANT.value, assistant_message)
        
        # Save conversation
        self.conversation_repo.save(conversation)
        logger.info(f"[GUIDED CHATBOT] Saved conversation {conversation.id}")
        
        return {
            "response": assistant_message,
            "conversation_id": conversation.id,
            "title": conversation.title,
            "message_count": len(conversation.messages)
        }
    
    def get_conversation_history(
        self,
        user_id: str,
        conversation_id: str
    ) -> Dict[str, Any]:
        """
        Get full conversation history with analysis context.
        
        Args:
            user_id: User's MongoDB ID
            conversation_id: Conversation MongoDB ID
            
        Returns:
            Dictionary with conversation data and analysis context
        """
        conversation = self.conversation_repo.get_by_id_for_user(conversation_id, user_id)
        if not conversation:
            raise ValueError(f"Conversation {conversation_id} not found")
        
        # Get analysis context
        analysis_context = None
        if conversation.analysis_ref_id:
            analysis = self.analysis_repo.get_by_ref_id(conversation.analysis_ref_id)
            if analysis and analysis.user_id == user_id:
                analysis_context = self._format_analysis_for_context(analysis)
        
        return {
            **conversation.to_dict(),
            "analysis_context": analysis_context
        }
    
    def _generate_title_from_analysis(self, analysis: AnalysisResult) -> str:
        """Generate conversation title from analysis result."""
        if analysis.is_scam:
            return f"Guidance: {analysis.scam_type}"
        else:
            return "Guidance: Legitimate Message"
    
    def _format_analysis_for_llm(self, analysis: AnalysisResult) -> str:
        """Format analysis result for LLM system prompt context."""
        context_parts = [
            "=== ANALYSIS RESULTS ===",
            f"Verdict: {'🚨 SCAM DETECTED' if analysis.is_scam else '✅ LEGITIMATE'}",
            f"Confidence: Scam {analysis.scam_score:.1f}% / Legitimate {analysis.legit_score:.1f}%",
        ]
        
        if analysis.is_scam:
            context_parts.append(f"Scam Type: {analysis.scam_type}")
            context_parts.append(f"Type Confidence: {analysis.type_confidence:.1f}%")
        
        if analysis.summary:
            context_parts.append(f"\nSummary: {analysis.summary[:1200]}")

        if analysis.details:
            context_parts.append(f"\nEvidence: {analysis.details[:1600]}")
        
        if analysis.key_markers:
            context_parts.append("\nKey Linguistic Markers Detected:")
            for marker in analysis.key_markers[:5]:
                context_parts.append(f"  • {marker}")
        
        if analysis.message:
            context_parts.append(f"\nOriginal Message:\n{'-' * 40}")
            context_parts.append(analysis.message[:2000])
            context_parts.append('-' * 40)
        
        context_parts.append("\nUse this analysis to provide specific, actionable guidance to the user.")
        
        return "\n".join(context_parts)
    
    def _format_analysis_for_context(self, analysis: AnalysisResult) -> Dict[str, Any]:
        """Format analysis result for API response."""
        return {
            "ref_id": analysis.ref_id,
            "is_scam": analysis.is_scam,
            "scam_score": analysis.scam_score,
            "legit_score": analysis.legit_score,
            "label": analysis.label,
            "scam_type": analysis.scam_type if analysis.is_scam else None,
            "type_confidence": analysis.type_confidence if analysis.is_scam else None,
            "summary": analysis.summary,
            "details": analysis.details,
            "image_attachment": analysis.image_attachment,
            "key_markers": analysis.key_markers,
            "message": analysis.message
        }
