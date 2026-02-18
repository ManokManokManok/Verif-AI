/**
 * MetricGauge Component
 * 
 * Circular gauge for percentage metrics (CPU, GPU, Memory).
 */

import React from 'react';
import PropTypes from 'prop-types';
import './MetricGauge.css';

export default function MetricGauge({ 
  label, 
  value, 
  maxValue = 100, 
  unit = '%',
  thresholds = { warning: 70, danger: 90 },
  size = 'medium',
  loading = false,
  className = ''
}) {
  const percentage = Math.min((value / maxValue) * 100, 100);
  const circumference = 2 * Math.PI * 45; // radius = 45
  const strokeDashoffset = circumference - (percentage / 100) * circumference;
  
  const getStatusClass = () => {
    if (percentage >= thresholds.danger) return 'metric-gauge--danger';
    if (percentage >= thresholds.warning) return 'metric-gauge--warning';
    return 'metric-gauge--normal';
  };

  const sizeClass = `metric-gauge--${size}`;

  if (loading) {
    return (
      <div className={`metric-gauge ${sizeClass} metric-gauge--loading ${className}`}>
        <div className="metric-gauge__skeleton" />
      </div>
    );
  }

  return (
    <div className={`metric-gauge ${sizeClass} ${getStatusClass()} ${className}`}>
      <svg className="metric-gauge__svg" viewBox="0 0 100 100">
        {/* Background circle */}
        <circle
          className="metric-gauge__background"
          cx="50"
          cy="50"
          r="45"
          fill="none"
          strokeWidth="8"
        />
        {/* Progress circle */}
        <circle
          className="metric-gauge__progress"
          cx="50"
          cy="50"
          r="45"
          fill="none"
          strokeWidth="8"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={strokeDashoffset}
          transform="rotate(-90 50 50)"
        />
      </svg>
      <div className="metric-gauge__content">
        <span className="metric-gauge__value">{Math.round(value)}{unit}</span>
        <span className="metric-gauge__label">{label}</span>
      </div>
    </div>
  );
}

MetricGauge.propTypes = {
  label: PropTypes.string.isRequired,
  value: PropTypes.number.isRequired,
  maxValue: PropTypes.number,
  unit: PropTypes.string,
  thresholds: PropTypes.shape({
    warning: PropTypes.number,
    danger: PropTypes.number,
  }),
  size: PropTypes.oneOf(['small', 'medium', 'large']),
  loading: PropTypes.bool,
  className: PropTypes.string,
};
