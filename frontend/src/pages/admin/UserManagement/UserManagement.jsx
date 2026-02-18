/**
 * User Management Tab
 * 
 * Admin interface for managing users: view, edit, delete, role management.
 */

import React, { useState, useEffect } from 'react';
import PropTypes from 'prop-types';
import { 
  DataTable,
  SearchInput,
  LoadingSpinner, 
  ErrorMessage,
  ConfirmModal,
} from '../../../components/admin';
import { useUsers } from '../../../hooks/useAdminData';
import PasswordResetModal from './components/PasswordResetModal';
import EditUserModal from './components/EditUserModal';
import { getUserTableColumns } from './columns';
import { formatRole } from './utils';
import './UserManagement.css';

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
      return { ...prev, roles: roles.length > 0 ? roles : ['user'] };
    });
  };

  // Get table columns with action handlers
  const columns = getUserTableColumns({
    onEdit: (user) => openModal('edit', user),
    onPassword: (user) => openModal('password', user),
    onDelete: (user) => openModal('delete', user),
  });

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
      <PasswordResetModal
        isOpen={modalState.type === 'password' && modalState.isOpen}
        user={selectedUser}
        password={newPassword}
        onPasswordChange={setNewPassword}
        onConfirm={handleResetPassword}
        onCancel={closeModal}
      />

      {/* Edit User Modal */}
      <EditUserModal
        isOpen={modalState.type === 'edit' && modalState.isOpen}
        user={selectedUser}
        editForm={editForm}
        onStatusChange={(status) => setEditForm(prev => ({ ...prev, status }))}
        onRoleToggle={toggleRole}
        onUpdateStatus={handleUpdateStatus}
        onUpdateRoles={handleUpdateRoles}
        onClose={closeModal}
      />
    </div>
  );
}

UserManagement.propTypes = {
  onNotify: PropTypes.func,
};
