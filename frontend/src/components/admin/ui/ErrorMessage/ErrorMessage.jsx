/**
 * ErrorMessage Component
 */

import React from 'react';
import PropTypes from 'prop-types';
import './ErrorMessage.css';

export default function ErrorMessage({ message, onRetry, className = '' }) {
  return (
    <div className={`error-message ${className}`}>
      <span className="error-message__icon">⚠️</span>
      <p className="error-message__text">{message}</p>
      {onRetry && (
        <button className="error-message__retry" onClick={onRetry}>
          Retry
        </button>
      )}
    </div>
  );
}

ErrorMessage.propTypes = {
  message: PropTypes.string.isRequired,
  onRetry: PropTypes.func,
  className: PropTypes.string,
};
