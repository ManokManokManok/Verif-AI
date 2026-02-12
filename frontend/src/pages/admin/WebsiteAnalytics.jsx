/**
 * Website Analytics Tab
 * 
 * Displays website visit statistics, device breakdown, traffic patterns,
 * and other analytics data.
 */

import React, { useState, useMemo } from 'react';
import PropTypes from 'prop-types';
import { 
  StatCard, 
  PeriodSelector,
  LoadingSpinner, 
  ErrorMessage,
} from '../../components/admin';
import { useAnalytics } from '../../hooks/useAdminData';

/**
 * Simple bar chart component
 */
function BarChart({ data, title, maxItems = 10 }) {
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

/**
 * Device breakdown donut visualization
 */
function DeviceBreakdown({ data }) {
  if (!data) return null;

  const devices = [
    { label: 'Desktop', value: data.desktop || 0, color: '#4361ee' },
    { label: 'Mobile', value: data.mobile || 0, color: '#7209b7' },
    { label: 'Tablet', value: data.tablet || 0, color: '#f72585' },
    { label: 'Unknown', value: data.unknown || 0, color: '#adb5bd' },
  ].filter(d => d.value > 0);

  const total = devices.reduce((sum, d) => sum + d.value, 0);

  return (
    <div className="analytics-devices">
      <h4>Device Breakdown</h4>
      <div className="analytics-devices__content">
        <div className="analytics-devices__list">
          {devices.map((device, index) => (
            <div key={index} className="analytics-devices__item">
              <span 
                className="analytics-devices__color"
                style={{ backgroundColor: device.color }}
              />
              <span className="analytics-devices__label">{device.label}</span>
              <span className="analytics-devices__value">
                {device.value.toLocaleString()}
              </span>
              <span className="analytics-devices__percentage">
                ({total > 0 ? ((device.value / total) * 100).toFixed(1) : 0}%)
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

DeviceBreakdown.propTypes = {
  data: PropTypes.object,
};

/**
 * Hourly traffic pattern visualization
 */
function HourlyPattern({ data }) {
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

/**
 * Recent visits live feed
 */
function RecentVisits({ data }) {
  if (!data || data.length === 0) {
    return (
      <div className="analytics-recent">
        <h4>Recent Visits</h4>
        <p className="analytics-recent__empty">No recent visits</p>
      </div>
    );
  }

  return (
    <div className="analytics-recent">
      <h4>Recent Visits (Live)</h4>
      <div className="analytics-recent__list">
        {data.slice(0, 10).map((visit, index) => (
          <div key={index} className="analytics-recent__item">
            <span className="analytics-recent__path">{visit.path}</span>
            <span className="analytics-recent__device">{visit.device_type || 'unknown'}</span>
            <span className="analytics-recent__time">
              {formatTimeAgo(visit.timestamp)}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

RecentVisits.propTypes = {
  data: PropTypes.array,
};

/**
 * Format timestamp as relative time
 */
function formatTimeAgo(timestamp) {
  if (!timestamp) return '';
  
  const date = new Date(timestamp);
  const now = new Date();
  const diffMs = now - date;
  const diffSecs = Math.floor(diffMs / 1000);
  const diffMins = Math.floor(diffSecs / 60);
  const diffHours = Math.floor(diffMins / 60);
  
  if (diffSecs < 60) return `${diffSecs}s ago`;
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  return date.toLocaleDateString();
}

/**
 * Main Website Analytics component
 */
export default function WebsiteAnalytics({ onNotify }) {
  const [period, setPeriod] = useState('week');
  
  const { 
    data: analytics, 
    loading, 
    error, 
    refresh 
  } = useAnalytics(period);

  // Format top pages data for bar chart
  const topPagesData = useMemo(() => {
    if (!analytics?.top_pages) return [];
    return analytics.top_pages.map(page => ({
      label: page.path,
      value: page.visit_count,
    }));
  }, [analytics]);

  // Format referrers data for bar chart  
  const referrersData = useMemo(() => {
    if (!analytics?.referrers) return [];
    return analytics.referrers.map(ref => ({
      label: ref.referrer || 'Direct',
      value: ref.count,
    }));
  }, [analytics]);

  if (loading && !analytics) {
    return (
      <div className="admin-section">
        <div className="admin-section__loading">
          <LoadingSpinner size="large" />
          <p>Loading website analytics...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="admin-section">
        <ErrorMessage 
          message={`Failed to load analytics: ${error}`}
          onRetry={refresh}
        />
      </div>
    );
  }

  const visits = analytics?.visits || {};
  const devices = analytics?.devices || {};
  const hourlyPattern = analytics?.hourly_pattern || {};
  const recentVisits = analytics?.recent || [];

  return (
    <div className="admin-section website-analytics">
      {/* Header */}
      <div className="admin-section__header">
        <h2 className="admin-section__title">Website Analytics</h2>
        <div className="admin-section__actions">
          <PeriodSelector value={period} onChange={setPeriod} />
          <button 
            className="admin-btn admin-btn--secondary admin-btn--sm"
            onClick={refresh}
            disabled={loading}
          >
            {loading ? 'Refreshing...' : 'Refresh'}
          </button>
        </div>
      </div>

      {/* Overview Stats */}
      <div className="admin-grid admin-grid--4">
        <StatCard
          title="Total Visits"
          value={visits.total_visits?.toLocaleString() || '0'}
          subtitle={`This ${period}`}
        />
        <StatCard
          title="Unique Visitors"
          value={visits.unique_visitors?.toLocaleString() || '0'}
          variant="info"
          subtitle="By IP hash"
        />
        <StatCard
          title="Authenticated"
          value={visits.authenticated_visits?.toLocaleString() || '0'}
          variant="success"
          subtitle="Logged in users"
        />
        <StatCard
          title="Anonymous"
          value={visits.anonymous_visits?.toLocaleString() || '0'}
          variant="warning"
          subtitle="Guest visitors"
        />
      </div>

      {/* Charts Row */}
      <div className="admin-grid admin-grid--2 text-gray-200 admin-mt-4">
        <div className="admin-card text-gray-200">
          <BarChart 
            data={topPagesData}
            title="Top Pages"
            maxItems={8}
          />
        </div>
        <div className="admin-card">
          <DeviceBreakdown data={devices} />
        </div>
      </div>

      {/* Second Row */}
      <div className="admin-grid admin-grid--2 admin-mt-4">
        <div className="admin-card">
          <HourlyPattern data={hourlyPattern} />
        </div>
        <div className="admin-card">
          <BarChart 
            data={referrersData}
            title="Top Referrers"
            maxItems={5}
          />
        </div>
      </div>

      {/* Recent Visits */}
      <div className="admin-card admin-mt-4">
        <RecentVisits data={recentVisits} />
      </div>
    </div>
  );
}

WebsiteAnalytics.propTypes = {
  onNotify: PropTypes.func,
};
