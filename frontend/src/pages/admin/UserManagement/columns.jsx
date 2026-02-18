/**
 * UserManagement Table Column Definitions
 */

import React from 'react';
import { StatusBadge } from '../../../components/admin';
import { formatRelativeTime } from '../shared/utils';

/**
 * User cell renderer with avatar and info
 */
export function renderUserCell(value, row) {
  return (
    <div className="user-mgmt__user-cell">
      <div className="user-mgmt__avatar">
        {value?.charAt(0)?.toUpperCase() || '?'}
      </div>
      <div className="user-mgmt__user-info">
        <span className="user-mgmt__username">{value}</span>
        <span className="user-mgmt__email">{row.email}</span>
      </div>
    </div>
  );
}

/**
 * Roles cell renderer with badges
 */
export function renderRolesCell(value) {
  return (
    <div className="user-mgmt__roles">
      {(value || ['user']).map(role => (
        <StatusBadge 
          key={role} 
          status={role}
          variant={role === 'admin' ? 'danger' : role === 'moderator' ? 'warning' : 'default'}
        />
      ))}
    </div>
  );
}

/**
 * Status cell renderer
 */
export function renderStatusCell(value) {
  return (
    <StatusBadge 
      status={value || 'active'} 
      variant={value === 'active' ? 'success' : 'danger'}
    />
  );
}

/**
 * Verified cell renderer
 */
export function renderVerifiedCell(value) {
  return (
    <span className={`user-mgmt__verified ${value ? 'user-mgmt__verified--yes' : ''}`}>
      {value ? 'Verified' : 'Not Verified'}
    </span>
  );
}

/**
 * Actions cell renderer with edit, password, delete buttons
 */
export function renderActionsCell(_, row, { onEdit, onPassword, onDelete }) {
  return (
    <div className="user-mgmt__actions">
      <button
        className="admin-btn admin-btn--sm admin-btn--ghost"
        onClick={() => onEdit(row)}
        title="Edit user"
      >
        ✏️
      </button>
      <button
        className="admin-btn admin-btn--sm admin-btn--ghost"
        onClick={() => onPassword(row)}
        title="Reset password"
      >
        🔑
      </button>
      <button
        className="admin-btn admin-btn--sm admin-btn--ghost"
        onClick={() => onDelete(row)}
        title="Delete user"
        disabled={row.roles?.includes('admin')}
      >
        🗑️
      </button>
    </div>
  );
}

/**
 * Get user table columns configuration
 */
export function getUserTableColumns(handlers) {
  return [
    {
      key: 'username',
      label: 'User',
      render: renderUserCell,
    },
    {
      key: 'roles',
      label: 'Roles',
      render: renderRolesCell,
    },
    {
      key: 'status',
      label: 'Status',
      render: renderStatusCell,
    },
    {
      key: 'is_verified',
      label: 'Verified',
      render: renderVerifiedCell,
    },
    {
      key: 'analysis_count',
      label: 'Analyses',
      render: (value) => value?.toLocaleString() || '0',
    },
    {
      key: 'created_at',
      label: 'Joined',
      render: (value) => value ? new Date(value).toLocaleDateString() : 'N/A',
    },
    {
      key: 'last_login',
      label: 'Last Login',
      render: (value) => value ? formatRelativeTime(value) : 'Never',
    },
    {
      key: 'actions',
      label: 'Actions',
      render: (value, row) => renderActionsCell(value, row, handlers),
    },
  ];
}
