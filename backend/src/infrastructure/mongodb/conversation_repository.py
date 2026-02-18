"""
Conversation Repository

MongoDB repository for storing and retrieving chat conversations.
Follows the repository pattern for clean architecture separation.
"""

from typing import Optional, List
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database
from datetime import datetime
from bson import ObjectId

from ...domain.chat_entities import ChatConversation, ChatMessage


class ConversationRepository:
    """
    MongoDB repository for chat conversations.
    
    Collection Schema:
    {
        "_id": ObjectId,
        "user_id": str,                    # User's MongoDB ID
        "conversation_type": str,           # "general" | "analysis_guided"
        "title": str,                       # Conversation title (auto-generated from first message)
        "analysis_ref_id": str (optional),  # UUID of analysis (for guided)
        "messages": [
            {
                "role": str,                # "user" | "assistant" | "system"
                "content": str,
                "timestamp": datetime
            }
        ],
        "created_at": datetime,
        "updated_at": datetime
    }
    """
    
    COLLECTION_NAME = "conversations"
    
    def __init__(self, client: MongoClient, database_name: str):
        self.db: Database = client[database_name]
        self.collection: Collection = self.db[self.COLLECTION_NAME]
        self._ensure_indexes()
    
    def _ensure_indexes(self) -> None:
        """Create indexes for efficient queries."""
        # Index on user_id for fetching user's conversations
        self.collection.create_index("user_id")
        # Compound index on user_id + conversation_type for finding general conversation
        self.collection.create_index([("user_id", 1), ("conversation_type", 1)])
        # Index on analysis_ref_id for finding analysis-guided conversations
        self.collection.create_index("analysis_ref_id", sparse=True)
        # Index on updated_at for sorting
        self.collection.create_index("updated_at")
    
    def save(self, conversation: ChatConversation) -> ChatConversation:
        """
        Save a conversation (create new or update existing).
        
        Args:
            conversation: ChatConversation entity to save
            
        Returns:
            Saved ChatConversation with generated ID
        """
        doc = self._entity_to_document(conversation)
        
        if conversation.id:
            # Update existing
            self.collection.update_one(
                {"_id": ObjectId(conversation.id)},
                {"$set": doc}
            )
        else:
            # Insert new
            insert_result = self.collection.insert_one(doc)
            conversation.id = str(insert_result.inserted_id)
        
        return conversation
    
    def get_by_id(self, conversation_id: str) -> Optional[ChatConversation]:
        """Get conversation by ID."""
        try:
            doc = self.collection.find_one({"_id": ObjectId(conversation_id)})
        except Exception:
            return None
        
        if not doc:
            return None
        
        return self._document_to_entity(doc)
    
    def get_by_id_for_user(self, conversation_id: str, user_id: str) -> Optional[ChatConversation]:
        """Get conversation by ID with user ownership verification."""
        try:
            doc = self.collection.find_one({
                "_id": ObjectId(conversation_id),
                "user_id": user_id
            })
        except Exception:
            return None
        
        if not doc:
            return None
        
        return self._document_to_entity(doc)
    
    def create_conversation(self, user_id: str, title: Optional[str] = None) -> ChatConversation:
        """
        Create a new general conversation for a user.
        
        Args:
            user_id: User's MongoDB ID
            title: Optional title (will be auto-generated from first message if not provided)
            
        Returns:
            Newly created ChatConversation
        """
        conversation = ChatConversation.create_general(user_id, title)
        return self.save(conversation)
    
    def get_latest_conversation(self, user_id: str) -> Optional[ChatConversation]:
        """
        Get user's most recent general conversation.
        
        Args:
            user_id: User's MongoDB ID
            
        Returns:
            Most recent ChatConversation or None
        """
        doc = self.collection.find_one(
            {"user_id": user_id, "conversation_type": "general"},
            sort=[("updated_at", -1)]
        )
        
        if doc:
            return self._document_to_entity(doc)
        
        return None
    
    def get_or_create_conversation(self, user_id: str, conversation_id: Optional[str] = None) -> ChatConversation:
        """
        Get existing conversation or create a new one.
        
        Args:
            user_id: User's MongoDB ID
            conversation_id: Optional specific conversation ID to retrieve
            
        Returns:
            ChatConversation (existing or newly created)
        """
        if conversation_id:
            conversation = self.get_by_id_for_user(conversation_id, user_id)
            if conversation:
                return conversation
        
        # If no conversation_id provided or not found, create a new one
        return self.create_conversation(user_id)
    
    def get_general_conversation(self, user_id: str) -> Optional[ChatConversation]:
        """
        Get user's most recent general conversation.
        Creates one if none exist.
        
        Args:
            user_id: User's MongoDB ID
            
        Returns:
            ChatConversation for general guidance
        """
        doc = self.collection.find_one(
            {"user_id": user_id, "conversation_type": "general"},
            sort=[("updated_at", -1)]
        )
        
        if doc:
            return self._document_to_entity(doc)
        
        # Create new general conversation
        conversation = ChatConversation.create_general(user_id)
        return self.save(conversation)
    
    def get_by_analysis_ref_id(
        self,
        analysis_ref_id: str,
        user_id: str
    ) -> Optional[ChatConversation]:
        """
        Find existing conversation for a specific analysis.
        
        Args:
            analysis_ref_id: UUID of the analysis
            user_id: User's MongoDB ID
            
        Returns:
            ChatConversation if found, None otherwise
        """
        doc = self.collection.find_one({
            "user_id": user_id,
            "conversation_type": "analysis_guided",
            "analysis_ref_id": analysis_ref_id
        })
        
        if doc:
            return self._document_to_entity(doc)
        
        return None
    
    def create_analysis_guided_conversation(
        self,
        user_id: str,
        analysis_ref_id: str,
        title: Optional[str] = None
    ) -> ChatConversation:
        """
        Create a new analysis-guided conversation.
        
        Args:
            user_id: User's MongoDB ID
            analysis_ref_id: UUID of the analysis
            title: Optional title
            
        Returns:
            Newly created ChatConversation
        """
        conversation = ChatConversation.create_analysis_guided(
            user_id=user_id,
            analysis_ref_id=analysis_ref_id,
            title=title
        )
        return self.save(conversation)
    
    def get_analysis_conversation(
        self, 
        user_id: str, 
        analysis_ref_id: str
    ) -> Optional[ChatConversation]:
        """
        Get or create conversation for a specific analysis.
        
        Args:
            user_id: User's MongoDB ID
            analysis_ref_id: UUID of the analysis
            
        Returns:
            ChatConversation for analysis-guided mode
        """
        doc = self.collection.find_one({
            "user_id": user_id,
            "conversation_type": "analysis_guided",
            "analysis_ref_id": analysis_ref_id
        })
        
        if doc:
            return self._document_to_entity(doc)
        
        # Create new analysis-guided conversation
        conversation = ChatConversation.create_analysis_guided(user_id, analysis_ref_id)
        return self.save(conversation)
    
    def get_user_conversations(
        self, 
        user_id: str, 
        limit: int = 50
    ) -> List[ChatConversation]:
        """
        Get all conversations for a user, sorted by most recent.
        
        Args:
            user_id: User's MongoDB ID
            limit: Maximum number of conversations to return
            
        Returns:
            List of ChatConversation entities
        """
        docs = self.collection.find(
            {"user_id": user_id}
        ).sort("updated_at", -1).limit(limit)
        
        return [self._document_to_entity(doc) for doc in docs]
    
    def delete_conversation(self, conversation_id: str, user_id: str) -> bool:
        """
        Delete a conversation (with ownership check).
        
        Args:
            conversation_id: MongoDB ObjectId as string
            user_id: User's MongoDB ID (for security check)
            
        Returns:
            True if deleted, False if not found or unauthorized
        """
        try:
            result = self.collection.delete_one({
                "_id": ObjectId(conversation_id),
                "user_id": user_id  # Ensure user owns this conversation
            })
            return result.deleted_count > 0
        except Exception:
            return False
    
    def _entity_to_document(self, conversation: ChatConversation) -> dict:
        """Convert ChatConversation entity to MongoDB document."""
        doc = {
            "user_id": conversation.user_id,
            "conversation_type": conversation.conversation_type,
            "title": conversation.title,
            "messages": [
                {
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": msg.timestamp
                }
                for msg in conversation.messages
            ],
            "created_at": conversation.created_at,
            "updated_at": conversation.updated_at
        }
        
        if conversation.analysis_ref_id:
            doc["analysis_ref_id"] = conversation.analysis_ref_id
        
        return doc
    
    def _document_to_entity(self, doc: dict) -> ChatConversation:
        """Convert MongoDB document to ChatConversation entity."""
        messages = [
            ChatMessage(
                role=msg["role"],
                content=msg["content"],
                timestamp=msg.get("timestamp")
            )
            for msg in doc.get("messages", [])
        ]
        
        conversation = ChatConversation(
            user_id=doc["user_id"],
            conversation_type=doc["conversation_type"],
            messages=messages,
            id=str(doc["_id"]),
            title=doc.get("title", "Untitled Conversation"),
            analysis_ref_id=doc.get("analysis_ref_id"),
            created_at=doc.get("created_at"),
            updated_at=doc.get("updated_at")
        )
        
        return conversation
