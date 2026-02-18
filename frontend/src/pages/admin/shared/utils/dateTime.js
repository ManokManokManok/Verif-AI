/**
 * Shared Date/Time Utilities
 * 
 * Common functions for formatting dates and times across admin pages.
 */

/**
 * Format timestamp as relative time (e.g., "5m ago", "2h ago")
 */
export function formatTimeAgo(timestamp) {
  if (!timestamp) return '';
  
  const date = new Date(timestamp);
  const now = new Date();
  const diffMs = now - date;
  const diffSecs = Math.floor(diffMs / 1000);
  const diffMins = Math.floor(diffSecs / 60);
  const diffHours = Math.floor(diffMins / 60);
  
  if (diffSecs < 60) return `${diffSecs}s ago`;
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  return date.toLocaleDateString();
}

/**
 * Format timestamp as relative time with more detail
 */
export function formatRelativeTime(dateString) {
  if (!dateString) return '';
  
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now - date;
  const diffSecs = Math.floor(diffMs / 1000);
  const diffMins = Math.floor(diffSecs / 60);
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffDays > 30) return date.toLocaleDateString();
  if (diffDays > 0) return `${diffDays}d ago`;
  if (diffHours > 0) return `${diffHours}h ago`;
  if (diffMins > 0) return `${diffMins}m ago`;
  return 'Just now';
}

/**
 * Format date as localized string
 */
export function formatDate(dateString, options = {}) {
  if (!dateString) return '';
  return new Date(dateString).toLocaleDateString(undefined, options);
}

/**
 * Format date and time as localized string
 */
export function formatDateTime(dateString) {
  if (!dateString) return '';
  return new Date(dateString).toLocaleString();
}
