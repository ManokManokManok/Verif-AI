/**
 * StatCard Component
 * 
 * Displays a single statistic with label, value, and optional trend indicator.
 */

import React from 'react';
import PropTypes from 'prop-types';
import './AdminComponents.css';

export function StatCard({ 
  title, 
  value, 
  subtitle, 
  icon, 
  trend, 
  trendValue,
  variant = 'default',
  loading = false,
  className = ''
}) {
  const variantClass = `admin-stat-card--${variant}`;
  const trendClass = trend === 'up' ? 'admin-stat-card__trend--up' 
    : trend === 'down' ? 'admin-stat-card__trend--down' 
    : 'admin-stat-card__trend--stable';

  if (loading) {
    return (
      <div className={`admin-stat-card ${variantClass} admin-stat-card--loading ${className}`}>
        <div className="admin-stat-card__skeleton" />
      </div>
    );
  }

  return (
    <div className={`admin-stat-card ${variantClass} ${className}`}>
      {icon && <div className="admin-stat-card__icon">{icon}</div>}
      <div className="admin-stat-card__content">
        <h3 className="admin-stat-card__title">{title}</h3>
        <p className="admin-stat-card__value">{value}</p>
        {subtitle && <span className="admin-stat-card__subtitle">{subtitle}</span>}
        {trend && trendValue && (
          <div className={`admin-stat-card__trend ${trendClass}`}>
            <span className="admin-stat-card__trend-arrow">
              {trend === 'up' ? '↑' : trend === 'down' ? '↓' : '→'}
            </span>
            <span className="admin-stat-card__trend-value">{trendValue}</span>
          </div>
        )}
      </div>
    </div>
  );
}

StatCard.propTypes = {
  title: PropTypes.string.isRequired,
  value: PropTypes.oneOfType([PropTypes.string, PropTypes.number]).isRequired,
  subtitle: PropTypes.string,
  icon: PropTypes.node,
  trend: PropTypes.oneOf(['up', 'down', 'stable']),
  trendValue: PropTypes.string,
  variant: PropTypes.oneOf(['default', 'success', 'warning', 'danger', 'info']),
  loading: PropTypes.bool,
  className: PropTypes.string,
};

/**
 * MetricGauge Component
 * 
 * Circular gauge for percentage metrics (CPU, GPU, Memory).
 */
export function MetricGauge({ 
  label, 
  value, 
  maxValue = 100, 
  unit = '%',
  thresholds = { warning: 70, danger: 90 },
  size = 'medium',
  loading = false,
  className = ''
}) {
  const percentage = Math.min((value / maxValue) * 100, 100);
  const circumference = 2 * Math.PI * 45; // radius = 45
  const strokeDashoffset = circumference - (percentage / 100) * circumference;
  
  const getStatusClass = () => {
    if (percentage >= thresholds.danger) return 'admin-gauge--danger';
    if (percentage >= thresholds.warning) return 'admin-gauge--warning';
    return 'admin-gauge--normal';
  };

  const sizeClass = `admin-gauge--${size}`;

  if (loading) {
    return (
      <div className={`admin-gauge ${sizeClass} admin-gauge--loading ${className}`}>
        <div className="admin-gauge__skeleton" />
      </div>
    );
  }

  return (
    <div className={`admin-gauge ${sizeClass} ${getStatusClass()} ${className}`}>
      <svg className="admin-gauge__svg" viewBox="0 0 100 100">
        {/* Background circle */}
        <circle
          className="admin-gauge__background"
          cx="50"
          cy="50"
          r="45"
          fill="none"
          strokeWidth="8"
        />
        {/* Progress circle */}
        <circle
          className="admin-gauge__progress"
          cx="50"
          cy="50"
          r="45"
          fill="none"
          strokeWidth="8"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={strokeDashoffset}
          transform="rotate(-90 50 50)"
        />
      </svg>
      <div className="admin-gauge__content">
        <span className="admin-gauge__value">{Math.round(value)}{unit}</span>
        <span className="admin-gauge__label">{label}</span>
      </div>
    </div>
  );
}

MetricGauge.propTypes = {
  label: PropTypes.string.isRequired,
  value: PropTypes.number.isRequired,
  maxValue: PropTypes.number,
  unit: PropTypes.string,
  thresholds: PropTypes.shape({
    warning: PropTypes.number,
    danger: PropTypes.number,
  }),
  size: PropTypes.oneOf(['small', 'medium', 'large']),
  loading: PropTypes.bool,
  className: PropTypes.string,
};

/**
 * DataTable Component
 * 
 * Reusable table with sorting, pagination, and actions.
 */
export function DataTable({
  columns,
  data,
  loading = false,
  pagination,
  onPageChange,
  emptyMessage = 'No data available',
  className = '',
}) {
  if (loading) {
    return (
      <div className={`admin-table admin-table--loading ${className}`}>
        <div className="admin-table__skeleton">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="admin-table__skeleton-row" />
          ))}
        </div>
      </div>
    );
  }

  if (!data || data.length === 0) {
    return (
      <div className={`admin-table admin-table--empty ${className}`}>
        <p className="admin-table__empty-message">{emptyMessage}</p>
      </div>
    );
  }

  return (
    <div className={`admin-table ${className}`}>
      <div className="admin-table__wrapper">
        <table className="admin-table__table">
          <thead className="admin-table__head">
            <tr>
              {columns.map((col) => (
                <th key={col.key} className="admin-table__th">
                  {col.label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="admin-table__body">
            {data.map((row, rowIndex) => (
              <tr key={row.id || rowIndex} className="admin-table__row">
                {columns.map((col) => (
                  <td key={col.key} className="admin-table__td">
                    {col.render ? col.render(row[col.key], row) : row[col.key]}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      
      {pagination && (
        <div className="admin-table__pagination">
          <span className="admin-table__pagination-info">
            Showing {((pagination.page - 1) * pagination.limit) + 1} - {Math.min(pagination.page * pagination.limit, pagination.total)} of {pagination.total}
          </span>
          <div className="admin-table__pagination-controls">
            <button
              className="admin-table__pagination-btn"
              onClick={() => onPageChange(pagination.page - 1)}
              disabled={pagination.page <= 1}
            >
              Previous
            </button>
            <span className="admin-table__pagination-current">
              Page {pagination.page} of {pagination.totalPages}
            </span>
            <button
              className="admin-table__pagination-btn"
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
    label: PropTypes.string.isRequired,
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

/**
 * StatusBadge Component
 * 
 * Displays status with colored badge.
 */
export function StatusBadge({ status, variant, className = '' }) {
  const statusConfig = {
    pending: { label: 'Pending', variant: 'warning' },
    in_progress: { label: 'In Progress', variant: 'info' },
    resolved: { label: 'Resolved', variant: 'success' },
    dismissed: { label: 'Dismissed', variant: 'default' },
    active: { label: 'Active', variant: 'success' },
    inactive: { label: 'Inactive', variant: 'danger' },
    verified: { label: 'Verified', variant: 'success' },
    unverified: { label: 'Unverified', variant: 'warning' },
  };

  const config = statusConfig[status] || { label: status, variant: variant || 'default' };
  const badgeVariant = variant || config.variant;

  return (
    <span className={`admin-badge admin-badge--${badgeVariant} ${className}`}>
      {config.label}
    </span>
  );
}

StatusBadge.propTypes = {
  status: PropTypes.string.isRequired,
  variant: PropTypes.oneOf(['default', 'success', 'warning', 'danger', 'info']),
  className: PropTypes.string,
};

/**
 * TabNavigation Component
 * 
 * Tab navigation for admin sections.
 */
export function TabNavigation({ tabs, activeTab, onTabChange, className = '' }) {
  return (
    <nav className={`admin-tabs ${className}`}>
      <ul className="admin-tabs__list">
        {tabs.map((tab) => (
          <li key={tab.id} className="admin-tabs__item">
            <button
              className={`admin-tabs__button ${activeTab === tab.id ? 'admin-tabs__button--active' : ''}`}
              onClick={() => onTabChange(tab.id)}
            >
              {tab.icon && <span className="admin-tabs__icon">{tab.icon}</span>}
              <span className="admin-tabs__label">{tab.label}</span>
            </button>
          </li>
        ))}
      </ul>
    </nav>
  );
}

TabNavigation.propTypes = {
  tabs: PropTypes.arrayOf(PropTypes.shape({
    id: PropTypes.string.isRequired,
    label: PropTypes.string.isRequired,
    icon: PropTypes.node,
  })).isRequired,
  activeTab: PropTypes.string.isRequired,
  onTabChange: PropTypes.func.isRequired,
  className: PropTypes.string,
};

/**
 * SearchInput Component
 * 
 * Search input with debounce support.
 */
export function SearchInput({ 
  value, 
  onChange, 
  placeholder = 'Search...', 
  debounce = 300,
  className = '' 
}) {
  const [localValue, setLocalValue] = React.useState(value);
  const timeoutRef = React.useRef(null);

  React.useEffect(() => {
    setLocalValue(value);
  }, [value]);

  const handleChange = (e) => {
    const newValue = e.target.value;
    setLocalValue(newValue);

    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }

    timeoutRef.current = setTimeout(() => {
      onChange(newValue);
    }, debounce);
  };

  return (
    <div className={`admin-search ${className}`}>
      <span className="admin-search__icon"></span>
      <input
        type="text"
        className="admin-search__input"
        placeholder={placeholder}
        value={localValue}
        onChange={handleChange}
      />
      {localValue && (
        <button
          className="admin-search__clear"
          onClick={() => { setLocalValue(''); onChange(''); }}
          aria-label="Clear search"
        >
          ✕
        </button>
      )}
    </div>
  );
}

SearchInput.propTypes = {
  value: PropTypes.string.isRequired,
  onChange: PropTypes.func.isRequired,
  placeholder: PropTypes.string,
  debounce: PropTypes.number,
  className: PropTypes.string,
};

/**
 * ConfirmModal Component
 * 
 * Confirmation dialog for destructive actions.
 */
export function ConfirmModal({
  isOpen,
  title,
  message,
  confirmLabel = 'Confirm',
  cancelLabel = 'Cancel',
  variant = 'danger',
  onConfirm,
  onCancel,
}) {
  if (!isOpen) return null;

  return (
    <div className="admin-modal__overlay" onClick={onCancel}>
      <div className="admin-modal" onClick={(e) => e.stopPropagation()}>
        <h3 className="admin-modal__title">{title}</h3>
        <p className="admin-modal__message">{message}</p>
        <div className="admin-modal__actions">
          <button
            className="admin-modal__btn admin-modal__btn--cancel"
            onClick={onCancel}
          >
            {cancelLabel}
          </button>
          <button
            className={`admin-modal__btn admin-modal__btn--${variant}`}
            onClick={onConfirm}
          >
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}

ConfirmModal.propTypes = {
  isOpen: PropTypes.bool.isRequired,
  title: PropTypes.string.isRequired,
  message: PropTypes.string.isRequired,
  confirmLabel: PropTypes.string,
  cancelLabel: PropTypes.string,
  variant: PropTypes.oneOf(['danger', 'warning', 'info']),
  onConfirm: PropTypes.func.isRequired,
  onCancel: PropTypes.func.isRequired,
};

/**
 * Alert Component
 * 
 * Displays alert/notification messages.
 */
export function Alert({ type = 'info', message, onClose, className = '' }) {
  return (
    <div className={`admin-alert admin-alert--${type} ${className}`}>
      <span className="admin-alert__message">{message}</span>
      {onClose && (
        <button className="admin-alert__close" onClick={onClose} aria-label="Close">
          ✕
        </button>
      )}
    </div>
  );
}

Alert.propTypes = {
  type: PropTypes.oneOf(['info', 'success', 'warning', 'error']),
  message: PropTypes.string.isRequired,
  onClose: PropTypes.func,
  className: PropTypes.string,
};

/**
 * DateRangePicker Component
 * 
 * Simple date range selection.
 */
export function DateRangePicker({ 
  startDate, 
  endDate, 
  onStartDateChange, 
  onEndDateChange,
  className = '' 
}) {
  return (
    <div className={`admin-date-range ${className}`}>
      <div className="admin-date-range__field">
        <label htmlFor="date-range-start" className="admin-date-range__label">From</label>
        <input
          id="date-range-start"
          type="date"
          className="admin-date-range__input"
          value={startDate || ''}
          onChange={(e) => onStartDateChange(e.target.value)}
        />
      </div>
      <div className="admin-date-range__field">
        <label htmlFor="date-range-end" className="admin-date-range__label">To</label>
        <input
          id="date-range-end"
          type="date"
          className="admin-date-range__input"
          value={endDate || ''}
          onChange={(e) => onEndDateChange(e.target.value)}
        />
      </div>
    </div>
  );
}

DateRangePicker.propTypes = {
  startDate: PropTypes.string,
  endDate: PropTypes.string,
  onStartDateChange: PropTypes.func.isRequired,
  onEndDateChange: PropTypes.func.isRequired,
  className: PropTypes.string,
};

/**
 * PeriodSelector Component
 * 
 * Dropdown for selecting time periods.
 */
export function PeriodSelector({ value, onChange, className = '' }) {
  const periods = [
    { value: 'day', label: 'Today' },
    { value: 'week', label: 'This Week' },
    { value: 'month', label: 'This Month' },
    { value: 'year', label: 'This Year' },
    { value: 'all_time', label: 'All Time' },
  ];

  return (
    <select
      className={`admin-select ${className}`}
      value={value}
      onChange={(e) => onChange(e.target.value)}
    >
      {periods.map((p) => (
        <option key={p.value} value={p.value}>
          {p.label}
        </option>
      ))}
    </select>
  );
}

PeriodSelector.propTypes = {
  value: PropTypes.string.isRequired,
  onChange: PropTypes.func.isRequired,
  className: PropTypes.string,
};

/**
 * LoadingSpinner Component
 */
export function LoadingSpinner({ size = 'medium', className = '' }) {
  return (
    <div className={`admin-spinner admin-spinner--${size} ${className}`}>
      <div className="admin-spinner__circle" />
    </div>
  );
}

LoadingSpinner.propTypes = {
  size: PropTypes.oneOf(['small', 'medium', 'large']),
  className: PropTypes.string,
};

/**
 * ErrorMessage Component
 */
export function ErrorMessage({ message, onRetry, className = '' }) {
  return (
    <div className={`admin-error ${className}`}>
      <span className="admin-error__icon">⚠️</span>
      <p className="admin-error__message">{message}</p>
      {onRetry && (
        <button className="admin-error__retry" onClick={onRetry}>
          Retry
        </button>
      )}
    </div>
  );
}

ErrorMessage.propTypes = {
  message: PropTypes.string.isRequired,
  onRetry: PropTypes.func,
  className: PropTypes.string,
};
