/**
 * Alert Component
 * 
 * Displays alert/notification messages.
 */

import React from 'react';
import PropTypes from 'prop-types';
import './Alert.css';

export default function Alert({ type = 'info', message, onClose, className = '' }) {
  return (
    <div className={`alert alert--${type} ${className}`}>
      <span className="alert__message">{message}</span>
      {onClose && (
        <button className="alert__close" onClick={onClose} aria-label="Close">
          ✕
        </button>
      )}
    </div>
  );
}

Alert.propTypes = {
  type: PropTypes.oneOf(['info', 'success', 'warning', 'error']),
  message: PropTypes.string.isRequired,
  onClose: PropTypes.func,
  className: PropTypes.string,
};
