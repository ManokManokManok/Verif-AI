/**
 * Blockchain Verification Tab
 * 
 * Admin interface for verifying and anchoring analysis results to the blockchain.
 * Uses shared BlockchainComponents for consistency with the standalone Blockchain page.
 */

import React, { useState, useEffect, useCallback, useMemo } from 'react';
import PropTypes from 'prop-types';
import {
  LoadingSpinner,
  ErrorMessage,
} from '../../components/admin';
import {
  BlockchainStatusCard,
  AnalysisCard,
} from '../../components/blockchain/BlockchainComponents';
import {
  getBlockchainStatus,
  listAnalyses,
  verifyAnalysis,
  anchorAnalysis,
} from '../../api/blockchain';

/**
 * Main Blockchain Verification Component
 */
export default function BlockchainVerification({ onNotify }) {
  // Blockchain status state
  const [blockchainStatus, setBlockchainStatus] = useState(null);
  const [statusLoading, setStatusLoading] = useState(true);
  const [statusError, setStatusError] = useState(null);

  // Analyses state
  const [analyses, setAnalyses] = useState([]);
  const [analysesLoading, setAnalysesLoading] = useState(true);
  const [analysesError, setAnalysesError] = useState(null);
  const [page, setPage] = useState(1);
  const [totalFiltered, setTotalFiltered] = useState(0);
  const [totalAnchored, setTotalAnchored] = useState(0);
  const [totalAll, setTotalAll] = useState(0);
  const [classifications, setClassifications] = useState([]);
  const limit = 12;

  // Filters
  const [filter, setFilter] = useState('all');
  const [classificationFilter, setClassificationFilter] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');

  // Fetch blockchain status
  const fetchStatus = useCallback(async () => {
    setStatusLoading(true);
    setStatusError(null);
    try {
      const status = await getBlockchainStatus();
      setBlockchainStatus(status);
    } catch (err) {
      setStatusError(err.message || 'Failed to fetch status');
    } finally {
      setStatusLoading(false);
    }
  }, []);

  // Fetch analyses
  const fetchAnalyses = useCallback(async () => {
    setAnalysesLoading(true);
    setAnalysesError(null);
    try {
      const response = await listAnalyses({
        page,
        limit,
        status: filter,
        classification: classificationFilter,
      });
      setAnalyses(response.analyses || []);
      setTotalFiltered(response.total || response.count || 0);
      setTotalAnchored(response.total_anchored || 0);
      setTotalAll(response.total_all || response.total || 0);
      if (response.classifications) {
        setClassifications(response.classifications);
      }
    } catch (err) {
      setAnalysesError(err.message || 'Failed to fetch analyses');
    } finally {
      setAnalysesLoading(false);
    }
  }, [page, filter, classificationFilter]);

  // Initial fetch
  useEffect(() => {
    fetchStatus();
    fetchAnalyses();
  }, [fetchStatus, fetchAnalyses]);

  // Auto-refresh status every 60s
  useEffect(() => {
    const interval = setInterval(fetchStatus, 60000);
    return () => clearInterval(interval);
  }, [fetchStatus]);

  // Handle verify - uses verifyAnalysis API (API already returns status field)
  const handleVerify = useCallback(async (refId) => {
    try {
      return await verifyAnalysis(refId);
    } catch (err) {
      onNotify?.('error', `Verification failed: ${err.message}`);
      throw err;
    }
  }, [onNotify]);

  // Handle anchor - uses anchorAnalysis API
  const handleAnchor = useCallback(async (refId, force) => {
    try {
      await anchorAnalysis(refId, force);
      onNotify?.('success', `Analysis ${refId.slice(0, 8)}... anchored to blockchain`);
      fetchAnalyses();
    } catch (err) {
      onNotify?.('error', `Anchor failed: ${err.message}`);
      throw err;
    }
  }, [onNotify, fetchAnalyses]);

  // Compute stats
  const stats = useMemo(() => ({
    total: totalAll,
    anchored: totalAnchored,
    pending: Math.max(0, totalAll - totalAnchored),
  }), [totalAll, totalAnchored]);

  // Filter analyses by search term (client-side)
  const filteredAnalyses = useMemo(() => {
    if (!searchTerm) return analyses;
    const term = searchTerm.toLowerCase();
    return analyses.filter(a => {
      const refId = (a.ref_id || a.refId || a.id || '').toLowerCase();
      const scamType = (a.scam_type || a.scamType || '').toLowerCase();
      const message = (a.message || '').toLowerCase();
      return refId.includes(term) || scamType.includes(term) || message.includes(term);
    });
  }, [analyses, searchTerm]);

  const totalPages = Math.ceil(totalFiltered / limit);

  if (analysesLoading && !analyses.length) {
    return (
      <div className="admin-section">
        <div className="admin-section__loading">
          <LoadingSpinner size="large" />
          <p>Loading blockchain data...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="admin-section blockchain-admin">
      {/* Header */}
      <div className="admin-section__header">
        <h2 className="admin-section__title">Blockchain Verification</h2>
        <div className="admin-section__actions">
          <button
            className="admin-btn admin-btn--secondary admin-btn--sm"
            onClick={() => { fetchStatus(); fetchAnalyses(); }}
            disabled={analysesLoading}
          >
            {analysesLoading ? 'Refreshing...' : 'Refresh'}
          </button>
        </div>
      </div>

      {/* Status and Stats Row */}
      <div className="blockchain-admin__top-row">
        {/* Use the shared BlockchainStatusCard component */}
        <BlockchainStatusCard
          status={blockchainStatus}
          isLoading={statusLoading}
          error={statusError}
        />

        <div className="blockchain-admin__stats-card">
          <h3 className="blockchain-admin__stats-title">Quick Stats</h3>
          <div className="blockchain-admin__stats-grid">
            <div className="blockchain-admin__stat-item">
              <span className="blockchain-admin__stat-value">{stats.total}</span>
              <span className="blockchain-admin__stat-label">Total Analyses</span>
            </div>
            <div className="blockchain-admin__stat-item blockchain-admin__stat-item--success">
              <span className="blockchain-admin__stat-value">{stats.anchored}</span>
              <span className="blockchain-admin__stat-label">Anchored</span>
            </div>
            <div className="blockchain-admin__stat-item blockchain-admin__stat-item--warning">
              <span className="blockchain-admin__stat-value">{stats.pending}</span>
              <span className="blockchain-admin__stat-label">Pending</span>
            </div>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="blockchain-admin__filters">
        <div className="blockchain-admin__filter-row">
          <div className="blockchain-admin__filter-group">
            <button
              className={`blockchain-admin__filter-btn ${filter === 'all' ? 'blockchain-admin__filter-btn--active' : ''}`}
              onClick={() => { setFilter('all'); setPage(1); }}
            >
              All
            </button>
            <button
              className={`blockchain-admin__filter-btn ${filter === 'anchored' ? 'blockchain-admin__filter-btn--active' : ''}`}
              onClick={() => { setFilter('anchored'); setPage(1); }}
            >
              Anchored
            </button>
            <button
              className={`blockchain-admin__filter-btn ${filter === 'pending' ? 'blockchain-admin__filter-btn--active' : ''}`}
              onClick={() => { setFilter('pending'); setPage(1); }}
            >
              Pending
            </button>
          </div>

          <select
            className="blockchain-admin__select"
            value={classificationFilter}
            onChange={(e) => { setClassificationFilter(e.target.value); setPage(1); }}
          >
            <option value="all">All Classifications</option>
            {classifications.map((cls) => (
              <option key={cls.value} value={cls.value}>
                {cls.label}
              </option>
            ))}
          </select>

          <div className="blockchain-admin__search">
            <input
              type="text"
              className="blockchain-admin__search-input"
              placeholder="Search by ID or type..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
        </div>
      </div>

      {/* Analyses Grid */}
      <div className="blockchain-admin__content">
        {analysesError ? (
          <ErrorMessage
            message={`Failed to load analyses: ${analysesError}`}
            onRetry={fetchAnalyses}
          />
        ) : filteredAnalyses.length === 0 ? (
          <div className="blockchain-admin__empty">
            <p>No analyses found.</p>
            {filter !== 'all' && (
              <button
                className="blockchain-admin__filter-btn"
                onClick={() => setFilter('all')}
              >
                Show All
              </button>
            )}
          </div>
        ) : (
          <>
            {/* Use the shared AnalysisCard component */}
            <div className="blockchain-admin__analyses-grid">
              {filteredAnalyses.map((analysis) => (
                <AnalysisCard
                  key={analysis.refId || analysis.ref_id || analysis.id}
                  analysis={analysis}
                  onVerify={handleVerify}
                  onAnchor={handleAnchor}
                  isAdmin={true}
                  onRefresh={fetchAnalyses}
                />
              ))}
            </div>

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="blockchain-admin__pagination">
                <button
                  className="blockchain-admin__page-btn"
                  disabled={page <= 1}
                  onClick={() => setPage(p => p - 1)}
                >
                  Previous
                </button>
                <span className="blockchain-admin__page-info">
                  Page {page} of {totalPages}
                </span>
                <button
                  className="blockchain-admin__page-btn"
                  disabled={page >= totalPages}
                  onClick={() => setPage(p => p + 1)}
                >
                  Next
                </button>
              </div>
            )}
          </>
        )}
      </div>

      <style>{`
        .blockchain-admin {
          padding: 1.5rem;
        }

        .blockchain-admin__top-row {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
          gap: 1.5rem;
          margin-bottom: 1.5rem;
        }

        .blockchain-admin__stats-card {
          background: var(--admin-card-bg, #1a1a1a);
          border: 1px solid var(--admin-border, #333);
          border-radius: 12px;
          padding: 1.25rem;
        }

        .blockchain-admin__stats-title {
          font-size: 1rem;
          font-weight: 600;
          color: var(--admin-text, #fff);
          margin: 0 0 1rem 0;
        }

        .blockchain-admin__stats-grid {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: 1rem;
        }

        .blockchain-admin__stat-item {
          text-align: center;
          padding: 0.75rem;
          background: var(--admin-bg-dark, #0f0f0f);
          border-radius: 8px;
        }

        .blockchain-admin__stat-item--success {
          border-left: 3px solid var(--admin-success, #22c55e);
        }

        .blockchain-admin__stat-item--warning {
          border-left: 3px solid var(--admin-warning, #f59e0b);
        }

        .blockchain-admin__stat-value {
          display: block;
          font-size: 1.5rem;
          font-weight: 700;
          color: var(--admin-text, #fff);
        }

        .blockchain-admin__stat-label {
          display: block;
          font-size: 0.75rem;
          color: var(--admin-text-muted, #a0a0a0);
          margin-top: 0.25rem;
        }

        .blockchain-admin__filters {
          background: var(--admin-card-bg, #1a1a1a);
          border: 1px solid var(--admin-border, #333);
          border-radius: 12px;
          padding: 1rem;
          margin-bottom: 1.5rem;
        }

        .blockchain-admin__filter-row {
          display: flex;
          flex-wrap: wrap;
          gap: 1rem;
          align-items: center;
        }

        .blockchain-admin__filter-group {
          display: flex;
          gap: 0.5rem;
        }

        .blockchain-admin__filter-btn {
          padding: 0.5rem 1rem;
          border: 1px solid var(--admin-border, #333);
          border-radius: 6px;
          background: transparent;
          color: var(--admin-text-muted, #a0a0a0);
          cursor: pointer;
          transition: all 0.2s;
        }

        .blockchain-admin__filter-btn:hover {
          border-color: var(--admin-primary, #855ad1);
          color: var(--admin-text, #fff);
        }

        .blockchain-admin__filter-btn--active {
          background: var(--admin-primary, #855ad1);
          border-color: var(--admin-primary, #855ad1);
          color: #fff;
        }

        .blockchain-admin__select {
          padding: 0.5rem 1rem;
          border: 1px solid var(--admin-border, #333);
          border-radius: 6px;
          background: var(--admin-bg-dark, #0f0f0f);
          color: var(--admin-text, #fff);
          cursor: pointer;
        }

        .blockchain-admin__search {
          flex: 1;
          min-width: 200px;
        }

        .blockchain-admin__search-input {
          width: 100%;
          padding: 0.5rem 1rem;
          border: 1px solid var(--admin-border, #333);
          border-radius: 6px;
          background: var(--admin-bg-dark, #0f0f0f);
          color: var(--admin-text, #fff);
        }

        .blockchain-admin__search-input::placeholder {
          color: var(--admin-text-muted, #a0a0a0);
        }

        .blockchain-admin__content {
          min-height: 300px;
        }

        .blockchain-admin__analyses-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
          gap: 1rem;
        }

        .blockchain-admin__empty {
          text-align: center;
          padding: 3rem;
          color: var(--admin-text-muted, #a0a0a0);
          background: var(--admin-card-bg, #1a1a1a);
          border: 1px solid var(--admin-border, #333);
          border-radius: 12px;
        }

        .blockchain-admin__pagination {
          display: flex;
          justify-content: center;
          align-items: center;
          gap: 1rem;
          margin-top: 1.5rem;
          padding-top: 1.5rem;
          border-top: 1px solid var(--admin-border, #333);
        }

        .blockchain-admin__page-btn {
          padding: 0.5rem 1rem;
          border: 1px solid var(--admin-border, #333);
          border-radius: 6px;
          background: transparent;
          color: var(--admin-text, #fff);
          cursor: pointer;
          transition: all 0.2s;
        }

        .blockchain-admin__page-btn:hover:not(:disabled) {
          border-color: var(--admin-primary, #855ad1);
        }

        .blockchain-admin__page-btn:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        .blockchain-admin__page-info {
          color: var(--admin-text-muted, #a0a0a0);
          font-size: 0.875rem;
        }

        @media (max-width: 768px) {
          .blockchain-admin {
            padding: 1rem;
          }

          .blockchain-admin__filter-row {
            flex-direction: column;
            align-items: stretch;
          }

          .blockchain-admin__search {
            min-width: 100%;
          }

          .blockchain-admin__stats-grid {
            grid-template-columns: 1fr;
          }

          .blockchain-admin__analyses-grid {
            grid-template-columns: 1fr;
          }
        }
      `}</style>
    </div>
  );
}

BlockchainVerification.propTypes = {
  onNotify: PropTypes.func,
};
