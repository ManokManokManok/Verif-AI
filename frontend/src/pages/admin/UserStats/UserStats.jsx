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
} from '../../../components/admin';
import { useUserStats, useUserReports } from '../../../hooks/useAdminData';
import { getReportDetails } from '../../../api/admin';
import ReportDetailsModal from './components/ReportDetailsModal';
import { getPercentage } from './utils';
import './UserStats.css';

export default function UserStats({ onNotify }) {
  const [period, setPeriod] = useState('month');
  const [reportFilter, setReportFilter] = useState('pending');
  const [selectedReport, setSelectedReport] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [modalAction, setModalAction] = useState(null);
  const [viewReportModal, setViewReportModal] = useState(false);
  const [selectedReportDetails, setSelectedReportDetails] = useState(null);
  const [loadingDetails, setLoadingDetails] = useState(false);

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

  // Handle viewing report details
  const handleViewReport = async (report) => {
    setLoadingDetails(true);
    setViewReportModal(true);
    try {
      const response = await getReportDetails(report.id || report.report_id);
      if (response.success) {
        setSelectedReportDetails(response.data);
      } else {
        onNotify?.('error', 'Failed to load report details');
        setViewReportModal(false);
      }
    } catch (err) {
      onNotify?.('error', `Error loading report: ${err.message}`);
      setViewReportModal(false);
    } finally {
      setLoadingDetails(false);
    }
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
      render: (value, row) => value?.username || value?.email || row?.user_email || value?.user_id || row?.user_id || 'Anonymous'
    },
    { 
      key: 'report_type', 
      label: 'Type',
      render: (value) => (
        <StatusBadge status={value} variant="info" />
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
          <button
            className="admin-btn admin-btn--sm admin-btn--secondary"
            onClick={() => handleViewReport(row)}
            title="View report details"
          >
            View
          </button>
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
  const topPowerUser = userStats.top_power_user || null;
  const topUserLabel = topPowerUser
    ? (topPowerUser.username || topPowerUser.email || 'Unknown User')
    : 'No activity yet';
  const topUserDetections = Number(topPowerUser?.total_detections || 0);
  const topUserPeriodLabel = period === 'all_time'
    ? 'All Time'
    : `This ${period.charAt(0).toUpperCase()}${period.slice(1)}`;

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
          title="Power User"
          value={topUserLabel}
          variant="warning"
          subtitle={`Top User (${topUserPeriodLabel}) • ${topUserDetections.toLocaleString()} detections`}
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

      {/* Report Details Modal */}
      <ReportDetailsModal
        isOpen={viewReportModal}
        report={selectedReportDetails}
        loading={loadingDetails}
        onClose={() => {
          setViewReportModal(false);
          setSelectedReportDetails(null);
        }}
        onResolve={(report) => {
          setViewReportModal(false);
          setSelectedReportDetails(null);
          openModal(report, 'resolve');
        }}
        onDismiss={(report) => {
          setViewReportModal(false);
          setSelectedReportDetails(null);
          openModal(report, 'dismiss');
        }}
      />
    </div>
  );
}

UserStats.propTypes = {
  onNotify: PropTypes.func,
};
