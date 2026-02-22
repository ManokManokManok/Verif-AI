/**
 * ReportDetailsModal Component
 * 
 * Modal for displaying detailed information about a user report.
 * Allows admins to view full report details and take actions (resolve/dismiss).
 */

import React from 'react';
import PropTypes from 'prop-types';
import { StatusBadge } from '../../../../components/admin';

const REPORT_TYPE_LABELS = {
  hallucination: 'Hallucination',
  false_positive: 'False Positive',
  false_negative: 'False Negative',
  bug: 'Bug Report',
  feedback: 'Feedback',
  other: 'Other',
};

export default function ReportDetailsModal({ isOpen, report, loading, onClose, onResolve, onDismiss }) {
  if (!isOpen) return null;

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleString();
  };

  const getReportTypeName = (type) => REPORT_TYPE_LABELS[type] || type;

  // Loading state
  if (loading) {
    return (
      <div className="admin-modal__overlay" onClick={onClose}>
        <div className="admin-modal report-details-modal" onClick={e => e.stopPropagation()}>
          <div className="report-details__loading">
            <div className="report-details__spinner" />
            <p>Loading report details...</p>
          </div>
        </div>
      </div>
    );
  }

  if (!report) return null;

  const isPending = report.status === 'pending';

  return (
    <div className="admin-modal__overlay" onClick={onClose}>
      <div
        className="admin-modal report-details-modal"
        onClick={e => e.stopPropagation()}
      >
        {/* Header */}
        <div className="report-details__header">
          <div className="report-details__header-left">
            <h3 className="admin-modal__title">Report Details</h3>
            <code className="report-details__id">#{report.report_id?.slice(0, 8) || report.id?.slice(0, 8)}</code>
          </div>
          <button className="report-details__close-btn" onClick={onClose} aria-label="Close">
            ✕
          </button>
        </div>

        {/* Status & Type */}
        <div className="report-details__section">
          <div className="report-details__grid">
            <div className="report-details__field">
              <label>Status</label>
              <StatusBadge status={report.status} />
            </div>
            <div className="report-details__field">
              <label>Type</label>
              <StatusBadge status={getReportTypeName(report.report_type)} variant="info" />
            </div>
            <div className="report-details__field">
              <label>Reporter</label>
              <p className="report-details__text">{report.user_email || 'N/A'}</p>
            </div>
            <div className="report-details__field">
              <label>Submitted</label>
              <p className="report-details__text">{formatDate(report.created_at)}</p>
            </div>
          </div>
        </div>

        {/* Title & Description */}
        <div className="report-details__section">
          <h4 className="report-details__section-title">Report Content</h4>
          <div className="report-details__field report-details__field--full">
            <label>Title</label>
            <p className="report-details__text">{report.title || 'No title provided'}</p>
          </div>
          <div className="report-details__field report-details__field--full" style={{ marginTop: '0.75rem' }}>
            <label>Description</label>
            <p className="report-details__description">
              {report.description || 'No description provided'}
            </p>
          </div>
        </div>

        {/* Analysis Context */}
        {(report.analysis_id || report.analysis_ref_id) && (
          <div className="report-details__section">
            <h4 className="report-details__section-title">Analysis Context</h4>
            <div className="report-details__grid">
              {report.analysis_id && (
                <div className="report-details__field">
                  <label>Analysis ID</label>
                  <code className="report-details__text">{report.analysis_id}</code>
                </div>
              )}
              {report.analysis_ref_id && (
                <div className="report-details__field">
                  <label>Reference ID</label>
                  <code className="report-details__text">{report.analysis_ref_id}</code>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Resolution Info (if resolved/dismissed) */}
        {report.is_resolved && (
          <div className="report-details__section">
            <h4 className="report-details__section-title">Resolution</h4>
            <div className="report-details__grid">
              <div className="report-details__field">
                <label>Resolved At</label>
                <p className="report-details__text">{formatDate(report.resolved_at)}</p>
              </div>
              {report.assigned_to && (
                <div className="report-details__field">
                  <label>Handled By</label>
                  <p className="report-details__text">{report.assigned_to}</p>
                </div>
              )}
            </div>
            {report.resolution_notes && (
              <div className="report-details__field report-details__field--full" style={{ marginTop: '0.75rem' }}>
                <label>Resolution Notes</label>
                <p className="report-details__description">{report.resolution_notes}</p>
              </div>
            )}
          </div>
        )}

        {/* Timestamps */}
        <div className="report-details__section report-details__section--no-border">
          <div className="report-details__grid">
            <div className="report-details__field">
              <label>Created</label>
              <p className="report-details__text report-details__text--muted">{formatDate(report.created_at)}</p>
            </div>
            <div className="report-details__field">
              <label>Last Updated</label>
              <p className="report-details__text report-details__text--muted">{formatDate(report.updated_at)}</p>
            </div>
          </div>
        </div>

        {/* Actions */}
        <div className="admin-modal__actions report-details__actions">
          <button
            className="admin-modal__btn admin-modal__btn--cancel"
            onClick={onClose}
          >
            Close
          </button>
          {isPending && (
            <>
              <button
                className="admin-modal__btn admin-modal__btn--warning"
                onClick={() => onDismiss?.(report)}
              >
                Dismiss
              </button>
              <button
                className="admin-modal__btn admin-modal__btn--info"
                onClick={() => onResolve?.(report)}
              >
                Resolve
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

ReportDetailsModal.propTypes = {
  isOpen: PropTypes.bool.isRequired,
  report: PropTypes.object,
  loading: PropTypes.bool,
  onClose: PropTypes.func.isRequired,
  onResolve: PropTypes.func,
  onDismiss: PropTypes.func,
};
