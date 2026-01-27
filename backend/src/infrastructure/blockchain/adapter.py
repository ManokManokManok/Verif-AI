"""
Blockchain Adapter

Main service for interacting with the Ethereum blockchain.
Provides create_record and verify_record operations.

This is a STUB implementation for Phase 0.
Full implementation will be added in Phase 3.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass

from .config import get_blockchain_config, BlockchainConfig
from .canonical import (
    CanonicalPayload,
    canonicalize_payload,
    compute_payload_hash,
    CURRENT_SCHEMA_VERSION
)
from ...domain.analysis_entities import (
    ChainMetadata,
    ChainDisabledError,
    ChainConnectionError,
    ContractError
)

logger = logging.getLogger(__name__)


@dataclass
class CreateRecordResult:
    """Result from creating a record on-chain."""
    success: bool
    tx_hash: Optional[str]
    payload_hash: str
    block_number: Optional[int]
    error: Optional[str] = None


@dataclass
class VerifyRecordResult:
    """Result from verifying a record against on-chain data."""
    verified: bool
    payload_hash: str
    on_chain_exists: bool
    on_chain_data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class BlockchainDisabled:
    """
    Marker class returned when blockchain is disabled.
    Allows calling code to check if blockchain operations are available.
    """
    pass


class BlockchainAdapter:
    """
    Adapter for blockchain operations.
    
    Handles:
    - Connecting to Ethereum JSON-RPC
    - Signing and sending transactions
    - Reading contract state
    - Error handling and retries
    
    Usage:
        adapter = BlockchainAdapter()
        
        if isinstance(adapter, BlockchainDisabled):
            # Blockchain is disabled, handle accordingly
            pass
        else:
            result = adapter.create_record(canonical_payload)
    """
    
    def __new__(cls) -> 'BlockchainAdapter | BlockchainDisabled':
        """
        Factory that returns BlockchainDisabled if chain is not enabled.
        """
        config = get_blockchain_config()
        if not config.enabled:
            logger.info("Blockchain features are disabled (CHAIN_ENABLED=false)")
            return BlockchainDisabled()
        
        instance = super().__new__(cls)
        return instance
    
    def __init__(self):
        """Initialize the blockchain adapter with configuration."""
        self.config: BlockchainConfig = get_blockchain_config()
        
        if not self.config.is_valid():
            errors = self.config.get_validation_errors()
            raise ValueError(f"Invalid blockchain configuration: {', '.join(errors)}")
        
        # These will be set during _connect()
        self._web3 = None
        self._contract = None
        self._account = None
        self._connected = False
        
        logger.info(f"BlockchainAdapter initialized for network: {self.config.network_name}")
    
    def _ensure_connected(self) -> None:
        """
        Ensure connection to blockchain is established.
        
        STUB: Full implementation in Phase 3.
        """
        if self._connected:
            return
        
        # TODO: Phase 3 - Implement actual web3 connection
        # from web3 import Web3
        # self._web3 = Web3(Web3.HTTPProvider(self.config.rpc_url))
        # self._account = self._web3.eth.account.from_key(self.config.private_key)
        # self._contract = self._web3.eth.contract(
        #     address=self.config.contract_address,
        #     abi=CONTRACT_ABI
        # )
        
        logger.warning("BlockchainAdapter._ensure_connected() is a STUB - Phase 3 required")
        self._connected = True
    
    def create_record(self, payload: CanonicalPayload) -> CreateRecordResult:
        """
        Anchor a canonical payload on-chain.
        
        Args:
            payload: CanonicalPayload to anchor
            
        Returns:
            CreateRecordResult with transaction details
            
        Raises:
            ChainConnectionError: If unable to connect to chain
            ContractError: If contract call fails
        """
        self._ensure_connected()
        
        # Compute payload hash
        payload_hash = compute_payload_hash(payload)
        
        logger.info(f"Creating on-chain record for ref_id={payload.ref_id}")
        logger.info(f"Payload hash: {payload_hash}")
        
        # TODO: Phase 3 - Implement actual contract call
        # tx = self._contract.functions.storeRecord(
        #     payloadHash=bytes.fromhex(payload_hash[2:]),
        #     scamClass=payload.scam_class,
        #     confidenceBps=payload.confidence_bps,
        #     timestamp=int(datetime.fromisoformat(payload.created_at.rstrip('Z')).timestamp()),
        #     refId=bytes.fromhex(payload.ref_id.replace('-', ''))
        # ).build_transaction({
        #     'from': self._account.address,
        #     'gas': self.config.gas_limit,
        #     'nonce': self._web3.eth.get_transaction_count(self._account.address)
        # })
        # signed = self._account.sign_transaction(tx)
        # tx_hash = self._web3.eth.send_raw_transaction(signed.rawTransaction)
        # receipt = self._web3.eth.wait_for_transaction_receipt(tx_hash)
        
        logger.warning("BlockchainAdapter.create_record() is a STUB - Phase 3 required")
        
        # STUB: Return mock result
        return CreateRecordResult(
            success=False,
            tx_hash=None,
            payload_hash=payload_hash,
            block_number=None,
            error="STUB: Blockchain integration not yet implemented (Phase 3)"
        )
    
    def verify_record(self, payload: CanonicalPayload) -> VerifyRecordResult:
        """
        Verify a canonical payload against on-chain data.
        
        Args:
            payload: CanonicalPayload to verify
            
        Returns:
            VerifyRecordResult with verification status
        """
        self._ensure_connected()
        
        # Compute payload hash
        payload_hash = compute_payload_hash(payload)
        
        logger.info(f"Verifying on-chain record for ref_id={payload.ref_id}")
        logger.info(f"Payload hash: {payload_hash}")
        
        # TODO: Phase 3 - Implement actual contract read
        # exists, scam_class, confidence_bps, timestamp, ref_id, stored_by = \
        #     self._contract.functions.getRecord(
        #         bytes.fromhex(payload_hash[2:])
        #     ).call()
        # 
        # if not exists:
        #     return VerifyRecordResult(verified=False, ...)
        # 
        # Compare on-chain data with payload...
        
        logger.warning("BlockchainAdapter.verify_record() is a STUB - Phase 3 required")
        
        # STUB: Return mock result
        return VerifyRecordResult(
            verified=False,
            payload_hash=payload_hash,
            on_chain_exists=False,
            error="STUB: Blockchain integration not yet implemented (Phase 3)"
        )
    
    def get_chain_metadata(
        self,
        payload: CanonicalPayload,
        tx_hash: str,
        block_number: int
    ) -> ChainMetadata:
        """
        Create ChainMetadata from anchoring results.
        
        Args:
            payload: The canonical payload that was anchored
            tx_hash: Transaction hash from create_record
            block_number: Block number where tx was mined
            
        Returns:
            ChainMetadata ready to store with AnalysisResult
        """
        return ChainMetadata(
            schema_version=payload.schema_version,
            canonical_payload=payload.to_dict(),
            payload_hash=compute_payload_hash(payload),
            chain_tx_hash=tx_hash,
            chain_network=self.config.network_name,
            chain_contract_address=self.config.contract_address,
            anchored_at=datetime.utcnow(),
            block_number=block_number
        )
    
    @property
    def network_name(self) -> str:
        """Get the configured network name."""
        return self.config.network_name
    
    @property
    def contract_address(self) -> str:
        """Get the configured contract address."""
        return self.config.contract_address