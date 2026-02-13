"""
Chat Domain Entities

Domain entities for chatbot conversations and messages.
These entities are framework-agnostic and contain only business logic.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List
from enum import Enum


class ConversationType(Enum):
    """Types of chat conversations."""
    GENERAL = "general"  # General scam prevention guidance
    ANALYSIS_GUIDED = "analysis_guided"  # Guidance based on specific analysis


class MessageRole(Enum):
    """Role of the message sender."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


@dataclass
class ChatMessage:
    """
    A single message in a chat conversation.
    """
    role: str  # "user" | "assistant" | "system"
    content: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for API response."""
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None
        }


@dataclass
class ChatConversation:
    """
    A chat conversation between user and the assistant.
    
    For GENERAL conversations: Multiple per user, each with its own title
    For ANALYSIS_GUIDED: One per analysis, specific scam guidance
    """
    user_id: str  # MongoDB user ID
    conversation_type: str  # "general" | "analysis_guided"
    messages: List[ChatMessage] = field(default_factory=list)
    
    # Optional fields
    id: Optional[str] = None  # MongoDB ObjectId as string
    title: Optional[str] = None  # Conversation title (auto-generated from first message)
    analysis_ref_id: Optional[str] = None  # UUID of analysis (for guided mode)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    @classmethod
    def create_general(cls, user_id: str, title: Optional[str] = None) -> 'ChatConversation':
        """Create a new general conversation for a user."""
        return cls(
            user_id=user_id,
            conversation_type=ConversationType.GENERAL.value,
            title=title or "New Conversation",
            messages=[],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
    
    @classmethod
    def create_analysis_guided(
        cls, 
        user_id: str, 
        analysis_ref_id: str,
        title: Optional[str] = None
    ) -> 'ChatConversation':
        """Create a new analysis-guided conversation."""
        return cls(
            user_id=user_id,
            conversation_type=ConversationType.ANALYSIS_GUIDED.value,
            title=title or "Analysis Discussion",
            analysis_ref_id=analysis_ref_id,
            messages=[],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
    
    def add_message(self, role: str, content: str) -> None:
        """Add a message to the conversation."""
        message = ChatMessage(
            role=role,
            content=content,
            timestamp=datetime.utcnow()
        )
        self.messages.append(message)
        self.updated_at = datetime.utcnow()
        
        # Auto-generate title from first user message if not set
        if self.title in [None, "New Conversation", "Analysis Discussion"]:
            if role == MessageRole.USER.value and content:
                self.title = self._generate_title_from_message(content)
    
    def _generate_title_from_message(self, message: str) -> str:
        """Generate a short title from the first user message."""
        # Clean and truncate the message for a title
        title = message.strip()
        # Remove line breaks
        title = title.replace('\n', ' ').replace('\r', '')
        # Truncate to 50 characters
        if len(title) > 50:
            title = title[:47] + "..."
        return title if title else "New Conversation"
    
    def get_message_history_for_llm(self) -> List[dict]:
        """
        Get message history formatted for LLM API.
        Excludes system messages from history (system prompt is added separately).
        """
        return [
            {"role": msg.role, "content": msg.content}
            for msg in self.messages
            if msg.role != MessageRole.SYSTEM.value
        ]
    
    def to_dict(self) -> dict:
        """Convert to dictionary for API response."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "conversation_type": self.conversation_type,
            "title": self.title,
            "analysis_ref_id": self.analysis_ref_id,
            "messages": [msg.to_dict() for msg in self.messages],
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
    
    def to_summary_dict(self) -> dict:
        """Convert to a summary dictionary (for listing conversations)."""
        return {
            "id": self.id,
            "title": self.title,
            "conversation_type": self.conversation_type,
            "message_count": len(self.messages),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
