/**
 * Analytics API Client
 * 
 * Functions for fetching website analytics data from the backend.
 * Requires admin role for all operations.
 */

import apiClient from './client';

/**
 * Get overall visit statistics
 * @param {Object} params - Query parameters
 * @param {string} [params.startDate] - Start date (ISO format)
 * @param {string} [params.endDate] - End date (ISO format)
 * @returns {Promise<Object>} Visit statistics
 */
export const getVisitStatistics = async (params = {}) => {
  const queryParams = new URLSearchParams();
  if (params.startDate) queryParams.append('start_date', params.startDate);
  if (params.endDate) queryParams.append('end_date', params.endDate);
  
  const queryString = queryParams.toString();
  const url = `/analytics/visits/${queryString ? `?${queryString}` : ''}`;
  
  const response = await apiClient.get(url);
  return response.data;
};

/**
 * Get page analytics (visits by path)
 * @param {Object} params - Query parameters
 * @param {string} [params.startDate] - Start date (ISO format)
 * @param {string} [params.endDate] - End date (ISO format)
 * @param {number} [params.limit=10] - Maximum pages to return
 * @returns {Promise<Array>} Page visit statistics
 */
export const getPageAnalytics = async (params = {}) => {
  const queryParams = new URLSearchParams();
  if (params.startDate) queryParams.append('start_date', params.startDate);
  if (params.endDate) queryParams.append('end_date', params.endDate);
  if (params.limit) queryParams.append('limit', params.limit.toString());
  
  const queryString = queryParams.toString();
  const url = `/analytics/pages/${queryString ? `?${queryString}` : ''}`;
  
  const response = await apiClient.get(url);
  return response.data;
};

/**
 * Get device breakdown (desktop, mobile, tablet)
 * @param {Object} params - Query parameters
 * @param {string} [params.startDate] - Start date (ISO format)
 * @param {string} [params.endDate] - End date (ISO format)
 * @returns {Promise<Object>} Device breakdown statistics
 */
export const getDeviceBreakdown = async (params = {}) => {
  const queryParams = new URLSearchParams();
  if (params.startDate) queryParams.append('start_date', params.startDate);
  if (params.endDate) queryParams.append('end_date', params.endDate);
  
  const queryString = queryParams.toString();
  const url = `/analytics/devices/${queryString ? `?${queryString}` : ''}`;
  
  const response = await apiClient.get(url);
  return response.data;
};

/**
 * Get visits time series data for graphing
 * @param {Object} params - Query parameters
 * @param {string} params.startDate - Start date (ISO format)
 * @param {string} params.endDate - End date (ISO format)
 * @param {string} [params.granularity='day'] - 'hour', 'day', 'week', 'month'
 * @returns {Promise<Array>} Time series data points
 */
export const getVisitsTimeSeries = async (params = {}) => {
  const queryParams = new URLSearchParams();
  if (params.startDate) queryParams.append('start_date', params.startDate);
  if (params.endDate) queryParams.append('end_date', params.endDate);
  if (params.granularity) queryParams.append('granularity', params.granularity);
  
  const queryString = queryParams.toString();
  const url = `/analytics/time-series/${queryString ? `?${queryString}` : ''}`;
  
  const response = await apiClient.get(url);
  return response.data;
};

/**
 * Get hourly traffic pattern
 * @param {Object} params - Query parameters
 * @param {string} [params.startDate] - Start date (ISO format)
 * @param {string} [params.endDate] - End date (ISO format)
 * @returns {Promise<Object>} Hourly traffic pattern (hour -> count)
 */
export const getHourlyPattern = async (params = {}) => {
  const queryParams = new URLSearchParams();
  if (params.startDate) queryParams.append('start_date', params.startDate);
  if (params.endDate) queryParams.append('end_date', params.endDate);
  
  const queryString = queryParams.toString();
  const url = `/analytics/hourly/${queryString ? `?${queryString}` : ''}`;
  
  const response = await apiClient.get(url);
  return response.data;
};

/**
 * Get top referrers
 * @param {Object} params - Query parameters
 * @param {string} [params.startDate] - Start date (ISO format)
 * @param {string} [params.endDate] - End date (ISO format)
 * @param {number} [params.limit=10] - Maximum referrers to return
 * @returns {Promise<Array>} Referrer statistics
 */
export const getReferrerStats = async (params = {}) => {
  const queryParams = new URLSearchParams();
  if (params.startDate) queryParams.append('start_date', params.startDate);
  if (params.endDate) queryParams.append('end_date', params.endDate);
  if (params.limit) queryParams.append('limit', params.limit.toString());
  
  const queryString = queryParams.toString();
  const url = `/analytics/referrers/${queryString ? `?${queryString}` : ''}`;
  
  const response = await apiClient.get(url);
  return response.data;
};

/**
 * Get recent visits for live monitoring
 * @param {Object} params - Query parameters
 * @param {number} [params.limit=50] - Maximum visits to return
 * @param {string} [params.path] - Optional path filter
 * @returns {Promise<Array>} Recent visit records
 */
export const getRecentVisits = async (params = {}) => {
  const queryParams = new URLSearchParams();
  if (params.limit) queryParams.append('limit', params.limit.toString());
  if (params.path) queryParams.append('path', params.path);
  
  const queryString = queryParams.toString();
  const url = `/analytics/recent/${queryString ? `?${queryString}` : ''}`;
  
  const response = await apiClient.get(url);
  return response.data;
};

/**
 * Get comprehensive analytics summary for dashboard
 * @param {Object} params - Query parameters
 * @param {string} [params.period='week'] - 'today', 'week', 'month', 'year'
 * @returns {Promise<Object>} Analytics summary with visits, devices, top pages
 */
export const getAnalyticsSummary = async (params = {}) => {
  const queryParams = new URLSearchParams();
  if (params.period) queryParams.append('period', params.period);
  
  const queryString = queryParams.toString();
  const url = `/analytics/summary/${queryString ? `?${queryString}` : ''}`;
  
  const response = await apiClient.get(url);
  return response.data;
};

// Export all functions as default object as well
export default {
  getVisitStatistics,
  getPageAnalytics,
  getDeviceBreakdown,
  getVisitsTimeSeries,
  getHourlyPattern,
  getReferrerStats,
  getRecentVisits,
  getAnalyticsSummary,
};
