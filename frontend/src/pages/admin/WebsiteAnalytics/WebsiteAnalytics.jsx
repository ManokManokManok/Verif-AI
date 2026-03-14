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
} from '../../../components/admin';
import { useAnalytics } from '../../../hooks/useAdminData';
import BarChart from './components/BarChart';
import DeviceBreakdown from './components/DeviceBreakdown';
import HourlyPattern from './components/HourlyPattern';
import RecentVisits from './components/RecentVisits';
import './WebsiteAnalytics.css';

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

  const totalVisits = visits.total_visits || 0;
  const authRate = totalVisits > 0
    ? (((visits.authenticated_visits || 0) / totalVisits) * 100).toFixed(1)
    : '0.0';
  const anonRate = totalVisits > 0
    ? (((visits.anonymous_visits || 0) / totalVisits) * 100).toFixed(1)
    : '0.0';
  const uniqueRate = totalVisits > 0
    ? (((visits.unique_visitors || 0) / totalVisits) * 100).toFixed(1)
    : '0.0';

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

      {/* Rate Summary Banner */}
      <div className="analytics-rate-banner admin-mt-4">
        <div className="analytics-rate-item">
          <span className="analytics-rate-label">Auth Rate</span>
          <span className="analytics-rate-value analytics-rate-value--success">{authRate}%</span>
        </div>
        <div className="analytics-rate-divider" />
        <div className="analytics-rate-item">
          <span className="analytics-rate-label">Anonymous Rate</span>
          <span className="analytics-rate-value analytics-rate-value--warning">{anonRate}%</span>
        </div>
        <div className="analytics-rate-divider" />
        <div className="analytics-rate-item">
          <span className="analytics-rate-label">Unique Visitor Rate</span>
          <span className="analytics-rate-value analytics-rate-value--info">{uniqueRate}%</span>
        </div>
        {topPagesData.length > 0 && (
          <>
            <div className="analytics-rate-divider" />
            <div className="analytics-rate-item">
              <span className="analytics-rate-label">Top Page</span>
              <span className="analytics-rate-value analytics-rate-value--page">
                {topPagesData[0].label}
              </span>
            </div>
          </>
        )}
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
