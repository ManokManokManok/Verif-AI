import { useState } from 'react';

/**
 * VerificationBadge - Displays verification status with colored badge and icon
 * 
 * @param {Object} props
 * @param {'VERIFIED' | 'NOT_VERIFIED' | 'NOT_ANCHORED' | 'ERROR' | 'LOADING'} props.status
 * @param {string} props.className - Additional CSS classes
 */
export function VerificationBadge({ status, className = '' }) {
  const config = {
    VERIFIED: {
      label: 'Verified',
      icon: '✓',
      bgClass: 'blockchain__badge--verified',
    },
    NOT_VERIFIED: {
      label: 'Not Verified',
      icon: '✗',
      bgClass: 'blockchain__badge--not-verified',
    },
    NOT_ANCHORED: {
      label: 'Not Anchored',
      icon: '○',
      bgClass: 'blockchain__badge--not-anchored',
    },
    ERROR: {
      label: 'Error',
      icon: '!',
      bgClass: 'blockchain__badge--error',
    },
    LOADING: {
      label: 'Loading...',
      icon: '⟳',
      bgClass: 'blockchain__badge--loading',
    },
  };

  const { label, icon, bgClass } = config[status] || config.NOT_ANCHORED;

  return (
    <span className={`blockchain__badge ${bgClass} ${className}`}>
      <span className="blockchain__badge-icon">{icon}</span>
      {label}
    </span>
  );
}

/**
 * VerifyButton - Button that triggers verification and shows result
 * 
 * @param {Object} props
 * @param {string} props.refId - Analysis reference ID
 * @param {Function} props.onVerify - Verify function (refId) => Promise<{status: string}>
 * @param {string} props.className - Additional CSS classes
 */
export function VerifyButton({ refId, onVerify, className = '' }) {
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleVerify = async () => {
    setIsLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await onVerify(refId);
      setResult(response);
    } catch (err) {
      setError(err.message || 'Verification failed');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className={`blockchain__verify-wrapper ${className}`}>
      <button
        type="button"
        className="blockchain__btn blockchain__btn--verify"
        onClick={handleVerify}
        disabled={isLoading}
      >
        {isLoading ? 'Verifying...' : 'Verify Integrity'}
      </button>
      
      {result && (
        <VerificationBadge status={result.status} className="blockchain__verify-result" />
      )}
      
      {error && (
        <span className="blockchain__error">{error}</span>
      )}
    </div>
  );
}

/**
 * AnchorButton - Button for admin anchoring with confirmation
 * 
 * @param {Object} props
 * @param {string} props.refId - Analysis reference ID
 * @param {boolean} props.isAnchored - Whether already anchored
 * @param {Function} props.onAnchor - Anchor function (refId, force) => Promise
 * @param {Function} props.onSuccess - Callback after successful anchor
 * @param {string} props.className - Additional CSS classes
 */
export function AnchorButton({ refId, isAnchored = false, onAnchor, onSuccess, className = '' }) {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleAnchor = async () => {
    // Confirm if re-anchoring
    if (isAnchored) {
      const confirmed = window.confirm(
        'This analysis is already anchored. Are you sure you want to re-anchor it?'
      );
      if (!confirmed) return;
    }

    setIsLoading(true);
    setError(null);

    try {
      await onAnchor(refId, isAnchored);
      if (onSuccess) onSuccess();
    } catch (err) {
      setError(err.message || 'Anchor failed');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className={`blockchain__anchor-wrapper ${className}`}>
      <button
        type="button"
        className={`blockchain__btn ${isAnchored ? 'blockchain__btn--reanchor' : 'blockchain__btn--anchor'}`}
        onClick={handleAnchor}
        disabled={isLoading}
      >
        {isLoading ? 'Anchoring...' : isAnchored ? 'Re-Anchor' : 'Anchor to Chain'}
      </button>
      
      {error && (
        <span className="blockchain__error">{error}</span>
      )}
    </div>
  );
}

/**
 * BlockchainStatusCard - Card showing blockchain connection status
 * 
 * @param {Object} props
 * @param {Object} props.status - Blockchain status object
 * @param {boolean} props.isLoading - Loading state
 * @param {string} props.error - Error message if any
 */
export function BlockchainStatusCard({ status, isLoading, error }) {
  if (isLoading) {
    return (
      <div className="blockchain__status-card blockchain__status-card--loading">
        <h3 className="blockchain__status-title">Blockchain Status</h3>
        <p className="blockchain__status-text">Connecting...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="blockchain__status-card blockchain__status-card--error">
        <h3 className="blockchain__status-title">Blockchain Status</h3>
        <p className="blockchain__status-text blockchain__status-text--error">
          Disconnected: {error}
        </p>
      </div>
    );
  }

  if (!status) {
    return null;
  }

  return (
    <div className={`blockchain__status-card ${status.connected ? 'blockchain__status-card--connected' : 'blockchain__status-card--disconnected'}`}>
      <h3 className="blockchain__status-title">Blockchain Status</h3>
      <div className="blockchain__status-grid">
        <div className="blockchain__status-item">
          <span className="blockchain__status-label">Status</span>
          <span className={`blockchain__status-value ${status.connected ? 'blockchain__status-value--connected' : 'blockchain__status-value--disconnected'}`}>
            {status.connected ? '● Connected' : '○ Disconnected'}
          </span>
        </div>
        <div className="blockchain__status-item">
          <span className="blockchain__status-label">Network</span>
          <span className="blockchain__status-value">{status.network || 'Unknown'}</span>
        </div>
        <div className="blockchain__status-item">
          <span className="blockchain__status-label">Block Number</span>
          <span className="blockchain__status-value">{status.blockNumber || '-'}</span>
        </div>
        <div className="blockchain__status-item">
          <span className="blockchain__status-label">Contract</span>
          <span className="blockchain__status-value blockchain__status-value--mono">
            {status.contractAddress ? `${status.contractAddress.slice(0, 10)}...${status.contractAddress.slice(-8)}` : '-'}
          </span>
        </div>
      </div>
    </div>
  );
}

/**
 * AnalysisCard - Card displaying analysis with verify/anchor actions
 * 
 * @param {Object} props
 * @param {Object} props.analysis - Analysis object
 * @param {Function} props.onVerify - Verify function
 * @param {Function} props.onAnchor - Anchor function
 * @param {boolean} props.isAdmin - Whether user is admin
 * @param {Function} props.onRefresh - Callback to refresh data
 */
export function AnalysisCard({ analysis, onVerify, onAnchor, isAdmin = false, onRefresh }) {
  const isAnchored = analysis.isAnchored || analysis.is_anchored;
  const refId = analysis.refId || analysis.ref_id || analysis.id;
  
  // Format date - handle ISO string format from backend
  const createdAt = analysis.createdAt || analysis.created_at;
  let formattedDate = 'Unknown';
  if (createdAt) {
    try {
      const date = new Date(createdAt);
      if (!isNaN(date.getTime())) {
        formattedDate = date.toLocaleString();
      }
    } catch (e) {
      formattedDate = createdAt;
    }
  }

  // Scam classification display - backend returns scam_type
  const scamType = analysis.scam_type || analysis.scamType || analysis.scamClassification || analysis.scam_classification || analysis.classification;
  
  // Confidence - backend returns confidence_bps (basis points 0-10000)
  const confidenceBps = analysis.confidence_bps || analysis.confidenceBps;
  const confidenceScore = analysis.confidence_score || analysis.confidenceScore || analysis.confidence;
  
  let confidencePercent = null;
  if (confidenceBps != null) {
    // Convert basis points to percentage (divide by 100)
    confidencePercent = (confidenceBps / 100).toFixed(1);
  } else if (confidenceScore != null) {
    // Handle if it's already a decimal or percentage
    if (confidenceScore <= 1) {
      confidencePercent = (confidenceScore * 100).toFixed(1);
    } else {
      confidencePercent = confidenceScore.toFixed(1);
    }
  }

  return (
    <div className={`blockchain__analysis-card ${isAnchored ? 'blockchain__analysis-card--anchored' : ''}`}>
      <div className="blockchain__analysis-header">
        <span className="blockchain__analysis-id" title={refId}>
          {refId ? `${refId.slice(0, 8)}...` : 'N/A'}
        </span>
        <VerificationBadge status={isAnchored ? 'VERIFIED' : 'NOT_ANCHORED'} />
      </div>

      <div className="blockchain__analysis-body">
        <div className="blockchain__analysis-row">
          <span className="blockchain__analysis-label">Classification:</span>
          <span className="blockchain__analysis-value">{scamType || 'Unknown'}</span>
        </div>
        {confidencePercent && (
          <div className="blockchain__analysis-row">
            <span className="blockchain__analysis-label">Confidence:</span>
            <span className="blockchain__analysis-value">{confidencePercent}%</span>
          </div>
        )}
        <div className="blockchain__analysis-row">
          <span className="blockchain__analysis-label">Created:</span>
          <span className="blockchain__analysis-value">{formattedDate}</span>
        </div>
        {isAnchored && analysis.txHash && (
          <div className="blockchain__analysis-row">
            <span className="blockchain__analysis-label">TX Hash:</span>
            <span className="blockchain__analysis-value blockchain__analysis-value--mono">
              {analysis.txHash.slice(0, 10)}...
            </span>
          </div>
        )}
      </div>

      <div className="blockchain__analysis-actions">
        <VerifyButton refId={refId} onVerify={onVerify} />
        {isAdmin && (
          <AnchorButton
            refId={refId}
            isAnchored={isAnchored}
            onAnchor={onAnchor}
            onSuccess={onRefresh}
          />
        )}
      </div>
    </div>
  );
}
