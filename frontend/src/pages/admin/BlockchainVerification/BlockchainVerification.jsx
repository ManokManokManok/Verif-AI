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
} from '../../../components/admin';
import {
  BlockchainStatusCard,
  AnalysisCard,
} from '../../../components/blockchain/BlockchainComponents';
import {
  getBlockchainStatus,
  listAnalyses,
  verifyAnalysis,
  anchorAnalysis,
} from '../../../api/blockchain';
import BlockchainStatsCard from './components/BlockchainStatsCard';
import BlockchainFilters from './components/BlockchainFilters';
import AnalysisDetailsModal from './components/AnalysisDetailsModal';
import './BlockchainVerification.css';

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
  const [minConfidence, setMinConfidence] = useState(null);
  const [scamOnly, setScamOnly] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');

  // Details modal state
  const [selectedAnalysis, setSelectedAnalysis] = useState(null);
  const [detailsModalOpen, setDetailsModalOpen] = useState(false);

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
        minConfidence,
        scamOnly,
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
  }, [page, filter, classificationFilter, minConfidence, scamOnly]);

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

  // Handle card click - open details modal
  const handleCardClick = useCallback((analysis) => {
    setSelectedAnalysis(analysis);
    setDetailsModalOpen(true);
  }, []);

  const closeDetailsModal = useCallback(() => {
    setDetailsModalOpen(false);
    setSelectedAnalysis(null);
  }, []);

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

        <BlockchainStatsCard stats={stats} />
      </div>

      {/* Filters */}
      <BlockchainFilters
        filter={filter}
        setFilter={setFilter}
        classificationFilter={classificationFilter}
        setClassificationFilter={setClassificationFilter}
        classifications={classifications}
        searchTerm={searchTerm}
        setSearchTerm={setSearchTerm}
        minConfidence={minConfidence}
        setMinConfidence={setMinConfidence}
        scamOnly={scamOnly}
        setScamOnly={setScamOnly}
        setPage={setPage}
      />

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
                  onClick={handleCardClick}
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
      {/* Analysis Details Modal */}
      <AnalysisDetailsModal
        isOpen={detailsModalOpen}
        analysis={selectedAnalysis}
        onClose={closeDetailsModal}
        onVerify={handleVerify}
        onAnchor={handleAnchor}
        onRefresh={fetchAnalyses}
      />
    </div>
  );
}

BlockchainVerification.propTypes = {
  onNotify: PropTypes.func,
};
