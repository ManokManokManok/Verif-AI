/**
 * UserStats Utility Functions
 */

export { formatRole } from '../shared/utils';

/**
 * Calculate percentage and return as string
 */
export function getPercentage(value, total) {
  if (!total || total === 0) return '0';
  return ((value || 0) / total * 100).toFixed(1);
}

/**
 * Get color for user role
 */
export function getRoleColor(role) {
  const colors = {
    admin: 'var(--admin-danger)',
    moderator: 'var(--admin-warning)',
    analyst: 'var(--admin-info)',
    premium_user: 'var(--admin-primary)',
    user: 'var(--admin-success)',
  };
  return colors[role] || 'var(--admin-text-muted)';
}
