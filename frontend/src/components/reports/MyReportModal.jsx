/**
 * MyReportModal Component
 *
 * Read-only view of the report a user submitted for an analysis.
 */

import PropTypes from 'prop-types';
import { getReportTypeLabel } from '../../api/reports';
import './ReportModal.css';

const STATUS_LABELS = {
  pending: 'Pending review',
  in_progress: 'In progress',
  resolved: 'Resolved',
  dismissed: 'Reviewed',
};

const formatDate = (value) => (value ? new Date(value).toLocaleString() : null);

function MyReportModal({ isOpen, onClose, report }) {
  if (!isOpen || !report) return null;

  const submitted = formatDate(report.created_at);
  const resolved = formatDate(report.resolved_at);

  return (
    <div className="report-modal__overlay" onClick={onClose}>
      <div
        className="report-modal__container"
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-labelledby="my-report-title"
      >
        <div className="report-modal__header">
          <h2 id="my-report-title" className="report-modal__title">Your Report</h2>
          <button className="report-modal__close" onClick={onClose} aria-label="Close modal" type="button">
            ×
          </button>
        </div>

        <div className="report-modal__form">
          <div className="report-modal__field">
            <span className="report-modal__label">Status</span>
            <p className="report-modal__hint">
              {STATUS_LABELS[report.status] || report.status}
              {report.status_message ? ` · ${report.status_message}` : ''}
            </p>
          </div>
          <div className="report-modal__field">
            <span className="report-modal__label">Type</span>
            <p className="report-modal__hint">{getReportTypeLabel(report.report_type)}</p>
          </div>
          <div className="report-modal__field">
            <span className="report-modal__label">Title</span>
            <p className="report-modal__hint">{report.title}</p>
          </div>
          <div className="report-modal__field">
            <span className="report-modal__label">Description</span>
            <p className="report-modal__hint" style={{ whiteSpace: 'pre-wrap' }}>{report.description}</p>
          </div>
          {report.admin_response && (
            <div className="report-modal__field">
              <span className="report-modal__label">Admin response</span>
              <p className="report-modal__hint" style={{ whiteSpace: 'pre-wrap' }}>{report.admin_response}</p>
            </div>
          )}
          {(submitted || resolved) && (
            <div className="report-modal__context">
              {submitted && <>Submitted {submitted}. </>}
              {resolved && <>Resolved {resolved}.</>}
            </div>
          )}
          <div className="report-modal__actions">
            <button type="button" className="report-modal__btn report-modal__btn--cancel" onClick={onClose}>
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

MyReportModal.propTypes = {
  isOpen: PropTypes.bool.isRequired,
  onClose: PropTypes.func.isRequired,
  report: PropTypes.object,
};

export default MyReportModal;
