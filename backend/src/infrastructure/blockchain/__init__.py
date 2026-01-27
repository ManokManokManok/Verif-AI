"""
Blockchain Infrastructure Module

Provides blockchain integration services for anchoring and verification.
"""

from .canonical import (
    CanonicalPayload,
    compute_payload_hash,
    canonicalize_payload,
    CURRENT_SCHEMA_VERSION,
    VALID_ANALYZER_TYPES
)
from .service import (
    BlockchainService,
    get_blockchain_service
)
from .config import BlockchainConfig, get_blockchain_config, reset_config
from .adapter import BlockchainAdapter, BlockchainDisabled

__all__ = [
    # Canonical payload
    'CanonicalPayload',
    'compute_payload_hash',
    'canonicalize_payload',
    'CURRENT_SCHEMA_VERSION',
    'VALID_ANALYZER_TYPES',
    # Service
    'BlockchainService',
    'get_blockchain_service',
    # Config
    'BlockchainConfig',
    'get_blockchain_config',
    'reset_config',
    # Adapter
    'BlockchainAdapter',
    'BlockchainDisabled',
]
