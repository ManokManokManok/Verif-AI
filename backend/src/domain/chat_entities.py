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
    
    For GENERAL conversations: One per user, ongoing general guidance
    For ANALYSIS_GUIDED: One per analysis, specific scam guidance
    """
    user_id: str  # MongoDB user ID
    conversation_type: str  # "general" | "analysis_guided"
    messages: List[ChatMessage] = field(default_factory=list)
    
    # Optional fields
    id: Optional[str] = None  # MongoDB ObjectId as string
    analysis_ref_id: Optional[str] = None  # UUID of analysis (for guided mode)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    @classmethod
    def create_general(cls, user_id: str) -> 'ChatConversation':
        """Create a new general conversation for a user."""
        return cls(
            user_id=user_id,
            conversation_type=ConversationType.GENERAL.value,
            messages=[],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
    
    @classmethod
    def create_analysis_guided(
        cls, 
        user_id: str, 
        analysis_ref_id: str
    ) -> 'ChatConversation':
        """Create a new analysis-guided conversation."""
        return cls(
            user_id=user_id,
            conversation_type=ConversationType.ANALYSIS_GUIDED.value,
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
            "analysis_ref_id": self.analysis_ref_id,
            "messages": [msg.to_dict() for msg in self.messages],
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
