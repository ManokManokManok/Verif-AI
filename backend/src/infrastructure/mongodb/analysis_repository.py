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
        
        # Index on message_hash for lookup by message
        self.collection.create_index("message_hash", sparse=True)
        
        # Index on created_at for time-based queries
        self.collection.create_index("created_at")
        
        # Index on chain metadata for anchored records
        self.collection.create_index("chain_metadata.payload_hash", sparse=True)
    
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
    
    def count_anchored(self) -> int:
        """Count total number of anchored analysis results."""
        return self.collection.count_documents({"chain_metadata": {"$exists": True}})
    
    def count_all(self) -> int:
        """Count total number of analysis results."""
        return self.collection.count_documents({})
    
    def _entity_to_document(self, entity: AnalysisResult) -> Dict[str, Any]:
        """Convert AnalysisResult entity to MongoDB document."""
        doc = {
            "ref_id": entity.ref_id,
            "scam_class": entity.scam_class,
            "scam_type": entity.scam_type,
            "confidence_bps": entity.confidence_bps,
            "is_scam": entity.is_scam,
            "analyzer_type": entity.analyzer_type,
            "analyzer_version": entity.analyzer_version,
            "created_at": entity.created_at or datetime.utcnow()
        }
        
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
            chain_metadata=chain_metadata
        )