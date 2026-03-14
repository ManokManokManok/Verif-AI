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
      label: 'High Risk',
      description: 'Confidence ≥ 70%',
      count: stats.high_risk_count || 0,
      variant: 'danger',
    },
    {
      label: 'Medium Risk',
      description: 'Confidence 40–69%',
      count: stats.medium_risk_count || 0,
      variant: 'warning',
    },
    {
      label: 'Low Risk',
      description: 'Confidence < 40%',
      count: stats.low_risk_count || 0,
      variant: 'info',
    },
    {
      label: 'Legitimate',
      description: 'Not a scam',
      count: stats.legitimate_count || 0,
      variant: 'success',
    },
  ];

  return (
    <div className="admin-card">
      <div className="admin-card__header">
        <h3 className="admin-card__title">Risk Level Breakdown</h3>
        <span className="analysis-stats__card-subtitle">{totalAnalyses.toLocaleString()} total</span>
      </div>
      <div className="analysis-stats__breakdown">
        {breakdownItems.map((item, index) => {
          const pct = getPercentage(item.count, totalAnalyses);
          return (
            <div key={index} className="analysis-stats__breakdown-item">
              <div className="analysis-stats__breakdown-header">
                <div className="analysis-stats__breakdown-label-group">
                  <span className={`analysis-stats__breakdown-dot analysis-stats__breakdown-dot--${item.variant}`} />
                  <div>
                    <span className="analysis-stats__breakdown-label">{item.label}</span>
                    <span className="analysis-stats__breakdown-desc">{item.description}</span>
                  </div>
                </div>
                <div className="analysis-stats__breakdown-stats">
                  <span className="analysis-stats__breakdown-pct">{pct.toFixed(1)}%</span>
                  <span className="analysis-stats__breakdown-value">{item.count.toLocaleString()}</span>
                </div>
              </div>
              <div className="analysis-stats__breakdown-bar">
                <div 
                  className={`analysis-stats__breakdown-fill analysis-stats__breakdown-fill--${item.variant}`}
                  style={{ width: `${pct}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

RiskBreakdownCard.propTypes = {
  stats: PropTypes.object.isRequired,
  totalAnalyses: PropTypes.number.isRequired,
  getPercentage: PropTypes.func.isRequired,
};
