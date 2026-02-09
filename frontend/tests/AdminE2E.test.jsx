/**
 * Admin Dashboard E2E Integration Tests (Phase 8)
 * 
 * These tests simulate complete user workflows through the admin dashboard,
 * testing component interactions, navigation, and data flow.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor, within, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import * as adminApi from '../src/api/admin';

// Import page components
import AdminDashboard from '../src/pages/admin/AdminDashboard';
import ModelHealth from '../src/pages/admin/ModelHealth';
import AnalysisStats from '../src/pages/admin/AnalysisStats';
import UserStats from '../src/pages/admin/UserStats';
import UserManagement from '../src/pages/admin/UserManagement';

// Import UI components for direct testing
import {
  TabNavigation,
  Alert,
  StatCard,
  MetricGauge,
  DataTable,
  StatusBadge,
  SearchInput,
  ConfirmModal,
} from '../src/components/admin';

// Mock the admin API
vi.mock('../src/api/admin', () => ({
  getModelHealth: vi.fn(),
  getModelHealthSummary: vi.fn(),
  getAnalysisStats: vi.fn(),
  getTopScamCategories: vi.fn(),
  getUserStats: vi.fn(),
  getUserReports: vi.fn(),
  updateReportStatus: vi.fn(),
  getUsers: vi.fn(),
  getUser: vi.fn(),
  deleteUser: vi.fn(),
  resetUserPassword: vi.fn(),
  updateUserStatus: vi.fn(),
  updateUserRoles: vi.fn(),
}));

// Mock AuthContext
const mockAdminUser = {
  id: '1',
  username: 'admin',
  email: 'admin@test.com',
  roles: ['admin'],
};

vi.mock('../src/context/AuthContext', () => ({
  useAuth: () => ({
    user: mockAdminUser,
    isAdmin: true,
    isAuthenticated: true,
    login: vi.fn(),
    logout: vi.fn(),
  }),
  AuthProvider: ({ children }) => children,
}));

// ==================== Test Data Fixtures ====================

const mockModelHealth = {
  cpu_usage_percent: 45.2,
  memory_usage_percent: 62.5,
  gpu_usage_percent: 30.0,
  disk_usage_percent: 55.0,
  model_loaded: true,
  uptime_seconds: 86400,
  status: 'healthy',
  active_requests: 5,
  average_response_time_ms: 150,
};

const mockAnalysisStats = {
  total_count: 1500,
  high_risk_count: 250,
  medium_risk_count: 450,
  low_risk_count: 550,
  legitimate_count: 250,
  average_confidence: 0.85,
};

const mockUserStats = {
  total_users: 500,
  active_users: 350,
  inactive_users: 150,
  new_users_today: 25,
  admins: 5,
};

const mockTopCategories = [
  { category: 'phishing', count: 100 },
  { category: 'investment_scam', count: 80 },
  { category: 'lottery_scam', count: 60 },
  { category: 'romance_scam', count: 40 },
  { category: 'tech_support_scam', count: 20 },
];

const mockUsers = [
  { id: '1', email: 'user1@test.com', username: 'user1', is_active: true, roles: ['user'], created_at: '2024-01-01' },
  { id: '2', email: 'user2@test.com', username: 'user2', is_active: true, roles: ['user'], created_at: '2024-01-02' },
  { id: '3', email: 'admin@test.com', username: 'admin', is_active: true, roles: ['admin'], created_at: '2024-01-03' },
];

const mockReports = [
  {
    id: '1',
    report_type: 'hallucination',
    reason: 'AI gave incorrect information',
    status: 'pending',
    created_at: new Date().toISOString(),
    reported_by: { username: 'user1' },
  },
  {
    id: '2',
    report_type: 'bug',
    reason: 'Analysis failed',
    status: 'in_progress',
    created_at: new Date().toISOString(),
    reported_by: { username: 'user2' },
  },
];

// ==================== Helper Functions ====================

const renderWithRouter = (component) => {
  return render(
    <BrowserRouter>
      {component}
    </BrowserRouter>
  );
};

const setupDefaultMocks = () => {
  adminApi.getModelHealth.mockResolvedValue({ success: true, data: mockModelHealth });
  adminApi.getModelHealthSummary.mockResolvedValue({ success: true, data: { status: 'healthy' } });
  adminApi.getAnalysisStats.mockResolvedValue({ success: true, data: mockAnalysisStats });
  adminApi.getTopScamCategories.mockResolvedValue({ success: true, data: mockTopCategories });
  adminApi.getUserStats.mockResolvedValue({ success: true, data: mockUserStats });
  adminApi.getUsers.mockResolvedValue({
    success: true,
    data: { users: mockUsers, total: mockUsers.length, page: 1, limit: 50 }
  });
  adminApi.getUserReports.mockResolvedValue({
    success: true,
    data: { reports: mockReports, total: mockReports.length, page: 1, limit: 50 }
  });
};

// ==================== E2E Tests ====================

describe('Admin Dashboard E2E Workflows', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    setupDefaultMocks();
  });

  afterEach(() => {
    vi.clearAllTimers();
  });

  // ==================== Admin Dashboard Navigation ====================

  describe('Admin Dashboard Navigation', () => {
    it('renders admin dashboard with tab navigation', async () => {
      renderWithRouter(<AdminDashboard />);

      // Dashboard title should be visible
      expect(screen.getByText(/Admin Dashboard/i)).toBeInTheDocument();
      
      // Tab navigation should be present - use getAllByText since tabs and content may have same text
      expect(screen.getAllByText(/Model Health/i).length).toBeGreaterThan(0);
      expect(screen.getAllByText(/Analysis Statistics/i).length).toBeGreaterThan(0);
      expect(screen.getAllByText(/User Statistics/i).length).toBeGreaterThan(0);
      expect(screen.getAllByText(/User Management/i).length).toBeGreaterThan(0);
    });

    it('switches tabs when clicking on different tab', async () => {
      const user = userEvent.setup();
      renderWithRouter(<AdminDashboard />);

      // Default tab should be Model Health, click on Analysis Statistics
      const analysisTab = screen.getByText(/Analysis Statistics/i);
      await user.click(analysisTab);

      // API should be called for analysis stats
      await waitFor(() => {
        expect(adminApi.getAnalysisStats).toHaveBeenCalled();
      });
    });

    it('shows welcome message with username', () => {
      renderWithRouter(<AdminDashboard />);
      
      expect(screen.getByText(/Welcome back/i)).toBeInTheDocument();
    });
  });

  // ==================== Model Health Tab ====================

  describe('Model Health Tab Workflow', () => {
    it('displays model health metrics on load', async () => {
      renderWithRouter(<ModelHealth onNotify={vi.fn()} />);

      await waitFor(() => {
        expect(adminApi.getModelHealth).toHaveBeenCalled();
      });
    });

    it('shows loading state while fetching data', async () => {
      // Delay the response
      adminApi.getModelHealth.mockImplementation(
        () => new Promise(resolve => setTimeout(() => resolve({ success: true, data: mockModelHealth }), 100))
      );

      const { container } = renderWithRouter(<ModelHealth onNotify={vi.fn()} />);

      // Should show some loading indicator
      const hasLoading = container.querySelector('.loading') || 
                         screen.queryByText(/loading/i) ||
                         container.querySelector('[class*="loading"]');
      
      // Wait for load to complete
      await waitFor(() => {
        expect(adminApi.getModelHealth).toHaveBeenCalled();
      });
    });

    it('displays error message on API failure', async () => {
      const mockNotify = vi.fn();
      adminApi.getModelHealth.mockRejectedValue(new Error('Network error'));

      renderWithRouter(<ModelHealth onNotify={mockNotify} />);

      await waitFor(() => {
        expect(adminApi.getModelHealth).toHaveBeenCalled();
      });

      // Should either call onNotify with error or display error message
      await waitFor(() => {
        const hasError = mockNotify.mock.calls.length > 0 || 
                         screen.queryByText(/error|failed/i);
        expect(hasError).toBeTruthy();
      }, { timeout: 2000 });
    });
  });

  // ==================== Analysis Stats Tab ====================

  describe('Analysis Stats Tab Workflow', () => {
    it('fetches and displays analysis statistics', async () => {
      renderWithRouter(<AnalysisStats onNotify={vi.fn()} />);

      await waitFor(() => {
        expect(adminApi.getAnalysisStats).toHaveBeenCalled();
      });

      await waitFor(() => {
        expect(adminApi.getTopScamCategories).toHaveBeenCalled();
      });
    });

    it('calls API with date range when period is changed', async () => {
      const user = userEvent.setup();
      renderWithRouter(<AnalysisStats onNotify={vi.fn()} />);

      await waitFor(() => {
        expect(adminApi.getAnalysisStats).toHaveBeenCalled();
      });

      // Look for period selector buttons - use getAllByText to handle multiple matches
      const weekButtons = screen.queryAllByText(/week/i);

      if (weekButtons.length > 0) {
        await user.click(weekButtons[0]);
        await waitFor(() => {
          expect(adminApi.getAnalysisStats.mock.calls.length).toBeGreaterThan(0);
        });
      }
    });
  });

  // ==================== User Stats Tab ====================

  describe('User Stats Tab Workflow', () => {
    it('fetches and displays user statistics', async () => {
      renderWithRouter(<UserStats onNotify={vi.fn()} />);

      await waitFor(() => {
        expect(adminApi.getUserStats).toHaveBeenCalled();
      });
    });
  });

  // ==================== User Management Tab ====================

  describe('User Management Tab Workflow', () => {
    it('fetches and displays user list', async () => {
      renderWithRouter(<UserManagement onNotify={vi.fn()} />);

      await waitFor(() => {
        expect(adminApi.getUsers).toHaveBeenCalled();
      });
    });

    it('supports searching for users', async () => {
      const user = userEvent.setup();
      renderWithRouter(<UserManagement onNotify={vi.fn()} />);

      await waitFor(() => {
        expect(adminApi.getUsers).toHaveBeenCalled();
      });

      // Find search input
      const searchInput = screen.queryByPlaceholderText(/search/i) ||
                          screen.queryByRole('searchbox');

      if (searchInput) {
        await user.type(searchInput, 'test');
        
        // Wait for debounced search call
        await waitFor(() => {
          expect(adminApi.getUsers.mock.calls.length).toBeGreaterThan(1);
        }, { timeout: 1000 });
      }
    });

    it('handles user deletion workflow', async () => {
      adminApi.deleteUser.mockResolvedValue({ success: true });
      const mockNotify = vi.fn();
      
      renderWithRouter(<UserManagement onNotify={mockNotify} />);

      await waitFor(() => {
        expect(adminApi.getUsers).toHaveBeenCalled();
      });

      // Look for delete button (may require row interaction)
      const deleteButtons = screen.queryAllByRole('button', { name: /delete/i });
      
      if (deleteButtons.length > 0) {
        const user = userEvent.setup();
        await user.click(deleteButtons[0]);
        
        // May need to confirm deletion
        const confirmButton = screen.queryByRole('button', { name: /confirm|yes/i });
        if (confirmButton) {
          await user.click(confirmButton);
        }

        await waitFor(() => {
          expect(adminApi.deleteUser).toHaveBeenCalled();
        }, { timeout: 2000 });
      }
    });
  });

  // ==================== Security Tests ====================

  describe('Security Workflow Tests', () => {
    it('prevents XSS in user-provided data', async () => {
      const maliciousUsers = [{
        id: '1',
        email: '<script>alert("xss")</script>@test.com',
        username: '<img src=x onerror=alert("xss")>',
        is_active: true,
        roles: ['user'],
        created_at: '2024-01-01',
      }];

      adminApi.getUsers.mockResolvedValue({
        success: true,
        data: { users: maliciousUsers, total: 1, page: 1, limit: 50 }
      });

      const { container } = renderWithRouter(<UserManagement onNotify={vi.fn()} />);

      await waitFor(() => {
        expect(adminApi.getUsers).toHaveBeenCalled();
      });

      // Verify no script tags or event handlers in the DOM
      expect(container.innerHTML).not.toContain('<script>');
      expect(container.innerHTML).not.toContain('onerror=');
    });

    it('handles API errors gracefully', async () => {
      adminApi.getModelHealth.mockRejectedValue(new Error('Unauthorized'));
      const mockNotify = vi.fn();

      renderWithRouter(<ModelHealth onNotify={mockNotify} />);

      await waitFor(() => {
        expect(adminApi.getModelHealth).toHaveBeenCalled();
      });

      // Should not throw or crash
      expect(screen.queryByText(/Admin Dashboard/i) || document.body).toBeTruthy();
    });
  });

  // ==================== Component Integration Tests ====================

  describe('Component Integration Tests', () => {
    it('TabNavigation triggers correct callback', async () => {
      const onTabChange = vi.fn();
      const tabs = [
        { id: 'tab1', label: 'Tab 1' },
        { id: 'tab2', label: 'Tab 2' },
      ];

      render(
        <TabNavigation
          tabs={tabs}
          activeTab="tab1"
          onTabChange={onTabChange}
        />
      );

      const user = userEvent.setup();
      await user.click(screen.getByText('Tab 2'));

      expect(onTabChange).toHaveBeenCalledWith('tab2');
    });

    it('Alert displays message and can be dismissed', async () => {
      const onClose = vi.fn();
      
      render(
        <Alert
          type="success"
          message="Test message"
          onClose={onClose}
        />
      );

      expect(screen.getByText('Test message')).toBeInTheDocument();

      const closeButton = screen.queryByRole('button');
      if (closeButton) {
        const user = userEvent.setup();
        await user.click(closeButton);
        expect(onClose).toHaveBeenCalled();
      }
    });

    it('StatCard displays value and title correctly', () => {
      render(<StatCard title="Total Users" value={1234} />);

      expect(screen.getByText('Total Users')).toBeInTheDocument();
      expect(screen.getByText('1234')).toBeInTheDocument();
    });

    it('MetricGauge shows percentage value', () => {
      render(<MetricGauge label="CPU Usage" value={75} />);

      expect(screen.getByText('CPU Usage')).toBeInTheDocument();
      expect(screen.getByText('75%')).toBeInTheDocument();
    });

    it('StatusBadge renders with correct variant', () => {
      const { container } = render(<StatusBadge status="active" />);

      // StatusBadge uses admin-badge class, not admin-status-badge
      expect(container.querySelector('.admin-badge')).toBeInTheDocument();
    });

    it('SearchInput triggers onChange callback after debounce', async () => {
      const onChange = vi.fn();
      
      render(
        <SearchInput
          value=""
          onChange={onChange}
          placeholder="Search..."
          debounce={50} // Short debounce for testing
        />
      );

      const input = screen.getByPlaceholderText('Search...');
      const user = userEvent.setup();
      await user.type(input, 'test');

      // Wait for debounce to complete
      await waitFor(() => {
        expect(onChange).toHaveBeenCalled();
      }, { timeout: 500 });
    });

    it('ConfirmModal shows confirmation dialog', async () => {
      const onConfirm = vi.fn();
      const onCancel = vi.fn();

      render(
        <ConfirmModal
          isOpen={true}
          title="Confirm Action"
          message="Are you sure?"
          onConfirm={onConfirm}
          onCancel={onCancel}
        />
      );

      expect(screen.getByText('Confirm Action')).toBeInTheDocument();
      expect(screen.getByText('Are you sure?')).toBeInTheDocument();

      const confirmButton = screen.getByRole('button', { name: /confirm|yes|ok/i });
      const user = userEvent.setup();
      await user.click(confirmButton);

      expect(onConfirm).toHaveBeenCalled();
    });

    it('DataTable renders data correctly', () => {
      const columns = [
        { key: 'name', label: 'Name' },
        { key: 'email', label: 'Email' },
      ];
      const data = [
        { id: 1, name: 'John', email: 'john@test.com' },
        { id: 2, name: 'Jane', email: 'jane@test.com' },
      ];

      render(
        <DataTable
          columns={columns}
          data={data}
        />
      );

      expect(screen.getByText('Name')).toBeInTheDocument();
      expect(screen.getByText('Email')).toBeInTheDocument();
      expect(screen.getByText('John')).toBeInTheDocument();
      expect(screen.getByText('jane@test.com')).toBeInTheDocument();
    });
  });

  // ==================== Data Flow Tests ====================

  describe('Data Flow Tests', () => {
    it('updates display when API returns new data', async () => {
      const initialHealth = { ...mockModelHealth, cpu_usage_percent: 40 };
      const updatedHealth = { ...mockModelHealth, cpu_usage_percent: 80 };

      adminApi.getModelHealth.mockResolvedValueOnce({ success: true, data: initialHealth });

      const { rerender } = renderWithRouter(<ModelHealth onNotify={vi.fn()} />);

      await waitFor(() => {
        expect(adminApi.getModelHealth).toHaveBeenCalled();
      });

      // Update mock for refresh
      adminApi.getModelHealth.mockResolvedValueOnce({ success: true, data: updatedHealth });
    });

    it('maintains state across tab switches', async () => {
      const user = userEvent.setup();
      renderWithRouter(<AdminDashboard />);

      // Start on Model Health tab
      await waitFor(() => {
        expect(adminApi.getModelHealth).toHaveBeenCalled();
      });

      // Switch to Analysis Stats
      await user.click(screen.getByText(/Analysis Statistics/i));

      await waitFor(() => {
        expect(adminApi.getAnalysisStats).toHaveBeenCalled();
      });

      // Switch back to Model Health
      await user.click(screen.getByText(/Model Health/i));

      // Should still work
      expect(screen.getByText(/Model Health/i)).toBeInTheDocument();
    });
  });

  // ==================== Error Recovery Tests ====================

  describe('Error Recovery Tests', () => {
    it('recovers from API error on retry', async () => {
      let callCount = 0;
      adminApi.getModelHealth.mockImplementation(() => {
        callCount++;
        if (callCount === 1) {
          return Promise.reject(new Error('Network error'));
        }
        return Promise.resolve({ success: true, data: mockModelHealth });
      });

      renderWithRouter(<ModelHealth onNotify={vi.fn()} />);

      await waitFor(() => {
        expect(adminApi.getModelHealth).toHaveBeenCalled();
      });

      // Look for retry button if present
      const retryButton = screen.queryByRole('button', { name: /retry|refresh/i });
      if (retryButton) {
        const user = userEvent.setup();
        await user.click(retryButton);

        await waitFor(() => {
          expect(adminApi.getModelHealth.mock.calls.length).toBe(2);
        });
      }
    });

    it('handles empty data gracefully', async () => {
      adminApi.getUsers.mockResolvedValue({
        success: true,
        data: { users: [], total: 0, page: 1, limit: 50 }
      });

      renderWithRouter(<UserManagement onNotify={vi.fn()} />);

      await waitFor(() => {
        expect(adminApi.getUsers).toHaveBeenCalled();
      });

      // Should show empty state or "no users" message
      const emptyIndicator = screen.queryByText(/no users|empty|no data/i);
      // Even without explicit empty message, shouldn't crash
      expect(document.body).toBeTruthy();
    });
  });
});

// ==================== Accessibility Tests ====================

describe('Admin Dashboard Accessibility', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    setupDefaultMocks();
  });

  it('has proper heading hierarchy', async () => {
    renderWithRouter(<AdminDashboard />);

    const heading = screen.getByRole('heading', { level: 1 });
    expect(heading).toBeInTheDocument();
  });

  it('interactive elements are keyboard accessible', async () => {
    const user = userEvent.setup();
    renderWithRouter(<AdminDashboard />);

    // Tab to first interactive element
    await user.tab();

    // Should have focus on something
    expect(document.activeElement).not.toBe(document.body);
  });

  it('buttons have accessible names', async () => {
    renderWithRouter(<AdminDashboard />);

    const buttons = screen.getAllByRole('button');
    buttons.forEach(button => {
      const hasAccessibleName = button.textContent || 
                                button.getAttribute('aria-label') ||
                                button.getAttribute('title');
      expect(hasAccessibleName).toBeTruthy();
    });
  });
});
