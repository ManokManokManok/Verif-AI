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
import { exportAnalysisStats } from '../../../api/admin';
import { useAuth } from '../../../context/AuthContext';
import RiskBreakdownCard from './components/RiskBreakdownCard';
import DailyActivityChart from './components/DailyActivityChart';
import { getPercentage, getTrend } from './utils';
import './AnalysisStats.css';

export default function AnalysisStats({ onNotify }) {
  const { user } = useAuth();
  const [period, setPeriod] = useState('month');
  const [exportingFormat, setExportingFormat] = useState(null);

  const { 
    data, 
    categories,
    loading, 
    error, 
    refresh 
  } = useAnalysisStats({ start: null, end: null }, period);

  const handleExport = async (format) => {
    setExportingFormat(format);
    try {
      const { blob, filename } = await exportAnalysisStats({
        period,
        format,
        limit: 10,
        preferClientExport: true,
        fallbackData: {
          stats: data || {},
          categories: categories || [],
        },
        fallbackMeta: {
          generatedBy: user?.email || user?.username || 'admin',
          timezone: Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC',
          filtersApplied: `period=${period};limit=10;format=${format}`,
        },
      });

      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);

      onNotify?.('success', `Analysis stats exported as ${format.toUpperCase()}`);
    } catch (err) {
      onNotify?.('error', err.message || 'Failed to export analysis stats');
    } finally {
      setExportingFormat(null);
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
  const scamCategories = (categories || []).map((cat, idx) => ({
    ...cat,
    rank: idx + 1,
  }));

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
  const hasAnalysisBaseline = Number(stats.previous_total_count) > 0;
  const hasScamBaseline = Number(stats.previous_scam_count) > 0;

  // Compute max category percentage for relative bar width scaling
  const maxCategoryPercentage = scamCategories.length > 0
    ? Math.max(...scamCategories.map(c => c.percentage || 0), 1)
    : 100;

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
      render: (value) => {
        const relWidth = ((value || 0) / maxCategoryPercentage) * 100;
        return (
          <div className="analysis-stats__percentage-bar">
            <div className="analysis-stats__percentage-track">
              <div 
                className="analysis-stats__percentage-fill" 
                style={{ width: `${relWidth}%` }}
              />
            </div>
            <span className="analysis-stats__percentage-text">{(value || 0).toFixed(1)}%</span>
          </div>
        );
      }
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
            className="admin-btn admin-btn--primary admin-btn--sm"
            onClick={() => handleExport('csv')}
            disabled={loading || exportingFormat !== null}
          >
            {exportingFormat === 'csv' ? 'Exporting CSV...' : 'Export CSV'}
          </button>
          <button
            className="admin-btn admin-btn--secondary admin-btn--sm"
            onClick={() => handleExport('excel')}
            disabled={loading || exportingFormat !== null}
          >
            {exportingFormat === 'excel' ? 'Exporting Excel...' : 'Export Excel'}
          </button>
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
          trend={hasAnalysisBaseline ? analysisTrend.direction : undefined}
          trendValue={hasAnalysisBaseline ? analysisTrend.value : undefined}
          subtitle={`${period === 'all_time' ? 'All time' : `This ${period}`}`}
        />
        <StatCard
          title="Scams Detected"
          value={scamDetectedCount.toLocaleString()}
          trend={hasScamBaseline ? scamTrend.direction : undefined}
          trendValue={hasScamBaseline ? scamTrend.value : undefined}
          variant="danger"
          subtitle={`${scamPercentage.toFixed(1)}% detection rate`}
        />
        <StatCard
          title="Legitimate"
          value={legitimateCount.toLocaleString()}
          variant="success"
          subtitle={`${legitimatePercentage.toFixed(1)}% pass rate`}
        />
        <StatCard
          title="High Risk"
          value={(stats.high_risk_count || 0).toLocaleString()}
          variant="danger"
          subtitle={`${totalAnalyses > 0 ? (((stats.high_risk_count || 0) / totalAnalyses) * 100).toFixed(1) : '0.0'}% of total`}
        />
      </div>

      {/* Rate Summary Banner */}
      <div className="analysis-stats__rate-banner admin-mt-4">
        <div className="analysis-stats__rate-item">
          <span className="analysis-stats__rate-label">Detection Rate</span>
          <span className="analysis-stats__rate-value analysis-stats__rate-value--danger">
            {scamPercentage.toFixed(1)}%
          </span>
        </div>
        <div className="analysis-stats__rate-divider" />
        <div className="analysis-stats__rate-item">
          <span className="analysis-stats__rate-label">High Risk Rate</span>
          <span className="analysis-stats__rate-value analysis-stats__rate-value--high">
            {totalAnalyses > 0 ? (((stats.high_risk_count || 0) / totalAnalyses) * 100).toFixed(1) : '0.0'}%
          </span>
        </div>
        <div className="analysis-stats__rate-divider" />
        <div className="analysis-stats__rate-item">
          <span className="analysis-stats__rate-label">Medium Risk Rate</span>
          <span className="analysis-stats__rate-value analysis-stats__rate-value--medium">
            {totalAnalyses > 0 ? (((stats.medium_risk_count || 0) / totalAnalyses) * 100).toFixed(1) : '0.0'}%
          </span>
        </div>
        {stats.top_scam_category && (
          <>
            <div className="analysis-stats__rate-divider" />
            <div className="analysis-stats__rate-item">
              <span className="analysis-stats__rate-label">Top Category</span>
              <span className="analysis-stats__rate-value analysis-stats__rate-value--category">
                {stats.top_scam_category.replace(/_/g, ' ')}
              </span>
            </div>
          </>
        )}
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
            loading={loading}
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
