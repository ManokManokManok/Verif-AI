/**
 * Admin Hooks Tests
 * 
 * Unit tests for admin data fetching hooks.
 * Tests verify hook return structure and basic data flow.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, waitFor, act } from '@testing-library/react';
import {
  useModelHealth,
  useAnalysisStats,
  useUserStats,
  useUserReports,
  useUsers,
  useUserDetails,
} from '../src/hooks/useAdminData';
import * as adminApi from '../src/api/admin';

// Mock the admin API module with proper response structure
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

describe('useModelHealth', () => {
  const mockHealthData = {
    cpu_percent: 45.2,
    memory_percent: 62.5,
    gpu_percent: 30.0,
    disk_percent: 55.0,
    model_loaded: true,
    uptime_seconds: 86400,
  };

  beforeEach(() => {
    vi.clearAllMocks();
    vi.clearAllTimers();
    // Mock with proper response structure
    adminApi.getModelHealth.mockResolvedValue({ success: true, data: mockHealthData });
    adminApi.getModelHealthSummary.mockResolvedValue({ success: true, data: { status: 'healthy' } });
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('fetches model health data on mount', async () => {
    const { result } = renderHook(() => useModelHealth(0)); // 0 disables refresh interval

    // Initially loading
    expect(result.current.loading).toBe(true);
    expect(result.current.data).toBe(null);

    // Wait for data
    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.data).toEqual(mockHealthData);
    expect(result.current.error).toBe(null);
    expect(adminApi.getModelHealth).toHaveBeenCalledTimes(1);
  });

  it('sets error when API call fails', async () => {
    adminApi.getModelHealth.mockRejectedValue(new Error('Network error'));

    const { result } = renderHook(() => useModelHealth(0));

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.error).toBe('Network error');
    expect(result.current.data).toBe(null);
  });

  it('provides refresh function', async () => {
    const { result } = renderHook(() => useModelHealth(0));

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(adminApi.getModelHealth).toHaveBeenCalledTimes(1);

    // Call refresh
    await act(async () => {
      await result.current.refresh();
    });

    expect(adminApi.getModelHealth).toHaveBeenCalledTimes(2);
  });
});

describe('useAnalysisStats', () => {
  const mockStats = {
    total_analyses: 1500,
    scam_detected_count: 250,
    legitimate_count: 1250,
  };

  const mockCategories = [
    { category: 'phishing', count: 100 },
    { category: 'scam', count: 80 },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
    adminApi.getAnalysisStats.mockResolvedValue({ success: true, data: mockStats });
    adminApi.getTopScamCategories.mockResolvedValue({ success: true, data: mockCategories });
  });

  it('fetches analysis stats on mount', async () => {
    const { result } = renderHook(() => useAnalysisStats());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.data).toEqual(mockStats);
    expect(result.current.categories).toEqual(mockCategories);
    expect(adminApi.getAnalysisStats).toHaveBeenCalled();
    expect(adminApi.getTopScamCategories).toHaveBeenCalled();
  });

  it('handles API error', async () => {
    adminApi.getAnalysisStats.mockRejectedValue(new Error('API Error'));

    const { result } = renderHook(() => useAnalysisStats());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.error).toBe('API Error');
  });
});

describe('useUserStats', () => {
  const mockUserStats = {
    total_users: 500,
    active_users: 350,
    new_users: 25,
    verified_users: 400,
  };

  beforeEach(() => {
    vi.clearAllMocks();
    adminApi.getUserStats.mockResolvedValue({ success: true, data: mockUserStats });
  });

  it('fetches user stats on mount', async () => {
    const { result } = renderHook(() => useUserStats());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.data).toEqual(mockUserStats);
    expect(adminApi.getUserStats).toHaveBeenCalled();
  });

  it('handles error correctly', async () => {
    adminApi.getUserStats.mockRejectedValue(new Error('Failed to fetch'));

    const { result } = renderHook(() => useUserStats());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.error).toBe('Failed to fetch');
  });
});

describe('useUserReports', () => {
  const mockReportsData = {
    reports: [
      { report_id: '1', reason: 'Spam', status: 'pending' },
      { report_id: '2', reason: 'Abuse', status: 'pending' },
    ],
    page: 1,
    limit: 50,
    total: 2,
    total_pages: 1,
  };

  beforeEach(() => {
    vi.clearAllMocks();
    adminApi.getUserReports.mockResolvedValue({ success: true, data: mockReportsData });
    adminApi.updateReportStatus.mockResolvedValue({ success: true, data: { report_id: '1', status: 'resolved' } });
  });

  it('fetches reports on mount', async () => {
    const { result } = renderHook(() => useUserReports('pending'));

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.data.reports).toEqual(mockReportsData.reports);
    expect(result.current.pagination.total).toBe(2);
    expect(adminApi.getUserReports).toHaveBeenCalled();
  });

  it('provides updateStatus function', async () => {
    const { result } = renderHook(() => useUserReports('pending'));

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    await act(async () => {
      await result.current.updateStatus('1', 'resolved', 'Fixed');
    });

    expect(adminApi.updateReportStatus).toHaveBeenCalledWith('1', { status: 'resolved', resolutionNotes: 'Fixed' });
  });
});

describe('useUsers', () => {
  const mockUsersData = {
    users: [
      { id: '1', username: 'john', email: 'john@test.com', roles: ['user'] },
      { id: '2', username: 'jane', email: 'jane@test.com', roles: ['admin'] },
    ],
    page: 1,
    limit: 50,
    total: 2,
    total_pages: 1,
  };

  beforeEach(() => {
    vi.clearAllMocks();
    adminApi.getUsers.mockResolvedValue({ success: true, data: mockUsersData });
    adminApi.deleteUser.mockResolvedValue({ success: true });
    adminApi.resetUserPassword.mockResolvedValue({ success: true, message: 'Password reset' });
    adminApi.updateUserStatus.mockResolvedValue({ success: true });
    adminApi.updateUserRoles.mockResolvedValue({ success: true });
  });

  it('fetches users on mount', async () => {
    const { result } = renderHook(() => useUsers({}, { page: 1, limit: 10 }));

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.users).toEqual(mockUsersData.users);
    expect(result.current.pagination.total).toBe(2);
    expect(adminApi.getUsers).toHaveBeenCalled();
  });

  it('provides deleteUser function', async () => {
    const { result } = renderHook(() => useUsers({}, { page: 1, limit: 10 }));

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    await act(async () => {
      await result.current.deleteUser('1');
    });

    // deleteUser is called with (userId, hardDelete=false)
    expect(adminApi.deleteUser).toHaveBeenCalledWith('1', false);
  });

  it('provides resetPassword function', async () => {
    const { result } = renderHook(() => useUsers({}, { page: 1, limit: 10 }));

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    await act(async () => {
      await result.current.resetPassword('1', 'newpass123');
    });

    expect(adminApi.resetUserPassword).toHaveBeenCalledWith('1', 'newpass123');
  });

  it('provides updateStatus function', async () => {
    const { result } = renderHook(() => useUsers({}, { page: 1, limit: 10 }));

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    await act(async () => {
      await result.current.updateStatus('1', false);
    });

    expect(adminApi.updateUserStatus).toHaveBeenCalledWith('1', false);
  });

  it('provides updateRoles function', async () => {
    const { result } = renderHook(() => useUsers({}, { page: 1, limit: 10 }));

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    await act(async () => {
      await result.current.updateRoles('1', ['admin', 'moderator']);
    });

    expect(adminApi.updateUserRoles).toHaveBeenCalledWith('1', ['admin', 'moderator']);
  });
});

describe('useUserDetails', () => {
  const mockUser = {
    id: '1',
    username: 'john',
    email: 'john@test.com',
    roles: ['user'],
    analysis_count: 50,
    created_at: '2024-01-01T00:00:00Z',
  };

  beforeEach(() => {
    vi.clearAllMocks();
    adminApi.getUser.mockResolvedValue({ success: true, data: mockUser });
  });

  it('does not fetch when userId is null', async () => {
    const { result } = renderHook(() => useUserDetails(null));

    // Wait for initial render to complete
    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    // Should not call API when userId is null
    expect(adminApi.getUser).not.toHaveBeenCalled();
    // Hook returns 'user' not 'data', and it's null when not loaded
    expect(result.current.user).toBe(null);
  });

  it('fetches user details when userId is provided', async () => {
    const { result } = renderHook(() => useUserDetails('1'));

    expect(result.current.loading).toBe(true);

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    // Hook returns 'user' not 'data'
    expect(result.current.user).toEqual(mockUser);
    expect(adminApi.getUser).toHaveBeenCalledWith('1');
  });
});
