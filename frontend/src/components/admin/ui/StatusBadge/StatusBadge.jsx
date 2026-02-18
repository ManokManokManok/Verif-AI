/**
 * StatusBadge Component
 * 
 * Displays status with colored badge.
 */

import React from 'react';
import PropTypes from 'prop-types';
import './StatusBadge.css';

export default function StatusBadge({ status, variant, className = '' }) {
  const statusConfig = {
    pending: { label: 'Pending', variant: 'warning' },
    in_progress: { label: 'In Progress', variant: 'info' },
    resolved: { label: 'Resolved', variant: 'success' },
    dismissed: { label: 'Dismissed', variant: 'default' },
    active: { label: 'Active', variant: 'success' },
    inactive: { label: 'Inactive', variant: 'danger' },
    verified: { label: 'Verified', variant: 'success' },
    unverified: { label: 'Unverified', variant: 'warning' },
  };

  const config = statusConfig[status] || { label: status, variant: variant || 'default' };
  const badgeVariant = variant || config.variant;

  return (
    <span className={`status-badge status-badge--${badgeVariant} ${className}`}>
      {config.label}
    </span>
  );
}

StatusBadge.propTypes = {
  status: PropTypes.string.isRequired,
  variant: PropTypes.oneOf(['default', 'success', 'warning', 'danger', 'info']),
  className: PropTypes.string,
};
