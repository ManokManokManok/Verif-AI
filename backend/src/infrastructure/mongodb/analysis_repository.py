"""
Analysis Result Repository

MongoDB repository for storing and retrieving scam analysis results.
Follows the repository pattern for clean architecture separation.
"""

from typing import Optional, List, Dict, Any
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database
from datetime import datetime
from bson import ObjectId

from ...domain.analysis_entities import (
    AnalysisResult, AnalysisNotFoundError
)


class AnalysisResultRepository:
    """
    MongoDB repository for analysis results.

    Collection Schema:
    {
        "_id": ObjectId,
        "ref_id": str,              # UUID for analysis reference
        "message_hash": str,        # SHA-256 of original message (optional)
        "scam_class": int,          # Integer classification
        "scam_type": str,           # Human-readable type
        "confidence_bps": int,      # Basis points (0-10000)
        "is_scam": bool,
        "analyzer_type": str,       # "stub" | "rules" | "bert" | "llm"
        "analyzer_version": str,
        "created_at": datetime,
    }
    """
    
    COLLECTION_NAME = "analysis_results"
    
    def __init__(self, client: MongoClient, database_name: str):
        self.db: Database = client[database_name]
        self.collection: Collection = self.db[self.COLLECTION_NAME]
        self._ensure_indexes()
    
    def _ensure_indexes(self) -> None:
        """Create indexes for efficient queries."""
        # Unique index on ref_id (analysis record lookup)
        self.collection.create_index("ref_id", unique=True)
        # Index on user_id for chat history
        self.collection.create_index("user_id", sparse=True)
        # Index on message_hash for lookup by message
        self.collection.create_index("message_hash", sparse=True)
        # Index on created_at for time-based queries
        self.collection.create_index("created_at")
        # Index to support user-visible history filtering
        self.collection.create_index([("user_id", 1), ("user_deleted", 1), ("created_at", -1)])

    @staticmethod
    def _active_user_visibility_query() -> Dict[str, Any]:
        """Query clause for records still visible in user history."""
        return {
            "$or": [
                {"user_deleted": {"$exists": False}},
                {"user_deleted": False},
            ]
        }

    def get_by_user_id(self, user_id: str, limit: int = 50, include_deleted: bool = False):
        """Fetch analysis results for a user, most recent first."""
        query: Dict[str, Any] = {"user_id": str(user_id)}
        if not include_deleted:
            query.update(self._active_user_visibility_query())

        docs = self.collection.find(query).sort("created_at", -1).limit(limit)
        return [self._document_to_entity(doc) for doc in docs]

    def get_by_id_for_user(self, analysis_id: str, user_id: str, include_deleted: bool = False) -> Optional[AnalysisResult]:
        """Get analysis by id with ownership and visibility checks."""
        try:
            query: Dict[str, Any] = {
                "_id": ObjectId(analysis_id),
                "user_id": str(user_id),
            }
            if not include_deleted:
                query.update(self._active_user_visibility_query())

            doc = self.collection.find_one(query)
        except Exception:
            return None

        if not doc:
            return None

        return self._document_to_entity(doc)

    def soft_delete_for_user(self, analysis_id: str, user_id: str) -> bool:
        """Hide one analysis from user history while retaining backend metadata."""
        try:
            result = self.collection.update_one(
                {
                    "_id": ObjectId(analysis_id),
                    "user_id": str(user_id),
                    **self._active_user_visibility_query(),
                },
                {
                    "$set": {
                        "user_deleted": True,
                        "user_deleted_at": datetime.utcnow(),
                        "deleted_by_user_id": str(user_id),
                        # Remove raw message content once user deletes history.
                        "message": None,
                    }
                },
            )
            return result.modified_count > 0
        except Exception:
            return False

    def soft_delete_all_for_user(self, user_id: str) -> int:
        """Hide all user analyses from history while retaining backend metadata."""
        try:
            result = self.collection.update_many(
                {
                    "user_id": str(user_id),
                    **self._active_user_visibility_query(),
                },
                {
                    "$set": {
                        "user_deleted": True,
                        "user_deleted_at": datetime.utcnow(),
                        "deleted_by_user_id": str(user_id),
                        "message": None,
                    }
                },
            )
            return int(result.modified_count)
        except Exception:
            return 0
    
    def save(self, result: AnalysisResult) -> AnalysisResult:
        """
        Save a new analysis result or update existing one.
        
        Args:
            result: AnalysisResult entity to save
            
        Returns:
            Saved AnalysisResult with generated ID
        """
        doc = self._entity_to_document(result)
        
        if result.id:
            # Update existing
            self.collection.update_one(
                {"_id": ObjectId(result.id)},
                {"$set": doc}
            )
        else:
            # Insert new
            insert_result = self.collection.insert_one(doc)
            result.id = str(insert_result.inserted_id)
        
        return result
    
    def get_by_id(self, analysis_id: str) -> Optional[AnalysisResult]:
        """
        Get analysis result by database ID.
        
        Args:
            analysis_id: MongoDB ObjectId as string
            
        Returns:
            AnalysisResult if found, None otherwise
        """
        try:
            doc = self.collection.find_one({"_id": ObjectId(analysis_id)})
        except Exception:
            return None
        
        if not doc:
            return None
        
        return self._document_to_entity(doc)
    
    def get_by_ref_id(self, ref_id: str) -> Optional[AnalysisResult]:
        """
        Get analysis result by reference ID (UUID).
        
        Args:
            ref_id: UUID string used for analysis reference
            
        Returns:
            AnalysisResult if found, None otherwise
        """
        doc = self.collection.find_one({"ref_id": ref_id})
        
        if not doc:
            return None
        
        return self._document_to_entity(doc)
    
    def get_by_message_hash(self, message_hash: str) -> Optional[AnalysisResult]:
        """
        Get the most recent analysis result by message hash.
        
        Args:
            message_hash: SHA-256 hash of the original message
            
        Returns:
            Most recent AnalysisResult for this message, or None
        """
        doc = self.collection.find_one(
            {"message_hash": message_hash},
            sort=[("created_at", -1)]  # Most recent first
        )
        
        if not doc:
            return None
        
        return self._document_to_entity(doc)
    


    def list_recent(
        self,
        limit: int = 50,
    ) -> List[AnalysisResult]:
        """
        List recent analysis results.

        Args:
            limit: Maximum number of results to return

        Returns:
            List of AnalysisResult entities
        """
        docs = self.collection.find({}).sort("created_at", -1).limit(limit)
        return [self._document_to_entity(doc) for doc in docs]
    
    def list_with_filter(
        self,
        page: int = 1,
        limit: int = 50,
        classification: int = None,
        min_confidence_bps: int = None,
        scam_only: bool = False
    ) -> List[AnalysisResult]:
        """
        List analysis results with filtering and pagination.

        Args:
            page: Page number (1-indexed)
            limit: Maximum number of results per page
            classification: Filter by scam_class (None for all)
            min_confidence_bps: Minimum confidence in basis points (0-10000)
            scam_only: If True, only include scam classifications (scam_class >= 0)

        Returns:
            List of AnalysisResult entities
        """
        query = {}

        # Classification filter
        if classification is not None:
            query["scam_class"] = classification

        # Confidence filter
        if min_confidence_bps is not None:
            query["confidence_bps"] = {"$gte": min_confidence_bps}

        # Scam-only filter (exclude legitimate classifications)
        if scam_only:
            if "scam_class" not in query:
                query["scam_class"] = {"$gte": 0}
            # If classification is already set, it takes priority

        # Calculate skip for pagination
        skip = (page - 1) * limit

        docs = self.collection.find(query).sort("created_at", -1).skip(skip).limit(limit)

        return [self._document_to_entity(doc) for doc in docs]
    
    def get_distinct_classifications(self) -> List[int]:
        """
        Get list of distinct scam_class values in the database.
        
        Returns:
            List of unique scam_class integers
        """
        return self.collection.distinct("scam_class")
    

    def count_all(self, classification: int = None, min_confidence_bps: int = None, scam_only: bool = False) -> int:
        """
        Count total number of analysis results.
        
        Args:
            classification: Filter by scam_class (None for all)
            min_confidence_bps: Minimum confidence threshold
            scam_only: Only count scam classifications
        """
        query = {}
        if classification is not None:
            query["scam_class"] = classification
        if min_confidence_bps is not None:
            query["confidence_bps"] = {"$gte": min_confidence_bps}
        if scam_only and "scam_class" not in query:
            query["scam_class"] = {"$gte": 0}
        return self.collection.count_documents(query)
    
    def _entity_to_document(self, entity: AnalysisResult) -> Dict[str, Any]:
        """Convert AnalysisResult entity to MongoDB document."""
        import logging
        logger = logging.getLogger(__name__)
        # Ensure user_id is always a string or None
        user_id_val = str(entity.user_id) if entity.user_id is not None else None
        doc = {
            "ref_id": entity.ref_id,
            "scam_class": entity.scam_class,
            "scam_type": entity.scam_type,
            "confidence_bps": entity.confidence_bps,
            "is_scam": entity.is_scam,
            "analyzer_type": entity.analyzer_type,
            "analyzer_version": entity.analyzer_version,
            "created_at": entity.created_at or datetime.utcnow(),
            "user_id": user_id_val,
            "message": entity.message,
            "scam_score": entity.scam_score,
            "legit_score": entity.legit_score,
            "label": entity.label,
            "type_confidence": entity.type_confidence,
            "summary": entity.summary,
            "details": entity.details,
            "image_attachment": entity.image_attachment,
            "key_markers": entity.key_markers,
            "needs_review": entity.needs_review,
            "review_reason": entity.review_reason,
        }
        if entity.id:
            doc["_id"] = entity.id
        if entity.message_hash:
            doc["message_hash"] = entity.message_hash
        logger.debug(f"[DEBUG] AnalysisResult entity before mapping: {entity}")
        logger.debug(f"[DEBUG] MongoDB document to be saved: {doc}")
        return doc
    
    def _document_to_entity(self, doc: Dict[str, Any]) -> AnalysisResult:
        """Convert MongoDB document to AnalysisResult entity."""
        return AnalysisResult(
            id=str(doc["_id"]),
            ref_id=doc["ref_id"],
            scam_class=doc["scam_class"],
            scam_type=doc["scam_type"],
            confidence_bps=doc["confidence_bps"],
            is_scam=doc["is_scam"],
            analyzer_type=doc["analyzer_type"],
            analyzer_version=doc["analyzer_version"],
            created_at=doc.get("created_at"),
            message_hash=doc.get("message_hash"),
            user_id=doc.get("user_id"),
            message=doc.get("message"),
            scam_score=doc.get("scam_score"),
            legit_score=doc.get("legit_score"),
            label=doc.get("label"),
            type_confidence=doc.get("type_confidence"),
            summary=doc.get("summary"),
            details=doc.get("details"),
            image_attachment=doc.get("image_attachment"),
            key_markers=doc.get("key_markers"),
            needs_review=doc.get("needs_review", False),
            review_reason=doc.get("review_reason"),
        )