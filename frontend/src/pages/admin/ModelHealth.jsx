/**
 * Model Health Tab
 * 
 * Displays real-time system metrics: CPU, GPU, Memory usage.
 */

import React from 'react';
import PropTypes from 'prop-types';
import { 
  MetricGauge, 
  StatCard, 
  LoadingSpinner, 
  ErrorMessage 
} from '../../components/admin';
import { useModelHealth } from '../../hooks/useAdminData';

export default function ModelHealth({ onNotify }) {
  const { 
    data, 
    loading, 
    error, 
    refresh, 
    lastUpdated 
  } = useModelHealth(30000); // Refresh every 30 seconds

  if (loading && !data) {
    return (
      <div className="admin-section">
        <div className="admin-section__loading">
          <LoadingSpinner size="large" />
          <p>Loading model health metrics...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="admin-section">
        <ErrorMessage 
          message={`Failed to load model health: ${error}`}
          onRetry={refresh}
        />
      </div>
    );
  }

  const rawMetrics = data || {};
  
  // Flatten nested API response structure for easier access
  const metrics = {
    // CPU metrics
    cpu_percent: rawMetrics.cpu?.usage_percent || 0,
    cpu_count: rawMetrics.cpu?.count || 0,
    load_average: rawMetrics.cpu?.load_average,
    
    // Memory metrics (convert MB to bytes for formatBytes helper)
    memory_percent: rawMetrics.memory?.usage_percent || 0,
    memory_used: (rawMetrics.memory?.used_mb || 0) * 1024 * 1024,
    memory_total: (rawMetrics.memory?.total_mb || 0) * 1024 * 1024,
    
    // GPU metrics
    gpu_percent: rawMetrics.gpu?.usage_percent || 0,
    gpu_memory_percent: rawMetrics.gpu?.memory_usage_percent || 0,
    gpu_available: rawMetrics.gpu?.available || false,
    
    // Disk metrics (convert MB to bytes for formatBytes helper)
    disk_percent: rawMetrics.disk?.usage_percent || 0,
    disk_used: (rawMetrics.disk?.used_mb || 0) * 1024 * 1024,
    disk_total: (rawMetrics.disk?.total_mb || 0) * 1024 * 1024,
    
    // Active sessions
    active_sessions: rawMetrics.active_sessions || 0,
    
    // Cache metrics
    cache_hit_rate: rawMetrics.cache?.hit_rate || 0,
    cache_size: (rawMetrics.cache?.size_mb || 0) * 1024 * 1024,
    
    // Model metrics
    model_loaded: rawMetrics.model?.name ? true : false,
    model_name: rawMetrics.model?.name || 'Unknown',
    token_count_today: rawMetrics.model?.token_count_today || 0,
    requests_today: rawMetrics.model?.requests_today || 0,
    
    // System metrics
    uptime_seconds: rawMetrics.system?.uptime_seconds || 0,
    uptime_formatted: rawMetrics.system?.uptime_formatted || '0s',
    
    // Additional info
    platform: 'Linux',
    python_version: '3.x',
    django_version: '4.x',
    database_connected: true,
  };

  return (
    <div className="admin-section">
      {/* Header */}
      <div className="admin-section__header">
        <h2 className="admin-section__title">System Health Metrics</h2>
        <div className="admin-section__actions">
          {lastUpdated && (
            <span className="admin-text-muted" style={{ fontSize: '0.75rem' }}>
              Last updated: {new Date(lastUpdated).toLocaleTimeString()}
            </span>
          )}
          <button 
            className="admin-btn admin-btn--secondary admin-btn--sm"
            onClick={refresh}
            disabled={loading}
          >
            {loading ? 'Refreshing...' : 'Refresh'}
          </button>
        </div>
      </div>

      {/* Main Gauges */}
      <div className="model-health__gauges">
        <div className="model-health__gauge-card admin-card">
          <MetricGauge
            label="CPU Usage"
            value={metrics.cpu_percent || 0}
            maxValue={100}
            unit="%"
            thresholds={{ warning: 70, danger: 90 }}
            size="large"
          />
          <div className="model-health__gauge-details">
            <div className="model-health__detail">
              <span className="model-health__detail-label">Cores</span>
              <span className="model-health__detail-value">{metrics.cpu_count || 'N/A'}</span>
            </div>
            <div className="model-health__detail">
              <span className="model-health__detail-label">Load Average</span>
              <span className="model-health__detail-value">
                {metrics.load_average ? metrics.load_average.toFixed(2) : 'N/A'}
              </span>
            </div>
          </div>
        </div>

        <div className="model-health__gauge-card admin-card">
          <MetricGauge
            label="Memory Usage"
            value={metrics.memory_percent || 0}
            maxValue={100}
            unit="%"
            thresholds={{ warning: 75, danger: 90 }}
            size="large"
          />
          <div className="model-health__gauge-details">
            <div className="model-health__detail">
              <span className="model-health__detail-label">Used</span>
              <span className="model-health__detail-value">
                {formatBytes(metrics.memory_used)}
              </span>
            </div>
            <div className="model-health__detail">
              <span className="model-health__detail-label">Total</span>
              <span className="model-health__detail-value">
                {formatBytes(metrics.memory_total)}
              </span>
            </div>
          </div>
        </div>

        <div className="model-health__gauge-card admin-card">
          <MetricGauge
            label="GPU Usage"
            value={metrics.gpu_percent || 0}
            maxValue={100}
            unit="%"
            thresholds={{ warning: 80, danger: 95 }}
            size="large"
          />
          <div className="model-health__gauge-details">
            <div className="model-health__detail">
              <span className="model-health__detail-label">GPU Memory</span>
              <span className="model-health__detail-value">
                {metrics.gpu_memory_percent ? `${metrics.gpu_memory_percent.toFixed(1)}%` : 'N/A'}
              </span>
            </div>
            <div className="model-health__detail">
              <span className="model-health__detail-label">Status</span>
              <span className="model-health__detail-value">
                {metrics.gpu_available ? 'Available' : ' Unavailable'}
              </span>
            </div>
          </div>
        </div>

        <div className="model-health__gauge-card admin-card">
          <MetricGauge
            label="Disk Usage"
            value={metrics.disk_percent || 0}
            maxValue={100}
            unit="%"
            thresholds={{ warning: 75, danger: 90 }}
            size="large"
          />
          <div className="model-health__gauge-details">
            <div className="model-health__detail">
              <span className="model-health__detail-label">Used</span>
              <span className="model-health__detail-value">
                {formatBytes(metrics.disk_used)}
              </span>
            </div>
            <div className="model-health__detail">
              <span className="model-health__detail-label">Total</span>
              <span className="model-health__detail-value">
                {formatBytes(metrics.disk_total)}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Additional Stats */}
      <div className="model-health__stats admin-grid admin-grid--4 admin-mt-4">
        <StatCard
          title="Active Sessions"
          value={metrics.active_sessions || 0}
          subtitle="Current connections"
          variant={metrics.active_sessions > 100 ? 'warning' : 'default'}
        />
        <StatCard
          title="Model Status"
          value={metrics.model_loaded ? 'Loaded' : 'Not Loaded'}
          subtitle={metrics.model_name || 'Unknown model'}
          variant={metrics.model_loaded ? 'success' : 'warning'}
        />
        <StatCard
          title="Uptime"
          value={metrics.uptime_formatted || formatUptime(metrics.uptime_seconds)}
          subtitle="System uptime"
        />
        <StatCard
          title="Cache Status"
          value={`${metrics.cache_hit_rate.toFixed(1)}%`}
          subtitle={`Hit rate (${formatBytes(metrics.cache_size)} cached)`}
          variant={metrics.cache_hit_rate > 80 ? 'success' : metrics.cache_hit_rate > 50 ? 'default' : 'warning'}
        />
      </div>

      {/* System Info Card */}
      <div className="admin-card admin-mt-4">
        <h3 className="admin-card__title">System Information</h3>
        <div className="model-health__system-info">
          <div className="model-health__info-row">
            <span className="model-health__info-label">Platform</span>
            <span className="model-health__info-value">{metrics.platform || 'Unknown'}</span>
          </div>
          <div className="model-health__info-row">
            <span className="model-health__info-label">Python Version</span>
            <span className="model-health__info-value">{metrics.python_version || 'Unknown'}</span>
          </div>
          <div className="model-health__info-row">
            <span className="model-health__info-label">Django Version</span>
            <span className="model-health__info-value">{metrics.django_version || 'Unknown'}</span>
          </div>
          <div className="model-health__info-row">
            <span className="model-health__info-label">Database Status</span>
            <span className="model-health__info-value">
              {metrics.database_connected ? '✅ Connected' : '❌ Disconnected'}
            </span>
          </div>
          <div className="model-health__info-row">
            <span className="model-health__info-label">Cache Status</span>
            <span className="model-health__info-value">
              {metrics.cache_connected ? '✅ Connected' : '❌ Disconnected'}
            </span>
          </div>
        </div>
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

        .model-health__gauges {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: 1.5rem;
        }

        @media (max-width: 1024px) {
          .model-health__gauges {
            grid-template-columns: repeat(2, 1fr);
          }
        }

        @media (max-width: 640px) {
          .model-health__gauges {
            grid-template-columns: 1fr;
          }
        }

        .model-health__gauge-card {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 1.5rem;
          padding: 2rem;
        }

        .model-health__gauge-details {
          display: flex;
          gap: 2rem;
          width: 100%;
          justify-content: center;
        }

        .model-health__detail {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 0.25rem;
        }

        .model-health__detail-label {
          font-size: 0.75rem;
          color: var(--admin-text-muted);
          text-transform: uppercase;
          letter-spacing: 0.05em;
        }

        .model-health__detail-value {
          font-size: 0.875rem;
          color: var(--admin-text);
          font-weight: 500;
        }

        .model-health__system-info {
          display: grid;
          grid-template-columns: repeat(2, 1fr);
          gap: 1rem;
          margin-top: 1rem;
        }

        @media (max-width: 640px) {
          .model-health__system-info {
            grid-template-columns: 1fr;
          }
        }

        .model-health__info-row {
          display: flex;
          justify-content: space-between;
          padding: 0.75rem;
          background: var(--admin-bg-hover);
          border-radius: var(--admin-radius-sm);
        }

        .model-health__info-label {
          color: var(--admin-text-muted);
          font-size: 0.875rem;
        }

        .model-health__info-value {
          color: var(--admin-text);
          font-size: 0.875rem;
          font-weight: 500;
        }

        .admin-text-muted {
          color: var(--admin-text-muted);
        }
      `}</style>
    </div>
  );
}

ModelHealth.propTypes = {
  onNotify: PropTypes.func,
};

// Utility functions
function formatBytes(bytes) {
  if (!bytes) return 'N/A';
  const units = ['B', 'KB', 'MB', 'GB', 'TB'];
  let unitIndex = 0;
  let size = bytes;
  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024;
    unitIndex++;
  }
  return `${size.toFixed(1)} ${units[unitIndex]}`;
}

function formatUptime(seconds) {
  if (!seconds) return 'N/A';
  const days = Math.floor(seconds / 86400);
  const hours = Math.floor((seconds % 86400) / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  
  if (days > 0) return `${days}d ${hours}h`;
  if (hours > 0) return `${hours}h ${minutes}m`;
  return `${minutes}m`;
}
