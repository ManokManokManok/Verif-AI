/**
 * Admin Components - Modular Architecture
 * 
 * Organized by concern for better maintainability:
 * - layout: Sidebar navigation
 * - ui: Display components (cards, badges, spinners)
 * - data: Data visualization (tables, gauges)
 * - forms: Input components (search, date pickers)
 * - feedback: Modals and alerts
 */

// Import theme
import './shared/theme.css';

// Layout components
export { default as AdminSidebar } from './layout/AdminSidebar/AdminSidebar';

// UI components
export { default as StatCard } from './ui/StatCard/StatCard';
export { default as StatusBadge } from './ui/StatusBadge/StatusBadge';
export { default as LoadingSpinner } from './ui/LoadingSpinner/LoadingSpinner';
export { default as ErrorMessage } from './ui/ErrorMessage/ErrorMessage';

// Data components
export { default as DataTable } from './data/DataTable/DataTable';
export { default as MetricGauge } from './data/MetricGauge/MetricGauge';

// Form components
export { default as SearchInput } from './forms/SearchInput/SearchInput';
export { default as DateRangePicker } from './forms/DateRangePicker/DateRangePicker';
export { default as PeriodSelector } from './forms/PeriodSelector/PeriodSelector';

// Feedback components
export { default as Alert } from './feedback/Alert/Alert';
export { default as ConfirmModal } from './feedback/ConfirmModal/ConfirmModal';

// Legacy exports from old AdminComponents.jsx (for backward compatibility)
// Keep these until all pages are updated to use new imports
export {
  StatCard as StatCard_Legacy,
  MetricGauge as MetricGauge_Legacy,
  DataTable as DataTable_Legacy,
  StatusBadge as StatusBadge_Legacy,
  TabNavigation,
  SearchInput as SearchInput_Legacy,
  ConfirmModal as ConfirmModal_Legacy,
  Alert as Alert_Legacy,
  DateRangePicker as DateRangePicker_Legacy,
  PeriodSelector as PeriodSelector_Legacy,
  LoadingSpinner as LoadingSpinner_Legacy,
  ErrorMessage as ErrorMessage_Legacy,
} from './AdminComponents';

