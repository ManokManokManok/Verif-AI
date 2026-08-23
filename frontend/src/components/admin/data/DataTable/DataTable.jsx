/**
 * DataTable Component
 * 
 * Reusable table with sorting, pagination, and actions.
 */

import React from 'react';
import PropTypes from 'prop-types';
import './DataTable.css';

export default function DataTable({
  columns,
  data,
  loading = false,
  pagination,
  onPageChange,
  emptyMessage = 'No data available',
  className = '',
  compact = false,
}) {
  if (loading) {
    return (
      <div className={`data-table ${compact ? 'data-table--compact' : ''} data-table--loading ${className}`}>
        <div className="data-table__skeleton">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="data-table__skeleton-row" />
          ))}
        </div>
      </div>
    );
  }

  if (!data || data.length === 0) {
    return (
      <div className={`data-table ${compact ? 'data-table--compact' : ''} data-table--empty ${className}`}>
        <p className="data-table__empty-message">{emptyMessage}</p>
      </div>
    );
  }

  return (
    <div className={`data-table ${compact ? 'data-table--compact' : ''} ${className}`}>
      <div className="data-table__wrapper">
        <table className="data-table__table">
          <thead className="data-table__head">
            <tr>
              {columns.map((col) => (
                <th key={col.key} className="data-table__th">
                  {col.label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="data-table__body">
            {data.map((row, rowIndex) => (
              <tr key={row.id || rowIndex} className="data-table__row">
                {columns.map((col) => (
                  <td key={col.key} className="data-table__td">
                    {col.render ? col.render(row[col.key], row) : row[col.key]}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      
      {pagination && (
        <div className="data-table__pagination">
          <span className="data-table__pagination-info">
            Showing {((pagination.page - 1) * pagination.limit) + 1} - {Math.min(pagination.page * pagination.limit, pagination.total)} of {pagination.total}
          </span>
          <div className="data-table__pagination-controls">
            <button
              className="data-table__pagination-btn"
              onClick={() => onPageChange(pagination.page - 1)}
              disabled={pagination.page <= 1}
            >
              Previous
            </button>
            <span className="data-table__pagination-current">
              Page {pagination.page} of {pagination.totalPages}
            </span>
            <button
              className="data-table__pagination-btn"
              onClick={() => onPageChange(pagination.page + 1)}
              disabled={pagination.page >= pagination.totalPages}
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

DataTable.propTypes = {
  columns: PropTypes.arrayOf(PropTypes.shape({
    key: PropTypes.string.isRequired,
    label: PropTypes.oneOfType([
      PropTypes.string,
      PropTypes.node,
    ]).isRequired,
    render: PropTypes.func,
  })).isRequired,
  data: PropTypes.array.isRequired,
  loading: PropTypes.bool,
  pagination: PropTypes.shape({
    page: PropTypes.number,
    limit: PropTypes.number,
    total: PropTypes.number,
    totalPages: PropTypes.number,
  }),
  onPageChange: PropTypes.func,
  emptyMessage: PropTypes.string,
  className: PropTypes.string,
};
