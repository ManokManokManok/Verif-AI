/**
 * BlockchainStatsCard Component
 * 
 * Displays quick statistics for blockchain verification.
 */

import React from 'react';
import PropTypes from 'prop-types';

export default function BlockchainStatsCard({ stats }) {
  return (
    <div className="blockchain-admin__stats-card">
      <h3 className="blockchain-admin__stats-title">Quick Stats</h3>
      <div className="blockchain-admin__stats-grid">
        <div className="blockchain-admin__stat-item">
          <span className="blockchain-admin__stat-value">{stats.total}</span>
          <span className="blockchain-admin__stat-label">Total Analyses</span>
        </div>
        <div className="blockchain-admin__stat-item blockchain-admin__stat-item--success">
          <span className="blockchain-admin__stat-value">{stats.anchored}</span>
          <span className="blockchain-admin__stat-label">Anchored</span>
        </div>
        <div className="blockchain-admin__stat-item blockchain-admin__stat-item--warning">
          <span className="blockchain-admin__stat-value">{stats.pending}</span>
          <span className="blockchain-admin__stat-label">Pending</span>
        </div>
      </div>
    </div>
  );
}

BlockchainStatsCard.propTypes = {
  stats: PropTypes.shape({
    total: PropTypes.number.isRequired,
    anchored: PropTypes.number.isRequired,
    pending: PropTypes.number.isRequired,
  }).isRequired,
};
