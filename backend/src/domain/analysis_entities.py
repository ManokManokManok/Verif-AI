"""
Analysis Domain Entities

Domain entities for scam analysis results and historical audit metadata.
These entities are framework-agnostic and contain only business logic.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any
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
class AnalysisResult:
    """
    Domain entity representing a scam analysis result.
    
    This entity stores both the analysis outcome and optional audit
    metadata. The message content itself is NOT stored to
    protect user privacy - only a hash is kept for lookup purposes.
    """
    # Core identification
    ref_id: str  # UUID for analysis reference

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
    user_id: Optional[str] = None  # User ID for chat history (None for anonymous)
    id: Optional[str] = None  # Database ID (set after persistence)
    message_hash: Optional[str] = None  # SHA-256 of original message (for lookup)
    # New fields for chat history and full analysis
    message: Optional[str] = None
    scam_score: Optional[float] = None
    legit_score: Optional[float] = None
    label: Optional[str] = None
    type_confidence: Optional[float] = None
    summary: Optional[str] = None
    key_markers: Optional[list] = None

    # Low confidence review fields
    needs_review: bool = False
    review_reason: Optional[str] = None


    
    @classmethod
    def create(
        cls,
        scam_class: int,
        scam_type: str,
        confidence_bps: int,
        is_scam: bool,
        analyzer_type: str = AnalyzerType.BERT,
        analyzer_version: str = "v1",
        message_hash: Optional[str] = None,
        user_id: Optional[str] = None,
        message: Optional[str] = None,
        scam_score: Optional[float] = None,
        legit_score: Optional[float] = None,
        label: Optional[str] = None,
        type_confidence: Optional[float] = None,
        summary: Optional[str] = None,
        key_markers: Optional[list] = None,
        needs_review: bool = False,
        review_reason: Optional[str] = None
    ) -> 'AnalysisResult':
        """
        Factory method to create a new AnalysisResult with generated ref_id.
        Accepts all analysis fields for full chat history support.
        """
        return cls(
            ref_id=str(uuid.uuid4()),
            user_id=user_id,
            scam_class=scam_class,
            scam_type=scam_type,
            confidence_bps=confidence_bps,
            is_scam=is_scam,
            analyzer_type=analyzer_type,
            analyzer_version=analyzer_version,
            message_hash=message_hash,
            message=message,
            scam_score=scam_score,
            legit_score=legit_score,
            label=label,
            type_confidence=type_confidence,
            summary=summary,
            key_markers=key_markers,
            needs_review=needs_review,
            review_reason=review_reason,
            created_at=datetime.utcnow()
        )
    
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
            "user_id": self.user_id,
            "message": self.message,
            "scam_score": self.scam_score,
            "legit_score": self.legit_score,
            "label": self.label,
            "type_confidence": self.type_confidence,
            "summary": self.summary,
            "key_markers": self.key_markers,
        }

        if self.id:
            result["id"] = self.id

        return result


class AnalysisNotFoundError(Exception):
    """Raised when an analysis result is not found."""
    pass