import { useState, useEffect, useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  getBlockchainStatus,
  listAnalyses,
  verifyAnalysis,
  anchorAnalysis,
} from '../api/blockchain';
import {
  VerificationBadge,
  BlockchainStatusCard,
  AnalysisCard,
} from '../components/blockchain/BlockchainComponents';
import { useAuth } from '../context/AuthContext';

/**
 * BlockchainPage - Full page component for blockchain verification admin
 * Requires admin role to access
 */
function BlockchainPage() {
  const navigate = useNavigate();
  const { isLoggedIn, isAdmin, logout, user } = useAuth();

  // State
  const [blockchainStatus, setBlockchainStatus] = useState(null);
  const [statusLoading, setStatusLoading] = useState(true);
  const [statusError, setStatusError] = useState(null);

  const [analyses, setAnalyses] = useState([]);
  const [analysesLoading, setAnalysesLoading] = useState(true);
  const [analysesError, setAnalysesError] = useState(null);
  const [page, setPage] = useState(1);
  const [totalAnalyses, setTotalAnalyses] = useState(0);
  const [totalAnchored, setTotalAnchored] = useState(0);
  const limit = 12;

  const [filter, setFilter] = useState('all'); // 'all', 'anchored', 'pending'
  const [searchTerm, setSearchTerm] = useState('');

  // Handle logout
  const handleLogout = async () => {
    await logout();
    navigate('/');
  };

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
      const response = await listAnalyses({ page, limit, status: filter });
      setAnalyses(response.analyses || []);
      // Backend returns: total (all), count (current page), total_anchored (all anchored)
      setTotalAnalyses(response.total || response.count || 0);
      setTotalAnchored(response.total_anchored || 0);
    } catch (err) {
      if (err.status === 401) {
        setAnalysesError('Please log in to view analyses');
      } else {
        setAnalysesError(err.message || 'Failed to fetch analyses');
      }
    } finally {
      setAnalysesLoading(false);
    }
  }, [page, filter]);

  // Initial fetch
  useEffect(() => {
    fetchStatus();
    if (isLoggedIn) {
      fetchAnalyses();
    }
  }, [fetchStatus, fetchAnalyses, isLoggedIn]);

  // Auto-refresh status every 60s
  useEffect(() => {
    const interval = setInterval(fetchStatus, 60000);
    return () => clearInterval(interval);
  }, [fetchStatus]);

  // Handle verify
  const handleVerify = async (refId) => {
    return verifyAnalysis(refId);
  };

  // Handle anchor
  const handleAnchor = async (refId, force) => {
    await anchorAnalysis(refId, force);
    // Refresh analyses after anchoring
    fetchAnalyses();
  };

  // Compute stats from backend data
  const stats = useMemo(() => {
    // total = total count of all analyses from backend
    // totalAnchored = total_anchored from backend (accurate count)
    // pending = total - anchored
    return {
      total: totalAnalyses,
      anchored: totalAnchored,
      pending: Math.max(0, totalAnalyses - totalAnchored),
    };
  }, [totalAnalyses, totalAnchored]);

  // Filter analyses by search term (client-side for displayed items)
  const filteredAnalyses = useMemo(() => {
    if (!searchTerm) return analyses;
    const term = searchTerm.toLowerCase();
    return analyses.filter(a => {
      const refId = (a.refId || a.ref_id || a.id || '').toLowerCase();
      const classification = (a.scamClassification || a.scam_classification || a.classification || '').toLowerCase();
      return refId.includes(term) || classification.includes(term);
    });
  }, [analyses, searchTerm]);

  // Total pages
  const totalPages = Math.ceil(totalAnalyses / limit);

  // Not logged in
  if (!isLoggedIn) {
    return (
      <div className="blockchain">
        <div className="blockchain__container">
          <div className="blockchain__auth-required">
            <h2>Authentication Required</h2>
            <p>Please log in to access the blockchain verification dashboard.</p>
            <button
              type="button"
              className="blockchain__btn blockchain__btn--primary"
              onClick={() => navigate('/login')}
            >
              Go to Login
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Logged in but not admin
  if (!isAdmin) {
    return (
      <div className="blockchain">
        <div className="blockchain__container">
          <div className="blockchain__auth-required">
            <h2>Admin Access Required</h2>
            <p>This page is restricted to administrators only.</p>
            <p className="blockchain__auth-user">
              Logged in as: {user?.email || 'Unknown'}
            </p>
            <div className="blockchain__auth-actions">
              <button
                type="button"
                className="blockchain__btn blockchain__btn--secondary"
                onClick={() => navigate('/')}
              >
                Go Home
              </button>
              <button
                type="button"
                className="blockchain__btn blockchain__btn--primary"
                onClick={handleLogout}
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="blockchain">
      {/* Sidebar */}
      <aside className="blockchain__sidebar">
        <button className="blockchain__sidebtn" type="button" onClick={() => navigate('/')}>
          ←
        </button>
        <button className="blockchain__sidebtn blockchain__sidebtn--active" type="button">
          ⛓
        </button>
        <div className="blockchain__spacer" />
        <button className="blockchain__sidebtn" type="button" onClick={() => navigate('/detection')}>
          🔍
        </button>
      </aside>

      {/* Main content */}
      <div className="blockchain__main">
        {/* Header */}
        <header className="blockchain__header">
          <div className="blockchain__header-left">
            <h1 className="blockchain__title">Blockchain Verification</h1>
            <p className="blockchain__subtitle">
              Verify and anchor analysis results to the blockchain
            </p>
          </div>
          <div className="blockchain__header-right">
            {isAdmin && (
              <span className="blockchain__admin-badge">Admin Mode</span>
            )}
            <button
              type="button"
              className="blockchain__btn blockchain__btn--secondary"
              onClick={() => { fetchStatus(); fetchAnalyses(); }}
            >
              Refresh
            </button>
          </div>
        </header>

        {/* Status and Stats Row */}
        <div className="blockchain__top-row">
          <BlockchainStatusCard
            status={blockchainStatus}
            isLoading={statusLoading}
            error={statusError}
          />

          <div className="blockchain__stats-card">
            <h3 className="blockchain__stats-title">Quick Stats</h3>
            <div className="blockchain__stats-grid">
              <div className="blockchain__stat">
                <span className="blockchain__stat-value">{stats.total}</span>
                <span className="blockchain__stat-label">Total Analyses</span>
              </div>
              <div className="blockchain__stat blockchain__stat--success">
                <span className="blockchain__stat-value">{stats.anchored}</span>
                <span className="blockchain__stat-label">Anchored</span>
              </div>
              <div className="blockchain__stat blockchain__stat--pending">
                <span className="blockchain__stat-value">{stats.pending}</span>
                <span className="blockchain__stat-label">Pending</span>
              </div>
            </div>
          </div>
        </div>

        {/* Filters and Search */}
        <div className="blockchain__filters">
          <div className="blockchain__filter-group">
            <button
              type="button"
              className={`blockchain__filter-btn ${filter === 'all' ? 'blockchain__filter-btn--active' : ''}`}
              onClick={() => { setFilter('all'); setPage(1); }}
            >
              All
            </button>
            <button
              type="button"
              className={`blockchain__filter-btn ${filter === 'anchored' ? 'blockchain__filter-btn--active' : ''}`}
              onClick={() => { setFilter('anchored'); setPage(1); }}
            >
              Anchored
            </button>
            <button
              type="button"
              className={`blockchain__filter-btn ${filter === 'pending' ? 'blockchain__filter-btn--active' : ''}`}
              onClick={() => { setFilter('pending'); setPage(1); }}
            >
              Pending
            </button>
          </div>
          <div className="blockchain__search">
            <input
              type="text"
              className="blockchain__search-input"
              placeholder="Search by ID or classification..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
        </div>

        {/* Analyses Grid */}
        <div className="blockchain__content">
          {analysesLoading ? (
            <div className="blockchain__loading">Loading analyses...</div>
          ) : analysesError ? (
            <div className="blockchain__error-box">
              <p>{analysesError}</p>
              <button
                type="button"
                className="blockchain__btn blockchain__btn--secondary"
                onClick={fetchAnalyses}
              >
                Retry
              </button>
            </div>
          ) : filteredAnalyses.length === 0 ? (
            <div className="blockchain__empty">
              <p>No analyses found.</p>
              {filter !== 'all' && (
                <button
                  type="button"
                  className="blockchain__btn blockchain__btn--secondary"
                  onClick={() => setFilter('all')}
                >
                  Show All
                </button>
              )}
            </div>
          ) : (
            <>
              <div className="blockchain__grid">
                {filteredAnalyses.map((analysis) => (
                  <AnalysisCard
                    key={analysis.refId || analysis.ref_id || analysis.id}
                    analysis={analysis}
                    onVerify={handleVerify}
                    onAnchor={handleAnchor}
                    isAdmin={isAdmin}
                    onRefresh={fetchAnalyses}
                  />
                ))}
              </div>

              {/* Pagination */}
              {totalPages > 1 && (
                <div className="blockchain__pagination">
                  <button
                    type="button"
                    className="blockchain__page-btn"
                    disabled={page <= 1}
                    onClick={() => setPage(p => p - 1)}
                  >
                    Previous
                  </button>
                  <span className="blockchain__page-info">
                    Page {page} of {totalPages}
                  </span>
                  <button
                    type="button"
                    className="blockchain__page-btn"
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
      </div>
    </div>
  );
}

export default BlockchainPage;
