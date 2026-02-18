/**
 * Analysis Statistics Tab
 * 
 * Displays analysis metrics, trends, and scam category breakdown.
 */

import React, { useState } from 'react';
import PropTypes from 'prop-types';
import { 
  StatCard, 
  PeriodSelector,
  LoadingSpinner, 
  ErrorMessage,
  DataTable,
  StatusBadge,
} from '../../../components/admin';
import { useAnalysisStats } from '../../../hooks/useAdminData';
import { getTopScamCategories } from '../../../api/admin';
import RiskBreakdownCard from './components/RiskBreakdownCard';
import DailyActivityChart from './components/DailyActivityChart';
import { getPercentage, getTrend } from './utils';
import './AnalysisStats.css';

export default function AnalysisStats({ onNotify }) {
  const [period, setPeriod] = useState('month');
  const [scamCategories, setScamCategories] = useState([]);
  const [loadingCategories, setLoadingCategories] = useState(false);

  const { 
    data, 
    loading, 
    error, 
    refresh 
  } = useAnalysisStats({ start: null, end: null }, period);

  // Load scam categories on mount and when period changes
  React.useEffect(() => {
    loadScamCategories();
  }, [period]);

  const loadScamCategories = async () => {
    setLoadingCategories(true);
    try {
      const response = await getTopScamCategories({ limit: 10, period });
      // API returns { success: true, data: [...categories] }
      // Add rank to each category
      const categoriesWithRank = (response.success ? (response.data || []) : []).map((cat, idx) => ({
        ...cat,
        rank: idx + 1
      }));
      setScamCategories(categoriesWithRank);
    } catch (err) {
      console.error('Failed to load scam categories:', err);
    } finally {
      setLoadingCategories(false);
    }
  };

  if (loading && !data) {
    return (
      <div className="admin-section">
        <div className="admin-section__loading">
          <LoadingSpinner size="large" />
          <p>Loading analysis statistics...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="admin-section">
        <ErrorMessage 
          message={`Failed to load analysis stats: ${error}`}
          onRetry={refresh}
        />
      </div>
    );
  }

  const stats = data || {};

  // Calculate derived values from API response fields
  const totalAnalyses = stats.total_count || 0;
  const scamDetectedCount = stats.scam_count || 0;
  const legitimateCount = stats.legitimate_count || 0;
  const scamPercentage = stats.scam_rate_percent || 0;
  const legitimatePercentage = totalAnalyses > 0 
    ? ((legitimateCount / totalAnalyses) * 100) 
    : 0;

  // Calculate trends
  const analysisTrend = getTrend(totalAnalyses, stats.previous_total_count);
  const scamTrend = getTrend(scamDetectedCount, stats.previous_scam_count);

  // Scam categories table columns
  const categoryColumns = [
    { key: 'rank', label: '#' },
    { key: 'category', label: 'Category' },
    { 
      key: 'count', 
      label: 'Detections',
      render: (value) => <strong>{(value || 0).toLocaleString()}</strong>
    },
    { 
      key: 'percentage', 
      label: 'Share',
      render: (value) => (
        <div className="analysis-stats__percentage-bar">
          <div 
            className="analysis-stats__percentage-fill" 
            style={{ width: `${value || 0}%` }}
          />
          <span>{(value || 0).toFixed(1)}%</span>
        </div>
      )
    },
    {
      key: 'severity',
      label: 'Risk Level',
      render: (value) => (
        <StatusBadge 
          status={value || 'unknown'} 
          variant={value === 'high' ? 'danger' : value === 'medium' ? 'warning' : 'success'}
        />
      )
    },
  ];

  return (
    <div className="admin-section">
      {/* Header with Filters */}
      <div className="admin-section__header">
        <h2 className="admin-section__title">Analysis Statistics</h2>
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
          title="Total Analyses"
          value={totalAnalyses.toLocaleString()}
          trend={analysisTrend.direction}
          trendValue={analysisTrend.value}
          subtitle={`${period === 'all_time' ? 'All time' : `This ${period}`}`}
        />
        <StatCard
          title="Scams Detected"
          value={scamDetectedCount.toLocaleString()}
          trend={scamTrend.direction}
          trendValue={scamTrend.value}
          variant="danger"
          subtitle={`${scamPercentage.toFixed(1)}% of total`}
        />
        <StatCard
          title="Legitimate"
          value={legitimateCount.toLocaleString()}
          variant="success"
          subtitle={`${legitimatePercentage.toFixed(1)}% of total`}
        />
        <StatCard
          title="High Risk"
          value={(stats.high_risk_count || 0).toLocaleString()}
          variant="info"
          subtitle="High confidence detections"
        />
      </div>

      {/* Detection Breakdown */}
      <div className="admin-grid admin-grid--2 admin-mt-4">
        {/* Scam Categories */}
        <div className="admin-card">
          <div className="admin-card__header">
            <h3 className="admin-card__title">Top Scam Categories</h3>
          </div>
          <DataTable
            columns={categoryColumns}
            data={scamCategories}
            loading={loadingCategories}
            emptyMessage="No scam categories found"
          />
        </div>

        {/* Analysis Breakdown by Risk Level */}
        <RiskBreakdownCard 
          stats={{ ...stats, legitimate_count: legitimateCount }}
          totalAnalyses={totalAnalyses}
          getPercentage={getPercentage}
        />
      </div>

      {/* Daily Activity Chart */}
      <div className="admin-mt-4">
        <DailyActivityChart dailyCounts={stats.daily_counts} />
      </div>
    </div>
  );
}

AnalysisStats.propTypes = {
  onNotify: PropTypes.func,
};
