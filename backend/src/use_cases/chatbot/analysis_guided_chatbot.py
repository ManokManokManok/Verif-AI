"""
Analysis Guided Chatbot Use Case

Business logic for analysis-guided scam prevention chatbot.
Uses Gemma LLM to provide specific guidance based on analysis results.
"""

import logging
from typing import Dict, Any, Optional

from ...domain.chat_entities import ChatConversation, MessageRole, ConversationType
from ...domain.analysis_entities import AnalysisResult


logger = logging.getLogger(__name__)


# System prompt for analysis-guided chatbot
ANALYSIS_GUIDED_SYSTEM_PROMPT = """You are Verif-AI, a specialized scam analysis advisor. A user has just received their analysis results and needs your guidance on what to do next.

**Your Core Responsibilities:**

1. **Interpret the Analysis**: Help users understand what the analysis results mean:
   - Explain the verdict (scam vs. legitimate)
   - Break down the confidence scores in plain language
   - Clarify the scam type if detected
   - Explain what the key linguistic markers indicate

2. **Provide Actionable Next Steps**: Based on the analysis results, give clear, specific recommendations:
   
   **If it's a SCAM:**
   - DO NOT respond to the message
   - DO NOT click any links or download attachments
   - DO NOT share personal information
   - Report it to relevant authorities (FTC, FBI IC3, local police)
   - Block the sender
   - Warn others if it came through a platform
   - If you've already engaged: specific steps to protect yourself (change passwords, contact bank, etc.)
   
   **If it's LEGITIMATE:**
   - Explain why it appears safe
   - Still recommend basic verification (check sender address, hover over links)
   - Suggest confirming through official channels if high-stakes
   - Remind them to stay vigilant

3. **Answer Follow-up Questions**: Users may ask:
   - "What exactly is [scam type]?"
   - "How did they get my information?"
   - "What happens if I already clicked the link?"
   - "Should I report this?"
   - "How can I verify this myself?"
   
   Provide clear, helpful answers specific to their situation.

4. **Be Reassuring BUT Realistic**:
   - Don't minimize real threats
   - Don't create unnecessary panic
   - Acknowledge their concerns
   - Empower them with knowledge and clear actions

5. **Reference the Analysis**: Throughout the conversation, you'll have access to the full analysis context. Use it to give specific, tailored advice based on:
   - The exact scam type detected
   - The confidence level
   - The specific markers found
   - The message content

**Tone & Style:**
- Expert but approachable
- Clear and direct (users need actionable info)
- Calm and reassuring
- Patient with follow-up questions
- Specific to their situation (not generic advice)

**Context Awareness:**
You will be provided with the complete analysis results including:
- The analyzed message
- Scam/legitimate verdict
- Confidence scores
- Scam type classification
- Key linguistic markers
- Summary of findings

Use this context to provide personalized, relevant guidance.

**What to Avoid:**
- Generic advice that ignores their specific results
- Overly technical jargon
- Guarantees (no detection is 100% perfect)
- Legal or financial advice beyond basic safety
- Dismissing user concerns

Remember: This user came here with a specific concern. Help them understand their results and know exactly what to do next!
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
            llm_model: Loaded Gemma LLM (llama_cpp.Llama instance)
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
        if not analysis:
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
        if not analysis:
            raise ValueError(f"Analysis {conversation.analysis_ref_id} not found")
        
        # Add user message to conversation
        conversation.add_message(MessageRole.USER.value, message)
        
        # Build context with analysis information
        analysis_context = self._format_analysis_for_llm(analysis)
        
        # Build message history for LLM
        message_history = conversation.get_message_history_for_llm()
        
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
                max_tokens=1024,
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
            if analysis:
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
            context_parts.append(f"\nSummary: {analysis.summary}")
        
        if analysis.key_markers:
            context_parts.append("\nKey Linguistic Markers Detected:")
            for marker in analysis.key_markers:
                context_parts.append(f"  • {marker}")
        
        if analysis.message:
            context_parts.append(f"\nOriginal Message:\n{'-' * 40}")
            context_parts.append(analysis.message)
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
            "key_markers": analysis.key_markers,
            "message": analysis.message
        }
