/**
 * Model Health Tab
 * 
 * Displays real-time system metrics: CPU, GPU, Memory usage.
 */

import React from 'react';
import PropTypes from 'prop-types';
import { 
  StatCard, 
  LoadingSpinner, 
  ErrorMessage 
} from '../../../components/admin';
import { useModelHealth } from '../../../hooks/useAdminData';
import SystemGaugeCard from './components/SystemGaugeCard';
import SystemInfoCard from './components/SystemInfoCard';
import { formatBytes, formatUptime } from './utils';
import './ModelHealth.css';

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
    cache_connected: rawMetrics.cache?.connected !== false,
    
    // Model metrics
    model_loaded: rawMetrics.model?.name ? true : false,
    model_name: rawMetrics.model?.name || 'Unknown',
    token_count_today: rawMetrics.model?.token_count_today || 0,
    requests_today: rawMetrics.model?.requests_today || 0,
    
    // System metrics
    uptime_seconds: rawMetrics.system?.uptime_seconds || 0,
    uptime_formatted: rawMetrics.system?.uptime_formatted || '0s',
    
    // Additional info
    platform: rawMetrics.system?.platform || 'Unknown',
    python_version: rawMetrics.system?.python_version || 'Unknown',
    django_version: rawMetrics.system?.django_version || 'Unknown',
    database_connected: rawMetrics.database?.connected !== false,
  };

  // Prepare gauge data
  const gauges = [
    {
      label: 'CPU Usage',
      value: metrics.cpu_percent,
      maxValue: 100,
      unit: '%',
      thresholds: { warning: 70, danger: 90 },
      details: [
        { label: 'Cores', value: metrics.cpu_count || 'N/A' },
        { label: 'Load Average', value: metrics.load_average ? metrics.load_average.toFixed(2) : 'N/A' },
      ],
    },
    {
      label: 'Memory Usage',
      value: metrics.memory_percent,
      maxValue: 100,
      unit: '%',
      thresholds: { warning: 75, danger: 90 },
      details: [
        { label: 'Used', value: formatBytes(metrics.memory_used) },
        { label: 'Total', value: formatBytes(metrics.memory_total) },
      ],
    },
    {
      label: 'GPU Usage',
      value: metrics.gpu_percent,
      maxValue: 100,
      unit: '%',
      thresholds: { warning: 80, danger: 95 },
      details: [
        { label: 'GPU Memory', value: metrics.gpu_memory_percent ? `${metrics.gpu_memory_percent.toFixed(1)}%` : 'N/A' },
        { label: 'Status', value: metrics.gpu_available ? 'Available' : 'Unavailable' },
      ],
    },
    {
      label: 'Disk Usage',
      value: metrics.disk_percent,
      maxValue: 100,
      unit: '%',
      thresholds: { warning: 75, danger: 90 },
      details: [
        { label: 'Used', value: formatBytes(metrics.disk_used) },
        { label: 'Total', value: formatBytes(metrics.disk_total) },
      ],
    },
  ];

  // Prepare system info
  const systemInfo = [
    { label: 'Platform', value: metrics.platform },
    { label: 'Python Version', value: metrics.python_version },
    { label: 'Django Version', value: metrics.django_version },
    { label: 'Database Status', value: metrics.database_connected ? '✅ Connected' : '❌ Disconnected' },
    { label: 'Cache Status', value: metrics.cache_connected ? '✅ Connected' : '❌ Disconnected' },
  ];

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
        {gauges.map((gauge, index) => (
          <SystemGaugeCard key={index} {...gauge} />
        ))}
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
      <div className="admin-mt-4">
        <SystemInfoCard info={systemInfo} />
      </div>
    </div>
  );
}

ModelHealth.propTypes = {
  onNotify: PropTypes.func,
};
