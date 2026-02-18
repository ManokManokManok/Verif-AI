/**
 * SystemGaugeCard Component
 * 
 * Displays a metric gauge with additional details.
 */

import React from 'react';
import PropTypes from 'prop-types';
import { MetricGauge } from '../../../../components/admin';

export default function SystemGaugeCard({ 
  label, 
  value, 
  maxValue, 
  unit,
  thresholds,
  details 
}) {
  return (
    <div className="model-health__gauge-card admin-card">
      <MetricGauge
        label={label}
        value={value}
        maxValue={maxValue}
        unit={unit}
        thresholds={thresholds}
        size="large"
      />
      {details && details.length > 0 && (
        <div className="model-health__gauge-details">
          {details.map((detail, index) => (
            <div key={index} className="model-health__detail">
              <span className="model-health__detail-label">{detail.label}</span>
              <span className="model-health__detail-value">{detail.value}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

SystemGaugeCard.propTypes = {
  label: PropTypes.string.isRequired,
  value: PropTypes.number.isRequired,
  maxValue: PropTypes.number,
  unit: PropTypes.string,
  thresholds: PropTypes.shape({
    warning: PropTypes.number,
    danger: PropTypes.number,
  }),
  details: PropTypes.arrayOf(PropTypes.shape({
    label: PropTypes.string.isRequired,
    value: PropTypes.oneOfType([PropTypes.string, PropTypes.number]).isRequired,
  })),
};
