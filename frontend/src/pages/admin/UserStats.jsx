/**
 * User Statistics Tab
 * 
 * Displays user metrics and user reports management.
 */

import React, { useState } from 'react';
import PropTypes from 'prop-types';
import { 
  StatCard, 
  DataTable,
  StatusBadge,
  PeriodSelector,
  LoadingSpinner, 
  ErrorMessage,
  ConfirmModal,
} from '../../components/admin';
import { useUserStats, useUserReports } from '../../hooks/useAdminData';

export default function UserStats({ onNotify }) {
  const [period, setPeriod] = useState('month');
  const [reportFilter, setReportFilter] = useState('pending');
  const [selectedReport, setSelectedReport] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [modalAction, setModalAction] = useState(null);

  const { 
    data: stats, 
    loading: statsLoading, 
    error: statsError, 
    refresh: refreshStats 
  } = useUserStats({ start: null, end: null }, period);

  const {
    data: reportsData,
    loading: reportsLoading,
    error: reportsError,
    refresh: refreshReports,
    updateStatus,
  } = useUserReports(reportFilter);

  // Handle report status update
  const handleUpdateReport = async (status) => {
    if (!selectedReport) return;
    
    try {
      await updateStatus(selectedReport.id, status, `Status updated to ${status} by admin`);
      onNotify?.('success', `Report marked as ${status}`);
      setIsModalOpen(false);
      setSelectedReport(null);
    } catch (err) {
      onNotify?.('error', `Failed to update report: ${err.message}`);
    }
  };

  // Open confirmation modal
  const openModal = (report, action) => {
    setSelectedReport(report);
    setModalAction(action);
    setIsModalOpen(true);
  };

  // Report table columns
  const reportColumns = [
    { 
      key: 'id', 
      label: 'ID',
      render: (value) => <code>#{value.slice(0, 8)}</code>
    },
    { 
      key: 'reported_by', 
      label: 'Reporter',
      render: (value) => value?.username || 'Anonymous'
    },
    { 
      key: 'report_type', 
      label: 'Type',
      render: (value) => (
        <StatusBadge status={value} variant="info" />
      )
    },
    { 
      key: 'reason', 
      label: 'Reason',
      render: (value) => (
        <span className="user-stats__truncate">{value}</span>
      )
    },
    { 
      key: 'status', 
      label: 'Status',
      render: (value) => <StatusBadge status={value} />
    },
    { 
      key: 'created_at', 
      label: 'Date',
      render: (value) => new Date(value).toLocaleDateString()
    },
    {
      key: 'actions',
      label: 'Actions',
      render: (_, row) => (
        <div className="user-stats__actions">
          {row.status === 'pending' && (
            <>
              <button
                className="admin-btn admin-btn--sm admin-btn--primary"
                onClick={() => openModal(row, 'resolve')}
              >
                Resolve
              </button>
              <button
                className="admin-btn admin-btn--sm admin-btn--ghost"
                onClick={() => openModal(row, 'dismiss')}
              >
                Dismiss
              </button>
            </>
          )}
          {row.status !== 'pending' && (
            <span className="user-stats__resolved-text">
              {row.status === 'resolved' ? '✓ Resolved' : '✗ Dismissed'}
            </span>
          )}
        </div>
      )
    },
  ];

  if (statsLoading && !stats) {
    return (
      <div className="admin-section">
        <div className="admin-section__loading">
          <LoadingSpinner size="large" />
          <p>Loading user statistics...</p>
        </div>
      </div>
    );
  }

  if (statsError) {
    return (
      <div className="admin-section">
        <ErrorMessage 
          message={`Failed to load user stats: ${statsError}`}
          onRetry={refreshStats}
        />
      </div>
    );
  }

  const userStats = stats || {};
  const reports = reportsData?.reports || [];

  return (
    <div className="admin-section">
      {/* Header */}
      <div className="admin-section__header">
        <h2 className="admin-section__title">User Statistics</h2>
        <div className="admin-section__actions">
          <PeriodSelector value={period} onChange={setPeriod} />
          <button 
            className="admin-btn admin-btn--secondary admin-btn--sm"
            onClick={refreshStats}
            disabled={statsLoading}
          >
            {statsLoading ? 'Refreshing...' : 'Refresh'}
          </button>
        </div>
      </div>

      {/* Overview Stats */}
      <div className="admin-grid admin-grid--4">
        <StatCard
          title="Total Users"
          value={userStats.total_users?.toLocaleString() || '0'}
          subtitle="Registered accounts"
        />
        <StatCard
          title="Active Users"
          value={(userStats.active_users_count || userStats.active_users || 0).toLocaleString()}
          variant="success"
          subtitle={`${getPercentage(userStats.active_users_count || userStats.active_users, userStats.total_users)}% of total`}
        />
        <StatCard
          title="New Users"
          value={(userStats.new_users_count || userStats.new_users || 0).toLocaleString()}
          variant="info"
          subtitle={`This ${period}`}
        />
        <StatCard
          title="Verified Users"
          value={(userStats.verified_users_count || userStats.verified_users || 0).toLocaleString()}
          subtitle={`${getPercentage(userStats.verified_users_count || userStats.verified_users, userStats.total_users)}% verified`}
        />
      </div>

      {/* User Engagement Stats */}
      <div className="admin-grid admin-grid--3 admin-mt-4">
        <StatCard
          title="Total Analyses"
          value={(userStats.total_analyses_by_users || userStats.total_user_analyses || 0).toLocaleString()}
          subtitle="By all users"
        />
        <StatCard
          title="Avg per User"
          value={(userStats.avg_analyses_per_user || 0).toFixed(1)}
          subtitle="Analyses average"
        />
        <StatCard
          title="Power Users"
          value={userStats.power_users?.toLocaleString() || '0'}
          variant="warning"
          subtitle=">50 analyses"
        />
      </div>

      {/* User Reports Section */}
      <div className="admin-card admin-mt-4">
        <div className="admin-card__header">
          <h3 className="admin-card__title">User Reports</h3>
          <div className="user-stats__report-filters">
            {['pending', 'resolved', 'dismissed', 'all'].map((status) => (
              <button
                key={status}
                className={`admin-btn admin-btn--sm ${
                  reportFilter === status ? 'admin-btn--primary' : 'admin-btn--ghost'
                }`}
                onClick={() => setReportFilter(status)}
              >
                {status.charAt(0).toUpperCase() + status.slice(1)}
                {status === 'pending' && userStats.pending_reports > 0 && (
                  <span className="user-stats__badge">{userStats.pending_reports}</span>
                )}
              </button>
            ))}
          </div>
        </div>

        {reportsError ? (
          <ErrorMessage 
            message={`Failed to load reports: ${reportsError}`}
            onRetry={refreshReports}
          />
        ) : (
          <DataTable
            columns={reportColumns}
            data={reports}
            loading={reportsLoading}
            emptyMessage={`No ${reportFilter === 'all' ? '' : reportFilter} reports found`}
            pagination={reportsData?.pagination}
            onPageChange={(page) => {
              // Handle pagination - would need to update the hook
              console.log('Page change:', page);
            }}
          />
        )}
      </div>

      {/* User Role Distribution */}
      <div className="admin-card admin-mt-4">
        <div className="admin-card__header">
          <h3 className="admin-card__title">User Role Distribution</h3>
        </div>
        <div className="user-stats__roles">
          {userStats.role_distribution ? (
            Object.entries(userStats.role_distribution).map(([role, count]) => (
              <div key={role} className="user-stats__role-item">
                <div className="user-stats__role-header">
                  <span className="user-stats__role-name">{formatRole(role)}</span>
                  <span className="user-stats__role-count">{count.toLocaleString()}</span>
                </div>
                <div className="user-stats__role-bar">
                  <div 
                    className="user-stats__role-fill"
                    style={{ 
                      width: `${getPercentage(count, userStats.total_users)}%`,
                      background: getRoleColor(role)
                    }}
                  />
                </div>
              </div>
            ))
          ) : (
            <p className="user-stats__no-data">No role distribution data available</p>
          )}
        </div>
      </div>

      {/* Confirmation Modal */}
      <ConfirmModal
        isOpen={isModalOpen}
        title={modalAction === 'resolve' ? 'Resolve Report' : 'Dismiss Report'}
        message={
          modalAction === 'resolve'
            ? 'Are you sure you want to mark this report as resolved? This indicates the issue has been addressed.'
            : 'Are you sure you want to dismiss this report? This indicates the report is invalid or doesn\'t require action.'
        }
        confirmLabel={modalAction === 'resolve' ? 'Resolve' : 'Dismiss'}
        variant={modalAction === 'resolve' ? 'info' : 'warning'}
        onConfirm={() => handleUpdateReport(modalAction === 'resolve' ? 'resolved' : 'dismissed')}
        onCancel={() => {
          setIsModalOpen(false);
          setSelectedReport(null);
        }}
      />

      <style>{`
        .admin-section__loading {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          min-height: 400px;
          color: var(--admin-text-muted);
        }

        .user-stats__report-filters {
          display: flex;
          gap: 0.5rem;
        }

        .user-stats__badge {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          min-width: 20px;
          height: 20px;
          padding: 0 6px;
          background: var(--admin-danger);
          color: white;
          border-radius: 10px;
          font-size: 0.75rem;
          font-weight: 600;
          margin-left: 0.5rem;
        }

        .user-stats__actions {
          display: flex;
          gap: 0.5rem;
        }

        .user-stats__truncate {
          display: block;
          max-width: 200px;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }

        .user-stats__resolved-text {
          font-size: 0.75rem;
          color: var(--admin-text-muted);
        }

        .user-stats__roles {
          display: flex;
          flex-direction: column;
          gap: 1rem;
          padding: 1rem 0;
        }

        .user-stats__role-item {
          display: flex;
          flex-direction: column;
          gap: 0.5rem;
        }

        .user-stats__role-header {
          display: flex;
          justify-content: space-between;
        }

        .user-stats__role-name {
          font-size: 0.875rem;
          color: var(--admin-text);
          font-weight: 500;
        }

        .user-stats__role-count {
          font-size: 0.875rem;
          color: var(--admin-text-muted);
        }

        .user-stats__role-bar {
          height: 8px;
          background: var(--admin-border);
          border-radius: 4px;
          overflow: hidden;
        }

        .user-stats__role-fill {
          height: 100%;
          border-radius: 4px;
          transition: width 0.3s ease;
        }

        .user-stats__no-data {
          color: var(--admin-text-muted);
          text-align: center;
          padding: 2rem;
        }

        code {
          font-family: monospace;
          font-size: 0.875rem;
          color: var(--admin-primary);
        }
      `}</style>
    </div>
  );
}

UserStats.propTypes = {
  onNotify: PropTypes.func,
};

// Helper functions
function getPercentage(value, total) {
  if (!total || total === 0) return '0';
  return ((value || 0) / total * 100).toFixed(1);
}

function formatRole(role) {
  return role.split('_').map(word => 
    word.charAt(0).toUpperCase() + word.slice(1)
  ).join(' ');
}

function getRoleColor(role) {
  const colors = {
    admin: 'var(--admin-danger)',
    moderator: 'var(--admin-warning)',
    analyst: 'var(--admin-info)',
    premium_user: 'var(--admin-primary)',
    user: 'var(--admin-success)',
  };
  return colors[role] || 'var(--admin-text-muted)';
}
