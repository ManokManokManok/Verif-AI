/**
 * SystemInfoCard Component
 * 
 * Displays system information in a grid.
 */

import React from 'react';
import PropTypes from 'prop-types';

function InfoValue({ item }) {
  if (item.type === 'status') {
    const connected = item.value;
    return (
      <span className={`model-health__info-badge model-health__info-badge--${connected ? 'connected' : 'disconnected'}`}>
        <span className="model-health__info-dot" />
        {connected ? 'Connected' : 'Disconnected'}
      </span>
    );
  }
  return (
    <span className="model-health__info-value">
      {item.value != null && item.value !== '' ? item.value : '—'}
    </span>
  );
}

export default function SystemInfoCard({ info }) {
  return (
    <div className="admin-card">
      <div className="admin-card__header">
        <h3 className="admin-card__title">System Information</h3>
      </div>
      <div className="model-health__system-info">
        {info.map((item, index) => (
          <div key={index} className="model-health__info-row">
            <span className="model-health__info-label">{item.label}</span>
            <InfoValue item={item} />
          </div>
        ))}
      </div>
    </div>
  );
}

SystemInfoCard.propTypes = {
  info: PropTypes.arrayOf(PropTypes.shape({
    label: PropTypes.string.isRequired,
    value: PropTypes.oneOfType([PropTypes.string, PropTypes.bool]),
    type: PropTypes.oneOf(['text', 'status']),
  })).isRequired,
};
