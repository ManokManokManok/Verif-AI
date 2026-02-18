/**
 * BlockchainFilters Component
 * 
 * Filter controls for blockchain verification page.
 */

import React from 'react';
import PropTypes from 'prop-types';

export default function BlockchainFilters({ 
  filter, 
  setFilter, 
  classificationFilter,
  setClassificationFilter,
  classifications,
  searchTerm,
  setSearchTerm,
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

  return (
    <div className="blockchain-admin__filters">
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
    </div>
  );
}

BlockchainFilters.propTypes = {
  filter: PropTypes.string.isRequired,
  setFilter: PropTypes.func.isRequired,
  classificationFilter: PropTypes.string.isRequired,
  setClassificationFilter: PropTypes.func.isRequired,
  classifications: PropTypes.arrayOf(PropTypes.shape({
    value: PropTypes.string.isRequired,
    label: PropTypes.string.isRequired,
  })).isRequired,
  searchTerm: PropTypes.string.isRequired,
  setSearchTerm: PropTypes.func.isRequired,
  setPage: PropTypes.func.isRequired,
};
