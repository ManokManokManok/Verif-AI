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
    AnalysisResult, ChainMetadata, AnalysisNotFoundError
)


class AnalysisResultRepository:
    """
    MongoDB repository for analysis results with blockchain metadata.
    
    Collection Schema:
    {
        "_id": ObjectId,
        "ref_id": str,              # UUID for blockchain reference
        "message_hash": str,        # SHA-256 of original message (optional)
        "scam_class": int,          # Integer classification
        "scam_type": str,           # Human-readable type
        "confidence_bps": int,      # Basis points (0-10000)
        "is_scam": bool,
        "analyzer_type": str,       # "stub" | "rules" | "bert" | "llm"
        "analyzer_version": str,
        "created_at": datetime,
        
        # Chain metadata (added after anchoring)
        "chain_metadata": {
            "schema_version": int,
            "canonical_payload": dict,
            "payload_hash": str,
            "chain_tx_hash": str,
            "chain_network": str,
            "chain_contract_address": str,
            "anchored_at": datetime,
            "block_number": int (optional)
        }
    }
    """
    
    COLLECTION_NAME = "analysis_results"
    
    def __init__(self, client: MongoClient, database_name: str):
        self.db: Database = client[database_name]
        self.collection: Collection = self.db[self.COLLECTION_NAME]
        self._ensure_indexes()
    
    def _ensure_indexes(self) -> None:
        """Create indexes for efficient queries."""
        # Unique index on ref_id (used for blockchain anchoring)
        self.collection.create_index("ref_id", unique=True)
        # Index on user_id for chat history
        self.collection.create_index("user_id", sparse=True)
        # Index on message_hash for lookup by message
        self.collection.create_index("message_hash", sparse=True)
        # Index on created_at for time-based queries
        self.collection.create_index("created_at")
        # Index to support user-visible history filtering
        self.collection.create_index([("user_id", 1), ("user_deleted", 1), ("created_at", -1)])
        # Index on chain metadata for anchored records
        self.collection.create_index("chain_metadata.payload_hash", sparse=True)

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
            ref_id: UUID string used for blockchain reference
            
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
    
    def get_by_payload_hash(self, payload_hash: str) -> Optional[AnalysisResult]:
        """
        Get analysis result by blockchain payload hash.
        
        Args:
            payload_hash: Keccak-256 hash stored on-chain
            
        Returns:
            AnalysisResult if found, None otherwise
        """
        doc = self.collection.find_one({"chain_metadata.payload_hash": payload_hash})
        
        if not doc:
            return None
        
        return self._document_to_entity(doc)
    
    def update_chain_metadata(
        self,
        ref_id: str,
        chain_metadata: ChainMetadata
    ) -> AnalysisResult:
        """
        Update an analysis result with blockchain anchoring metadata.
        
        Args:
            ref_id: Reference ID of the analysis
            chain_metadata: Blockchain metadata to add
            
        Returns:
            Updated AnalysisResult
            
        Raises:
            AnalysisNotFoundError: If analysis with ref_id doesn't exist
        """
        chain_doc = {
            "schema_version": chain_metadata.schema_version,
            "canonical_payload": chain_metadata.canonical_payload,
            "payload_hash": chain_metadata.payload_hash,
            "chain_tx_hash": chain_metadata.chain_tx_hash,
            "chain_network": chain_metadata.chain_network,
            "chain_contract_address": chain_metadata.chain_contract_address,
            "anchored_at": chain_metadata.anchored_at,
            "block_number": chain_metadata.block_number
        }
        
        result = self.collection.find_one_and_update(
            {"ref_id": ref_id},
            {"$set": {"chain_metadata": chain_doc}},
            return_document=True
        )
        
        if not result:
            raise AnalysisNotFoundError(f"Analysis with ref_id {ref_id} not found")
        
        return self._document_to_entity(result)
    
    def list_recent(
        self,
        limit: int = 50,
        anchored_only: bool = False
    ) -> List[AnalysisResult]:
        """
        List recent analysis results.
        
        Args:
            limit: Maximum number of results to return
            anchored_only: If True, only return anchored results
            
        Returns:
            List of AnalysisResult entities
        """
        query = {}
        if anchored_only:
            query["chain_metadata"] = {"$exists": True}
        
        docs = self.collection.find(query).sort("created_at", -1).limit(limit)
        
        return [self._document_to_entity(doc) for doc in docs]
    
    def list_with_filter(
        self,
        filter_mode: str = 'all',
        page: int = 1,
        limit: int = 50,
        classification: int = None
    ) -> List[AnalysisResult]:
        """
        List analysis results with filtering and pagination.
        
        Args:
            filter_mode: 'all', 'anchored', or 'pending'
            page: Page number (1-indexed)
            limit: Maximum number of results per page
            classification: Filter by scam_class (None for all)
            
        Returns:
            List of AnalysisResult entities
        """
        query = {}
        
        # Status filter
        if filter_mode == 'anchored':
            query["chain_metadata"] = {"$exists": True}
        elif filter_mode == 'pending':
            query["$or"] = [
                {"chain_metadata": {"$exists": False}},
                {"chain_metadata": None}
            ]
        
        # Classification filter
        if classification is not None:
            query["scam_class"] = classification
        
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
    
    def count_anchored(self, classification: int = None) -> int:
        """
        Count total number of anchored analysis results.
        
        Args:
            classification: Filter by scam_class (None for all)
        """
        query = {"chain_metadata": {"$exists": True}}
        if classification is not None:
            query["scam_class"] = classification
        return self.collection.count_documents(query)
    
    def count_all(self, classification: int = None) -> int:
        """
        Count total number of analysis results.
        
        Args:
            classification: Filter by scam_class (None for all)
        """
        query = {}
        if classification is not None:
            query["scam_class"] = classification
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
            "key_markers": entity.key_markers,
            "needs_review": entity.needs_review,
            "review_reason": entity.review_reason,
        }
        if entity.id:
            doc["_id"] = entity.id
        if entity.message_hash:
            doc["message_hash"] = entity.message_hash
        if entity.chain_metadata:
            doc["chain_metadata"] = {
                "schema_version": entity.chain_metadata.schema_version,
                "canonical_payload": entity.chain_metadata.canonical_payload,
                "payload_hash": entity.chain_metadata.payload_hash,
                "chain_tx_hash": entity.chain_metadata.chain_tx_hash,
                "chain_network": entity.chain_metadata.chain_network,
                "chain_contract_address": entity.chain_metadata.chain_contract_address,
                "anchored_at": entity.chain_metadata.anchored_at,
                "block_number": entity.chain_metadata.block_number
            }
        logger.debug(f"[DEBUG] AnalysisResult entity before mapping: {entity}")
        logger.debug(f"[DEBUG] MongoDB document to be saved: {doc}")
        return doc
    
    def _document_to_entity(self, doc: Dict[str, Any]) -> AnalysisResult:
        """Convert MongoDB document to AnalysisResult entity."""
        chain_metadata = None
        if "chain_metadata" in doc and doc["chain_metadata"]:
            chain_doc = doc["chain_metadata"]
            chain_metadata = ChainMetadata(
                schema_version=chain_doc["schema_version"],
                canonical_payload=chain_doc["canonical_payload"],
                payload_hash=chain_doc["payload_hash"],
                chain_tx_hash=chain_doc["chain_tx_hash"],
                chain_network=chain_doc["chain_network"],
                chain_contract_address=chain_doc["chain_contract_address"],
                anchored_at=chain_doc["anchored_at"],
                block_number=chain_doc.get("block_number")
            )
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
            key_markers=doc.get("key_markers"),
            needs_review=doc.get("needs_review", False),
            review_reason=doc.get("review_reason"),
            chain_metadata=chain_metadata
        )