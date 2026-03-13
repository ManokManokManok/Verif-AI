/**
 * Shared Date/Time Utilities
 * 
 * Common functions for formatting dates and times across admin pages.
 */

/**
 * Normalise a datetime string from the API to UTC.
 * Python's datetime.utcnow().isoformat() produces strings like "2026-03-12T14:47:57"
 * without a timezone marker. JavaScript's Date constructor treats those as LOCAL time,
 * which shifts the apparent time by the browser's UTC offset.
 * Appending "Z" forces UTC interpretation, matching how the value was originally stored.
 */
function toUtcDate(dateString) {
  if (!dateString) return null;
  // Already has timezone info (ends with Z or contains +/- offset like +00:00)
  if (/Z$/.test(dateString) || /[+-]\d{2}:\d{2}$/.test(dateString)) {
    return new Date(dateString);
  }
  // Naive datetime string — assume UTC
  return new Date(dateString + 'Z');
}

/**
 * Parse a timestamp for relative-time calculations.
 *
 * For legacy records where a local-naive timestamp may have been stored,
 * interpreting as UTC can create future values (e.g. -28800s ago in UTC+8).
 * If a naive timestamp appears too far in the future, retry local parsing.
 */
function parseDateForRelativeTime(dateString) {
  if (!dateString) return null;

  const hasTimezone = /Z$/.test(dateString) || /[+-]\d{2}:\d{2}$/.test(dateString);
  if (hasTimezone) return new Date(dateString);

  const utcInterpreted = toUtcDate(dateString);
  if (!utcInterpreted || Number.isNaN(utcInterpreted.getTime())) {
    return utcInterpreted;
  }

  const fiveMinutesMs = 5 * 60 * 1000;
  if (utcInterpreted.getTime() - Date.now() > fiveMinutesMs) {
    const localInterpreted = new Date(dateString);
    if (!Number.isNaN(localInterpreted.getTime())) {
      return localInterpreted;
    }
  }

  return utcInterpreted;
}

/**
 * Format timestamp as relative time (e.g., "5m ago", "2h ago")
 */
export function formatTimeAgo(timestamp) {
  if (!timestamp) return '';
  
  const date = parseDateForRelativeTime(timestamp);
  if (!date || Number.isNaN(date.getTime())) return '';
  const now = new Date();
  const diffMs = now - date;
  const diffSecs = Math.floor(diffMs / 1000);
  const diffMins = Math.floor(diffSecs / 60);
  const diffHours = Math.floor(diffMins / 60);
  
  if (diffSecs < 0) return 'Just now';
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
  
  const date = parseDateForRelativeTime(dateString);
  if (!date || Number.isNaN(date.getTime())) return '';
  const now = new Date();
  const diffMs = now - date;
  const diffSecs = Math.floor(diffMs / 1000);
  const diffMins = Math.floor(diffSecs / 60);
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffSecs < 0) return 'Just now';
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
  return toUtcDate(dateString).toLocaleDateString(undefined, options);
}

/**
 * Format date and time as localized string
 */
export function formatDateTime(dateString) {
  if (!dateString) return '';
  return toUtcDate(dateString).toLocaleString();
}
