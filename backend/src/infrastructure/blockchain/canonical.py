"""
Canonical Payload Schema and Hashing (Phase 1)

Defines the canonical payload format for blockchain anchoring.
Ensures deterministic serialization and hashing.

============================================================================
SCHEMA VERSION 1 (Current)
============================================================================
Required Fields:
    - schemaVersion: integer (always 1 for this version)
    - analyzerType: string enum ("stub" | "rules" | "bert" | "llm")
    - analyzerVersion: string (e.g., "v1", "v2.1.0")
    - refId: string (UUID v4 format)
    - createdAt: string (ISO 8601 UTC with milliseconds, e.g., "2026-01-26T10:30:00.000Z")
    - scamClass: integer (-1 for not scam, 0-14 for scam types)
    - confidenceBps: integer (basis points 0-10000, where 10000 = 100%)

Optional Fields:
    - modelVersion: string (for LLM model tracking, e.g., "gemma-2b-v1")

============================================================================
CANONICALIZATION RULES
============================================================================
1. JSON format with sorted keys (alphabetical)
2. No whitespace between elements (compact)
3. UTF-8 encoding
4. No floating point numbers (use integers with basis points)
5. Dates in ISO 8601 UTC format with Z suffix
6. Optional fields omitted when null/None (not included as null)

============================================================================
HASH ALGORITHM
============================================================================
Primary: Keccak-256 (Ethereum-native, used by Solidity)
- Output: 32 bytes (64 hex characters)
- Prefix: 0x
- Example: 0x1234567890abcdef...

Fallback: SHA-256 (if pycryptodome unavailable)
- Note: SHA-256 != Keccak-256, will cause verification failures with Ethereum

============================================================================
SCHEMA EVOLUTION RULES
============================================================================
1. NEVER change the meaning of existing fields in a schema version
2. NEVER remove required fields from an existing schema version
3. To add new required fields, create a new schema version
4. Optional fields can be added to existing versions (with null default)
5. Backend must support verification of ALL historical schema versions
6. On-chain contract ABI should remain stable across schema versions

IMPORTANT: This schema must remain stable. When adding fields, bump schemaVersion.
"""

import json
import hashlib
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Tuple
from enum import Enum


# Current schema version - NEVER change the meaning of existing versions
CURRENT_SCHEMA_VERSION = 1

# Valid analyzer types
VALID_ANALYZER_TYPES = frozenset(["stub", "rules", "bert", "llm"])

# Scam class range
SCAM_CLASS_MIN = -1  # -1 means "not a scam"
SCAM_CLASS_MAX = 14  # 0-14 are valid scam types

# Confidence basis points range
CONFIDENCE_BPS_MIN = 0
CONFIDENCE_BPS_MAX = 10000  # 10000 = 100%

# UUID v4 regex pattern
UUID_V4_PATTERN = re.compile(
    r'^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$',
    re.IGNORECASE
)

# ISO 8601 UTC pattern (with Z suffix)
ISO8601_UTC_PATTERN = re.compile(
    r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$'
)


class PayloadValidationError(Exception):
    """Raised when canonical payload validation fails."""
    
    def __init__(self, errors: List[str]):
        self.errors = errors
        super().__init__(f"Payload validation failed: {'; '.join(errors)}")


@dataclass
class CanonicalPayload:
    """
    Canonical payload for blockchain anchoring.
    
    This payload contains ONLY non-PII fields required for:
    1. Auditability - proving an analysis was performed
    2. Verification - confirming analysis hasn't been tampered with
    3. Traceability - linking on-chain record to off-chain data
    
    PRIVACY REQUIREMENTS - NEVER include:
    - Raw message text
    - Email addresses
    - Phone numbers
    - Usernames or user IDs
    - IP addresses
    - Any personally identifiable information
    
    Attributes:
        schema_version: Schema version number (currently 1)
        analyzer_type: Type of analyzer ("stub", "rules", "bert", "llm")
        analyzer_version: Version string of the analyzer
        ref_id: UUID v4 reference ID for the analysis
        created_at: ISO 8601 UTC timestamp with milliseconds
        scam_class: Integer classification (-1 to 14)
        confidence_bps: Confidence in basis points (0-10000)
        model_version: Optional LLM model version for future use
    """
    schema_version: int
    analyzer_type: str
    analyzer_version: str
    ref_id: str
    created_at: str  # ISO 8601 UTC
    scam_class: int
    confidence_bps: int
    
    # Optional fields for future LLM integration
    model_version: Optional[str] = None
    
    def __post_init__(self):
        """Validate payload after initialization."""
        errors = self.validate()
        if errors:
            raise PayloadValidationError(errors)
    
    def validate(self) -> List[str]:
        """
        Validate all payload fields.
        
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        
        # Schema version
        if self.schema_version != CURRENT_SCHEMA_VERSION:
            errors.append(
                f"Invalid schemaVersion: {self.schema_version}, "
                f"expected {CURRENT_SCHEMA_VERSION}"
            )
        
        # Analyzer type
        if self.analyzer_type not in VALID_ANALYZER_TYPES:
            errors.append(
                f"Invalid analyzerType: '{self.analyzer_type}', "
                f"must be one of {sorted(VALID_ANALYZER_TYPES)}"
            )
        
        # Analyzer version (non-empty string)
        if not self.analyzer_version or not isinstance(self.analyzer_version, str):
            errors.append("analyzerVersion must be a non-empty string")
        
        # Reference ID (UUID v4 format)
        if not UUID_V4_PATTERN.match(self.ref_id or ''):
            errors.append(
                f"Invalid refId: '{self.ref_id}', must be UUID v4 format"
            )
        
        # Created at (ISO 8601 UTC)
        if not ISO8601_UTC_PATTERN.match(self.created_at or ''):
            errors.append(
                f"Invalid createdAt: '{self.created_at}', "
                "must be ISO 8601 UTC format (YYYY-MM-DDTHH:MM:SS.sssZ)"
            )
        
        # Scam class (integer in range)
        if not isinstance(self.scam_class, int):
            errors.append(f"scamClass must be an integer, got {type(self.scam_class).__name__}")
        elif not (SCAM_CLASS_MIN <= self.scam_class <= SCAM_CLASS_MAX):
            errors.append(
                f"Invalid scamClass: {self.scam_class}, "
                f"must be between {SCAM_CLASS_MIN} and {SCAM_CLASS_MAX}"
            )
        
        # Confidence (integer basis points)
        if not isinstance(self.confidence_bps, int):
            errors.append(f"confidenceBps must be an integer, got {type(self.confidence_bps).__name__}")
        elif not (CONFIDENCE_BPS_MIN <= self.confidence_bps <= CONFIDENCE_BPS_MAX):
            errors.append(
                f"Invalid confidenceBps: {self.confidence_bps}, "
                f"must be between {CONFIDENCE_BPS_MIN} and {CONFIDENCE_BPS_MAX}"
            )
        
        # Model version (optional, but if provided must be non-empty string)
        if self.model_version is not None:
            if not isinstance(self.model_version, str) or not self.model_version:
                errors.append("modelVersion must be a non-empty string if provided")
        
        return errors
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary with sorted keys for deterministic serialization.
        
        The keys are in camelCase to match JSON conventions and the
        Solidity contract interface.
        
        Returns:
            Dictionary with sorted keys (excluding None values)
        """
        data = {
            "analyzerType": self.analyzer_type,
            "analyzerVersion": self.analyzer_version,
            "confidenceBps": self.confidence_bps,
            "createdAt": self.created_at,
            "refId": self.ref_id,
            "scamClass": self.scam_class,
            "schemaVersion": self.schema_version,
        }
        
        # Only include modelVersion if set (for future LLM support)
        if self.model_version is not None:
            data["modelVersion"] = self.model_version
        
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CanonicalPayload':
        """
        Create CanonicalPayload from dictionary.
        
        Args:
            data: Dictionary with camelCase keys
            
        Returns:
            CanonicalPayload instance
            
        Raises:
            PayloadValidationError: If validation fails
            KeyError: If required field is missing
        """
        return cls(
            schema_version=data["schemaVersion"],
            analyzer_type=data["analyzerType"],
            analyzer_version=data["analyzerVersion"],
            ref_id=data["refId"],
            created_at=data["createdAt"],
            scam_class=data["scamClass"],
            confidence_bps=data["confidenceBps"],
            model_version=data.get("modelVersion")
        )
    
    @classmethod
    def from_analysis_result(
        cls,
        ref_id: str,
        scam_class: int,
        confidence_bps: int,
        created_at: datetime,
        analyzer_type: str = "bert",
        analyzer_version: str = "v1",
        model_version: Optional[str] = None
    ) -> 'CanonicalPayload':
        """
        Create canonical payload from analysis result fields.
        
        Args:
            ref_id: UUID string for the analysis
            scam_class: Integer classification (-1 to 14)
            confidence_bps: Confidence in basis points (0-10000)
            created_at: Analysis timestamp (naive assumed UTC, or timezone-aware)
            analyzer_type: Type of analyzer used
            analyzer_version: Version of the analyzer
            model_version: Optional model version (for LLM)
            
        Returns:
            CanonicalPayload instance
            
        Raises:
            PayloadValidationError: If validation fails
        """
        # Ensure UTC ISO 8601 format with milliseconds and Z suffix
        # Truncate microseconds to milliseconds for consistency
        if created_at.tzinfo is None:
            # Assume naive datetime is UTC
            created_at_str = created_at.strftime('%Y-%m-%dT%H:%M:%S') + \
                f'.{created_at.microsecond // 1000:03d}Z'
        else:
            # Convert to UTC if timezone-aware
            utc_dt = created_at.astimezone(timezone.utc)
            created_at_str = utc_dt.strftime('%Y-%m-%dT%H:%M:%S') + \
                f'.{utc_dt.microsecond // 1000:03d}Z'
        
        return cls(
            schema_version=CURRENT_SCHEMA_VERSION,
            analyzer_type=analyzer_type,
            analyzer_version=analyzer_version,
            ref_id=ref_id,
            created_at=created_at_str,
            scam_class=scam_class,
            confidence_bps=confidence_bps,
            model_version=model_version
        )


def canonicalize_payload(payload: CanonicalPayload) -> str:
    """
    Serialize payload to canonical JSON string.
    
    Canonicalization rules:
    1. Keys are sorted alphabetically
    2. No whitespace (separators=(',', ':'))
    3. UTF-8 encoding
    4. No floating point numbers (use integers)
    
    Args:
        payload: CanonicalPayload to serialize
        
    Returns:
        Canonical JSON string
    """
    return json.dumps(
        payload.to_dict(),
        sort_keys=True,
        separators=(',', ':'),
        ensure_ascii=False
    )


def compute_payload_hash(payload: CanonicalPayload, algorithm: str = "keccak256") -> str:
    """
    Compute hash of canonical payload.
    
    Args:
        payload: CanonicalPayload to hash
        algorithm: Hash algorithm - "keccak256" (Ethereum-native) or "sha256"
        
    Returns:
        Hex-encoded hash string with 0x prefix
        
    Raises:
        ValueError: If unsupported algorithm specified
    """
    canonical_json = canonicalize_payload(payload)
    data = canonical_json.encode('utf-8')
    
    if algorithm == "keccak256":
        # Keccak-256 (Ethereum's hash function)
        try:
            from Crypto.Hash import keccak
            k = keccak.new(digest_bits=256)
            k.update(data)
            return '0x' + k.hexdigest()
        except ImportError:
            # Fallback to sha3 if pycryptodome not available
            # Note: Python's hashlib.sha3_256 is NOT the same as Keccak-256
            # For production, ensure pycryptodome is installed
            import warnings
            warnings.warn(
                "pycryptodome not installed, using SHA3-256 instead of Keccak-256. "
                "Install pycryptodome for Ethereum-compatible hashing."
            )
            hash_obj = hashlib.sha3_256(data)
            return '0x' + hash_obj.hexdigest()
    
    elif algorithm == "sha256":
        hash_obj = hashlib.sha256(data)
        return '0x' + hash_obj.hexdigest()
    
    else:
        raise ValueError(f"Unsupported hash algorithm: {algorithm}")


def verify_payload_hash(payload: CanonicalPayload, expected_hash: str) -> bool:
    """
    Verify that a payload produces the expected hash.
    
    Args:
        payload: CanonicalPayload to verify
        expected_hash: Expected hash (with 0x prefix)
        
    Returns:
        True if hash matches, False otherwise
    """
    # Determine algorithm from hash length
    if len(expected_hash) == 66:  # 0x + 64 hex chars
        computed = compute_payload_hash(payload, "keccak256")
    else:
        computed = compute_payload_hash(payload, "sha256")
    
    return computed.lower() == expected_hash.lower()


# Schema evolution helpers

def get_canonicalizer_for_version(version: int):
    """
    Get the appropriate canonicalizer for a schema version.
    
    This allows verification of records created under older schemas.
    
    Args:
        version: Schema version number
        
    Returns:
        Canonicalization function for that version
        
    Raises:
        ValueError: If version is not supported
    """
    if version == 1:
        return canonicalize_payload
    else:
        raise ValueError(f"Unsupported schema version: {version}")


def reconstruct_payload_from_stored(stored_payload: Dict[str, Any]) -> CanonicalPayload:
    """
    Reconstruct a CanonicalPayload from stored canonical_payload data.
    
    This is used during verification to rebuild the exact payload
    that was originally hashed and anchored.
    
    Args:
        stored_payload: The canonical_payload dict stored in the database
        
    Returns:
        CanonicalPayload instance
        
    Raises:
        ValueError: If schema version is unsupported
        PayloadValidationError: If stored data is invalid
    """
    version = stored_payload.get("schemaVersion", 1)
    
    if version == 1:
        return CanonicalPayload.from_dict(stored_payload)
    else:
        raise ValueError(f"Cannot reconstruct payload for schema version {version}")


def get_json_schema() -> Dict[str, Any]:
    """
    Get JSON Schema definition for canonical payload v1.
    
    This can be used for external validation or API documentation.
    
    Returns:
        JSON Schema as dictionary
    """
    return {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "$id": "https://verif-ai.com/schemas/canonical-payload-v1.json",
        "title": "Canonical Payload Schema v1",
        "description": "Schema for blockchain-anchored analysis results (non-PII only)",
        "type": "object",
        "required": [
            "schemaVersion",
            "analyzerType",
            "analyzerVersion",
            "refId",
            "createdAt",
            "scamClass",
            "confidenceBps"
        ],
        "additionalProperties": False,
        "properties": {
            "schemaVersion": {
                "type": "integer",
                "const": 1,
                "description": "Schema version number"
            },
            "analyzerType": {
                "type": "string",
                "enum": ["stub", "rules", "bert", "llm"],
                "description": "Type of analyzer that produced this result"
            },
            "analyzerVersion": {
                "type": "string",
                "minLength": 1,
                "description": "Version of the analyzer (e.g., 'v1', 'v2.1.0')"
            },
            "refId": {
                "type": "string",
                "pattern": "^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
                "description": "UUID v4 reference ID"
            },
            "createdAt": {
                "type": "string",
                "pattern": "^\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}\\.\\d{3}Z$",
                "description": "ISO 8601 UTC timestamp with milliseconds"
            },
            "scamClass": {
                "type": "integer",
                "minimum": -1,
                "maximum": 14,
                "description": "Scam classification (-1 = not scam, 0-14 = scam types)"
            },
            "confidenceBps": {
                "type": "integer",
                "minimum": 0,
                "maximum": 10000,
                "description": "Confidence in basis points (10000 = 100%)"
            },
            "modelVersion": {
                "type": "string",
                "minLength": 1,
                "description": "Optional LLM model version"
            }
        }
    }


def validate_against_schema(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate data against the canonical payload schema without creating an object.
    
    This is useful for validating incoming API requests or stored data.
    
    Args:
        data: Dictionary to validate
        
    Returns:
        Tuple of (is_valid, error_messages)
    """
    errors = []
    
    # Check required fields
    required = ["schemaVersion", "analyzerType", "analyzerVersion", 
                "refId", "createdAt", "scamClass", "confidenceBps"]
    for field in required:
        if field not in data:
            errors.append(f"Missing required field: {field}")
    
    if errors:
        return False, errors
    
    # Validate types and values
    if data.get("schemaVersion") != CURRENT_SCHEMA_VERSION:
        errors.append(f"Invalid schemaVersion: expected {CURRENT_SCHEMA_VERSION}")
    
    if data.get("analyzerType") not in VALID_ANALYZER_TYPES:
        errors.append(f"Invalid analyzerType: must be one of {sorted(VALID_ANALYZER_TYPES)}")
    
    if not isinstance(data.get("analyzerVersion"), str) or not data.get("analyzerVersion"):
        errors.append("analyzerVersion must be a non-empty string")
    
    if not UUID_V4_PATTERN.match(data.get("refId", "")):
        errors.append("refId must be a valid UUID v4")
    
    if not ISO8601_UTC_PATTERN.match(data.get("createdAt", "")):
        errors.append("createdAt must be ISO 8601 UTC format (YYYY-MM-DDTHH:MM:SS.sssZ)")
    
    scam_class = data.get("scamClass")
    if not isinstance(scam_class, int) or not (SCAM_CLASS_MIN <= scam_class <= SCAM_CLASS_MAX):
        errors.append(f"scamClass must be integer between {SCAM_CLASS_MIN} and {SCAM_CLASS_MAX}")
    
    confidence = data.get("confidenceBps")
    if not isinstance(confidence, int) or not (CONFIDENCE_BPS_MIN <= confidence <= CONFIDENCE_BPS_MAX):
        errors.append(f"confidenceBps must be integer between {CONFIDENCE_BPS_MIN} and {CONFIDENCE_BPS_MAX}")
    
    # Optional field validation
    if "modelVersion" in data:
        if data["modelVersion"] is not None:
            if not isinstance(data["modelVersion"], str) or not data["modelVersion"]:
                errors.append("modelVersion must be a non-empty string if provided")
    
    return len(errors) == 0, errors


# Example payload for documentation and testing
EXAMPLE_PAYLOAD_V1 = {
    "analyzerType": "bert",
    "analyzerVersion": "v1",
    "confidenceBps": 8550,
    "createdAt": "2026-01-26T10:30:00.000Z",
    "refId": "550e8400-e29b-41d4-a716-446655440000",
    "scamClass": 0,
    "schemaVersion": 1
}

EXAMPLE_PAYLOAD_V1_WITH_LLM = {
    "analyzerType": "llm",
    "analyzerVersion": "v1",
    "confidenceBps": 9200,
    "createdAt": "2026-01-26T10:30:00.000Z",
    "modelVersion": "gemma-2b-v1",
    "refId": "550e8400-e29b-41d4-a716-446655440000",
    "scamClass": 3,
    "schemaVersion": 1
}