"""
Blockchain Service Module

Provides high-level operations for blockchain anchoring and verification.
This module wraps the lower-level adapter with business logic and error handling.

Phase 3 Implementation.
"""

import logging
import json
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path

from web3 import Web3
from web3.exceptions import ContractLogicError, TransactionNotFound
from eth_account import Account
from eth_account.signers.local import LocalAccount

from .config import get_blockchain_config, BlockchainConfig
from .canonical import (
    CanonicalPayload,
    canonicalize_payload,
    compute_payload_hash,
    verify_payload_hash,
    CURRENT_SCHEMA_VERSION
)
from ...domain.analysis_entities import (
    AnalysisResult,
    ChainMetadata,
    ChainDisabledError,
    ChainConnectionError,
    ContractError
)

logger = logging.getLogger(__name__)


def _load_contract_abi() -> list:
    """Load the AnalysisAnchor contract ABI from file."""
    abi_path = Path(__file__).parent / "abi" / "AnalysisAnchor.json"
    
    if not abi_path.exists():
        raise FileNotFoundError(
            f"Contract ABI not found at {abi_path}. "
            "Run 'npm run extract-abi' in the contracts directory."
        )
    
    with open(abi_path, 'r') as f:
        return json.load(f)


def _uuid_to_bytes32(uuid_str: str) -> bytes:
    """
    Convert a UUID string to bytes32 for contract storage.
    
    Args:
        uuid_str: UUID in format "550e8400-e29b-41d4-a716-446655440000"
        
    Returns:
        32-byte representation (padded with zeros on the right)
    """
    # Remove dashes and convert to bytes
    hex_str = uuid_str.replace('-', '')
    uuid_bytes = bytes.fromhex(hex_str)
    
    # Pad to 32 bytes (UUID is 16 bytes)
    return uuid_bytes.ljust(32, b'\x00')


def _bytes32_to_uuid(data: bytes) -> str:
    """
    Convert bytes32 back to UUID string.
    
    Args:
        data: 32-byte data from contract
        
    Returns:
        UUID string in standard format
    """
    # Take first 16 bytes (UUID length)
    uuid_bytes = data[:16]
    hex_str = uuid_bytes.hex()
    
    # Format as UUID: 8-4-4-4-12
    return f"{hex_str[:8]}-{hex_str[8:12]}-{hex_str[12:16]}-{hex_str[16:20]}-{hex_str[20:]}"


def _timestamp_to_unix(iso_timestamp: str) -> int:
    """
    Convert ISO 8601 timestamp to Unix timestamp.
    
    Args:
        iso_timestamp: ISO 8601 format (e.g., "2026-01-26T10:30:00.000Z")
        
    Returns:
        Unix timestamp as integer
    """
    # Remove Z suffix and parse
    dt_str = iso_timestamp.rstrip('Z')
    if '.' in dt_str:
        dt = datetime.fromisoformat(dt_str)
    else:
        dt = datetime.fromisoformat(dt_str)
    
    return int(dt.timestamp())


def _scam_class_to_uint8(scam_class: int) -> int:
    """
    Convert scam class to uint8 for contract storage.
    
    Args:
        scam_class: -1 to 14 (domain value)
        
    Returns:
        0-14 or 255 (for -1/unknown)
    """
    if scam_class == -1:
        return 255
    return scam_class


def _uint8_to_scam_class(value: int) -> int:
    """
    Convert uint8 from contract back to scam class.
    
    Args:
        value: 0-14 or 255
        
    Returns:
        -1 to 14
    """
    if value == 255:
        return -1
    return value


class BlockchainService:
    """
    High-level service for blockchain operations.
    
    Provides:
    - anchor_analysis(): Store analysis result on-chain
    - verify_analysis(): Verify on-chain data matches local data
    - get_record(): Retrieve on-chain record
    
    Usage:
        service = BlockchainService()
        
        if not service.is_enabled:
            # Handle disabled state
            return
            
        result = service.anchor_analysis(canonical_payload)
    """
    
    def __init__(self):
        """Initialize the blockchain service."""
        self._config: BlockchainConfig = get_blockchain_config()
        self._web3: Optional[Web3] = None
        self._contract = None
        self._account: Optional[LocalAccount] = None
        self._connected = False
        self._abi: Optional[list] = None
        
        if self._config.enabled:
            logger.info(f"BlockchainService initialized for network: {self._config.network_name}")
        else:
            logger.info("BlockchainService: Blockchain features are disabled")
    
    @property
    def is_enabled(self) -> bool:
        """Check if blockchain features are enabled."""
        return self._config.enabled
    
    @property
    def network_name(self) -> str:
        """Get the configured network name."""
        return self._config.network_name
    
    @property
    def contract_address(self) -> Optional[str]:
        """Get the configured contract address."""
        return self._config.contract_address
    
    def _ensure_enabled(self) -> None:
        """Raise error if blockchain is disabled."""
        if not self._config.enabled:
            raise ChainDisabledError("Blockchain features are disabled (CHAIN_ENABLED=false)")
    
    def _connect(self) -> None:
        """
        Establish connection to blockchain.
        
        Raises:
            ChainConnectionError: If connection fails
            ValueError: If configuration is invalid
        """
        if self._connected:
            return
        
        self._ensure_enabled()
        
        # Validate configuration
        if not self._config.is_valid():
            errors = self._config.get_validation_errors()
            raise ValueError(f"Invalid blockchain configuration: {', '.join(errors)}")
        
        try:
            # Connect to RPC
            self._web3 = Web3(Web3.HTTPProvider(self._config.rpc_url))
            
            if not self._web3.is_connected():
                raise ChainConnectionError(
                    f"Failed to connect to blockchain RPC at {self._config.rpc_url}"
                )
            
            # Load account from private key
            self._account = Account.from_key(self._config.private_key)
            
            # Load contract ABI and create contract instance
            self._abi = _load_contract_abi()
            self._contract = self._web3.eth.contract(
                address=Web3.to_checksum_address(self._config.contract_address),
                abi=self._abi
            )
            
            self._connected = True
            
            logger.info(
                f"Connected to blockchain: {self._config.network_name} "
                f"(chain_id={self._web3.eth.chain_id})"
            )
            logger.info(f"Signer address: {self._account.address}")
            logger.info(f"Contract address: {self._config.contract_address}")
            
        except ChainConnectionError:
            raise
        except Exception as e:
            raise ChainConnectionError(f"Failed to connect to blockchain: {str(e)}")
    
    def anchor_analysis(
        self,
        payload: CanonicalPayload,
        wait_for_receipt: bool = True,
        gas_limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Anchor an analysis result on the blockchain.
        
        Args:
            payload: Canonical payload to anchor
            wait_for_receipt: Whether to wait for transaction receipt
            gas_limit: Override default gas limit
            
        Returns:
            Dictionary with:
                - success: bool
                - tx_hash: str (transaction hash)
                - payload_hash: str (computed hash)
                - block_number: int (if wait_for_receipt)
                - gas_used: int (if wait_for_receipt)
                
        Raises:
            ChainDisabledError: If blockchain is disabled
            ChainConnectionError: If connection fails
            ContractError: If contract call fails (e.g., duplicate hash)
        """
        self._connect()
        
        # Compute payload hash
        payload_hash = compute_payload_hash(payload)
        payload_hash_bytes = bytes.fromhex(payload_hash[2:])  # Remove 0x prefix
        
        # Convert payload fields for contract
        scam_class_uint8 = _scam_class_to_uint8(payload.scam_class)
        timestamp_unix = _timestamp_to_unix(payload.created_at)
        ref_id_bytes = _uuid_to_bytes32(payload.ref_id)
        
        logger.info(f"Anchoring analysis: ref_id={payload.ref_id}")
        logger.info(f"  Payload hash: {payload_hash}")
        logger.info(f"  Scam class: {payload.scam_class} (uint8: {scam_class_uint8})")
        logger.info(f"  Confidence: {payload.confidence_bps} bps")
        
        try:
            # Build transaction
            nonce = self._web3.eth.get_transaction_count(self._account.address)
            
            tx = self._contract.functions.storeRecord(
                payload_hash_bytes,
                scam_class_uint8,
                payload.confidence_bps,
                timestamp_unix,
                ref_id_bytes
            ).build_transaction({
                'from': self._account.address,
                'gas': gas_limit or self._config.gas_limit,
                'gasPrice': self._web3.eth.gas_price,
                'nonce': nonce,
                'chainId': self._web3.eth.chain_id
            })
            
            # Sign transaction
            signed_tx = self._account.sign_transaction(tx)
            
            # Send transaction
            tx_hash = self._web3.eth.send_raw_transaction(signed_tx.raw_transaction)
            tx_hash_hex = tx_hash.hex()
            
            logger.info(f"Transaction sent: {tx_hash_hex}")
            
            result = {
                'success': True,
                'tx_hash': f"0x{tx_hash_hex}" if not tx_hash_hex.startswith('0x') else tx_hash_hex,
                'payload_hash': payload_hash,
                'block_number': None,
                'gas_used': None
            }
            
            if wait_for_receipt:
                # Wait for transaction to be mined
                receipt = self._web3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
                
                result['block_number'] = receipt['blockNumber']
                result['gas_used'] = receipt['gasUsed']
                
                if receipt['status'] == 0:
                    raise ContractError("Transaction reverted on-chain")
                
                logger.info(
                    f"Transaction mined: block={receipt['blockNumber']}, "
                    f"gas_used={receipt['gasUsed']}"
                )
            
            return result
            
        except ContractLogicError as e:
            # Contract reverted (e.g., RecordAlreadyExists)
            error_msg = str(e)
            logger.error(f"Contract error: {error_msg}")
            raise ContractError(f"Smart contract error: {error_msg}")
            
        except Exception as e:
            logger.error(f"Anchor failed: {str(e)}")
            raise ContractError(f"Failed to anchor analysis: {str(e)}")
    
    def verify_analysis(self, payload: CanonicalPayload) -> Dict[str, Any]:
        """
        Verify an analysis result against on-chain data.
        
        Args:
            payload: Canonical payload to verify
            
        Returns:
            Dictionary with:
                - verified: bool (True if on-chain data matches payload)
                - payload_hash: str
                - on_chain_exists: bool
                - on_chain_data: dict (if exists)
                - mismatches: list (if not verified)
                
        Raises:
            ChainDisabledError: If blockchain is disabled
            ChainConnectionError: If connection fails
        """
        self._connect()
        
        # Compute payload hash
        payload_hash = compute_payload_hash(payload)
        payload_hash_bytes = bytes.fromhex(payload_hash[2:])
        
        logger.info(f"Verifying analysis: ref_id={payload.ref_id}")
        logger.info(f"  Payload hash: {payload_hash}")
        
        try:
            # Call getRecord on contract
            result = self._contract.functions.getRecord(payload_hash_bytes).call()
            
            exists, scam_class, confidence_bps, timestamp, ref_id, stored_by = result
            
            if not exists:
                logger.info("Record not found on-chain")
                return {
                    'verified': False,
                    'payload_hash': payload_hash,
                    'on_chain_exists': False,
                    'on_chain_data': None,
                    'mismatches': ['Record does not exist on-chain']
                }
            
            # Convert on-chain values back to domain values
            on_chain_scam_class = _uint8_to_scam_class(scam_class)
            on_chain_ref_id = _bytes32_to_uuid(ref_id)
            
            on_chain_data = {
                'scam_class': on_chain_scam_class,
                'confidence_bps': confidence_bps,
                'timestamp': timestamp,
                'ref_id': on_chain_ref_id,
                'stored_by': stored_by
            }
            
            # Compare values
            mismatches = []
            
            if on_chain_scam_class != payload.scam_class:
                mismatches.append(
                    f"scam_class: on-chain={on_chain_scam_class}, expected={payload.scam_class}"
                )
            
            if confidence_bps != payload.confidence_bps:
                mismatches.append(
                    f"confidence_bps: on-chain={confidence_bps}, expected={payload.confidence_bps}"
                )
            
            expected_timestamp = _timestamp_to_unix(payload.created_at)
            if timestamp != expected_timestamp:
                mismatches.append(
                    f"timestamp: on-chain={timestamp}, expected={expected_timestamp}"
                )
            
            # Compare ref_id (case-insensitive)
            if on_chain_ref_id.lower() != payload.ref_id.lower():
                mismatches.append(
                    f"ref_id: on-chain={on_chain_ref_id}, expected={payload.ref_id}"
                )
            
            verified = len(mismatches) == 0
            
            logger.info(f"Verification result: {'VERIFIED' if verified else 'NOT VERIFIED'}")
            if mismatches:
                for m in mismatches:
                    logger.warning(f"  Mismatch: {m}")
            
            return {
                'verified': verified,
                'payload_hash': payload_hash,
                'on_chain_exists': True,
                'on_chain_data': on_chain_data,
                'mismatches': mismatches if mismatches else None
            }
            
        except Exception as e:
            logger.error(f"Verification failed: {str(e)}")
            raise ChainConnectionError(f"Failed to verify analysis: {str(e)}")
    
    def get_record(self, payload_hash: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a record from the blockchain by payload hash.
        
        Args:
            payload_hash: The 0x-prefixed keccak256 hash
            
        Returns:
            Record data if found, None if not exists
            
        Raises:
            ChainDisabledError: If blockchain is disabled
            ChainConnectionError: If connection fails
        """
        self._connect()
        
        # Ensure 0x prefix
        if not payload_hash.startswith('0x'):
            payload_hash = f'0x{payload_hash}'
        
        payload_hash_bytes = bytes.fromhex(payload_hash[2:])
        
        try:
            result = self._contract.functions.getRecord(payload_hash_bytes).call()
            exists, scam_class, confidence_bps, timestamp, ref_id, stored_by = result
            
            if not exists:
                return None
            
            return {
                'exists': True,
                'scam_class': _uint8_to_scam_class(scam_class),
                'confidence_bps': confidence_bps,
                'timestamp': timestamp,
                'ref_id': _bytes32_to_uuid(ref_id),
                'stored_by': stored_by,
                'payload_hash': payload_hash
            }
            
        except Exception as e:
            raise ChainConnectionError(f"Failed to get record: {str(e)}")
    
    def record_exists(self, payload_hash: str) -> bool:
        """
        Check if a record exists on-chain.
        
        Args:
            payload_hash: The 0x-prefixed keccak256 hash
            
        Returns:
            True if record exists, False otherwise
        """
        self._connect()
        
        if not payload_hash.startswith('0x'):
            payload_hash = f'0x{payload_hash}'
        
        payload_hash_bytes = bytes.fromhex(payload_hash[2:])
        
        try:
            return self._contract.functions.recordExists(payload_hash_bytes).call()
        except Exception as e:
            raise ChainConnectionError(f"Failed to check record existence: {str(e)}")
    
    def get_record_count(self) -> int:
        """
        Get total number of records stored on-chain.
        
        Returns:
            Number of records
        """
        self._connect()
        
        try:
            return self._contract.functions.recordCount().call()
        except Exception as e:
            raise ChainConnectionError(f"Failed to get record count: {str(e)}")
    
    def get_owner(self) -> str:
        """
        Get the contract owner address.
        
        Returns:
            Owner address
        """
        self._connect()
        
        try:
            return self._contract.functions.owner().call()
        except Exception as e:
            raise ChainConnectionError(f"Failed to get owner: {str(e)}")
    
    def create_chain_metadata(
        self,
        payload: CanonicalPayload,
        tx_hash: str,
        block_number: int
    ) -> ChainMetadata:
        """
        Create ChainMetadata from anchoring results.
        
        Args:
            payload: The canonical payload that was anchored
            tx_hash: Transaction hash from anchor_analysis
            block_number: Block number where tx was mined
            
        Returns:
            ChainMetadata ready to store with AnalysisResult
        """
        return ChainMetadata(
            schema_version=payload.schema_version,
            canonical_payload=payload.to_dict(),
            payload_hash=compute_payload_hash(payload),
            chain_tx_hash=tx_hash,
            chain_network=self._config.network_name,
            chain_contract_address=self._config.contract_address,
            anchored_at=datetime.utcnow(),
            block_number=block_number
        )


# Singleton instance
_blockchain_service: Optional[BlockchainService] = None


def get_blockchain_service() -> BlockchainService:
    """
    Get the singleton BlockchainService instance.
    
    Returns:
        BlockchainService instance
    """
    global _blockchain_service
    if _blockchain_service is None:
        _blockchain_service = BlockchainService()
    return _blockchain_service
