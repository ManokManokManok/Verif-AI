"""
Blockchain API Views

Admin-only API endpoints for blockchain anchoring and verification.
These endpoints allow administrators to:
- Anchor analysis results on the blockchain
- Verify the integrity of anchored analyses
- List and query anchored analyses

Phase 5 Implementation.

OWASP References:
- https://cheatsheetseries.owasp.org/cheatsheets/REST_Security_Cheat_Sheet.html
"""

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.request import Request
from rest_framework.response import Response
import logging

from ...domain.analysis_entities import (
    AnalysisNotFoundError,
    AnalysisAlreadyAnchoredError,
    ChainDisabledError,
    ChainConnectionError,
    ContractError
)
from ...use_cases.analysis import (
    AnchorAnalysisUseCase,
    VerifyAnalysisUseCase,
    GetAnchoredAnalysisUseCase,
    ListAnalysesUseCase
)
from ...infrastructure.mongodb.connection import get_mongo_client, get_database_name
from ...infrastructure.mongodb.analysis_repository import AnalysisResultRepository
from ...infrastructure.rate_limiter import get_rate_limiter, get_client_ip
from ...interfaces.rest.middleware import admin_required, authenticated_required

# Configure logger
logger = logging.getLogger(__name__)
security_logger = logging.getLogger('security')


def get_analysis_repository():
    """Get analysis repository instance."""
    client = get_mongo_client()
    db_name = get_database_name()
    return AnalysisResultRepository(client, db_name)


def _rate_limit_check(request: Request, category: str) -> Response | None:
    """
    Check rate limit for blockchain operations.
    
    Returns None if allowed, or a 429 Response if rate limited.
    """
    rate_limiter = get_rate_limiter()
    client_ip = get_client_ip(request)
    user_id = getattr(request, 'user_id', None)
    
    identifier = f"user:{user_id}" if user_id else f"ip:{client_ip}"
    
    is_limited, retry_after, headers = rate_limiter.is_rate_limited(
        identifier, category
    )
    
    if is_limited:
        security_logger.warning(
            f"Rate limit exceeded for blockchain operation: "
            f"identifier={identifier}, category={category}"
        )
        response = Response({
            'error': {
                'code': 'RATE_LIMIT_EXCEEDED',
                'message': 'Too many blockchain requests. Please try again later.',
                'retry_after': retry_after
            }
        }, status=429)
        
        for header, value in (headers or {}).items():
            response[header] = value
        
        return response
    
    return None


@api_view(['POST'])
@admin_required
def anchor_analysis(request: Request, ref_id: str) -> Response:
    """
    Anchor an analysis result on the blockchain.
    
    POST /api/blockchain/analysis/{ref_id}/anchor
    
    Path Parameters:
        ref_id: UUID of the analysis result to anchor
        
    Query Parameters:
        force: If "true", re-anchor even if already anchored (optional)
        
    Returns:
        200: Successfully anchored
        {
            "success": true,
            "ref_id": "uuid",
            "payload_hash": "0x...",
            "tx_hash": "0x...",
            "block_number": 123,
            "anchored_at": "2026-01-26T12:00:00",
            "schema_version": 1
        }
        
        400: Already anchored (without force flag)
        404: Analysis not found
        429: Rate limited
        500: Blockchain error
        503: Blockchain disabled or unavailable
    """
    # Rate limiting for blockchain write operations
    rate_response = _rate_limit_check(request, 'blockchain_write')
    if rate_response:
        return rate_response
    
    # Get force parameter
    force = request.query_params.get('force', '').lower() == 'true'
    
    try:
        repository = get_analysis_repository()
        use_case = AnchorAnalysisUseCase(repository)
        
        result = use_case.execute(ref_id=ref_id, force=force)
        
        # Log successful anchor
        security_logger.info(
            f"Analysis anchored: ref_id={ref_id}, "
            f"tx_hash={result['tx_hash']}, "
            f"user_id={getattr(request, 'user_id', 'unknown')}"
        )
        
        return Response(result, status=status.HTTP_200_OK)
        
    except AnalysisNotFoundError as e:
        logger.warning(f"Anchor failed - not found: ref_id={ref_id}")
        return Response({
            'error': {
                'code': 'ANALYSIS_NOT_FOUND',
                'message': str(e)
            }
        }, status=status.HTTP_404_NOT_FOUND)
        
    except AnalysisAlreadyAnchoredError as e:
        logger.info(f"Anchor failed - already anchored: ref_id={ref_id}")
        return Response({
            'error': {
                'code': 'ALREADY_ANCHORED',
                'message': str(e),
                'hint': 'Use ?force=true to re-anchor'
            }
        }, status=status.HTTP_400_BAD_REQUEST)
        
    except ChainDisabledError as e:
        logger.warning(f"Anchor failed - chain disabled: {e}")
        return Response({
            'error': {
                'code': 'BLOCKCHAIN_DISABLED',
                'message': 'Blockchain features are disabled'
            }
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
    except ChainConnectionError as e:
        logger.error(f"Anchor failed - connection error: {e}")
        return Response({
            'error': {
                'code': 'BLOCKCHAIN_UNAVAILABLE',
                'message': 'Unable to connect to blockchain'
            }
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
    except ContractError as e:
        logger.error(f"Anchor failed - contract error: {e}")
        return Response({
            'error': {
                'code': 'CONTRACT_ERROR',
                'message': 'Smart contract operation failed'
            }
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    except Exception as e:
        logger.exception(f"Anchor failed - unexpected error: {e}")
        return Response({
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'An unexpected error occurred'
            }
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@authenticated_required
def verify_analysis(request: Request, ref_id: str) -> Response:
    """
    Verify an analysis result against on-chain data.
    
    GET /api/blockchain/analysis/{ref_id}/verify
    
    Path Parameters:
        ref_id: UUID of the analysis result to verify
        
    Returns:
        200: Verification complete
        {
            "verified": true,
            "ref_id": "uuid",
            "is_anchored": true,
            "payload_hash": "0x...",
            "stored_tx_hash": "0x...",
            "stored_block_number": 123,
            "on_chain_data": { ... }
        }
        
        200: Not anchored
        {
            "verified": false,
            "ref_id": "uuid",
            "is_anchored": false,
            "reason": "Analysis has not been anchored on-chain"
        }
        
        404: Analysis not found
        429: Rate limited
        503: Blockchain disabled or unavailable
    """
    # Rate limiting for blockchain read operations
    rate_response = _rate_limit_check(request, 'blockchain_read')
    if rate_response:
        return rate_response
    
    try:
        repository = get_analysis_repository()
        use_case = VerifyAnalysisUseCase(repository)
        
        result = use_case.execute(ref_id=ref_id)
        
        # Log verification attempt
        logger.info(
            f"Analysis verified: ref_id={ref_id}, "
            f"verified={result.get('verified')}, "
            f"user_id={getattr(request, 'user_id', 'unknown')}"
        )
        
        return Response(result, status=status.HTTP_200_OK)
        
    except AnalysisNotFoundError as e:
        logger.warning(f"Verify failed - not found: ref_id={ref_id}")
        return Response({
            'error': {
                'code': 'ANALYSIS_NOT_FOUND',
                'message': str(e)
            }
        }, status=status.HTTP_404_NOT_FOUND)
        
    except ChainDisabledError as e:
        logger.warning(f"Verify failed - chain disabled: {e}")
        return Response({
            'error': {
                'code': 'BLOCKCHAIN_DISABLED',
                'message': 'Blockchain features are disabled'
            }
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
    except ChainConnectionError as e:
        logger.error(f"Verify failed - connection error: {e}")
        return Response({
            'error': {
                'code': 'BLOCKCHAIN_UNAVAILABLE',
                'message': 'Unable to connect to blockchain'
            }
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
    except Exception as e:
        logger.exception(f"Verify failed - unexpected error: {e}")
        return Response({
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'An unexpected error occurred'
            }
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@authenticated_required
def get_analysis(request: Request, ref_id: str) -> Response:
    """
    Get detailed information about an analysis, including chain metadata.
    
    GET /api/blockchain/analysis/{ref_id}
    
    Path Parameters:
        ref_id: UUID of the analysis result
        
    Returns:
        200: Analysis found
        {
            "ref_id": "uuid",
            "scam_class": 5,
            "scam_type": "Legal Document Scam",
            "confidence_bps": 7800,
            "is_scam": true,
            "analyzer_type": "bert",
            "analyzer_version": "v1.2.0",
            "created_at": "2026-01-26T12:00:00",
            "is_anchored": true,
            "anchoring_status": "anchored",
            "chain": {
                "schema_version": 1,
                "payload_hash": "0x...",
                "tx_hash": "0x...",
                "network": "ganache",
                "contract_address": "0x...",
                "anchored_at": "2026-01-26T12:05:00",
                "block_number": 123
            }
        }
        
        404: Analysis not found
        429: Rate limited
    """
    # Rate limiting for read operations
    rate_response = _rate_limit_check(request, 'api_read')
    if rate_response:
        return rate_response
    
    try:
        repository = get_analysis_repository()
        use_case = GetAnchoredAnalysisUseCase(repository)
        
        result = use_case.execute(ref_id=ref_id)
        
        return Response(result, status=status.HTTP_200_OK)
        
    except AnalysisNotFoundError as e:
        return Response({
            'error': {
                'code': 'ANALYSIS_NOT_FOUND',
                'message': str(e)
            }
        }, status=status.HTTP_404_NOT_FOUND)
        
    except Exception as e:
        logger.exception(f"Get analysis failed: {e}")
        return Response({
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'An unexpected error occurred'
            }
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@authenticated_required
def list_analyses(request: Request) -> Response:
    """
    List analysis results with optional filtering.
    
    GET /api/blockchain/analyses
    
    Query Parameters:
        anchored_only: If "true", only return anchored analyses (default: false)
        limit: Maximum number of results (default: 50, max: 100)
        
    Returns:
        200: List of analyses
        {
            "analyses": [...],
            "count": 10,
            "total_anchored": 5,
            "filters": {
                "anchored_only": false,
                "limit": 50
            }
        }
        
        429: Rate limited
    """
    # Rate limiting for list operations
    rate_response = _rate_limit_check(request, 'api_read')
    if rate_response:
        return rate_response
    
    # Parse query parameters
    anchored_only = request.query_params.get('anchored_only', '').lower() == 'true'
    
    try:
        limit = int(request.query_params.get('limit', '50'))
        limit = min(max(limit, 1), 100)  # Clamp between 1 and 100
    except ValueError:
        limit = 50
    
    try:
        repository = get_analysis_repository()
        use_case = ListAnalysesUseCase(repository)
        
        result = use_case.execute(anchored_only=anchored_only, limit=limit)
        
        return Response(result, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.exception(f"List analyses failed: {e}")
        return Response({
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'An unexpected error occurred'
            }
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET', 'POST'])
@authenticated_required
def create_analysis(request: Request) -> Response:
    """
    Create a test analysis (for development/testing purposes).
    
    POST /api/blockchain/analyses/create
    
    Request Body:
        {
            "scam_class": 5,          // 0-14 for scam types, -1 for legit
            "scam_type": "Phishing",  // Human-readable name
            "confidence_bps": 8500,   // 0-10000 (85.00%)
            "is_scam": true,
            "analyzer_type": "bert",  // optional, default: "bert"
            "analyzer_version": "v1"  // optional, default: "v1"
        }
        
    Returns:
        201: Created analysis with ref_id
        400: Invalid input
        429: Rate limited
    """
    # Rate limiting
    rate_response = _rate_limit_check(request, 'api_write')
    if rate_response:
        return rate_response
    
    try:
        from ...domain.analysis_entities import AnalysisResult
        
        data = request.data
        
        # Validate required fields
        required_fields = ['scam_class', 'scam_type', 'confidence_bps', 'is_scam']
        missing = [f for f in required_fields if f not in data]
        if missing:
            return Response({
                'error': {
                    'code': 'MISSING_FIELDS',
                    'message': f'Missing required fields: {missing}'
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate scam_class range
        scam_class = data['scam_class']
        if not isinstance(scam_class, int) or (scam_class < -1 or scam_class > 14):
            return Response({
                'error': {
                    'code': 'INVALID_SCAM_CLASS',
                    'message': 'scam_class must be integer between -1 and 14'
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate confidence_bps range
        confidence = data['confidence_bps']
        if not isinstance(confidence, int) or (confidence < 0 or confidence > 10000):
            return Response({
                'error': {
                    'code': 'INVALID_CONFIDENCE',
                    'message': 'confidence_bps must be integer between 0 and 10000'
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create analysis result
        analysis = AnalysisResult.create(
            scam_class=scam_class,
            scam_type=data['scam_type'],
            confidence_bps=confidence,
            is_scam=bool(data['is_scam']),
            analyzer_type=data.get('analyzer_type', 'bert'),
            analyzer_version=data.get('analyzer_version', 'v1')
        )
        
        # Save to database
        repository = get_analysis_repository()
        saved = repository.save(analysis)
        
        logger.info(f"Created test analysis: {saved.ref_id}")
        
        return Response({
            'success': True,
            'ref_id': saved.ref_id,
            'scam_class': saved.scam_class,
            'scam_type': saved.scam_type,
            'confidence_bps': saved.confidence_bps,
            'is_scam': saved.is_scam,
            'created_at': saved.created_at.isoformat() if saved.created_at else None,
            'is_anchored': saved.is_anchored
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.exception(f"Create analysis failed: {e}")
        return Response({
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'An unexpected error occurred'
            }
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def blockchain_status(request: Request) -> Response:
    """
    Get blockchain service status (public endpoint).
    
    GET /api/blockchain/status
    
    Returns:
        200: Status information
        {
            "enabled": true,
            "network": "ganache",
            "contract_address": "0x...",
            "connected": true,
            "record_count": 42
        }
    """
    try:
        from ...infrastructure.blockchain import get_blockchain_service
        
        service = get_blockchain_service()
        
        result = {
            'enabled': service.is_enabled,
            'network': service.network_name if service.is_enabled else None,
            'contract_address': service.contract_address if service.is_enabled else None,
        }
        
        # Only check connection and count if enabled
        if service.is_enabled:
            try:
                service._connect()
                result['connected'] = True
                result['record_count'] = service.get_record_count()
            except Exception as e:
                result['connected'] = False
                result['record_count'] = None
                logger.warning(f"Blockchain connection check failed: {e}")
        else:
            result['connected'] = False
            result['record_count'] = None
        
        return Response(result, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.exception(f"Blockchain status check failed: {e}")
        return Response({
            'enabled': False,
            'connected': False,
            'error': 'Unable to check blockchain status'
        }, status=status.HTTP_200_OK)