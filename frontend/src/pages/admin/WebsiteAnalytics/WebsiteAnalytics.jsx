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
