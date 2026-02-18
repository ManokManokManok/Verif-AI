/**
 * BarChart Component
 * 
 * Simple horizontal bar chart for analytics data.
 */

import React from 'react';
import PropTypes from 'prop-types';

export default function BarChart({ data, title, maxItems = 10 }) {
  if (!data || data.length === 0) {
    return (
      <div className="analytics-chart analytics-chart--empty">
        <h4>{title}</h4>
        <p>No data available</p>
      </div>
    );
  }

  const items = data.slice(0, maxItems);
  const maxValue = Math.max(...items.map(item => item.value || item.count || 0));

  return (
    <div className="analytics-chart">
      <h4>{title}</h4>
      <div className="analytics-chart__bars">
        {items.map((item, index) => {
          const value = item.value || item.count || 0;
          const percentage = maxValue > 0 ? (value / maxValue) * 100 : 0;
          return (
            <div key={index} className="analytics-chart__bar-item">
              <span className="analytics-chart__label">{item.label || item.path || 'Unknown'}</span>
              <div className="analytics-chart__bar-container">
                <div 
                  className="analytics-chart__bar"
                  style={{ width: `${percentage}%` }}
                />
                <span className="analytics-chart__value">{value.toLocaleString()}</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

BarChart.propTypes = {
  data: PropTypes.array,
  title: PropTypes.string.isRequired,
  maxItems: PropTypes.number,
};
