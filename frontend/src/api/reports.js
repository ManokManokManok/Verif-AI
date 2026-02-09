/**
 * Reports API Client
 * 
 * API functions for user report submission and management.
 * These endpoints are available to all authenticated users (not just admins).
 */

import { authApiRequest } from './client';

// API base URL
const API_BASE =
  import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, '') ||
  'http://localhost:8000/api';

/**
 * Report types enum for consistency
 */
export const REPORT_TYPES = {
  HALLUCINATION: 'hallucination',
  FALSE_POSITIVE: 'false_positive',
  FALSE_NEGATIVE: 'false_negative',
  BUG: 'bug',
  FEEDBACK: 'feedback',
  OTHER: 'other',
};

/**
 * Report status enum
 */
export const REPORT_STATUS = {
  PENDING: 'pending',
  IN_PROGRESS: 'in_progress',
  RESOLVED: 'resolved',
  DISMISSED: 'dismissed',
};

/**
 * Get available report types with descriptions
 * This endpoint is public (no auth required)
 * 
 * @returns {Promise<Object>} List of report types
 */
export async function getReportTypes() {
  const response = await fetch(`${API_BASE}/reports/types/`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
  });
  
  const data = await response.json();
  
  if (!response.ok) {
    throw new Error(data.error || 'Failed to fetch report types');
  }
  
  return data;
}

/**
 * Submit a new user report
 * Requires authentication
 * 
 * @param {Object} reportData - Report data
 * @param {string} reportData.report_type - Type of report (see REPORT_TYPES)
 * @param {string} reportData.title - Report title (min 3 characters)
 * @param {string} reportData.description - Detailed description (min 10 characters)
 * @param {string} [reportData.analysis_id] - Optional analysis ID
 * @param {string} [reportData.analysis_ref_id] - Optional analysis reference ID
 * @returns {Promise<Object>} Created report data
 */
export async function submitReport(reportData) {
  return authApiRequest('/reports/', {
    method: 'POST',
    body: JSON.stringify(reportData),
  });
}

/**
 * Get current user's reports
 * Requires authentication
 * 
 * @param {Object} params - Query parameters
 * @param {string} [params.status] - Filter by status
 * @param {number} [params.page] - Page number (default 1)
 * @param {number} [params.limit] - Items per page (default 20, max 50)
 * @returns {Promise<Object>} Paginated list of user's reports
 */
export async function getMyReports({ status, page = 1, limit = 20 } = {}) {
  const params = new URLSearchParams();
  if (status) params.append('status', status);
  if (page) params.append('page', page.toString());
  if (limit) params.append('limit', limit.toString());
  
  const queryString = params.toString();
  const url = `/reports/my/${queryString ? `?${queryString}` : ''}`;
  
  return authApiRequest(url, {
    method: 'GET',
  });
}

/**
 * Get human-readable label for report type
 * 
 * @param {string} reportType - Report type value
 * @returns {string} Human-readable label
 */
export function getReportTypeLabel(reportType) {
  const labels = {
    [REPORT_TYPES.HALLUCINATION]: 'AI Hallucination',
    [REPORT_TYPES.FALSE_POSITIVE]: 'False Positive',
    [REPORT_TYPES.FALSE_NEGATIVE]: 'False Negative',
    [REPORT_TYPES.BUG]: 'Bug Report',
    [REPORT_TYPES.FEEDBACK]: 'Feedback',
    [REPORT_TYPES.OTHER]: 'Other',
  };
  return labels[reportType] || reportType;
}

/**
 * Get human-readable label for report status
 * 
 * @param {string} status - Report status value
 * @returns {string} Human-readable label
 */
export function getReportStatusLabel(status) {
  const labels = {
    [REPORT_STATUS.PENDING]: 'Pending',
    [REPORT_STATUS.IN_PROGRESS]: 'In Progress',
    [REPORT_STATUS.RESOLVED]: 'Resolved',
    [REPORT_STATUS.DISMISSED]: 'Dismissed',
  };
  return labels[status] || status;
}
