import { httpClient } from './HttpClient';
import type {
  BlockchainStatus,
  AnalysisBlockchainInfo,
  VerificationResult,
  AnchorResult,
  AnalysesListResponse,
  BlockchainAnalysisItem,
} from '../../domain/types/blockchain';

/**
 * Transform snake_case backend response to camelCase frontend types
 */
function transformAnalysisItem(item: any): BlockchainAnalysisItem {
  return {
    refId: item.ref_id,
    createdAt: item.created_at,
    isAnchored: item.is_anchored,
    payloadHash: item.chain?.payload_hash,
    txHash: item.chain?.tx_hash,
    anchoredAt: item.chain?.anchored_at,
  };
}

/**
 * API service for blockchain verification endpoints
 * Handles communication with /api/blockchain/* endpoints
 */
export class BlockchainApi {
  private client = httpClient.getInstance();

  /**
   * Get blockchain connection status (public endpoint)
   */
  async getStatus(): Promise<BlockchainStatus> {
    const response = await this.client.get<BlockchainStatus>('/blockchain/status/');
    return response.data;
  }

  /**
   * List all analyses with blockchain info (authenticated)
   */
  async listAnalyses(page: number = 1, pageSize: number = 20): Promise<AnalysesListResponse> {
    const response = await this.client.get<any>('/blockchain/analyses/', {
      params: { limit: pageSize }
    });
    
    // Transform snake_case response to camelCase
    const analyses = (response.data.analyses || []).map(transformAnalysisItem);
    
    return {
      analyses,
      total: response.data.count || analyses.length,
      page,
      pageSize,
      hasMore: analyses.length >= pageSize,
    };
  }

  /**
   * Get blockchain info for a specific analysis (authenticated)
   */
  async getAnalysis(refId: string): Promise<AnalysisBlockchainInfo> {
    const response = await this.client.get<AnalysisBlockchainInfo>(`/blockchain/analysis/${refId}/`);
    return response.data;
  }

  /**
   * Anchor an analysis to the blockchain (admin only)
   * @param refId - Analysis reference ID
   * @param force - If true, re-anchor even if already anchored
   */
  async anchorAnalysis(refId: string, force: boolean = false): Promise<AnchorResult> {
    const url = force 
      ? `/blockchain/analysis/${refId}/anchor/?force=true`
      : `/blockchain/analysis/${refId}/anchor/`;
    const response = await this.client.post<AnchorResult>(url);
    return response.data;
  }

  /**
   * Verify an analysis against blockchain (authenticated)
   */
  async verifyAnalysis(refId: string): Promise<VerificationResult> {
    const response = await this.client.get<any>(`/blockchain/analysis/${refId}/verify/`);
    const data = response.data;
    
    // Transform backend response to frontend format
    // Backend returns: verified, is_anchored, payload_hash, etc.
    // Frontend expects: status field
    let status: 'VERIFIED' | 'NOT_VERIFIED' | 'NOT_ANCHORED' | 'ERROR';
    
    if (!data.is_anchored) {
      status = 'NOT_ANCHORED';
    } else if (data.verified) {
      status = 'VERIFIED';
    } else {
      status = 'NOT_VERIFIED';
    }
    
    return {
      verified: data.verified,
      status,
      refId: data.ref_id || refId,
      payloadHash: data.payload_hash,
      message: data.reason,
      error: data.mismatches?.join(', '),
    };
  }
}

// Export singleton instance
export const blockchainApi = new BlockchainApi();
