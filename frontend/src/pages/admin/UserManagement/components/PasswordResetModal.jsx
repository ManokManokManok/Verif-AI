/**
 * PasswordResetModal Component
 * 
 * Modal for resetting user passwords.
 */

import React from 'react';
import PropTypes from 'prop-types';

export default function PasswordResetModal({ 
  isOpen, 
  user, 
  password,
  onPasswordChange,
  onConfirm, 
  onCancel 
}) {
  if (!isOpen || !user) return null;

  return (
    <div className="admin-modal__overlay" onClick={onCancel}>
      <div className="admin-modal user-mgmt__password-modal" onClick={e => e.stopPropagation()}>
        <h3 className="admin-modal__title">Reset Password</h3>
        <p className="admin-modal__text">
          Set a new password for <strong>{user.username}</strong> ({user.email})
        </p>
        <div className="admin-form-group">
          <label className="admin-form-label">New Password</label>
          <input
            type="password"
            className="admin-form-input"
            value={password}
            onChange={(e) => onPasswordChange(e.target.value)}
            placeholder="Enter new password (min 8 characters)"
            minLength={8}
          />
        </div>
        <div className="admin-modal__actions">
          <button className="admin-btn admin-btn--ghost" onClick={onCancel}>
            Cancel
          </button>
          <button 
            className="admin-btn admin-btn--primary"
            onClick={onConfirm}
            disabled={password.length < 8}
          >
            Reset Password
          </button>
        </div>
      </div>
    </div>
  );
}

PasswordResetModal.propTypes = {
  isOpen: PropTypes.bool.isRequired,
  user: PropTypes.object,
  password: PropTypes.string.isRequired,
  onPasswordChange: PropTypes.func.isRequired,
  onConfirm: PropTypes.func.isRequired,
  onCancel: PropTypes.func.isRequired,
};
