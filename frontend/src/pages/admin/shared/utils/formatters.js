/**
 * Shared String Formatting Utilities
 * 
 * Common functions for formatting strings across admin pages.
 */

/**
 * Format snake_case or kebab-case to Title Case
 */
export function formatRole(role) {
  if (!role) return '';
  return role.split(/[_-]/).map(word => 
    word.charAt(0).toUpperCase() + word.slice(1).toLowerCase()
  ).join(' ');
}

/**
 * Truncate text with ellipsis
 */
export function truncate(text, maxLength = 50) {
  if (!text || text.length <= maxLength) return text;
  return text.substring(0, maxLength) + '...';
}

/**
 * Format bytes to human-readable size
 */
export function formatBytes(bytes, decimals = 2) {
  if (!bytes || bytes === 0) return '0 Bytes';
  
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(decimals)) + ' ' + sizes[i];
}

/**
 * Format number with locale-specific thousands separator
 */
export function formatNumber(num, decimals = 0) {
  if (num == null) return '0';
  return Number(num).toLocaleString(undefined, {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
}

/**
 * Format percentage
 */
export function formatPercentage(value, total, decimals = 1) {
  if (!total || total === 0) return '0%';
  const percentage = (value / total) * 100;
  return `${percentage.toFixed(decimals)}%`;
}

/**
 * Calculate percentage (returns number, not string)
 */
export function getPercentage(value, total) {
  if (!total || total === 0) return 0;
  return ((value || 0) / total) * 100;
}

/**
 * Calculate trend between current and previous values
 */
export function getTrend(current, previous) {
  if (!previous || previous === 0) return { direction: 'stable', value: '0%' };
  const change = ((current - previous) / previous) * 100;
  if (change > 0) return { direction: 'up', value: `+${change.toFixed(1)}%` };
  if (change < 0) return { direction: 'down', value: `${change.toFixed(1)}%` };
  return { direction: 'stable', value: '0%' };
}
