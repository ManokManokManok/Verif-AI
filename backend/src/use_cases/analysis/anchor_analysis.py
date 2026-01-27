"""
Anchor Analysis Use Case

Orchestrates the process of anchoring an analysis result on the blockchain.
Implements the transactional flow: save analysis → anchor on-chain → update DB.

Phase 4 Implementation.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from ...domain.analysis_entities import (
    AnalysisResult,
    ChainMetadata,
    AnalysisNotFoundError,
    AnalysisAlreadyAnchoredError,
    ChainDisabledError,
    ChainConnectionError,
    ContractError
)
from ...infrastructure.mongodb.analysis_repository import AnalysisResultRepository
from ...infrastructure.blockchain import (
    get_blockchain_service,
    CanonicalPayload,
    compute_payload_hash,
    CURRENT_SCHEMA_VERSION
)

logger = logging.getLogger(__name__)


class AnchorAnalysisUseCase:
    """
    Use case for anchoring analysis results on the blockchain.
    
    This class orchestrates:
    1. Validating the analysis exists and is not already anchored
    2. Building the canonical payload
    3. Anchoring on-chain
    4. Updating the DB with chain metadata
    
    Usage:
        use_case = AnchorAnalysisUseCase(repository)
        result = use_case.execute(ref_id="550e8400-...")
    """
    
    def __init__(self, repository: AnalysisResultRepository):
        """
        Initialize the use case.
        
        Args:
            repository: Analysis result repository for DB operations
        """
        self._repository = repository
        self._blockchain_service = get_blockchain_service()
    
    def execute(
        self,
        ref_id: str,
        force: bool = False
    ) -> Dict[str, Any]:
        """
        Anchor an analysis result on the blockchain.
        
        Args:
            ref_id: Reference ID (UUID) of the analysis to anchor
            force: If True, re-anchor even if already anchored (creates new record)
            
        Returns:
            Dict with:
                - success: bool
                - ref_id: str
                - payload_hash: str
                - tx_hash: str
                - block_number: int
                - anchored_at: str (ISO format)
                
        Raises:
            AnalysisNotFoundError: If analysis doesn't exist
            AnalysisAlreadyAnchoredError: If already anchored and force=False
            ChainDisabledError: If blockchain is disabled
            ChainConnectionError: If cannot connect to blockchain
            ContractError: If contract call fails
        """
        logger.info(f"Anchoring analysis: ref_id={ref_id}")
        
        # Step 1: Get the analysis from DB
        analysis = self._repository.get_by_ref_id(ref_id)
        if not analysis:
            raise AnalysisNotFoundError(f"Analysis with ref_id {ref_id} not found")
        
        # Step 2: Check if already anchored
        if analysis.is_anchored and not force:
            raise AnalysisAlreadyAnchoredError(
                f"Analysis {ref_id} is already anchored. "
                f"tx_hash: {analysis.chain_metadata.chain_tx_hash}"
            )
        
        # Step 3: Build canonical payload
        canonical_payload = self._build_canonical_payload(analysis)
        
        # Step 4: Anchor on-chain
        anchor_result = self._blockchain_service.anchor_analysis(canonical_payload)
        
        if not anchor_result['success']:
            raise ContractError(f"Failed to anchor: {anchor_result.get('error')}")
        
        # Step 5: Create chain metadata
        chain_metadata = self._blockchain_service.create_chain_metadata(
            payload=canonical_payload,
            tx_hash=anchor_result['tx_hash'],
            block_number=anchor_result['block_number']
        )
        
        # Step 6: Update DB with chain metadata
        updated_analysis = self._repository.update_chain_metadata(
            ref_id=ref_id,
            chain_metadata=chain_metadata
        )
        
        logger.info(
            f"Analysis anchored: ref_id={ref_id}, "
            f"tx_hash={anchor_result['tx_hash']}, "
            f"block={anchor_result['block_number']}"
        )
        
        return {
            'success': True,
            'ref_id': ref_id,
            'payload_hash': anchor_result['payload_hash'],
            'tx_hash': anchor_result['tx_hash'],
            'block_number': anchor_result['block_number'],
            'gas_used': anchor_result.get('gas_used'),
            'anchored_at': chain_metadata.anchored_at.isoformat(),
            'schema_version': chain_metadata.schema_version
        }
    
    def _build_canonical_payload(self, analysis: AnalysisResult) -> CanonicalPayload:
        """
        Build a canonical payload from an analysis result.
        
        Args:
            analysis: The analysis result to convert
            
        Returns:
            CanonicalPayload ready for anchoring
        """
        # Format created_at to ISO 8601 with milliseconds
        if analysis.created_at:
            created_at_str = analysis.created_at.strftime("%Y-%m-%dT%H:%M:%S.000Z")
        else:
            created_at_str = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.000Z")
        
        return CanonicalPayload(
            schema_version=CURRENT_SCHEMA_VERSION,
            analyzer_type=analysis.analyzer_type,
            analyzer_version=analysis.analyzer_version,
            ref_id=analysis.ref_id,
            created_at=created_at_str,
            scam_class=analysis.scam_class,
            confidence_bps=analysis.confidence_bps
        )


class VerifyAnalysisUseCase:
    """
    Use case for verifying an analysis result against on-chain data.
    
    This class orchestrates:
    1. Getting the analysis from DB
    2. Rebuilding the canonical payload
    3. Verifying against on-chain data
    
    Usage:
        use_case = VerifyAnalysisUseCase(repository)
        result = use_case.execute(ref_id="550e8400-...")
    """
    
    def __init__(self, repository: AnalysisResultRepository):
        """
        Initialize the use case.
        
        Args:
            repository: Analysis result repository for DB operations
        """
        self._repository = repository
        self._blockchain_service = get_blockchain_service()
    
    def execute(self, ref_id: str) -> Dict[str, Any]:
        """
        Verify an analysis result against on-chain data.
        
        Args:
            ref_id: Reference ID (UUID) of the analysis to verify
            
        Returns:
            Dict with:
                - verified: bool
                - ref_id: str
                - is_anchored: bool
                - payload_hash: str (if anchored)
                - on_chain_data: dict (if verified)
                - mismatches: list (if not verified)
                
        Raises:
            AnalysisNotFoundError: If analysis doesn't exist
            ChainDisabledError: If blockchain is disabled
            ChainConnectionError: If cannot connect to blockchain
        """
        logger.info(f"Verifying analysis: ref_id={ref_id}")
        
        # Step 1: Get the analysis from DB
        analysis = self._repository.get_by_ref_id(ref_id)
        if not analysis:
            raise AnalysisNotFoundError(f"Analysis with ref_id {ref_id} not found")
        
        # Step 2: Check if anchored
        if not analysis.is_anchored:
            return {
                'verified': False,
                'ref_id': ref_id,
                'is_anchored': False,
                'reason': 'Analysis has not been anchored on-chain'
            }
        
        # Step 3: Rebuild canonical payload from CURRENT data to detect tampering
        # This computes a fresh hash from the current DB values
        current_payload = self._build_canonical_payload(analysis)
        
        # Step 4: Verify the current payload against on-chain data
        verification = self._blockchain_service.verify_analysis(current_payload)
        
        # Step 5: Also check if current hash matches stored hash (detect DB tampering)
        current_hash = compute_payload_hash(current_payload)
        stored_hash = analysis.chain_metadata.payload_hash
        
        # If hashes don't match, data was tampered with
        if current_hash != stored_hash:
            logger.warning(
                f"Tampering detected: ref_id={ref_id}, "
                f"current_hash={current_hash}, stored_hash={stored_hash}"
            )
            return {
                'verified': False,
                'ref_id': ref_id,
                'is_anchored': True,
                'payload_hash': current_hash,
                'stored_payload_hash': stored_hash,
                'stored_tx_hash': analysis.chain_metadata.chain_tx_hash,
                'stored_block_number': analysis.chain_metadata.block_number,
                'reason': 'Data has been modified since anchoring',
                'mismatches': ['payload_hash mismatch - data tampered']
            }
        
        result = {
            'verified': verification['verified'],
            'ref_id': ref_id,
            'is_anchored': True,
            'payload_hash': verification['payload_hash'],
            'stored_tx_hash': analysis.chain_metadata.chain_tx_hash,
            'stored_block_number': analysis.chain_metadata.block_number
        }
        
        if verification['verified']:
            result['on_chain_data'] = verification.get('on_chain_data')
            logger.info(f"Analysis verified: ref_id={ref_id}")
        else:
            result['mismatches'] = verification.get('mismatches', [])
            result['reason'] = 'On-chain data does not match local data'
            logger.warning(f"Analysis verification failed: ref_id={ref_id}")
        
        return result
    
    def _build_canonical_payload(self, analysis: AnalysisResult) -> CanonicalPayload:
        """Build canonical payload from analysis result."""
        if analysis.created_at:
            created_at_str = analysis.created_at.strftime("%Y-%m-%dT%H:%M:%S.000Z")
        else:
            created_at_str = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.000Z")
        
        return CanonicalPayload(
            schema_version=analysis.chain_metadata.schema_version if analysis.chain_metadata else CURRENT_SCHEMA_VERSION,
            analyzer_type=analysis.analyzer_type,
            analyzer_version=analysis.analyzer_version,
            ref_id=analysis.ref_id,
            created_at=created_at_str,
            scam_class=analysis.scam_class,
            confidence_bps=analysis.confidence_bps
        )


class GetAnchoredAnalysisUseCase:
    """
    Use case for retrieving anchored analysis details.
    
    Usage:
        use_case = GetAnchoredAnalysisUseCase(repository)
        result = use_case.execute(ref_id="550e8400-...")
    """
    
    def __init__(self, repository: AnalysisResultRepository):
        self._repository = repository
    
    def execute(self, ref_id: str) -> Dict[str, Any]:
        """
        Get detailed information about an anchored analysis.
        
        Args:
            ref_id: Reference ID of the analysis
            
        Returns:
            Dict with analysis and chain details
        """
        analysis = self._repository.get_by_ref_id(ref_id)
        if not analysis:
            raise AnalysisNotFoundError(f"Analysis with ref_id {ref_id} not found")
        
        result = analysis.to_dict()
        
        if analysis.is_anchored:
            result['anchoring_status'] = 'anchored'
        else:
            result['anchoring_status'] = 'pending'
        
        return result


class ListAnalysesUseCase:
    """
    Use case for listing analysis results with filtering.
    
    Usage:
        use_case = ListAnalysesUseCase(repository)
        results = use_case.execute(anchored_only=True, limit=20)
    """
    
    def __init__(self, repository: AnalysisResultRepository):
        self._repository = repository
    
    def execute(
        self,
        anchored_only: bool = False,
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        List analysis results.
        
        Args:
            anchored_only: If True, only return anchored analyses
            limit: Maximum number of results
            
        Returns:
            Dict with:
                - analyses: List of analysis dicts
                - total: int (total count of all analyses)
                - total_anchored: int
                - count: int (count in current response)
        """
        analyses = self._repository.list_recent(limit=limit, anchored_only=anchored_only)
        total_anchored = self._repository.count_anchored()
        total = self._repository.count_all()
        
        return {
            'analyses': [a.to_dict() for a in analyses],
            'total': total,
            'count': len(analyses),
            'total_anchored': total_anchored,
            'filters': {
                'anchored_only': anchored_only,
                'limit': limit
            }
        }