/**
 * ReportModal Component
 * 
 * Modal dialog for users to submit reports about issues
 * such as hallucinations, false positives/negatives, bugs, etc.
 */

import { useState, useEffect } from 'react';
import PropTypes from 'prop-types';
import { submitReport, getReportTypes, REPORT_TYPES } from '../../api/reports';
import './ReportModal.css';

/**
 * Default report type options (fallback if API fails)
 */
const DEFAULT_REPORT_TYPES = [
  {
    value: REPORT_TYPES.HALLUCINATION,
    label: 'AI Hallucination',
    description: 'The AI provided incorrect or fabricated information',
  },
  {
    value: REPORT_TYPES.FALSE_POSITIVE,
    label: 'False Positive',
    description: 'Legitimate content was incorrectly flagged as a scam',
  },
  {
    value: REPORT_TYPES.FALSE_NEGATIVE,
    label: 'False Negative',
    description: 'A scam was not detected or was marked as legitimate',
  },
  {
    value: REPORT_TYPES.BUG,
    label: 'Bug Report',
    description: 'A technical issue or error in the application',
  },
  {
    value: REPORT_TYPES.FEEDBACK,
    label: 'Feedback',
    description: 'General feedback or suggestions for improvement',
  },
  {
    value: REPORT_TYPES.OTHER,
    label: 'Other',
    description: 'Other issues not covered by the above categories',
  },
];

function ReportModal({ 
  isOpen, 
  onClose, 
  analysisId = null,
  analysisRefId = null,
  preselectedType = null,
}) {
  const [reportTypes, setReportTypes] = useState(DEFAULT_REPORT_TYPES);
  const [selectedType, setSelectedType] = useState(preselectedType || '');
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);

  // Fetch report types on mount
  useEffect(() => {
    async function fetchTypes() {
      try {
        const response = await getReportTypes();
        if (response.success && response.data) {
          setReportTypes(response.data);
        }
      } catch (err) {
        // Use default types on error
        console.warn('Failed to fetch report types, using defaults:', err);
      }
    }
    fetchTypes();
  }, []);

  // Reset form when modal opens/closes
  useEffect(() => {
    if (isOpen) {
      setSelectedType(preselectedType || '');
      setTitle('');
      setDescription('');
      setError(null);
      setSuccess(false);
    }
  }, [isOpen, preselectedType]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Validate
    if (!selectedType) {
      setError('Please select a report type');
      return;
    }
    if (title.trim().length < 3) {
      setError('Title must be at least 3 characters');
      return;
    }
    if (description.trim().length < 10) {
      setError('Description must be at least 10 characters');
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      const result = await submitReport({
        report_type: selectedType,
        title: title.trim(),
        description: description.trim(),
        analysis_id: analysisId,
        analysis_ref_id: analysisRefId,
      });

      if (result.success) {
        setSuccess(true);
        // Auto-close after success
        setTimeout(() => {
          onClose();
        }, 2000);
      } else {
        setError(result.error || 'Failed to submit report');
      }
    } catch (err) {
      setError(err.message || 'Failed to submit report. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="report-modal__overlay" onClick={onClose}>
      <div 
        className="report-modal__container" 
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-labelledby="report-modal-title"
      >
        <div className="report-modal__header">
          <h2 id="report-modal-title" className="report-modal__title">
            Submit a Report
          </h2>
          <button 
            className="report-modal__close"
            onClick={onClose}
            aria-label="Close modal"
            type="button"
          >
            ×
          </button>
        </div>

        {success ? (
          <div className="report-modal__success">
            <div className="report-modal__success-icon">✓</div>
            <h3>Report Submitted Successfully!</h3>
            <p>Thank you for your feedback. Our team will review your report.</p>
          </div>
        ) : (
          <form className="report-modal__form" onSubmit={handleSubmit}>
            {error && (
              <div className="report-modal__error" role="alert">
                {error}
              </div>
            )}

            <div className="report-modal__field">
              <label className="report-modal__label" htmlFor="report-type">
                Report Type *
              </label>
              <select
                id="report-type"
                className="report-modal__select"
                value={selectedType}
                onChange={(e) => setSelectedType(e.target.value)}
                required
              >
                <option value="">Select a category...</option>
                {reportTypes.map((type) => (
                  <option key={type.value} value={type.value}>
                    {type.label}
                  </option>
                ))}
              </select>
              {selectedType && (
                <p className="report-modal__hint">
                  {reportTypes.find(t => t.value === selectedType)?.description}
                </p>
              )}
            </div>

            <div className="report-modal__field">
              <label className="report-modal__label" htmlFor="report-title">
                Title *
              </label>
              <input
                id="report-title"
                type="text"
                className="report-modal__input"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="Brief summary of the issue"
                maxLength={200}
                required
              />
              <span className="report-modal__char-count">
                {title.length}/200
              </span>
            </div>

            <div className="report-modal__field">
              <label className="report-modal__label" htmlFor="report-description">
                Description *
              </label>
              <textarea
                id="report-description"
                className="report-modal__textarea"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Please provide details about the issue. Include any relevant context, what you expected to happen, and what actually happened."
                rows={5}
                maxLength={2000}
                required
              />
              <span className="report-modal__char-count">
                {description.length}/2000
              </span>
            </div>

            {(analysisId || analysisRefId) && (
              <div className="report-modal__context">
                <span className="report-modal__context-icon">🔗</span>
                This report will be linked to the current analysis
              </div>
            )}

            <div className="report-modal__actions">
              <button
                type="button"
                className="report-modal__btn report-modal__btn--cancel"
                onClick={onClose}
                disabled={isSubmitting}
              >
                Cancel
              </button>
              <button
                type="submit"
                className="report-modal__btn report-modal__btn--submit"
                disabled={isSubmitting}
              >
                {isSubmitting ? 'Submitting...' : 'Submit Report'}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}

ReportModal.propTypes = {
  isOpen: PropTypes.bool.isRequired,
  onClose: PropTypes.func.isRequired,
  analysisId: PropTypes.string,
  analysisRefId: PropTypes.string,
  preselectedType: PropTypes.string,
};

export default ReportModal;
