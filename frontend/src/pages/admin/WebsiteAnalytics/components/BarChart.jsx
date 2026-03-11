/**
 * BarChart Component
 * 
 * Simple horizontal bar chart for analytics data.
 */

import React, { useState } from 'react';
import PropTypes from 'prop-types';

export default function BarChart({ data, title, maxItems = 10 }) {
  const [hoveredIdx, setHoveredIdx] = useState(null);

  if (!data || data.length === 0) {
    return (
      <div className="analytics-chart analytics-chart--empty">
        <h4>{title}</h4>
        <p>No data available</p>
      </div>
    );
  }

  const items = data.slice(0, maxItems);
  const maxValue = Math.max(...items.map(item => item.value || item.count || 0), 1);

  return (
    <div className="analytics-chart">
      <h4>{title}</h4>
      <div className="analytics-chart__bars">
        {items.map((item, index) => {
          const value = item.value || item.count || 0;
          const percentage = (value / maxValue) * 100;
          const isHovered = hoveredIdx === index;
          return (
            <div
              key={index}
              className="analytics-chart__bar-item"
              onMouseEnter={() => setHoveredIdx(index)}
              onMouseLeave={() => setHoveredIdx(null)}
            >
              <span className="analytics-chart__rank">#{index + 1}</span>
              <span className="analytics-chart__label" title={item.label || item.path}>
                {item.label || item.path || 'Unknown'}
              </span>
              <div className="analytics-chart__bar-container">
                <div 
                  className={`analytics-chart__bar${isHovered ? ' analytics-chart__bar--hovered' : ''}`}
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
