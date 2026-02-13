/**
 * User Management Tab
 * 
 * Admin interface for managing users: view, edit, delete, role management.
 */

import React, { useState, useEffect } from 'react';
import PropTypes from 'prop-types';
import { 
  DataTable,
  StatusBadge,
  SearchInput,
  LoadingSpinner, 
  ErrorMessage,
  ConfirmModal,
  Alert,
} from '../../components/admin';
import { useUsers, useUserDetails } from '../../hooks/useAdminData';

const AVAILABLE_ROLES = ['admin', 'moderator', 'analyst', 'premium_user', 'user'];

export default function UserManagement({ onNotify }) {
  const [search, setSearch] = useState('');
  const [filters, setFilters] = useState({
    status: '',
    role: '',
    verified: '',
  });
  const [pagination, setPagination] = useState({ page: 1, limit: 10 });
  const [selectedUser, setSelectedUser] = useState(null);
  const [modalState, setModalState] = useState({ type: null, isOpen: false });
  const [editForm, setEditForm] = useState({ roles: [], status: '' });
  const [newPassword, setNewPassword] = useState('');

  const {
    data,
    loading,
    error,
    refresh,
    deleteUser,
    resetPassword,
    updateStatus,
    updateRoles,
  } = useUsers({ ...filters, search }, pagination);

  // Update edit form when selecting a user
  useEffect(() => {
    if (selectedUser) {
      setEditForm({
        roles: selectedUser.roles || ['user'],
        status: selectedUser.status || 'active',
      });
    }
  }, [selectedUser]);

  // Handle modal open
  const openModal = (type, user = null) => {
    setSelectedUser(user);
    setModalState({ type, isOpen: true });
  };

  // Handle modal close
  const closeModal = () => {
    setModalState({ type: null, isOpen: false });
    setSelectedUser(null);
    setEditForm({ roles: [], status: '' });
    setNewPassword('');
  };

  // Handle user deletion
  const handleDeleteUser = async () => {
    if (!selectedUser) return;
    const result = await deleteUser(selectedUser.id);
    if (result.success) {
      onNotify?.('success', `User "${selectedUser.username}" has been deleted`);
      closeModal();
    } else {
      onNotify?.('error', `Failed to delete user: ${result.error || 'Unknown error'}`);
    }
  };

  // Handle password reset
  const handleResetPassword = async () => {
    if (!selectedUser) return;
    if (!newPassword || newPassword.length < 8) {
      onNotify?.('error', 'Password must be at least 8 characters');
      return;
    }
    const result = await resetPassword(selectedUser.id, newPassword);
    if (result.success) {
      onNotify?.('success', `Password has been reset for ${selectedUser.email}`);
      closeModal();
    } else {
      onNotify?.('error', `Failed to reset password: ${result.error || 'Unknown error'}`);
    }
  };

  // Handle status update
  const handleUpdateStatus = async () => {
    if (!selectedUser || !editForm.status) return;
    // Convert status string to boolean is_active
    const isActive = editForm.status === 'active';
    const result = await updateStatus(selectedUser.id, isActive);
    if (result.success) {
      onNotify?.('success', `User status updated to ${editForm.status}`);
      closeModal();
    } else {
      onNotify?.('error', `Failed to update status: ${result.error || 'Unknown error'}`);
    }
  };

  // Handle roles update
  const handleUpdateRoles = async () => {
    if (!selectedUser || editForm.roles.length === 0) return;
    const result = await updateRoles(selectedUser.id, editForm.roles);
    if (result.success) {
      onNotify?.('success', `User roles updated successfully`);
      closeModal();
    } else {
      onNotify?.('error', `Failed to update roles: ${result.error || 'Unknown error'}`);
    }
  };

  // Toggle role in edit form
  const toggleRole = (role) => {
    setEditForm(prev => {
      const roles = prev.roles.includes(role)
        ? prev.roles.filter(r => r !== role)
        : [...prev.roles, role];
      // Ensure at least one role is selected
      return { ...prev, roles: roles.length > 0 ? roles : ['user'] };
    });
  };

  // User table columns
  const columns = [
    {
      key: 'username',
      label: 'User',
      render: (value, row) => (
        <div className="user-mgmt__user-cell">
          <div className="user-mgmt__avatar">
            {value?.charAt(0)?.toUpperCase() || '?'}
          </div>
          <div className="user-mgmt__user-info">
            <span className="user-mgmt__username">{value}</span>
            <span className="user-mgmt__email">{row.email}</span>
          </div>
        </div>
      ),
    },
    {
      key: 'roles',
      label: 'Roles',
      render: (value) => (
        <div className="user-mgmt__roles">
          {(value || ['user']).map(role => (
            <StatusBadge 
              key={role} 
              status={role}
              variant={role === 'admin' ? 'danger' : role === 'moderator' ? 'warning' : 'default'}
            />
          ))}
        </div>
      ),
    },
    {
      key: 'status',
      label: 'Status',
      render: (value) => (
        <StatusBadge 
          status={value || 'active'} 
          variant={value === 'active' ? 'success' : 'danger'}
        />
      ),
    },
    {
      key: 'is_verified',
      label: 'Verified',
      render: (value) => (
        <span className={`user-mgmt__verified ${value ? 'user-mgmt__verified--yes' : ''}`}>
          {value ? 'Verified' : 'Not Verified'}
        </span>
      ),
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
      render: (_, row) => (
        <div className="user-mgmt__actions">
          <button
            className="admin-btn admin-btn--sm admin-btn--ghost"
            onClick={() => openModal('edit', row)}
            title="Edit user"
          >
            ✏️
          </button>
          <button
            className="admin-btn admin-btn--sm admin-btn--ghost"
            onClick={() => openModal('password', row)}
            title="Reset password"
          >
            🔑
          </button>
          <button
            className="admin-btn admin-btn--sm admin-btn--ghost"
            onClick={() => openModal('delete', row)}
            title="Delete user"
            disabled={row.roles?.includes('admin')}
          >
            🗑️
          </button>
        </div>
      ),
    },
  ];

  if (loading && !data) {
    return (
      <div className="admin-section">
        <div className="admin-section__loading">
          <LoadingSpinner size="large" />
          <p>Loading users...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="admin-section">
        <ErrorMessage 
          message={`Failed to load users: ${error}`}
          onRetry={refresh}
        />
      </div>
    );
  }

  const users = data?.users || [];
  const paginationData = data?.pagination;

  return (
    <div className="admin-section">
      {/* Header */}
      <div className="admin-section__header">
        <h2 className="admin-section__title">User Management</h2>
        <div className="admin-section__actions">
          <button 
            className="admin-btn admin-btn--secondary admin-btn--sm"
            onClick={refresh}
            disabled={loading}
          >
            {loading ? 'Refreshing...' : 'Refresh'}
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="user-mgmt__filters admin-card">
        <SearchInput
          value={search}
          onChange={setSearch}
          placeholder="Search by username or email..."
          className="user-mgmt__search"
        />
        <div className="user-mgmt__filter-group">
          <select
            className="admin-select"
            value={filters.status}
            onChange={(e) => setFilters(prev => ({ ...prev, status: e.target.value }))}
          >
            <option value="">All Status</option>
            <option value="active">Active</option>
            <option value="inactive">Inactive</option>
            <option value="suspended">Suspended</option>
          </select>
          <select
            className="admin-select"
            value={filters.role}
            onChange={(e) => setFilters(prev => ({ ...prev, role: e.target.value }))}
          >
            <option value="">All Roles</option>
            {AVAILABLE_ROLES.map(role => (
              <option key={role} value={role}>{formatRole(role)}</option>
            ))}
          </select>
          <select
            className="admin-select"
            value={filters.verified}
            onChange={(e) => setFilters(prev => ({ ...prev, verified: e.target.value }))}
          >
            <option value="">All Verification</option>
            <option value="true">Verified</option>
            <option value="false">Not Verified</option>
          </select>
        </div>
      </div>

      {/* Users Table */}
      <div className="admin-mt-3">
        <DataTable
          columns={columns}
          data={users}
          loading={loading}
          emptyMessage="No users found matching your filters"
          pagination={paginationData}
          onPageChange={(page) => setPagination(prev => ({ ...prev, page }))}
        />
      </div>

      {/* Delete Confirmation Modal */}
      <ConfirmModal
        isOpen={modalState.type === 'delete' && modalState.isOpen}
        title="Delete User"
        message={`Are you sure you want to delete user "${selectedUser?.username}"? This action cannot be undone. All user data including analyses will be permanently removed.`}
        confirmLabel="Delete User"
        variant="danger"
        onConfirm={handleDeleteUser}
        onCancel={closeModal}
      />

      {/* Password Reset Modal */}
      {modalState.type === 'password' && modalState.isOpen && selectedUser && (
        <div className="admin-modal__overlay" onClick={closeModal}>
          <div className="admin-modal user-mgmt__password-modal" onClick={e => e.stopPropagation()}>
            <h3 className="admin-modal__title">Reset Password</h3>
            <p className="admin-modal__text">
              Set a new password for <strong>{selectedUser.username}</strong> ({selectedUser.email})
            </p>
            <div className="admin-form-group">
              <label className="admin-form-label">New Password</label>
              <input
                type="password"
                className="admin-form-input"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                placeholder="Enter new password (min 8 characters)"
                minLength={8}
              />
            </div>
            <div className="admin-modal__actions">
              <button className="admin-btn admin-btn--ghost" onClick={closeModal}>
                Cancel
              </button>
              <button 
                className="admin-btn admin-btn--primary"
                onClick={handleResetPassword}
                disabled={newPassword.length < 8}
              >
                Reset Password
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Edit User Modal */}
      {modalState.type === 'edit' && modalState.isOpen && selectedUser && (
        <div className="admin-modal__overlay" onClick={closeModal}>
          <div className="admin-modal user-mgmt__edit-modal" onClick={e => e.stopPropagation()}>
            <h3 className="admin-modal__title">Edit User: {selectedUser.username}</h3>
            
            {/* Status Section */}
            <div className="user-mgmt__edit-section">
              <label className="admin-form-label">Status</label>
              <div className="user-mgmt__status-options">
                {['active', 'inactive', 'suspended'].map(status => (
                  <button
                    key={status}
                    className={`admin-btn admin-btn--sm ${
                      editForm.status === status ? 'admin-btn--primary' : 'admin-btn--ghost'
                    }`}
                    onClick={() => setEditForm(prev => ({ ...prev, status }))}
                  >
                    {status.charAt(0).toUpperCase() + status.slice(1)}
                  </button>
                ))}
              </div>
              <button
                className="admin-btn admin-btn--secondary admin-mt-2"
                onClick={handleUpdateStatus}
                disabled={editForm.status === selectedUser.status}
              >
                Update Status
              </button>
            </div>

            {/* Roles Section */}
            <div className="user-mgmt__edit-section">
              <label className="admin-form-label">Roles</label>
              <div className="user-mgmt__roles-options">
                {AVAILABLE_ROLES.map(role => (
                  <label key={role} className="user-mgmt__role-checkbox">
                    <input
                      type="checkbox"
                      checked={editForm.roles.includes(role)}
                      onChange={() => toggleRole(role)}
                    />
                    <span>{formatRole(role)}</span>
                  </label>
                ))}
              </div>
              <button
                className="admin-btn admin-btn--secondary admin-mt-2"
                onClick={handleUpdateRoles}
                disabled={
                  JSON.stringify(editForm.roles.sort()) === 
                  JSON.stringify((selectedUser.roles || ['user']).sort())
                }
              >
                Update Roles
              </button>
            </div>

            {/* Close button */}
            <div className="admin-modal__actions">
              <button className="admin-btn admin-btn--ghost" onClick={closeModal}>
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      <style>{`
        .admin-section__loading {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          min-height: 400px;
          color: var(--admin-text-muted);
        }

        .user-mgmt__filters {
          display: flex;
          flex-wrap: wrap;
          gap: 1rem;
          align-items: center;
          padding: 1rem;
        }

        .user-mgmt__search {
          flex: 1;
          min-width: 250px;
        }

        .user-mgmt__filter-group {
          display: flex;
          gap: 0.5rem;
        }

        .user-mgmt__user-cell {
          display: flex;
          align-items: center;
          gap: 0.75rem;
        }

        .user-mgmt__avatar {
          width: 40px;
          height: 40px;
          background: var(--admin-primary);
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          font-weight: 600;
          color: white;
        }

        .user-mgmt__user-info {
          display: flex;
          flex-direction: column;
        }

        .user-mgmt__username {
          font-weight: 500;
          color: var(--admin-text);
        }

        .user-mgmt__email {
          font-size: 0.75rem;
          color: var(--admin-text-muted);
        }

        .user-mgmt__roles {
          display: flex;
          flex-wrap: wrap;
          gap: 0.25rem;
        }

        .user-mgmt__verified {
          font-size: 0.75rem;
          color: var(--admin-danger);
        }

        .user-mgmt__verified--yes {
          color: var(--admin-success);
        }

        .user-mgmt__actions {
          display: flex;
          gap: 0.25rem;
        }

        .user-mgmt__edit-modal {
          max-width: 500px;
        }

        .user-mgmt__edit-section {
          margin-bottom: 1.5rem;
          padding-bottom: 1.5rem;
          border-bottom: 1px solid var(--admin-border);
        }

        .user-mgmt__edit-section:last-of-type {
          border-bottom: none;
        }

        .user-mgmt__status-options {
          display: flex;
          gap: 0.5rem;
          margin-top: 0.5rem;
        }

        .user-mgmt__roles-options {
          display: grid;
          grid-template-columns: repeat(2, 1fr);
          gap: 0.75rem;
          margin-top: 0.5rem;
        }

        .user-mgmt__role-checkbox {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          cursor: pointer;
          font-size: 0.875rem;
          color: var(--admin-text);
        }

        .user-mgmt__role-checkbox input {
          width: 18px;
          height: 18px;
          accent-color: var(--admin-primary);
        }

        .user-mgmt__password-modal {
          max-width: 400px;
        }

        .admin-modal__text {
          color: var(--admin-text-muted);
          margin-bottom: 1rem;
        }

        .admin-modal__text strong {
          color: var(--admin-text);
        }

        @media (max-width: 768px) {
          .user-mgmt__filters {
            flex-direction: column;
            align-items: stretch;
          }

          .user-mgmt__search {
            min-width: 100%;
          }

          .user-mgmt__filter-group {
            flex-wrap: wrap;
          }
        }
      `}</style>
    </div>
  );
}

UserManagement.propTypes = {
  onNotify: PropTypes.func,
};

// Helper functions
function formatRole(role) {
  return role.split('_').map(word => 
    word.charAt(0).toUpperCase() + word.slice(1)
  ).join(' ');
}

function formatRelativeTime(dateString) {
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
