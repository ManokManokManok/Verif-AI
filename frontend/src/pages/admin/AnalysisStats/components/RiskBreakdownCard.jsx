/**
 * RiskBreakdownCard Component
 * 
 * Displays analysis breakdown by risk level with progress bars.
 */

import React from 'react';
import PropTypes from 'prop-types';

export default function RiskBreakdownCard({ stats, totalAnalyses, getPercentage }) {
  const breakdownItems = [
    {
      label: '🔴 High Risk',
      count: stats.high_risk_count || 0,
      variant: 'danger',
    },
    {
      label: '🟠 Medium Risk',
      count: stats.medium_risk_count || 0,
      variant: 'warning',
    },
    {
      label: '🟡 Low Risk',
      count: stats.low_risk_count || 0,
      variant: 'info',
    },
    {
      label: '🟢 Legitimate',
      count: stats.legitimate_count || 0,
      variant: 'success',
    },
  ];

  return (
    <div className="admin-card">
      <div className="admin-card__header">
        <h3 className="admin-card__title">Risk Level Breakdown</h3>
      </div>
      <div className="analysis-stats__breakdown">
        {breakdownItems.map((item, index) => (
          <div key={index} className="analysis-stats__breakdown-item">
            <div className="analysis-stats__breakdown-header">
              <span className="analysis-stats__breakdown-label">{item.label}</span>
              <span className="analysis-stats__breakdown-value">
                {item.count.toLocaleString()}
              </span>
            </div>
            <div className="analysis-stats__breakdown-bar">
              <div 
                className={`analysis-stats__breakdown-fill analysis-stats__breakdown-fill--${item.variant}`}
                style={{ width: `${getPercentage(item.count, totalAnalyses)}%` }}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

RiskBreakdownCard.propTypes = {
  stats: PropTypes.object.isRequired,
  totalAnalyses: PropTypes.number.isRequired,
  getPercentage: PropTypes.func.isRequired,
};
