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
        className="admin-btn user-mgmt__action-btn user-mgmt__action-btn--edit"
        onClick={() => onEdit(row)}
        title="Edit user"
      >
        <svg className="user-mgmt__icon" viewBox="0 0 24 24" width="14" height="14" stroke="currentColor" strokeWidth="2.5" fill="none" strokeLinecap="round" strokeLinejoin="round">
          <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
          <path d="M18.5 2.5a2.121 2.121 0 1 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
        </svg>
      </button>
      <button
        className="admin-btn user-mgmt__action-btn user-mgmt__action-btn--password"
        onClick={() => onPassword(row)}
        title="Reset password"
      >
        <svg className="user-mgmt__icon" viewBox="0 0 24 24" width="14" height="14" stroke="currentColor" strokeWidth="2.5" fill="none" strokeLinecap="round" strokeLinejoin="round">
          <path d="M21 2l-2 2m-7.61 7.61a5.5 5.5 0 1 1-7.778 7.778 5.5 5.5 0 0 1 7.777-7.777zm0 0L15.5 7.5m0 0l3 3L22 7l-3-3m-3.5 3.5L19 4" />
        </svg>
      </button>
      <button
        className="admin-btn user-mgmt__action-btn user-mgmt__action-btn--delete"
        onClick={() => onDelete(row)}
        title="Delete user"
        disabled={row.roles?.includes('admin')}
      >
        <svg className="user-mgmt__icon" viewBox="0 0 24 24" width="14" height="14" stroke="currentColor" strokeWidth="2.5" fill="none" strokeLinecap="round" strokeLinejoin="round">
          <polyline points="3 6 5 6 21 6" />
          <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
          <line x1="10" y1="11" x2="10" y2="17" />
          <line x1="14" y1="11" x2="14" y2="17" />
        </svg>
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
