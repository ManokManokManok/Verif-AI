/**
 * HourlyPattern Component
 * 
 * Displays 24-hour traffic pattern visualization.
 */

import React from 'react';
import PropTypes from 'prop-types';

export default function HourlyPattern({ data }) {
  if (!data) return null;

  // Convert object to array of 24 hours
  const hours = Array.from({ length: 24 }, (_, i) => ({
    hour: i,
    label: `${i.toString().padStart(2, '0')}:00`,
    value: data[i] || 0,
  }));

  const maxValue = Math.max(...hours.map(h => h.value));

  return (
    <div className="analytics-hourly">
      <h4>Hourly Traffic Pattern</h4>
      <div className="analytics-hourly__chart">
        {hours.map((hour) => {
          const height = maxValue > 0 ? (hour.value / maxValue) * 100 : 0;
          return (
            <div key={hour.hour} className="analytics-hourly__bar-wrapper">
              <div 
                className="analytics-hourly__bar"
                style={{ height: `${height}%` }}
                title={`${hour.label}: ${hour.value} visits`}
              />
              {hour.hour % 4 === 0 && (
                <span className="analytics-hourly__label">{hour.hour}h</span>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

HourlyPattern.propTypes = {
  data: PropTypes.object,
};
