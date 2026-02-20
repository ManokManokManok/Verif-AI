/**
 * BlockchainFilters Component
 * 
 * Filter controls for blockchain verification page.
 * Includes status, classification, search, confidence threshold, and scam-only filters.
 */

import React, { useCallback } from 'react';
import PropTypes from 'prop-types';

export default function BlockchainFilters({ 
  filter, 
  setFilter, 
  classificationFilter,
  setClassificationFilter,
  classifications,
  searchTerm,
  setSearchTerm,
  minConfidence,
  setMinConfidence,
  scamOnly,
  setScamOnly,
  setPage
}) {
  const handleFilterChange = (newFilter) => {
    setFilter(newFilter);
    setPage(1);
  };

  const handleClassificationChange = (e) => {
    setClassificationFilter(e.target.value);
    setPage(1);
  };

  const handleConfidenceChange = useCallback((e) => {
    const value = parseInt(e.target.value, 10);
    setMinConfidence(value === 0 ? null : value);
    setPage(1);
  }, [setMinConfidence, setPage]);

  const handleConfidenceInput = useCallback((e) => {
    const value = e.target.value;
    if (value === '' || value === '0') {
      setMinConfidence(null);
    } else {
      const num = parseInt(value, 10);
      if (!isNaN(num) && num >= 0 && num <= 100) {
        setMinConfidence(num);
      }
    }
    setPage(1);
  }, [setMinConfidence, setPage]);

  const handleScamOnlyChange = useCallback((e) => {
    setScamOnly(e.target.checked);
    setPage(1);
  }, [setScamOnly, setPage]);

  const applyHighConfidenceScams = useCallback(() => {
    setMinConfidence(80);
    setScamOnly(true);
    setPage(1);
  }, [setMinConfidence, setScamOnly, setPage]);

  const applyMediumConfidence = useCallback(() => {
    setMinConfidence(50);
    setScamOnly(false);
    setPage(1);
  }, [setMinConfidence, setScamOnly, setPage]);

  const clearConfidenceFilters = useCallback(() => {
    setMinConfidence(null);
    setScamOnly(false);
    setPage(1);
  }, [setMinConfidence, setScamOnly, setPage]);

  const hasConfidenceFilters = minConfidence !== null || scamOnly;
  const isHighConfidenceScams = minConfidence === 80 && scamOnly;
  const isMediumConfidence = minConfidence === 50 && !scamOnly;

  return (
    <div className="blockchain-admin__filters">
      {/* Primary filter row */}
      <div className="blockchain-admin__filter-row">
        <div className="blockchain-admin__filter-group">
          <button
            className={`blockchain-admin__filter-btn ${filter === 'all' ? 'blockchain-admin__filter-btn--active' : ''}`}
            onClick={() => handleFilterChange('all')}
          >
            All
          </button>
          <button
            className={`blockchain-admin__filter-btn ${filter === 'anchored' ? 'blockchain-admin__filter-btn--active' : ''}`}
            onClick={() => handleFilterChange('anchored')}
          >
            Anchored
          </button>
          <button
            className={`blockchain-admin__filter-btn ${filter === 'pending' ? 'blockchain-admin__filter-btn--active' : ''}`}
            onClick={() => handleFilterChange('pending')}
          >
            Pending
          </button>
        </div>

        <select
          className="blockchain-admin__select"
          value={classificationFilter}
          onChange={handleClassificationChange}
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

      {/* Secondary filter row - Confidence threshold */}
      <div className="blockchain-admin__filter-row--secondary">
        <div className="blockchain-admin__confidence-filter">
          <label className="blockchain-admin__filter-label">
            Min Confidence:
          </label>
          <div className="blockchain-admin__confidence-controls">
            <input
              type="range"
              className="blockchain-admin__confidence-slider"
              min="0"
              max="100"
              step="5"
              value={minConfidence || 0}
              onChange={handleConfidenceChange}
              aria-label="Minimum confidence threshold"
            />
            <input
              type="number"
              className="blockchain-admin__confidence-input"
              min="0"
              max="100"
              value={minConfidence || ''}
              onChange={handleConfidenceInput}
              placeholder="0"
              aria-label="Minimum confidence percentage"
            />
            <span className="blockchain-admin__confidence-label">%</span>
          </div>
        </div>

        <label className="blockchain-admin__checkbox-label">
          <input
            type="checkbox"
            className="blockchain-admin__checkbox"
            checked={scamOnly}
            onChange={handleScamOnlyChange}
          />
          Scam Only
        </label>

        <div className="blockchain-admin__quick-filters">
          <button
            className={`blockchain-admin__quick-filter-btn ${isHighConfidenceScams ? 'blockchain-admin__quick-filter-btn--active' : ''}`}
            onClick={applyHighConfidenceScams}
            title="Show only scam analyses with confidence >= 80%"
          >
            High Confidence Scams (&ge;80%)
          </button>
          <button
            className={`blockchain-admin__quick-filter-btn ${isMediumConfidence ? 'blockchain-admin__quick-filter-btn--active' : ''}`}
            onClick={applyMediumConfidence}
            title="Show all analyses with confidence >= 50%"
          >
            Medium+ (&ge;50%)
          </button>
          {hasConfidenceFilters && (
            <button
              className="blockchain-admin__quick-filter-btn blockchain-admin__quick-filter-btn--clear"
              onClick={clearConfidenceFilters}
              title="Clear confidence and scam-only filters"
            >
              Clear
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

BlockchainFilters.propTypes = {
  filter: PropTypes.string.isRequired,
  setFilter: PropTypes.func.isRequired,
  classificationFilter: PropTypes.string.isRequired,
  setClassificationFilter: PropTypes.func.isRequired,
  classifications: PropTypes.arrayOf(PropTypes.shape({
    value: PropTypes.oneOfType([PropTypes.string, PropTypes.number]).isRequired,
    label: PropTypes.string.isRequired,
  })).isRequired,
  searchTerm: PropTypes.string.isRequired,
  setSearchTerm: PropTypes.func.isRequired,
  minConfidence: PropTypes.number,
  setMinConfidence: PropTypes.func.isRequired,
  scamOnly: PropTypes.bool.isRequired,
  setScamOnly: PropTypes.func.isRequired,
  setPage: PropTypes.func.isRequired,
};
