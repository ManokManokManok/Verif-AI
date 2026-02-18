/**
 * LogoutConfirmModal Component
 * 
 * Confirmation dialog for logout action.
 */

import React from 'react';
import PropTypes from 'prop-types';
import './LogoutConfirmModal.css';

export default function LogoutConfirmModal({
  isOpen,
  onConfirm,
  onCancel,
}) {
  if (!isOpen) return null;

  return (
    <div className="logout-modal__overlay" onClick={onCancel}>
      <div className="logout-modal" onClick={(e) => e.stopPropagation()}>
        <h3 className="logout-modal__title">Confirm Logout</h3>
        <p className="logout-modal__message">
          Are you sure you want to logout? You will need to sign in again to access your account.
        </p>
        <div className="logout-modal__actions">
          <button
            className="logout-modal__btn logout-modal__btn--cancel"
            onClick={onCancel}
          >
            No
          </button>
          <button
            className="logout-modal__btn logout-modal__btn--confirm"
            onClick={onConfirm}
          >
            Yes
          </button>
        </div>
      </div>
    </div>
  );
}

LogoutConfirmModal.propTypes = {
  isOpen: PropTypes.bool.isRequired,
  onConfirm: PropTypes.func.isRequired,
  onCancel: PropTypes.func.isRequired,
};
