/**
 * PeriodSelector Component
 * 
 * Dropdown for selecting time periods.
 */

import React from 'react';
import PropTypes from 'prop-types';
import './PeriodSelector.css';

export default function PeriodSelector({ value, onChange, className = '' }) {
  const periods = [
    { value: 'day', label: 'Today' },
    { value: 'week', label: 'This Week' },
    { value: 'month', label: 'This Month' },
    { value: 'year', label: 'This Year' },
    { value: 'all_time', label: 'All Time' },
  ];

  return (
    <select
      className={`period-selector ${className}`}
      value={value}
      onChange={(e) => onChange(e.target.value)}
    >
      {periods.map((p) => (
        <option key={p.value} value={p.value}>
          {p.label}
        </option>
      ))}
    </select>
  );
}

PeriodSelector.propTypes = {
  value: PropTypes.string.isRequired,
  onChange: PropTypes.func.isRequired,
  className: PropTypes.string,
};
