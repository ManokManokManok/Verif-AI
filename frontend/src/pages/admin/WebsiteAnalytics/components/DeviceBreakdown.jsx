/**
 * DeviceBreakdown Component
 * 
 * Displays visitor device type statistics.
 */

import React from 'react';
import PropTypes from 'prop-types';

export default function DeviceBreakdown({ data }) {
  if (!data) return null;

  const devices = [
    { label: 'Desktop', value: data.desktop || 0, color: '#3b82f6' },
    { label: 'Mobile', value: data.mobile || 0, color: '#8b5cf6' },
    { label: 'Tablet', value: data.tablet || 0, color: '#ec4899' },
    { label: 'Unknown', value: data.unknown || 0, color: '#6b7280' },
  ].filter(d => d.value > 0);

  const total = devices.reduce((sum, d) => sum + d.value, 0);

  return (
    <div className="analytics-devices">
      <h4>Device Breakdown</h4>
      <div className="analytics-devices__content">
        <div className="analytics-devices__list">
          {devices.map((device, index) => (
            <div key={index} className="analytics-devices__item">
              <span 
                className="analytics-devices__color"
                style={{ backgroundColor: device.color }}
              />
              <span className="analytics-devices__label">{device.label}</span>
              <span className="analytics-devices__value">
                {device.value.toLocaleString()}
              </span>
              <span className="analytics-devices__percentage">
                ({total > 0 ? ((device.value / total) * 100).toFixed(1) : 0}%)
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

DeviceBreakdown.propTypes = {
  data: PropTypes.object,
};
