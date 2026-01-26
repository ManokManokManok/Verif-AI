"""
Blockchain Infrastructure Module

This module provides blockchain interaction capabilities for anchoring
analysis results on-chain. It follows the clean architecture principle
of infrastructure adapters.

Components:
- service.py: High-level blockchain service (anchor_analysis, verify_analysis)
- adapter.py: Low-level blockchain adapter (legacy, use service.py for new code)
- canonical.py: Payload canonicalization and hashing
- config.py: Blockchain configuration from environment

Usage (Phase 3+):
    from src.infrastructure.blockchain import get_blockchain_service
    
    service = get_blockchain_service()
    
    if not service.is_enabled:
        # Blockchain is disabled, handle accordingly
        pass
    else:
        result = service.anchor_analysis(canonical_payload)
        verification = service.verify_analysis(canonical_payload)
        
Legacy Usage:
    from src.infrastructure.blockchain import BlockchainAdapter
    adapter = BlockchainAdapter()
"""

from .config import BlockchainConfig, get_blockchain_config
from .adapter import BlockchainAdapter, BlockchainDisabled
from .service import BlockchainService, get_blockchain_service
from .canonical import (
    # Core classes
    CanonicalPayload,
    PayloadValidationError,
    
    # Functions
    canonicalize_payload,
    compute_payload_hash,
    verify_payload_hash,
    validate_against_schema,
    get_json_schema,
    get_canonicalizer_for_version,
    reconstruct_payload_from_stored,
    
    # Constants
    CURRENT_SCHEMA_VERSION,
    VALID_ANALYZER_TYPES,
    SCAM_CLASS_MIN,
    SCAM_CLASS_MAX,
    CONFIDENCE_BPS_MIN,
    CONFIDENCE_BPS_MAX,
    
    # Examples (for testing/documentation)
    EXAMPLE_PAYLOAD_V1,
    EXAMPLE_PAYLOAD_V1_WITH_LLM
)

__all__ = [
    # Config
    'BlockchainConfig',
    'get_blockchain_config',
    
    # Service (Phase 3+)
    'BlockchainService',
    'get_blockchain_service',
    
    # Adapter (legacy)
    'BlockchainAdapter',
    'BlockchainDisabled',
    
    # Canonical payload
    'CanonicalPayload',
    'PayloadValidationError',
    'canonicalize_payload',
    'compute_payload_hash',
    'verify_payload_hash',
    'validate_against_schema',
    'get_json_schema',
    'get_canonicalizer_for_version',
    'reconstruct_payload_from_stored',
    
    # Constants
    'CURRENT_SCHEMA_VERSION',
    'VALID_ANALYZER_TYPES',
    'SCAM_CLASS_MIN',
    'SCAM_CLASS_MAX',
    'CONFIDENCE_BPS_MIN',
    'CONFIDENCE_BPS_MAX',
    
    # Examples
    'EXAMPLE_PAYLOAD_V1',
    'EXAMPLE_PAYLOAD_V1_WITH_LLM'
]
