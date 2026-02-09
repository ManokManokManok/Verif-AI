/**
 * Admin Components Tests
 * 
 * Unit tests for reusable admin UI components.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import {
  StatCard,
  MetricGauge,
  DataTable,
  StatusBadge,
  TabNavigation,
  SearchInput,
  ConfirmModal,
  Alert,
  DateRangePicker,
  PeriodSelector,
  LoadingSpinner,
  ErrorMessage,
} from '../src/components/admin';

describe('StatCard', () => {
  it('renders title and value', () => {
    render(<StatCard title="Total Users" value={1234} />);
    
    expect(screen.getByText('Total Users')).toBeInTheDocument();
    expect(screen.getByText('1234')).toBeInTheDocument();
  });

  it('renders subtitle when provided', () => {
    render(<StatCard title="Total Users" value={1234} subtitle="Active accounts" />);
    
    expect(screen.getByText('Active accounts')).toBeInTheDocument();
  });

  it('renders trend indicator when provided', () => {
    render(
      <StatCard 
        title="Revenue" 
        value="$5000" 
        trend="up" 
        trendValue="+15%" 
      />
    );
    
    expect(screen.getByText('+15%')).toBeInTheDocument();
    expect(screen.getByText('↑')).toBeInTheDocument();
  });

  it('shows loading skeleton when loading', () => {
    const { container } = render(
      <StatCard title="Test" value={0} loading />
    );
    
    expect(container.querySelector('.admin-stat-card--loading')).toBeInTheDocument();
    expect(container.querySelector('.admin-stat-card__skeleton')).toBeInTheDocument();
  });

  it('applies variant class correctly', () => {
    const { container } = render(
      <StatCard title="Errors" value={50} variant="danger" />
    );
    
    expect(container.querySelector('.admin-stat-card--danger')).toBeInTheDocument();
  });

  it('renders icon when provided', () => {
    render(<StatCard title="Test" value={100} icon="📊" />);
    
    expect(screen.getByText('📊')).toBeInTheDocument();
  });
});

describe('MetricGauge', () => {
  it('renders label and value', () => {
    render(<MetricGauge label="CPU Usage" value={75} />);
    
    expect(screen.getByText('CPU Usage')).toBeInTheDocument();
    expect(screen.getByText('75%')).toBeInTheDocument();
  });

  it('applies warning threshold class', () => {
    const { container } = render(
      <MetricGauge 
        label="Memory" 
        value={80} 
        thresholds={{ warning: 70, danger: 90 }} 
      />
    );
    
    expect(container.querySelector('.admin-gauge--warning')).toBeInTheDocument();
  });

  it('applies danger threshold class', () => {
    const { container } = render(
      <MetricGauge 
        label="Disk" 
        value={95} 
        thresholds={{ warning: 70, danger: 90 }} 
      />
    );
    
    expect(container.querySelector('.admin-gauge--danger')).toBeInTheDocument();
  });

  it('renders custom unit', () => {
    render(<MetricGauge label="Temperature" value={45} unit="°C" />);
    
    expect(screen.getByText('45°C')).toBeInTheDocument();
  });

  it('applies size class correctly', () => {
    const { container } = render(
      <MetricGauge label="Test" value={50} size="large" />
    );
    
    expect(container.querySelector('.admin-gauge--large')).toBeInTheDocument();
  });
});

describe('DataTable', () => {
  const columns = [
    { key: 'name', label: 'Name' },
    { key: 'email', label: 'Email' },
    { key: 'status', label: 'Status' },
  ];

  const data = [
    { id: '1', name: 'John Doe', email: 'john@example.com', status: 'active' },
    { id: '2', name: 'Jane Smith', email: 'jane@example.com', status: 'inactive' },
  ];

  it('renders table headers', () => {
    render(<DataTable columns={columns} data={data} />);
    
    expect(screen.getByText('Name')).toBeInTheDocument();
    expect(screen.getByText('Email')).toBeInTheDocument();
    expect(screen.getByText('Status')).toBeInTheDocument();
  });

  it('renders data rows', () => {
    render(<DataTable columns={columns} data={data} />);
    
    expect(screen.getByText('John Doe')).toBeInTheDocument();
    expect(screen.getByText('john@example.com')).toBeInTheDocument();
    expect(screen.getByText('Jane Smith')).toBeInTheDocument();
  });

  it('shows empty message when no data', () => {
    render(
      <DataTable 
        columns={columns} 
        data={[]} 
        emptyMessage="No users found" 
      />
    );
    
    expect(screen.getByText('No users found')).toBeInTheDocument();
  });

  it('shows loading skeleton when loading', () => {
    const { container } = render(
      <DataTable columns={columns} data={[]} loading />
    );
    
    expect(container.querySelector('.admin-table--loading')).toBeInTheDocument();
  });

  it('renders custom cell content via render function', () => {
    const customColumns = [
      { key: 'name', label: 'Name' },
      { 
        key: 'status', 
        label: 'Status',
        render: (value) => <span data-testid="custom-status">{value.toUpperCase()}</span>
      },
    ];

    render(<DataTable columns={customColumns} data={data} />);
    
    const statusCells = screen.getAllByTestId('custom-status');
    expect(statusCells[0]).toHaveTextContent('ACTIVE');
    expect(statusCells[1]).toHaveTextContent('INACTIVE');
  });

  it('renders pagination controls', () => {
    const pagination = { page: 1, limit: 10, total: 25, totalPages: 3 };
    const onPageChange = vi.fn();

    render(
      <DataTable 
        columns={columns} 
        data={data} 
        pagination={pagination}
        onPageChange={onPageChange}
      />
    );
    
    expect(screen.getByText(/Page 1 of 3/)).toBeInTheDocument();
    expect(screen.getByText('Previous')).toBeInTheDocument();
    expect(screen.getByText('Next')).toBeInTheDocument();
  });

  it('calls onPageChange when clicking next', async () => {
    const pagination = { page: 1, limit: 10, total: 25, totalPages: 3 };
    const onPageChange = vi.fn();

    render(
      <DataTable 
        columns={columns} 
        data={data} 
        pagination={pagination}
        onPageChange={onPageChange}
      />
    );
    
    await userEvent.click(screen.getByText('Next'));
    expect(onPageChange).toHaveBeenCalledWith(2);
  });
});

describe('StatusBadge', () => {
  it('renders status label', () => {
    render(<StatusBadge status="active" />);
    
    expect(screen.getByText('Active')).toBeInTheDocument();
  });

  it('applies correct variant class for known status', () => {
    const { container } = render(<StatusBadge status="resolved" />);
    
    expect(container.querySelector('.admin-badge--success')).toBeInTheDocument();
  });

  it('uses custom variant when provided', () => {
    const { container } = render(
      <StatusBadge status="custom" variant="warning" />
    );
    
    expect(container.querySelector('.admin-badge--warning')).toBeInTheDocument();
  });
});

describe('TabNavigation', () => {
  const tabs = [
    { id: 'tab1', label: 'Tab 1' },
    { id: 'tab2', label: 'Tab 2' },
    { id: 'tab3', label: 'Tab 3', icon: '⚙️' },
  ];

  it('renders all tabs', () => {
    render(
      <TabNavigation 
        tabs={tabs} 
        activeTab="tab1" 
        onTabChange={() => {}} 
      />
    );
    
    expect(screen.getByText('Tab 1')).toBeInTheDocument();
    expect(screen.getByText('Tab 2')).toBeInTheDocument();
    expect(screen.getByText('Tab 3')).toBeInTheDocument();
  });

  it('marks active tab correctly', () => {
    const { container } = render(
      <TabNavigation 
        tabs={tabs} 
        activeTab="tab2" 
        onTabChange={() => {}} 
      />
    );
    
    const activeButton = container.querySelector('.admin-tabs__button--active');
    expect(activeButton).toHaveTextContent('Tab 2');
  });

  it('calls onTabChange when clicking tab', async () => {
    const onTabChange = vi.fn();

    render(
      <TabNavigation 
        tabs={tabs} 
        activeTab="tab1" 
        onTabChange={onTabChange} 
      />
    );
    
    await userEvent.click(screen.getByText('Tab 2'));
    expect(onTabChange).toHaveBeenCalledWith('tab2');
  });

  it('renders tab icon when provided', () => {
    render(
      <TabNavigation 
        tabs={tabs} 
        activeTab="tab1" 
        onTabChange={() => {}} 
      />
    );
    
    expect(screen.getByText('⚙️')).toBeInTheDocument();
  });
});

describe('SearchInput', () => {
  it('renders with placeholder', () => {
    render(
      <SearchInput 
        value="" 
        onChange={() => {}} 
        placeholder="Search users..." 
      />
    );
    
    expect(screen.getByPlaceholderText('Search users...')).toBeInTheDocument();
  });

  it('shows current value', () => {
    render(
      <SearchInput 
        value="test query" 
        onChange={() => {}} 
      />
    );
    
    expect(screen.getByDisplayValue('test query')).toBeInTheDocument();
  });

  it('calls onChange after debounce', async () => {
    vi.useFakeTimers();
    const onChange = vi.fn();

    render(
      <SearchInput 
        value="" 
        onChange={onChange} 
        debounce={300}
      />
    );
    
    const input = screen.getByRole('textbox');
    
    // Type without delay to avoid timer issues
    await act(async () => {
      fireEvent.change(input, { target: { value: 'hello' } });
    });
    
    // Should not be called immediately
    expect(onChange).not.toHaveBeenCalled();
    
    // Fast forward past debounce and wrap in act
    await act(async () => {
      vi.advanceTimersByTime(300);
    });
    
    expect(onChange).toHaveBeenCalledWith('hello');
    vi.useRealTimers();
  });

  it('shows clear button when value exists', () => {
    render(
      <SearchInput 
        value="test" 
        onChange={() => {}} 
      />
    );
    
    expect(screen.getByRole('button', { name: /clear/i })).toBeInTheDocument();
  });

  it('clears value when clicking clear button', async () => {
    const onChange = vi.fn();

    render(
      <SearchInput 
        value="test" 
        onChange={onChange} 
      />
    );
    
    await userEvent.click(screen.getByRole('button', { name: /clear/i }));
    expect(onChange).toHaveBeenCalledWith('');
  });
});

describe('ConfirmModal', () => {
  it('does not render when closed', () => {
    render(
      <ConfirmModal
        isOpen={false}
        title="Confirm"
        message="Are you sure?"
        onConfirm={() => {}}
        onCancel={() => {}}
      />
    );
    
    expect(screen.queryByText('Confirm')).not.toBeInTheDocument();
  });

  it('renders title and message when open', () => {
    render(
      <ConfirmModal
        isOpen={true}
        title="Delete User"
        message="Are you sure you want to delete this user?"
        onConfirm={() => {}}
        onCancel={() => {}}
      />
    );
    
    expect(screen.getByText('Delete User')).toBeInTheDocument();
    expect(screen.getByText('Are you sure you want to delete this user?')).toBeInTheDocument();
  });

  it('calls onConfirm when clicking confirm button', async () => {
    const onConfirm = vi.fn();

    render(
      <ConfirmModal
        isOpen={true}
        title="Test"
        message="Test message"
        confirmLabel="Yes, Delete"
        onConfirm={onConfirm}
        onCancel={() => {}}
      />
    );
    
    await userEvent.click(screen.getByText('Yes, Delete'));
    expect(onConfirm).toHaveBeenCalled();
  });

  it('calls onCancel when clicking cancel button', async () => {
    const onCancel = vi.fn();

    render(
      <ConfirmModal
        isOpen={true}
        title="Test"
        message="Test message"
        cancelLabel="No"
        onConfirm={() => {}}
        onCancel={onCancel}
      />
    );
    
    await userEvent.click(screen.getByText('No'));
    expect(onCancel).toHaveBeenCalled();
  });

  it('calls onCancel when clicking overlay', async () => {
    const onCancel = vi.fn();

    const { container } = render(
      <ConfirmModal
        isOpen={true}
        title="Test"
        message="Test message"
        onConfirm={() => {}}
        onCancel={onCancel}
      />
    );
    
    await userEvent.click(container.querySelector('.admin-modal__overlay'));
    expect(onCancel).toHaveBeenCalled();
  });
});

describe('Alert', () => {
  it('renders message', () => {
    render(<Alert message="Operation successful" type="success" />);
    
    expect(screen.getByText('Operation successful')).toBeInTheDocument();
  });

  it('applies type class', () => {
    const { container } = render(
      <Alert message="Error occurred" type="error" />
    );
    
    expect(container.querySelector('.admin-alert--error')).toBeInTheDocument();
  });

  it('shows close button when onClose provided', () => {
    render(
      <Alert 
        message="Test" 
        type="info" 
        onClose={() => {}} 
      />
    );
    
    expect(screen.getByRole('button', { name: /close/i })).toBeInTheDocument();
  });

  it('calls onClose when clicking close button', async () => {
    const onClose = vi.fn();

    render(
      <Alert 
        message="Test" 
        type="info" 
        onClose={onClose} 
      />
    );
    
    await userEvent.click(screen.getByRole('button', { name: /close/i }));
    expect(onClose).toHaveBeenCalled();
  });
});

describe('DateRangePicker', () => {
  it('renders start and end date inputs', () => {
    render(
      <DateRangePicker
        startDate=""
        endDate=""
        onStartDateChange={() => {}}
        onEndDateChange={() => {}}
      />
    );
    
    expect(screen.getByLabelText('From')).toBeInTheDocument();
    expect(screen.getByLabelText('To')).toBeInTheDocument();
  });

  it('calls onStartDateChange when start date changes', async () => {
    const onStartDateChange = vi.fn();

    render(
      <DateRangePicker
        startDate=""
        endDate=""
        onStartDateChange={onStartDateChange}
        onEndDateChange={() => {}}
      />
    );
    
    fireEvent.change(screen.getByLabelText('From'), { 
      target: { value: '2024-01-01' } 
    });
    
    expect(onStartDateChange).toHaveBeenCalledWith('2024-01-01');
  });
});

describe('PeriodSelector', () => {
  it('renders all period options', () => {
    render(
      <PeriodSelector value="month" onChange={() => {}} />
    );
    
    expect(screen.getByText('Today')).toBeInTheDocument();
    expect(screen.getByText('This Week')).toBeInTheDocument();
    expect(screen.getByText('This Month')).toBeInTheDocument();
    expect(screen.getByText('This Year')).toBeInTheDocument();
    expect(screen.getByText('All Time')).toBeInTheDocument();
  });

  it('calls onChange when selection changes', async () => {
    const onChange = vi.fn();

    render(
      <PeriodSelector value="month" onChange={onChange} />
    );
    
    fireEvent.change(screen.getByRole('combobox'), { 
      target: { value: 'week' } 
    });
    
    expect(onChange).toHaveBeenCalledWith('week');
  });
});

describe('LoadingSpinner', () => {
  it('renders with default size', () => {
    const { container } = render(<LoadingSpinner />);
    
    expect(container.querySelector('.admin-spinner--medium')).toBeInTheDocument();
  });

  it('renders with custom size', () => {
    const { container } = render(<LoadingSpinner size="large" />);
    
    expect(container.querySelector('.admin-spinner--large')).toBeInTheDocument();
  });
});

describe('ErrorMessage', () => {
  it('renders error message', () => {
    render(<ErrorMessage message="Something went wrong" />);
    
    expect(screen.getByText('Something went wrong')).toBeInTheDocument();
  });

  it('shows retry button when onRetry provided', () => {
    render(
      <ErrorMessage 
        message="Failed to load" 
        onRetry={() => {}} 
      />
    );
    
    expect(screen.getByText('Retry')).toBeInTheDocument();
  });

  it('calls onRetry when clicking retry button', async () => {
    const onRetry = vi.fn();

    render(
      <ErrorMessage 
        message="Failed to load" 
        onRetry={onRetry} 
      />
    );
    
    await userEvent.click(screen.getByText('Retry'));
    expect(onRetry).toHaveBeenCalled();
  });
});
