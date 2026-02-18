/**
 * StatCard Component
 * 
 * Displays a single statistic with label, value, and optional trend indicator.
 */

import React from 'react';
import PropTypes from 'prop-types';
import './StatCard.css';

export default function StatCard({ 
  title, 
  value, 
  subtitle, 
  icon, 
  trend, 
  trendValue,
  variant = 'default',
  loading = false,
  className = ''
}) {
  const variantClass = `stat-card--${variant}`;
  const trendClass = trend === 'up' ? 'stat-card__trend--up' 
    : trend === 'down' ? 'stat-card__trend--down' 
    : 'stat-card__trend--stable';

  if (loading) {
    return (
      <div className={`stat-card ${variantClass} stat-card--loading ${className}`}>
        <div className="stat-card__skeleton" />
      </div>
    );
  }

  return (
    <div className={`stat-card ${variantClass} ${className}`}>
      {icon && <div className="stat-card__icon">{icon}</div>}
      <div className="stat-card__content">
        <h3 className="stat-card__title">{title}</h3>
        <p className="stat-card__value">{value}</p>
        {subtitle && <span className="stat-card__subtitle">{subtitle}</span>}
        {trend && trendValue && (
          <div className={`stat-card__trend ${trendClass}`}>
            <span className="stat-card__trend-arrow">
              {trend === 'up' ? '↑' : trend === 'down' ? '↓' : '→'}
            </span>
            <span className="stat-card__trend-value">{trendValue}</span>
          </div>
        )}
      </div>
    </div>
  );
}

StatCard.propTypes = {
  title: PropTypes.string.isRequired,
  value: PropTypes.oneOfType([PropTypes.string, PropTypes.number]).isRequired,
  subtitle: PropTypes.string,
  icon: PropTypes.node,
  trend: PropTypes.oneOf(['up', 'down', 'stable']),
  trendValue: PropTypes.string,
  variant: PropTypes.oneOf(['default', 'success', 'warning', 'danger', 'info']),
  loading: PropTypes.bool,
  className: PropTypes.string,
};
