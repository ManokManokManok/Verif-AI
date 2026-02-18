/**
 * DateRangePicker Component
 * 
 * Simple date range selection.
 */

import React from 'react';
import PropTypes from 'prop-types';
import './DateRangePicker.css';

export default function DateRangePicker({ 
  startDate, 
  endDate, 
  onStartDateChange, 
  onEndDateChange,
  className = '' 
}) {
  return (
    <div className={`date-range-picker ${className}`}>
      <div className="date-range-picker__field">
        <label htmlFor="date-range-start" className="date-range-picker__label">From</label>
        <input
          id="date-range-start"
          type="date"
          className="date-range-picker__input"
          value={startDate || ''}
          onChange={(e) => onStartDateChange(e.target.value)}
        />
      </div>
      <div className="date-range-picker__field">
        <label htmlFor="date-range-end" className="date-range-picker__label">To</label>
        <input
          id="date-range-end"
          type="date"
          className="date-range-picker__input"
          value={endDate || ''}
          onChange={(e) => onEndDateChange(e.target.value)}
        />
      </div>
    </div>
  );
}

DateRangePicker.propTypes = {
  startDate: PropTypes.string,
  endDate: PropTypes.string,
  onStartDateChange: PropTypes.func.isRequired,
  onEndDateChange: PropTypes.func.isRequired,
  className: PropTypes.string,
};
