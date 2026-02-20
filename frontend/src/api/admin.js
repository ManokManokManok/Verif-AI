/**
 * Admin API Client
 * 
 * API functions for admin dashboard features including:
 * - Model health monitoring
 * - Analysis statistics
 * - User statistics
 * - User reports management
 * - User management
 */

import { authApiRequest } from './client';

// ==================== Model Health ====================

/**
 * Get current model health metrics (GPU, CPU, Memory, etc.)
 * @returns {Promise<Object>} Model health data
 */
export async function getModelHealth() {
  return authApiRequest('/admin/model-health/', {
    method: 'GET',
  });
}

/**
 * Get model health summary with status indicators
 * @returns {Promise<Object>} Health summary
 */
export async function getModelHealthSummary() {
  return authApiRequest('/admin/model-health/summary/', {
    method: 'GET',
  });
}

// ==================== Analysis Statistics ====================

/**
 * Get analysis statistics
 * @param {Object} params - Query parameters
 * @param {string} params.startDate - Start date (YYYY-MM-DD)
 * @param {string} params.endDate - End date (YYYY-MM-DD)
 * @param {string} params.period - Period grouping (day|week|month|year|all_time)
 * @returns {Promise<Object>} Analysis statistics
 */
export async function getAnalysisStats({ startDate, endDate, period } = {}) {
  const params = new URLSearchParams();
  if (startDate) params.append('start_date', startDate);
  if (endDate) params.append('end_date', endDate);
  if (period) params.append('period', period);
  
  const queryString = params.toString();
  const url = `/admin/analysis-stats/${queryString ? `?${queryString}` : ''}`;
  
  return authApiRequest(url, {
    method: 'GET',
  });
}

/**
 * Get top scam categories
 * @param {Object} params - Query parameters
 * @param {string} params.startDate - Start date
 * @param {string} params.endDate - End date
 * @param {number} params.limit - Max categories to return (default 10)
 * @returns {Promise<Object>} Top categories data
 */
export async function getTopScamCategories({ startDate, endDate, limit = 10 } = {}) {
  const params = new URLSearchParams();
  if (startDate) params.append('start_date', startDate);
  if (endDate) params.append('end_date', endDate);
  if (limit) params.append('limit', limit.toString());
  
  const queryString = params.toString();
  const url = `/admin/analysis-stats/top-categories/${queryString ? `?${queryString}` : ''}`;
  
  return authApiRequest(url, {
    method: 'GET',
  });
}

// ==================== User Statistics ====================

/**
 * Get user statistics
 * @param {Object} params - Query parameters
 * @param {string} params.startDate - Start date
 * @param {string} params.endDate - End date
 * @param {string} params.period - Period grouping
 * @returns {Promise<Object>} User statistics
 */
export async function getUserStats({ startDate, endDate, period } = {}) {
  const params = new URLSearchParams();
  if (startDate) params.append('start_date', startDate);
  if (endDate) params.append('end_date', endDate);
  if (period) params.append('period', period);
  
  const queryString = params.toString();
  const url = `/admin/user-stats/${queryString ? `?${queryString}` : ''}`;
  
  return authApiRequest(url, {
    method: 'GET',
  });
}

// ==================== User Reports ====================

/**
 * Get user reports with optional filtering
 * @param {Object} params - Query parameters
 * @param {string} params.status - Filter by status (pending|in_progress|resolved|dismissed)
 * @param {number} params.page - Page number (default 1)
 * @param {number} params.limit - Results per page (default 50)
 * @returns {Promise<Object>} Reports list with pagination
 */
export async function getUserReports({ status, page = 1, limit = 50 } = {}) {
  const params = new URLSearchParams();
  if (status) params.append('status', status);
  params.append('page', page.toString());
  params.append('limit', limit.toString());
  
  const queryString = params.toString();
  const url = `/admin/reports/?${queryString}`;
  
  return authApiRequest(url, {
    method: 'GET',
  });
}

/**
 * Get detailed information for a specific report
 * @param {string} reportId - Report ID
 * @returns {Promise<Object>} Report details
 */
export async function getReportDetails(reportId) {
  return authApiRequest(`/admin/reports/${reportId}/detail/`, {
    method: 'GET',
  });
}

/**
 * Update a report's status
 * @param {string} reportId - Report ID
 * @param {Object} data - Update data
 * @param {string} data.status - New status (pending|in_progress|resolved|dismissed)
 * @param {string} data.resolutionNotes - Optional resolution notes
 * @returns {Promise<Object>} Updated report
 */
export async function updateReportStatus(reportId, { status, resolutionNotes }) {
  const body = { status };
  if (resolutionNotes) body.resolution_notes = resolutionNotes;
  
  return authApiRequest(`/admin/reports/${reportId}/`, {
    method: 'PATCH',
    body: JSON.stringify(body),
  });
}

// ==================== User Management ====================

/**
 * Get paginated list of users
 * @param {Object} params - Query parameters
 * @param {string} params.search - Search by email or username
 * @param {string} params.role - Filter by role
 * @param {boolean} params.isActive - Filter by active status
 * @param {boolean} params.isVerified - Filter by verification status
 * @param {number} params.page - Page number (default 1)
 * @param {number} params.limit - Results per page (default 50)
 * @param {string} params.sortBy - Sort field (default 'created_at')
 * @param {string} params.sortOrder - Sort direction (asc|desc)
 * @returns {Promise<Object>} Users list with pagination
 */
export async function getUsers({ 
  search, 
  role, 
  isActive, 
  isVerified, 
  page = 1, 
  limit = 50,
  sortBy = 'created_at',
  sortOrder = 'desc'
} = {}) {
  const params = new URLSearchParams();
  if (search) params.append('search', search);
  if (role) params.append('role', role);
  if (isActive !== undefined) params.append('is_active', isActive.toString());
  if (isVerified !== undefined) params.append('is_verified', isVerified.toString());
  params.append('page', page.toString());
  params.append('limit', limit.toString());
  params.append('sort_by', sortBy);
  params.append('sort_order', sortOrder);
  
  const queryString = params.toString();
  const url = `/admin/users/?${queryString}`;
  
  return authApiRequest(url, {
    method: 'GET',
  });
}

/**
 * Get single user details
 * @param {string} userId - User ID
 * @returns {Promise<Object>} User details
 */
export async function getUser(userId) {
  return authApiRequest(`/admin/users/${userId}/`, {
    method: 'GET',
  });
}

/**
 * Delete a user account
 * @param {string} userId - User ID
 * @param {boolean} hardDelete - If true, permanently delete
 * @returns {Promise<Object>} Deletion result
 */
export async function deleteUser(userId, hardDelete = false) {
  const params = hardDelete ? '?hard_delete=true' : '';
  return authApiRequest(`/admin/users/${userId}/delete/${params}`, {
    method: 'DELETE',
  });
}

/**
 * Admin reset user's password
 * @param {string} userId - User ID
 * @param {string} newPassword - New password
 * @returns {Promise<Object>} Reset result
 */
export async function resetUserPassword(userId, newPassword) {
  return authApiRequest(`/admin/users/${userId}/reset-password/`, {
    method: 'POST',
    body: JSON.stringify({ new_password: newPassword }),
  });
}

/**
 * Update user account status
 * @param {string} userId - User ID
 * @param {string} newStatus - New status ('active', 'inactive', 'suspended')
 * @returns {Promise<Object>} Update result
 */
export async function updateUserStatus(userId, newStatus) {
  return authApiRequest(`/admin/users/${userId}/status/`, {
    method: 'PATCH',
    body: JSON.stringify({ status: newStatus.toLowerCase() }),
  });
}

/**
 * Update a user's roles
 * @param {string} userId - User ID
 * @param {string[]} roles - Array of role names
 * @returns {Promise<Object>} Update result
 */
export async function updateUserRoles(userId, roles) {
  return authApiRequest(`/admin/users/${userId}/roles/`, {
    method: 'PATCH',
    body: JSON.stringify({ roles }),
  });
}
