/**
 * AnalysisDetailsModal Component
 * 
 * Modal displaying full details of a blockchain analysis record.
 * Shows analysis info, confidence scores, chain metadata, and message content.
 */

import React from 'react';
import PropTypes from 'prop-types';
import { VerificationBadge } from '../../../../components/blockchain/BlockchainComponents';

/**
 * Format a date string for display
 */
function formatDate(dateStr) {
  if (!dateStr) return 'N/A';
  try {
    const date = new Date(dateStr);
    if (isNaN(date.getTime())) return dateStr;
    return date.toLocaleString();
  } catch {
    return dateStr;
  }
}

/**
 * Truncate or format a hash string for display
 */
function formatHash(hash, full = false) {
  if (!hash) return 'N/A';
  if (full || hash.length <= 20) return hash;
  return `${hash.slice(0, 14)}...${hash.slice(-10)}`;
}

/**
 * Convert confidence basis points to percentage
 */
function bpsToPercent(bps) {
  if (bps == null) return null;
  return (bps / 100).toFixed(2);
}

export default function AnalysisDetailsModal({ isOpen, analysis, onClose, onVerify, onAnchor, onRefresh }) {
  if (!isOpen || !analysis) return null;

  const isAnchored = analysis.is_anchored || analysis.isAnchored;
  const refId = analysis.ref_id || analysis.refId || analysis.id;
  const scamType = analysis.scam_type || analysis.scamType || 'Unknown';
  const scamClass = analysis.scam_class ?? analysis.scamClass ?? 'N/A';
  const confidenceBps = analysis.confidence_bps ?? analysis.confidenceBps;
  const confidencePercent = bpsToPercent(confidenceBps);
  const analyzerType = analysis.analyzer_type || analysis.analyzerType || 'N/A';
  const analyzerVersion = analysis.analyzer_version || analysis.analyzerVersion || 'N/A';
  const createdAt = analysis.created_at || analysis.createdAt;
  const isScam = analysis.is_scam ?? analysis.isScam;
  const message = analysis.message || null;
  const summary = analysis.summary || null;
  const keyMarkers = analysis.key_markers || analysis.keyMarkers || [];
  const scamScore = analysis.scam_score ?? analysis.scamScore;
  const legitScore = analysis.legit_score ?? analysis.legitScore;
  const label = analysis.label || null;
  const typeConfidence = analysis.type_confidence ?? analysis.typeConfidence;
  const chain = analysis.chain || null;

  const handleOverlayClick = (e) => {
    if (e.target === e.currentTarget) onClose();
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Escape') onClose();
  };

  return (
    <div
      className="analysis-details-overlay"
      onClick={handleOverlayClick}
      onKeyDown={handleKeyDown}
      role="dialog"
      aria-modal="true"
      aria-label="Analysis Details"
      tabIndex={-1}
    >
      <div className="analysis-details-modal">
        {/* Header */}
        <div className="analysis-details__header">
          <div className="analysis-details__header-left">
            <h2 className="analysis-details__title">Analysis Details</h2>
            <VerificationBadge status={isAnchored ? 'ANCHORED' : 'NOT_ANCHORED'} />
          </div>
          <button
            className="analysis-details__close-btn"
            onClick={onClose}
            aria-label="Close modal"
          >
            &times;
          </button>
        </div>

        {/* Content */}
        <div className="analysis-details__content">
          {/* Reference & Classification Section */}
          <section className="analysis-details__section">
            <h3 className="analysis-details__section-title">Identification</h3>
            <div className="analysis-details__grid">
              <div className="analysis-details__field analysis-details__field--full">
                <label>Reference ID</label>
                <p className="analysis-details__text analysis-details__text--mono">{refId || 'N/A'}</p>
              </div>
              <div className="analysis-details__field">
                <label>Classification</label>
                <p className="analysis-details__text">{scamType}</p>
              </div>
              <div className="analysis-details__field">
                <label>Scam Class</label>
                <p className="analysis-details__text">{scamClass === -1 ? 'Legitimate (-1)' : scamClass}</p>
              </div>
              <div className="analysis-details__field">
                <label>Is Scam</label>
                <span className={`analysis-details__badge ${isScam ? 'analysis-details__badge--danger' : 'analysis-details__badge--success'}`}>
                  {isScam ? 'Yes' : 'No'}
                </span>
              </div>
              <div className="analysis-details__field">
                <label>Label</label>
                <p className="analysis-details__text">{label || 'N/A'}</p>
              </div>
            </div>
          </section>

          {/* Confidence & Scores Section */}
          <section className="analysis-details__section">
            <h3 className="analysis-details__section-title">Confidence & Scores</h3>
            <div className="analysis-details__grid">
              <div className="analysis-details__field">
                <label>Confidence</label>
                <div className="analysis-details__confidence">
                  {confidencePercent != null ? (
                    <>
                      <div className="analysis-details__confidence-bar">
                        <div
                          className="analysis-details__confidence-fill"
                          style={{ width: `${confidencePercent}%` }}
                        />
                      </div>
                      <span className="analysis-details__confidence-value">{confidencePercent}%</span>
                    </>
                  ) : (
                    <p className="analysis-details__text">N/A</p>
                  )}
                </div>
              </div>
              <div className="analysis-details__field">
                <label>Confidence (BPS)</label>
                <p className="analysis-details__text">{confidenceBps ?? 'N/A'} / 10,000</p>
              </div>
              {scamScore != null && (
                <div className="analysis-details__field">
                  <label>Scam Score</label>
                  <p className="analysis-details__text">{typeof scamScore === 'number' ? scamScore.toFixed(4) : scamScore}</p>
                </div>
              )}
              {legitScore != null && (
                <div className="analysis-details__field">
                  <label>Legit Score</label>
                  <p className="analysis-details__text">{typeof legitScore === 'number' ? legitScore.toFixed(4) : legitScore}</p>
                </div>
              )}
              {typeConfidence != null && (
                <div className="analysis-details__field">
                  <label>Type Confidence</label>
                  <p className="analysis-details__text">{typeof typeConfidence === 'number' ? (typeConfidence * 100).toFixed(2) + '%' : typeConfidence}</p>
                </div>
              )}
            </div>
          </section>

          {/* Analyzer Section */}
          <section className="analysis-details__section">
            <h3 className="analysis-details__section-title">Analyzer</h3>
            <div className="analysis-details__grid">
              <div className="analysis-details__field">
                <label>Analyzer Type</label>
                <p className="analysis-details__text">{analyzerType}</p>
              </div>
              <div className="analysis-details__field">
                <label>Analyzer Version</label>
                <p className="analysis-details__text">{analyzerVersion}</p>
              </div>
              <div className="analysis-details__field">
                <label>Created At</label>
                <p className="analysis-details__text">{formatDate(createdAt)}</p>
              </div>
            </div>
          </section>

          {/* Summary & Key Markers Section */}
          {(summary || keyMarkers.length > 0) && (
            <section className="analysis-details__section">
              <h3 className="analysis-details__section-title">Analysis Summary</h3>
              {summary && (
                <div className="analysis-details__field analysis-details__field--full">
                  <label>Summary</label>
                  <p className="analysis-details__description">{summary}</p>
                </div>
              )}
              {keyMarkers.length > 0 && (
                <div className="analysis-details__field analysis-details__field--full">
                  <label>Key Markers</label>
                  <div className="analysis-details__markers">
                    {keyMarkers.map((marker, idx) => (
                      <span key={idx} className="analysis-details__marker-tag">
                        {marker}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </section>
          )}

          {/* Message Section */}
          {message && (
            <section className="analysis-details__section">
              <h3 className="analysis-details__section-title">Original Message</h3>
              <div className="analysis-details__field analysis-details__field--full">
                <p className="analysis-details__description analysis-details__description--message">
                  {message}
                </p>
              </div>
            </section>
          )}

          {/* Blockchain Details Section */}
          <section className="analysis-details__section">
            <h3 className="analysis-details__section-title">Blockchain Details</h3>
            {isAnchored && chain ? (
              <div className="analysis-details__grid">
                <div className="analysis-details__field analysis-details__field--full">
                  <label>Transaction Hash</label>
                  <p className="analysis-details__text analysis-details__text--mono">
                    {chain.tx_hash || chain.txHash || 'N/A'}
                  </p>
                </div>
                <div className="analysis-details__field analysis-details__field--full">
                  <label>Payload Hash</label>
                  <p className="analysis-details__text analysis-details__text--mono">
                    {chain.payload_hash || chain.payloadHash || 'N/A'}
                  </p>
                </div>
                <div className="analysis-details__field">
                  <label>Network</label>
                  <p className="analysis-details__text">{chain.network || 'N/A'}</p>
                </div>
                <div className="analysis-details__field">
                  <label>Block Number</label>
                  <p className="analysis-details__text">{chain.block_number ?? chain.blockNumber ?? 'N/A'}</p>
                </div>
                <div className="analysis-details__field">
                  <label>Schema Version</label>
                  <p className="analysis-details__text">{chain.schema_version ?? chain.schemaVersion ?? 'N/A'}</p>
                </div>
                <div className="analysis-details__field">
                  <label>Anchored At</label>
                  <p className="analysis-details__text">{formatDate(chain.anchored_at || chain.anchoredAt)}</p>
                </div>
                <div className="analysis-details__field analysis-details__field--full">
                  <label>Contract Address</label>
                  <p className="analysis-details__text analysis-details__text--mono">
                    {chain.contract_address || chain.contractAddress || 'N/A'}
                  </p>
                </div>
              </div>
            ) : (
              <div className="analysis-details__empty-chain">
                <span className="analysis-details__empty-icon">○</span>
                <p>This analysis has not been anchored to the blockchain yet.</p>
              </div>
            )}
          </section>
        </div>

        {/* Footer Actions */}
        <div className="analysis-details__footer">
          <button
            className="analysis-details__btn analysis-details__btn--secondary"
            onClick={onClose}
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}

AnalysisDetailsModal.propTypes = {
  isOpen: PropTypes.bool.isRequired,
  analysis: PropTypes.object,
  onClose: PropTypes.func.isRequired,
  onVerify: PropTypes.func,
  onAnchor: PropTypes.func,
  onRefresh: PropTypes.func,
};
