/**
 * RoleDistributionCard Component
 * 
 * Displays user role distribution with progress bars.
 */

import React from 'react';
import PropTypes from 'prop-types';
import { formatRole } from '../utils';

export default function RoleDistributionCard({ roleDistribution, totalUsers, getRoleColor }) {
  if (!roleDistribution || Object.keys(roleDistribution).length === 0) {
    return (
      <div className="admin-card">
        <div className="admin-card__header">
          <h3 className="admin-card__title">User Role Distribution</h3>
        </div>
        <p className="user-stats__no-data">No role distribution data available</p>
      </div>
    );
  }

  const getPercentage = (count) => {
    if (!totalUsers || totalUsers === 0) return '0';
    return ((count || 0) / totalUsers * 100).toFixed(1);
  };

  return (
    <div className="admin-card">
      <div className="admin-card__header">
        <h3 className="admin-card__title">User Role Distribution</h3>
      </div>
      <div className="user-stats__roles">
        {Object.entries(roleDistribution).map(([role, count]) => (
          <div key={role} className="user-stats__role-item">
            <div className="user-stats__role-header">
              <span className="user-stats__role-name">{formatRole(role)}</span>
              <span className="user-stats__role-count">{count.toLocaleString()}</span>
            </div>
            <div className="user-stats__role-bar">
              <div 
                className="user-stats__role-fill"
                style={{ 
                  width: `${getPercentage(count)}%`,
                  background: getRoleColor(role)
                }}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

RoleDistributionCard.propTypes = {
  roleDistribution: PropTypes.object,
  totalUsers: PropTypes.number,
  getRoleColor: PropTypes.func.isRequired,
};
