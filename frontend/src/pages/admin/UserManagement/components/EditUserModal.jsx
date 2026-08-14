/**
 * EditUserModal Component
 * 
 * Modal for editing user status and roles.
 */

import React from 'react';
import PropTypes from 'prop-types';
import { formatRole } from '../utils';

const AVAILABLE_ROLES = ['admin', 'moderator', 'analyst', 'premium_user', 'user'];
const STATUS_OPTIONS = ['active', 'inactive', 'suspended'];

export default function EditUserModal({ 
  isOpen, 
  user, 
  editForm,
  onStatusChange,
  onRoleToggle,
  onUpdateStatus,
  onUpdateRoles,
  onClose 
}) {
  if (!isOpen || !user) return null;

  const isStatusChanged = editForm.status !== user.status;
  const isRolesChanged = JSON.stringify(editForm.roles.sort()) !== 
    JSON.stringify((user.roles || ['user']).sort());

  return (
    <div className="admin-modal__overlay" onClick={onClose}>
      <div className="admin-modal user-mgmt__edit-modal" onClick={e => e.stopPropagation()}>
        <h3 className="admin-modal__title">Edit User: {user.username}</h3>
        
        {/* Status Section */}
        <div className="user-mgmt__edit-section">
          <label className="admin-form-label">Status</label>
          <div className="user-mgmt__status-options">
            {STATUS_OPTIONS.map(status => (
              <button
                key={status}
                className={`admin-btn admin-btn--sm ${
                  editForm.status === status ? 'admin-btn--primary' : 'admin-btn--ghost'
                }`}
                onClick={() => onStatusChange(status)}
              >
                {status.charAt(0).toUpperCase() + status.slice(1)}
              </button>
            ))}
          </div>
          <button
            className="admin-btn admin-btn--secondary admin-mt-2"
            onClick={onUpdateStatus}
            disabled={!isStatusChanged}
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
                  onChange={() => onRoleToggle(role)}
                />
                <span>{formatRole(role)}</span>
              </label>
            ))}
          </div>
          <button
            className="admin-btn admin-btn--secondary admin-mt-2"
            onClick={onUpdateRoles}
            disabled={!isRolesChanged}
          >
            Update Roles
          </button>
        </div>

        {/* Close button */}
        <div className="admin-modal__actions">
          <button className="admin-btn admin-btn--ghost" onClick={onClose}>
            Close
          </button>
        </div>
      </div>
    </div>
  );
}

EditUserModal.propTypes = {
  isOpen: PropTypes.bool.isRequired,
  user: PropTypes.object,
  editForm: PropTypes.shape({
    status: PropTypes.string,
    roles: PropTypes.arrayOf(PropTypes.string),
  }).isRequired,
  onStatusChange: PropTypes.func.isRequired,
  onRoleToggle: PropTypes.func.isRequired,
  onUpdateStatus: PropTypes.func.isRequired,
  onUpdateRoles: PropTypes.func.isRequired,
  onClose: PropTypes.func.isRequired,
};
