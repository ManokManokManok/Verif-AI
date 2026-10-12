/**
 * ReportDetailsModal Component
 * 
 * Modal for displaying detailed information about a user report.
 * Allows admins to view full report details and take actions (resolve/dismiss).
 */

import React, { useEffect, useState } from 'react';
import PropTypes from 'prop-types';
import { StatusBadge } from '../../../../components/admin';

const REPORT_TYPE_LABELS = {
  hallucination: 'Hallucination',
  false_positive: 'False Positive',
  false_negative: 'False Negative',
  bug: 'Bug Report',
  feedback: 'Feedback',
  support: 'Support Request',
  other: 'Other',
};

const SCAM_TYPE_OPTIONS = [
  'Banking Access & Payment',
  'Financial and Investment',
  'Health and Wellness',
  'Impersonation and Authority',
  'International or Cross-Border',
  'Job, Business, and Work-from-Home',
  'Legal and Document',
  'Mobile and Digital',
  'Prize, Raffle & Reward',
  'Property & Rental',
  'Psychological, Urgency, & Emotional',
  'Romance, Dating, and Relationship',
  'Shopping and E-Commerce',
  'Tax, Banking, and Loan',
  'Tech and Online Account',
];

const getHumanRiskLevel = (score) => {
  if (score < 20) return 'Very low';
  if (score < 40) return 'Low';
  if (score < 70) return 'Medium';
  if (score < 90) return 'High';
  return 'Very high';
};

const getActivityLabel = (activity) => {
  const actions = activity.actions || [activity.action || 'status_updated'];
  const labels = [];
  if (actions.includes('resolved')) labels.push('Report resolved');
  if (actions.includes('dismissed')) labels.push('Report dismissed');
  if (actions.includes('support_response')) labels.push('Admin responded to support request');
  if (actions.includes('human_review')) {
    labels.push(`Human review recorded${activity.review_decision ? `: ${activity.review_decision.replaceAll('_', ' ')}` : ''}`);
  }
  if (labels.length === 0) {
    labels.push(`Report status updated${activity.status ? ` to ${activity.status.replaceAll('_', ' ')}` : ''}`);
  }
  return labels.join(' · ');
};

export default function ReportDetailsModal({
  isOpen,
  report,
  loading,
  savingChanges = false,
  onClose,
  onResolve,
  onDismiss,
  onSaveChanges,
}) {
  const [editedStatus, setEditedStatus] = useState('pending');
  const [response, setResponse] = useState('');
  const [reviewDecision, setReviewDecision] = useState('');
  const [reviewRiskScore, setReviewRiskScore] = useState(50);
  const [reviewScamType, setReviewScamType] = useState('');
  const [reviewExplanation, setReviewExplanation] = useState('');
  const [reviewSummary, setReviewSummary] = useState('');
  const [reviewDetails, setReviewDetails] = useState('');
  const [reviewMarkers, setReviewMarkers] = useState([]);
  const [newReviewMarker, setNewReviewMarker] = useState('');

  useEffect(() => {
    setEditedStatus(report?.status || 'pending');
    setResponse(report?.resolution_notes || '');
    setReviewDecision(report?.analysis?.reviewed_result?.decision || '');
    setReviewRiskScore(report?.analysis?.reviewed_result?.risk_score ?? 50);
    setReviewScamType(report?.analysis?.reviewed_result?.scam_type || '');
    setReviewExplanation(report?.analysis?.reviewed_result?.explanation || '');
    setReviewSummary(report?.analysis?.reviewed_result?.summary || '');
    setReviewDetails(report?.analysis?.reviewed_result?.details || '');
    setReviewMarkers(report?.analysis?.reviewed_result?.key_markers || []);
    setNewReviewMarker('');
  }, [report]);

  if (!isOpen) return null;

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleString();
  };

  const getReportTypeName = (type) => REPORT_TYPE_LABELS[type] || type;
  const analysis = report?.analysis;
  const existingReview = analysis?.reviewed_result;
  const existingReviews = analysis?.review_history || [];
  const reviewChanged = reviewDecision !== (existingReview?.decision || '')
    || reviewRiskScore !== (existingReview?.risk_score ?? 50)
    || reviewScamType !== (existingReview?.scam_type || '')
    || reviewExplanation !== (existingReview?.explanation || '')
    || reviewSummary !== (existingReview?.summary || '')
    || reviewDetails !== (existingReview?.details || '')
    || JSON.stringify(reviewMarkers) !== JSON.stringify(existingReview?.key_markers || []);
  const reviewIsPublishDecision = reviewDecision === 'confirmed_scam' || reviewDecision === 'confirmed_legitimate';
  const reviewIsValid = !reviewDecision
    || (
      reviewExplanation.trim().length >= 10
      && reviewExplanation.length <= 2000
      && (!reviewIsPublishDecision || (
        reviewSummary.trim().length >= 10
        && reviewSummary.length <= 2000
        && reviewDetails.length <= 5000
        && (reviewDecision !== 'confirmed_scam' || SCAM_TYPE_OPTIONS.includes(reviewScamType))
        && (reviewDecision !== 'confirmed_scam' || (Number.isInteger(reviewRiskScore) && reviewRiskScore >= 0 && reviewRiskScore <= 100))
        && reviewMarkers.length <= 10
        && !newReviewMarker.trim()
        && reviewMarkers.every((marker) => marker.trim().length > 0 && marker.length <= 200)
      ))
    );

  const addReviewMarker = () => {
    const marker = newReviewMarker.trim();
    if (!marker || reviewMarkers.length >= 10 || reviewMarkers.some((item) => item.toLowerCase() === marker.toLowerCase())) {
      return;
    }
    setReviewMarkers([...reviewMarkers, marker]);
    setNewReviewMarker('');
  };

  // Loading state
  if (loading) {
    return (
      <div className="admin-modal__overlay report-details__overlay" onClick={onClose}>
        <div className="admin-modal report-details-modal" role="dialog" aria-modal="true" onClick={e => e.stopPropagation()}>
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
    <div className="admin-modal__overlay report-details__overlay" onClick={onClose}>
      <div
        className="admin-modal report-details-modal"
        role="dialog"
        aria-modal="true"
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
              {analysis && (
                <div className="report-details__analysis">
                  <h4 className="report-details__section-title">Original analysis output</h4>
                  <div className="report-details__analysisVerdict">
                    <span className={`report-details__verdictBadge ${analysis.is_scam ? 'report-details__verdictBadge--scam' : 'report-details__verdictBadge--legit'}`}>
                      {analysis.is_scam ? 'Model flagged as scam' : 'Model marked as likely legitimate'}
                    </span>
                    {analysis.needs_review && <span className="report-details__autoFlag">Automatically flagged for review</span>}
                  </div>
                  <div className="report-details__metrics">
                    <div><span>Scam likelihood</span><strong>{Number.isFinite(analysis.scam_score) ? `${analysis.scam_score.toFixed(1)}%` : 'N/A'}</strong></div>
                    <div><span>Legitimate likelihood</span><strong>{Number.isFinite(analysis.legit_score) ? `${analysis.legit_score.toFixed(1)}%` : 'N/A'}</strong></div>
                    <div><span>Type confidence</span><strong>{Number.isFinite(analysis.type_confidence) ? `${analysis.type_confidence.toFixed(1)}%` : 'N/A'}</strong></div>
                    <div><span>Model type</span><strong>{analysis.scam_type || 'N/A'}</strong></div>
                  </div>
                  {analysis.needs_review && (
                    <div className="report-details__analysisNote">
                      <strong>Automatic review reason</strong>
                      <p>{analysis.review_reason || 'Flagged for human review'}</p>
                    </div>
                  )}
                  {(analysis.summary || analysis.details) && (
                    <div className="report-details__analysisCopy">
                      {analysis.summary && <div><label>Model summary</label><p>{analysis.summary}</p></div>}
                      {analysis.details && <div><label>Model details</label><p>{analysis.details}</p></div>}
                    </div>
                  )}
                  {analysis.key_markers?.length > 0 && (
                    <div className="report-details__field report-details__field--full">
                      <label>Model indicators</label>
                      <ul className="report-details__indicatorList">
                        {analysis.key_markers.map((marker, index) => <li key={`${index}-${marker}`}>{marker}</li>)}
                      </ul>
                    </div>
                  )}
                  {analysis.message && (
                    <div className="report-details__analysisMessage">
                      <label>Analyzed message</label>
                      <p>{analysis.message}</p>
                    </div>
                  )}
                  {analysis.image_attachment?.data_url && (
                    <div className="report-details__field report-details__field--full">
                      <label>Analyzed image</label>
                      <img
                        src={analysis.image_attachment.data_url}
                        alt="User-submitted analysis"
                        className="report-details__analysisImage"
                      />
                    </div>
                  )}
                </div>
              )}
              {existingReviews.length > 0 && (
                <div className="report-details__section">
                  <h4 className="report-details__section-title">Human review history</h4>
                  {existingReviews.slice().reverse().map((item, index) => (
                    <div className="report-details__reviewHistoryItem" key={`${item.reviewed_at || 'review'}-${index}`}>
                      <p className="report-details__text">
                        {item.decision?.replaceAll('_', ' ')} · {formatDate(item.reviewed_at)} · {item.reviewed_by || 'Admin'}
                      </p>
                      {item.summary && <p className="report-details__description">{item.summary}</p>}
                      <p className="report-details__description">{item.explanation}</p>
                    </div>
                  ))}
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

        {(report.activity_history?.length > 0 || report.assigned_to) && (
          <div className="report-details__section">
            <h4 className="report-details__section-title">Admin activity history</h4>
            {report.activity_history?.length > 0 ? (
              <ol className="report-details__activityList">
                {report.activity_history.slice().reverse().map((activity, index) => (
                  <li className="report-details__activityItem" key={`${activity.created_at || 'activity'}-${index}`}>
                    <span className="report-details__activityMarker" aria-hidden="true" />
                    <div className="report-details__activityBody">
                      <strong>{getActivityLabel(activity)}</strong>
                      <p className="report-details__activityMeta">
                        {activity.admin_email || activity.admin_user_id || 'Admin'}
                        {' · '}
                        {formatDate(activity.created_at)}
                      </p>
                      {activity.resolution_notes && (
                        <p className="report-details__description report-details__activityNote">
                          {activity.resolution_notes}
                        </p>
                      )}
                    </div>
                  </li>
                ))}
              </ol>
            ) : (
              <div className="report-details__field">
                <label>Currently assigned / latest handler</label>
                <p className="report-details__text">{report.assigned_to}</p>
                <small className="report-details__hint">Detailed action history is available for updates recorded after audit tracking was enabled.</small>
              </div>
            )}
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
              {report.activity_history?.length > 0 && (
                <div className="report-details__field">
                  <label>Latest action by</label>
                  <p className="report-details__text">
                    {report.activity_history[report.activity_history.length - 1].admin_email
                      || report.activity_history[report.activity_history.length - 1].admin_user_id
                      || 'Admin'}
                  </p>
                </div>
              )}
            </div>
            {report.report_type !== 'support' && report.resolution_notes && (
              <div className="report-details__field report-details__field--full" style={{ marginTop: '0.75rem' }}>
                <label>Resolution Notes</label>
                <p className="report-details__description">{report.resolution_notes}</p>
              </div>
            )}
          </div>
        )}
        {report.report_type === 'support' && report.resolution_notes && (
          <div className="report-details__section">
            <h4 className="report-details__section-title">Saved Admin Response</h4>
            <p className="report-details__description">{report.resolution_notes}</p>
          </div>
        )}

        <div className="report-details__section">
          <h4 className="report-details__section-title">Update report</h4>
          <div className="report-details__field report-details__field--full">
            <label htmlFor="report-status">Status</label>
            <select
              id="report-status"
              className="report-details__editor"
              value={editedStatus}
              onChange={(event) => setEditedStatus(event.target.value)}
            >
              <option value="pending">Pending</option>
              <option value="in_progress">In Progress</option>
              <option value="resolved">Resolved</option>
              <option value="dismissed">Dismissed</option>
            </select>
          </div>
          {report.report_type === 'support' && (
            <div className="report-details__field report-details__field--full" style={{ marginTop: '0.75rem' }}>
              <label htmlFor="report-admin-response">Response visible to the reporter</label>
              <textarea
                id="report-admin-response"
                className="report-details__editor report-details__editor--response"
                value={response}
                onChange={(event) => setResponse(event.target.value)}
                maxLength={5000}
                placeholder="Add an update or response for the user"
              />
            </div>
          )}
        </div>
        {analysis && (
          <div className="report-details__section report-details__verification">
            <div className="report-details__verificationHeader">
              <div>
                <h4 className="report-details__section-title">Human verification</h4>
                <p className="report-details__description">
                  Write the final result that the reporter will see. The original model output stays available above for comparison.
                </p>
              </div>
              {reviewDecision && (
                <button className="report-details__clearReview" type="button" onClick={() => setReviewDecision('')}>
                  Clear review choice
                </button>
              )}
            </div>
            <label className="report-details__choiceLabel" id="report-review-decision-label">Decision</label>
            <div className="report-details__decisionChoices" role="group" aria-labelledby="report-review-decision-label">
              {[
                ['confirmed_scam', 'Confirmed scam', 'Publish a human-verified scam result.'],
                ['confirmed_legitimate', 'Confirmed legitimate', 'Publish a human-verified safe result.'],
                ['inconclusive', 'Inconclusive', 'Record the review without changing the result.'],
                ['needs_more_info', 'Needs more info', 'Keep the result unchanged while follow-up is needed.'],
              ].map(([value, title, description]) => (
                <button
                  key={value}
                  type="button"
                  className={`report-details__decisionChoice ${reviewDecision === value ? 'report-details__decisionChoice--selected' : ''}`}
                  aria-pressed={reviewDecision === value}
                  onClick={() => setReviewDecision(value)}
                >
                  <strong>{title}</strong>
                  <span>{description}</span>
                </button>
              ))}
            </div>
            {reviewDecision && (
              <div className="report-details__reviewEditor">
                {reviewDecision === 'confirmed_scam' && (
                  <div className="report-details__grid">
                <div className="report-details__field">
                  <label htmlFor="report-review-type">Scam type</label>
                  <select
                    id="report-review-type"
                    className="report-details__editor"
                    value={reviewScamType}
                    onChange={(event) => setReviewScamType(event.target.value)}
                    required
                  >
                    <option value="">Choose one of the 15 model categories</option>
                    {SCAM_TYPE_OPTIONS.map((scamType) => (
                      <option key={scamType} value={scamType}>{scamType}</option>
                    ))}
                  </select>
                </div>
                    <div className="report-details__field report-details__field--full">
                      <div className="report-details__riskHeader">
                        <label htmlFor="report-review-risk-score">Human risk estimate</label>
                        <strong className={`report-details__riskValue report-details__riskValue--${getHumanRiskLevel(Number(reviewRiskScore)).toLowerCase().replace(' ', '-')}`}>
                          {reviewRiskScore}% · {getHumanRiskLevel(Number(reviewRiskScore))}
                        </strong>
                      </div>
                      <div className="report-details__riskControls">
                        <input
                          id="report-review-risk-score"
                          className="report-details__riskSlider"
                          type="range"
                          min="0"
                          max="100"
                          step="1"
                          value={reviewRiskScore}
                          onChange={(event) => setReviewRiskScore(Number(event.target.value))}
                          aria-label="Human risk estimate percentage"
                        />
                        <div className="report-details__riskNumber">
                          <input
                            className="report-details__editor"
                            type="number"
                            min="0"
                            max="100"
                            step="1"
                            value={reviewRiskScore}
                            onChange={(event) => setReviewRiskScore(event.target.value === '' ? '' : Number(event.target.value))}
                            aria-label="Human risk estimate number"
                          />
                          <span>%</span>
                        </div>
                      </div>
                      <div className="report-details__riskScale" aria-hidden="true">
                        <span>Very low<br />0–19</span>
                        <span>Low<br />20–39</span>
                        <span>Medium<br />40–69</span>
                        <span>High<br />70–89</span>
                        <span>Very high<br />90–100</span>
                      </div>
                      <small className="report-details__hint">A separate human estimate of the risk this message poses; it is not the model’s scam-likelihood score.</small>
                    </div>
                  </div>
                )}
                {reviewDecision === 'confirmed_legitimate' && (
                  <div className="report-details__publishedRisk">
                    <span>Published human risk estimate</span><strong>0% · Very low</strong>
                  </div>
                )}
                {(reviewDecision === 'confirmed_scam' || reviewDecision === 'confirmed_legitimate') && (
                  <>
                    <div className="report-details__field report-details__field--full">
                      <label htmlFor="report-review-summary">Human-written result summary <span className="report-details__required">Required</span></label>
                      <textarea
                        id="report-review-summary"
                        className="report-details__editor report-details__editor--response"
                        value={reviewSummary}
                        onChange={(event) => setReviewSummary(event.target.value)}
                        minLength={10}
                        maxLength={2000}
                        required
                        placeholder="Write a concise summary of the verified result"
                      />
                      <small className="report-details__hint">This becomes the main summary shown with the result.</small>
                    </div>
                    <div className="report-details__field report-details__field--full">
                      <label htmlFor="report-review-details">Additional human-reviewed details</label>
                      <textarea
                        id="report-review-details"
                        className="report-details__editor report-details__editor--response"
                        value={reviewDetails}
                        onChange={(event) => setReviewDetails(event.target.value)}
                        maxLength={5000}
                        placeholder="Add context, evidence, or practical explanation"
                      />
                    </div>
                    <div className="report-details__field report-details__field--full">
                      <label htmlFor="report-review-indicator">Human-verified red flags / indicators</label>
                      <div className="report-details__markerEditor">
                        <input
                          id="report-review-indicator"
                          className="report-details__editor"
                          value={newReviewMarker}
                          onChange={(event) => setNewReviewMarker(event.target.value)}
                          onKeyDown={(event) => {
                            if (event.key === 'Enter') {
                              event.preventDefault();
                              addReviewMarker();
                            }
                          }}
                          maxLength={200}
                          disabled={reviewMarkers.length >= 10}
                          placeholder={reviewMarkers.length >= 10 ? 'Maximum of 10 indicators reached' : 'Add a verified indicator and press Enter'}
                        />
                        <button
                          className="report-details__addMarker"
                          type="button"
                          onClick={addReviewMarker}
                          disabled={!newReviewMarker.trim() || reviewMarkers.length >= 10}
                        >
                          Add indicator
                        </button>
                      </div>
                      {reviewMarkers.length > 0 ? (
                        <ul className="report-details__markerChips">
                          {reviewMarkers.map((marker, index) => (
                            <li key={`${marker}-${index}`}>
                              <span>{marker}</span>
                              <button type="button" aria-label={`Remove ${marker}`} onClick={() => setReviewMarkers(reviewMarkers.filter((_, markerIndex) => markerIndex !== index))}>×</button>
                            </li>
                          ))}
                        </ul>
                      ) : <p className="report-details__hint">No human-verified indicators added.</p>}
                    </div>
                  </>
                )}
                <div className="report-details__field report-details__field--full">
                  <label htmlFor="report-review-explanation">
                    Reviewer rationale <span className="report-details__required">Required</span>
                  </label>
                  <textarea
                    id="report-review-explanation"
                    className="report-details__editor report-details__editor--response"
                    value={reviewExplanation}
                    onChange={(event) => setReviewExplanation(event.target.value)}
                    minLength={10}
                    maxLength={2000}
                    required
                    placeholder="Explain the evidence for this decision"
                  />
                  <small className="report-details__hint">This note is included with the human-reviewed result.</small>
                </div>
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
          <button
            className="admin-modal__btn admin-modal__btn--info"
            onClick={() => onSaveChanges?.(
              report,
              editedStatus,
              report.report_type === 'support' ? response : undefined,
              reviewDecision && reviewChanged ? {
                decision: reviewDecision,
                risk_score: reviewDecision === 'confirmed_legitimate' ? 0 : reviewRiskScore,
                scam_type: reviewScamType,
                summary: reviewSummary,
                details: reviewDetails,
                key_markers: reviewMarkers,
                explanation: reviewExplanation,
              } : undefined,
            )}
            disabled={savingChanges || !reviewIsValid}
          >
            {savingChanges ? 'Saving...' : analysis ? 'Save report and review' : 'Save status and response'}
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
  savingChanges: PropTypes.bool,
  onClose: PropTypes.func.isRequired,
  onResolve: PropTypes.func,
  onDismiss: PropTypes.func,
  onSaveChanges: PropTypes.func,
};
