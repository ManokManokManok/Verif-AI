/**
 * DeviceBreakdown Component
 * 
 * Displays visitor device type statistics.
 */

import React from 'react';
import PropTypes from 'prop-types';

const DEVICE_VARS = {
  Desktop: 'var(--admin-primary, #3b82f6)',
  Mobile:  'var(--admin-info, #8b5cf6)',
  Tablet:  'var(--admin-warning, #f59e0b)',
  Unknown: 'var(--admin-text-dim, #6b7280)',
};

export default function DeviceBreakdown({ data }) {
  if (!data) return null;

  const devices = [
    { label: 'Desktop', value: data.desktop || 0 },
    { label: 'Mobile',  value: data.mobile  || 0 },
    { label: 'Tablet',  value: data.tablet  || 0 },
    { label: 'Unknown', value: data.unknown || 0 },
  ].filter(d => d.value > 0);

  const total = devices.reduce((sum, d) => sum + d.value, 0);

  return (
    <div className="analytics-devices">
      <div className="analytics-devices__header">
        <h4>Device Breakdown</h4>
        <span className="analytics-devices__total">{total.toLocaleString()} total</span>
      </div>
      <div className="analytics-devices__list">
        {devices.map((device, index) => {
          const pct = total > 0 ? ((device.value / total) * 100) : 0;
          const color = DEVICE_VARS[device.label];
          return (
            <div key={index} className="analytics-devices__item">
              <div className="analytics-devices__item-header">
                <span className="analytics-devices__color" style={{ backgroundColor: color }} />
                <span className="analytics-devices__label">{device.label}</span>
                <span className="analytics-devices__pct">{pct.toFixed(1)}%</span>
                <span className="analytics-devices__value">{device.value.toLocaleString()}</span>
              </div>
              <div className="analytics-devices__bar-track">
                <div
                  className="analytics-devices__bar-fill"
                  style={{ width: `${pct}%`, background: color }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

DeviceBreakdown.propTypes = {
  data: PropTypes.object,
};
