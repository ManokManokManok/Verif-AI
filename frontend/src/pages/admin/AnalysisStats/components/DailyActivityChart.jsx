/**
 * DailyActivityChart Component
 * 
 * Displays daily activity chart with total and scam detection bars.
 */

import React from 'react';
import PropTypes from 'prop-types';

export default function DailyActivityChart({ dailyCounts }) {
  if (!dailyCounts || dailyCounts.length === 0) {
    return (
      <div className="admin-card">
        <div className="admin-card__header">
          <h3 className="admin-card__title">Daily Activity (Last 30 Days)</h3>
        </div>
        <div className="analysis-stats__chart-empty">
          <p>📊 No activity data available for the selected period</p>
          <p className="analysis-stats__chart-hint">
            Data will appear as analyses are performed
          </p>
        </div>
      </div>
    );
  }

  const maxCount = Math.max(...dailyCounts.map(d => d.total || 0));
  const displayData = dailyCounts.slice(-14); // Show last 14 days

  return (
    <div className="admin-card">
      <div className="admin-card__header">
        <h3 className="admin-card__title">Daily Activity (Last 30 Days)</h3>
      </div>
      <div className="analysis-stats__daily-chart">
        <div className="analysis-stats__chart-bars">
          {displayData.map((day, idx) => {
            const height = maxCount > 0 ? ((day.total || 0) / maxCount) * 100 : 0;
            const scamPercentage = day.total > 0 ? ((day.scams || 0) / day.total) * 100 : 0;
            
            return (
              <div key={idx} className="analysis-stats__chart-bar-wrapper">
                <div 
                  className="analysis-stats__chart-bar"
                  style={{ height: `${height}%` }}
                  title={`${day.date}: ${day.total || 0} analyses (${day.scams || 0} scams)`}
                >
                  <div 
                    className="analysis-stats__chart-bar-scam"
                    style={{ height: `${scamPercentage}%` }}
                  />
                </div>
                <span className="analysis-stats__chart-label">
                  {new Date(day.date).getDate()}
                </span>
              </div>
            );
          })}
        </div>
        <div className="analysis-stats__chart-legend">
          <span className="analysis-stats__legend-item">
            <span className="analysis-stats__legend-color analysis-stats__legend-color--total" />
            Total
          </span>
          <span className="analysis-stats__legend-item">
            <span className="analysis-stats__legend-color analysis-stats__legend-color--scam" />
            Scams Detected
          </span>
        </div>
      </div>
    </div>
  );
}

DailyActivityChart.propTypes = {
  dailyCounts: PropTypes.arrayOf(PropTypes.shape({
    date: PropTypes.string.isRequired,
    total: PropTypes.number,
    scams: PropTypes.number,
  })),
};
