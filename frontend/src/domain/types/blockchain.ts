/**
 * Blockchain domain types
 * Types for blockchain verification and anchoring
 */

/**
 * Verification status enum
 */
export type VerificationStatus = 'VERIFIED' | 'NOT_VERIFIED' | 'NOT_ANCHORED' | 'ERROR';

/**
 * Blockchain connection status
 */
export interface BlockchainStatus {
  connected: boolean;
  network: string;
  contractAddress: string;
  blockNumber?: number;
  error?: string;
}

/**
 * Analysis blockchain metadata
 */
export interface AnalysisBlockchainInfo {
  refId: string;
  isAnchored: boolean;
  payloadHash?: string;
  txHash?: string;
  blockNumber?: number;
  anchoredAt?: string;
  schemaVersion?: string;
  networkName?: string;
  contractAddress?: string;
}

/**
 * Verification result from backend
 */
export interface VerificationResult {
  verified: boolean;
  status: VerificationStatus;
  refId: string;
  payloadHash?: string;
  txHash?: string;
  blockNumber?: number;
  schemaVersion?: string;
  timestamp?: number;
  message?: string;
  error?: string;
}

/**
 * Anchor result from backend
 */
export interface AnchorResult {
  success: boolean;
  refId: string;
  payloadHash: string;
  txHash: string;
  blockNumber: number;
  schemaVersion: string;
  anchoredAt: string;
  message?: string;
  error?: string;
}

/**
 * Analysis list item for blockchain page
 */
export interface BlockchainAnalysisItem {
  refId: string;
  createdAt: string;
  isAnchored: boolean;
  payloadHash?: string;
  txHash?: string;
  anchoredAt?: string;
}

/**
 * Paginated analyses response
 */
export interface AnalysesListResponse {
  analyses: BlockchainAnalysisItem[];
  total: number;
  page: number;
  pageSize: number;
  hasMore: boolean;
}
