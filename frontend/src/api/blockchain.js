/**
 * Blockchain API Client
 * 
 * Provides functions for blockchain verification operations.
 */

const API_BASE =
  import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, '') ||
  'http://localhost:8000/api';

/**
 * Get auth headers with access token
 */
function getAuthHeaders() {
  const token = window.localStorage.getItem('access_token');
  return token ? { Authorization: `Bearer ${token}` } : {};
}

/**
 * Make an authenticated API request
 */
async function apiRequest(path, options = {}) {
  const url = `${API_BASE}${path.startsWith('/') ? path : `/${path}`}`;

  const headers = {
    'Content-Type': 'application/json',
    ...getAuthHeaders(),
    ...(options.headers || {}),
  };

  const response = await fetch(url, {
    ...options,
    headers,
  });

  const isJson = response.headers
    .get('content-type')
    ?.includes('application/json');
  const data = isJson ? await response.json() : null;

  if (!response.ok) {
    const message =
      data?.error?.message ||
      data?.message ||
      data?.detail ||
      `Request failed with status ${response.status}`;
    const error = new Error(message);
    error.status = response.status;
    error.payload = data;
    throw error;
  }

  return data;
}

/**
 * Get blockchain connection status (public endpoint)
 * @returns {Promise<{connected: boolean, network: string, chainId: number, blockNumber: number, contractAddress: string}>}
 */
export async function getBlockchainStatus() {
  return apiRequest('/blockchain/status/');
}

/**
 * List all analyses with blockchain info
 * @param {Object} params - Query parameters
 * @param {number} params.page - Page number (default: 1)
 * @param {number} params.limit - Items per page (default: 20)
 * @param {string} params.status - Filter by status: 'anchored', 'pending', 'all'
 * @returns {Promise<{analyses: Array, total: number, page: number, limit: number}>}
 */
export async function listAnalyses({ page = 1, limit = 20, status = 'all' } = {}) {
  const params = new URLSearchParams({
    page: String(page),
    limit: String(limit),
    ...(status !== 'all' && { status }),
  });
  return apiRequest(`/blockchain/analyses/?${params}`);
}

/**
 * Get a specific analysis by reference ID
 * @param {string} refId - Analysis reference ID (UUID)
 * @returns {Promise<Object>} Analysis details with blockchain info
 */
export async function getAnalysis(refId) {
  return apiRequest(`/blockchain/analysis/${refId}/`);
}

/**
 * Anchor an analysis to the blockchain (admin only)
 * @param {string} refId - Analysis reference ID (UUID)
 * @param {boolean} force - Force re-anchor if already anchored
 * @returns {Promise<{success: boolean, txHash: string, blockNumber: number}>}
 */
export async function anchorAnalysis(refId, force = false) {
  const params = force ? '?force=true' : '';
  return apiRequest(`/blockchain/analysis/${refId}/anchor/${params}`, {
    method: 'POST',
  });
}

/**
 * Verify an analysis integrity against blockchain
 * @param {string} refId - Analysis reference ID (UUID)
 * @returns {Promise<{verified: boolean, status: string, details: Object}>}
 */
export async function verifyAnalysis(refId) {
  const response = await apiRequest(`/blockchain/analysis/${refId}/verify/`);
  
  // Transform response to include status field
  let status = 'NOT_ANCHORED';
  if (response.verified === true) {
    status = 'VERIFIED';
  } else if (response.verified === false) {
    status = 'NOT_VERIFIED';
  }
  
  return {
    ...response,
    status,
  };
}
