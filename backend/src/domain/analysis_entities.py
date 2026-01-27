"""
Analysis Domain Entities

Domain entities for scam analysis results with blockchain anchoring support.
These entities are framework-agnostic and contain only business logic.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import IntEnum
import uuid


class ScamClass(IntEnum):
    """
    Scam classification types matching the BERT model output.
    Maps to scam_types dictionary in domain/scam_types.py
    """
    BANKING_ACCESS_PAYMENT = 0
    FINANCIAL_INVESTMENT = 1
    HEALTH_WELLNESS = 2
    IMPERSONATION_AUTHORITY = 3
    INTERNATIONAL_CROSS_BORDER = 4
    JOB_BUSINESS_WORK = 5
    LEGAL_DOCUMENT = 6
    MOBILE_DIGITAL = 7
    PRIZE_RAFFLE_REWARD = 8
    PROPERTY_RENTAL = 9
    PSYCHOLOGICAL_URGENCY = 10
    ROMANCE_DATING = 11
    SHOPPING_ECOMMERCE = 12
    TAX_BANKING_LOAN = 13
    TECH_ONLINE_ACCOUNT = 14
    NOT_SCAM = -1  # Special case for legitimate messages


class AnalyzerType:
    """Analyzer type identifiers for schema versioning."""
    STUB = "stub"
    RULES = "rules"
    BERT = "bert"
    LLM = "llm"


@dataclass
class ChainMetadata:
    """
    Blockchain anchoring metadata.
    Added to an AnalysisResult after successful on-chain storage.
    """
    schema_version: int
    canonical_payload: Dict[str, Any]  # The exact JSON used for hashing (non-PII)
    payload_hash: str  # Keccak-256 or SHA-256 hash
    chain_tx_hash: str  # Transaction hash
    chain_network: str  # e.g., "ganache", "sepolia", "mainnet"
    chain_contract_address: str
    anchored_at: datetime
    block_number: Optional[int] = None


@dataclass
class AnalysisResult:
    """
    Domain entity representing a scam analysis result.
    
    This entity stores both the analysis outcome and optional blockchain
    anchoring metadata. The message content itself is NOT stored to
    protect user privacy - only a hash is kept for lookup purposes.
    """
    # Core identification
    ref_id: str  # UUID for blockchain reference
    
    # Analysis results (non-PII)
    scam_class: int  # Integer classification (ScamClass enum value)
    scam_type: str  # Human-readable scam type name
    confidence_bps: int  # Confidence in basis points (0-10000)
    is_scam: bool
    
    # Analyzer metadata
    analyzer_type: str  # "stub" | "rules" | "bert" | "llm"
    analyzer_version: str
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    # Optional fields
    id: Optional[str] = None  # Database ID (set after persistence)
    message_hash: Optional[str] = None  # SHA-256 of original message (for lookup)
    
    # Blockchain anchoring (None until anchored)
    chain_metadata: Optional[ChainMetadata] = None
    
    @classmethod
    def create(
        cls,
        scam_class: int,
        scam_type: str,
        confidence_bps: int,
        is_scam: bool,
        analyzer_type: str = AnalyzerType.BERT,
        analyzer_version: str = "v1",
        message_hash: Optional[str] = None
    ) -> 'AnalysisResult':
        """
        Factory method to create a new AnalysisResult with generated ref_id.
        
        Args:
            scam_class: Integer classification (0-14 for scam types, -1 for not scam)
            scam_type: Human-readable scam type name
            confidence_bps: Confidence in basis points (0-10000)
            is_scam: Whether the message is classified as scam
            analyzer_type: Type of analyzer used
            analyzer_version: Version of the analyzer
            message_hash: Optional SHA-256 hash of original message
            
        Returns:
            New AnalysisResult instance
        """
        return cls(
            ref_id=str(uuid.uuid4()),
            scam_class=scam_class,
            scam_type=scam_type,
            confidence_bps=confidence_bps,
            is_scam=is_scam,
            analyzer_type=analyzer_type,
            analyzer_version=analyzer_version,
            message_hash=message_hash,
            created_at=datetime.utcnow()
        )
    
    @property
    def is_anchored(self) -> bool:
        """Check if this result has been anchored on-chain."""
        return self.chain_metadata is not None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        result = {
            "ref_id": self.ref_id,
            "scam_class": self.scam_class,
            "scam_type": self.scam_type,
            "confidence_bps": self.confidence_bps,
            "is_scam": self.is_scam,
            "analyzer_type": self.analyzer_type,
            "analyzer_version": self.analyzer_version,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "is_anchored": self.is_anchored
        }
        
        if self.id:
            result["id"] = self.id
            
        if self.chain_metadata:
            result["chain"] = {
                "schema_version": self.chain_metadata.schema_version,
                "payload_hash": self.chain_metadata.payload_hash,
                "tx_hash": self.chain_metadata.chain_tx_hash,
                "network": self.chain_metadata.chain_network,
                "contract_address": self.chain_metadata.chain_contract_address,
                "anchored_at": self.chain_metadata.anchored_at.isoformat(),
                "block_number": self.chain_metadata.block_number
            }
            
        return result


class AnalysisNotFoundError(Exception):
    """Raised when an analysis result is not found."""
    pass


class AnalysisAlreadyAnchoredError(Exception):
    """Raised when trying to anchor an already-anchored analysis."""
    pass


class BlockchainError(Exception):
    """Base exception for blockchain-related errors."""
    pass


class ChainDisabledError(BlockchainError):
    """Raised when blockchain operations are attempted but chain is disabled."""
    pass


class ChainConnectionError(BlockchainError):
    """Raised when unable to connect to the blockchain."""
    pass


class ContractError(BlockchainError):
    """Raised when a smart contract operation fails."""
    pass