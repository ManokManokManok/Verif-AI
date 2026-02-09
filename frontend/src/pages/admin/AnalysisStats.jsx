/**
 * Analysis Statistics Tab
 * 
 * Displays analysis metrics, trends, and scam category breakdown.
 */

import React, { useState } from 'react';
import PropTypes from 'prop-types';
import { 
  StatCard, 
  DateRangePicker,
  PeriodSelector,
  LoadingSpinner, 
  ErrorMessage,
  DataTable,
  StatusBadge,
} from '../../components/admin';
import { useAnalysisStats } from '../../hooks/useAdminData';
import { getTopScamCategories } from '../../api/admin';

export default function AnalysisStats({ onNotify }) {
  const [period, setPeriod] = useState('month');
  const [dateRange, setDateRange] = useState({
    start: null,
    end: null,
  });
  const [scamCategories, setScamCategories] = useState([]);
  const [loadingCategories, setLoadingCategories] = useState(false);

  const { 
    data, 
    loading, 
    error, 
    refresh 
  } = useAnalysisStats(dateRange, period);

  // Load scam categories on mount and when period changes
  React.useEffect(() => {
    loadScamCategories();
  }, [period]);

  const loadScamCategories = async () => {
    setLoadingCategories(true);
    try {
      const response = await getTopScamCategories({ limit: 10, period });
      // API returns { success: true, data: [...categories] }
      setScamCategories(response.success ? (response.data || []) : []);
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
  const getTrend = (current, previous) => {
    if (!previous || previous === 0) return { direction: 'stable', value: '0%' };
    const change = ((current - previous) / previous) * 100;
    if (change > 0) return { direction: 'up', value: `+${change.toFixed(1)}%` };
    if (change < 0) return { direction: 'down', value: `${change.toFixed(1)}%` };
    return { direction: 'stable', value: '0%' };
  };

  const analysisTrend = getTrend(totalAnalyses, stats.previous_total_count);
  const scamTrend = getTrend(scamDetectedCount, stats.previous_scam_count);

  // Scam categories table columns
  const categoryColumns = [
    { key: 'rank', label: '#', render: (_, row, idx) => idx + 1 },
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
          <DateRangePicker
            startDate={dateRange.start}
            endDate={dateRange.end}
            onStartDateChange={(date) => setDateRange(prev => ({ ...prev, start: date }))}
            onEndDateChange={(date) => setDateRange(prev => ({ ...prev, end: date }))}
          />
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
        <div className="admin-card">
          <div className="admin-card__header">
            <h3 className="admin-card__title">Risk Level Breakdown</h3>
          </div>
          <div className="analysis-stats__breakdown">
            <div className="analysis-stats__breakdown-item">
              <div className="analysis-stats__breakdown-header">
                <span className="analysis-stats__breakdown-label">🔴 High Risk</span>
                <span className="analysis-stats__breakdown-value">
                  {(stats.high_risk_count || 0).toLocaleString()}
                </span>
              </div>
              <div className="analysis-stats__breakdown-bar">
                <div 
                  className="analysis-stats__breakdown-fill analysis-stats__breakdown-fill--danger"
                  style={{ width: `${getPercentage(stats.high_risk_count, totalAnalyses)}%` }}
                />
              </div>
            </div>
            <div className="analysis-stats__breakdown-item">
              <div className="analysis-stats__breakdown-header">
                <span className="analysis-stats__breakdown-label">🟠 Medium Risk</span>
                <span className="analysis-stats__breakdown-value">
                  {(stats.medium_risk_count || 0).toLocaleString()}
                </span>
              </div>
              <div className="analysis-stats__breakdown-bar">
                <div 
                  className="analysis-stats__breakdown-fill analysis-stats__breakdown-fill--warning"
                  style={{ width: `${getPercentage(stats.medium_risk_count, totalAnalyses)}%` }}
                />
              </div>
            </div>
            <div className="analysis-stats__breakdown-item">
              <div className="analysis-stats__breakdown-header">
                <span className="analysis-stats__breakdown-label">🟡 Low Risk</span>
                <span className="analysis-stats__breakdown-value">
                  {(stats.low_risk_count || 0).toLocaleString()}
                </span>
              </div>
              <div className="analysis-stats__breakdown-bar">
                <div 
                  className="analysis-stats__breakdown-fill analysis-stats__breakdown-fill--info"
                  style={{ width: `${getPercentage(stats.low_risk_count, totalAnalyses)}%` }}
                />
              </div>
            </div>
            <div className="analysis-stats__breakdown-item">
              <div className="analysis-stats__breakdown-header">
                <span className="analysis-stats__breakdown-label">🟢 Legitimate</span>
                <span className="analysis-stats__breakdown-value">
                  {legitimateCount.toLocaleString()}
                </span>
              </div>
              <div className="analysis-stats__breakdown-bar">
                <div 
                  className="analysis-stats__breakdown-fill analysis-stats__breakdown-fill--success"
                  style={{ width: `${getPercentage(legitimateCount, totalAnalyses)}%` }}
                />
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Daily Activity Chart */}
      <div className="admin-card admin-mt-4">
        <div className="admin-card__header">
          <h3 className="admin-card__title">Daily Activity (Last 30 Days)</h3>
        </div>
        {stats.daily_counts && stats.daily_counts.length > 0 ? (
          <div className="analysis-stats__daily-chart">
            <div className="analysis-stats__chart-bars">
              {stats.daily_counts.slice(-14).map((day, idx) => {
                const maxCount = Math.max(...stats.daily_counts.map(d => d.total || 0));
                const height = maxCount > 0 ? ((day.total || 0) / maxCount) * 100 : 0;
                return (
                  <div key={idx} className="analysis-stats__chart-bar-wrapper">
                    <div 
                      className="analysis-stats__chart-bar"
                      style={{ height: `${height}%` }}
                      title={`${day.date}: ${day.total || 0} analyses (${day.scams || 0} scams)`}
                    >
                      <div 
                        className="analysis-stats__chart-bar-scam"
                        style={{ height: `${day.total > 0 ? ((day.scams || 0) / day.total) * 100 : 0}%` }}
                      />
                    </div>
                    <span className="analysis-stats__chart-label">
                      {new Date(day.date).getDate()}
                    </span>
                  </div>
                );
              })}
            </div>
            <div className="analysis-stats__chart-legend">
              <span className="analysis-stats__legend-item">
                <span className="analysis-stats__legend-color analysis-stats__legend-color--total" />
                Total
              </span>
              <span className="analysis-stats__legend-item">
                <span className="analysis-stats__legend-color analysis-stats__legend-color--scam" />
                Scams Detected
              </span>
            </div>
          </div>
        ) : (
          <div className="analysis-stats__chart-empty">
            <p>📊 No activity data available for the selected period</p>
            <p className="analysis-stats__chart-hint">
              Data will appear as analyses are performed
            </p>
          </div>
        )}
      </div>

      <style>{`
        .admin-section__loading {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          min-height: 400px;
          color: var(--admin-text-muted);
        }

        .analysis-stats__percentage-bar {
          display: flex;
          align-items: center;
          gap: 0.5rem;
        }

        .analysis-stats__percentage-fill {
          height: 8px;
          background: var(--admin-primary);
          border-radius: 4px;
          min-width: 4px;
        }

        .analysis-stats__breakdown {
          display: flex;
          flex-direction: column;
          gap: 1.5rem;
          padding: 1rem 0;
        }

        .analysis-stats__breakdown-item {
          display: flex;
          flex-direction: column;
          gap: 0.5rem;
        }

        .analysis-stats__breakdown-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
        }

        .analysis-stats__breakdown-label {
          font-size: 0.875rem;
          color: var(--admin-text);
        }

        .analysis-stats__breakdown-value {
          font-size: 0.875rem;
          font-weight: 600;
          color: var(--admin-text);
        }

        .analysis-stats__breakdown-bar {
          height: 8px;
          background: var(--admin-border);
          border-radius: 4px;
          overflow: hidden;
        }

        .analysis-stats__breakdown-fill {
          height: 100%;
          border-radius: 4px;
          transition: width 0.3s ease;
        }

        .analysis-stats__breakdown-fill--url {
          background: var(--admin-info);
        }

        .analysis-stats__breakdown-fill--text {
          background: var(--admin-success);
        }

        .analysis-stats__breakdown-fill--image {
          background: var(--admin-warning);
        }

        .analysis-stats__breakdown-fill--blockchain {
          background: var(--admin-primary);
        }

        .analysis-stats__chart-placeholder {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          min-height: 200px;
          background: var(--admin-bg-hover);
          border-radius: var(--admin-radius-sm);
          color: var(--admin-text-muted);
        }

        .analysis-stats__chart-hint {
          font-size: 0.75rem;
          margin-top: 0.5rem;
        }
      `}</style>
    </div>
  );
}

AnalysisStats.propTypes = {
  onNotify: PropTypes.func,
};

// Helper function
function getPercentage(value, total) {
  if (!total || total === 0) return 0;
  return ((value || 0) / total) * 100;
}
