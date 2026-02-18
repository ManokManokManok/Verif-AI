/**
 * SystemInfoCard Component
 * 
 * Displays system information in a grid.
 */

import React from 'react';
import PropTypes from 'prop-types';

export default function SystemInfoCard({ info }) {
  return (
    <div className="admin-card">
      <h3 className="admin-card__title">System Information</h3>
      <div className="model-health__system-info">
        {info.map((item, index) => (
          <div key={index} className="model-health__info-row">
            <span className="model-health__info-label">{item.label}</span>
            <span className="model-health__info-value">{item.value}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

SystemInfoCard.propTypes = {
  info: PropTypes.arrayOf(PropTypes.shape({
    label: PropTypes.string.isRequired,
    value: PropTypes.oneOfType([PropTypes.string, PropTypes.node]).isRequired,
  })).isRequired,
};
