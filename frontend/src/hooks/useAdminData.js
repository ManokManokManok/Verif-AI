/**
 * Admin Data Hooks
 * 
 * Custom React hooks for fetching and managing admin dashboard data.
 * Provides loading states, error handling, and automatic refresh.
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import {
  getModelHealth,
  getModelHealthSummary,
  getAnalysisStats,
  getTopScamCategories,
  getUserStats,
  getUserReports,
  updateReportStatus as apiUpdateReportStatus,
  getUsers,
  getUser,
  deleteUser as apiDeleteUser,
  resetUserPassword as apiResetPassword,
  updateUserStatus as apiUpdateUserStatus,
  updateUserRoles as apiUpdateUserRoles,
} from '../api/admin';
import { getAnalyticsSummary, getRecentVisits } from '../api/analytics';

/**
 * Hook for fetching model health metrics
 * @param {number} refreshInterval - Auto-refresh interval in ms (0 to disable)
 */
export function useModelHealth(refreshInterval = 30000) {
  const [data, setData] = useState(null);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const intervalRef = useRef(null);

  const fetchData = useCallback(async () => {
    try {
      setError(null);
      const [healthRes, summaryRes] = await Promise.all([
        getModelHealth(),
        getModelHealthSummary(),
      ]);
      
      if (healthRes.success) setData(healthRes.data);
      if (summaryRes.success) setSummary(summaryRes.data);
    } catch (err) {
      setError(err.message || 'Failed to fetch model health');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();

    if (refreshInterval > 0) {
      intervalRef.current = setInterval(fetchData, refreshInterval);
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [fetchData, refreshInterval]);

  return { data, summary, loading, error, refresh: fetchData };
}

/**
 * Hook for fetching analysis statistics
 * @param {Object} dateRange - Date range filter
 * @param {string} period - Period grouping
 */
export function useAnalysisStats(dateRange = {}, period = 'all_time') {
  const [stats, setStats] = useState(null);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
      const params = {
        startDate: dateRange.startDate,
        endDate: dateRange.endDate,
        period,
      };
      
      const [statsRes, categoriesRes] = await Promise.all([
        getAnalysisStats(params),
        getTopScamCategories(params),
      ]);
      
      if (statsRes.success) setStats(statsRes.data);
      if (categoriesRes.success) setCategories(categoriesRes.data);
    } catch (err) {
      setError(err.message || 'Failed to fetch analysis statistics');
    } finally {
      setLoading(false);
    }
  }, [dateRange.startDate, dateRange.endDate, period]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { data: stats, categories, loading, error, refresh: fetchData };
}

/**
 * Hook for fetching user statistics
 * @param {Object} dateRange - Date range filter
 * @param {string} period - Period grouping
 */
export function useUserStats(dateRange = {}, period = 'all_time') {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
      const res = await getUserStats({
        startDate: dateRange.startDate,
        endDate: dateRange.endDate,
        period,
      });
      
      if (res.success) setStats(res.data);
    } catch (err) {
      setError(err.message || 'Failed to fetch user statistics');
    } finally {
      setLoading(false);
    }
  }, [dateRange.startDate, dateRange.endDate, period]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { data: stats, loading, error, refresh: fetchData };
}

/**
 * Hook for fetching and managing user reports
 * @param {string} status - Filter by status
 */
export function useUserReports(status = null) {
  const [reports, setReports] = useState([]);
  const [pagination, setPagination] = useState({
    page: 1,
    limit: 50,
    total: 0,
    totalPages: 0,
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchData = useCallback(async (page = 1) => {
    try {
      setLoading(true);
      setError(null);
      
      const res = await getUserReports({
        status,
        page,
        limit: pagination.limit,
      });
      
      if (res.success) {
        setReports(res.data.reports);
        setPagination({
          page: res.data.page,
          limit: res.data.limit,
          total: res.data.total,
          totalPages: res.data.total_pages,
        });
      }
    } catch (err) {
      setError(err.message || 'Failed to fetch reports');
    } finally {
      setLoading(false);
    }
  }, [status, pagination.limit]);

  useEffect(() => {
    fetchData(1);
  }, [status]); // Reset to page 1 when status filter changes

  const updateStatus = useCallback(async (reportId, newStatus, notes) => {
    try {
      const res = await apiUpdateReportStatus(reportId, {
        status: newStatus,
        resolutionNotes: notes,
      });
      
      if (res.success) {
        // Update local state
        setReports(prev => 
          prev.map(r => r.report_id === reportId ? res.data : r)
        );
        return { success: true };
      }
      return { success: false, error: 'Update failed' };
    } catch (err) {
      return { success: false, error: err.message };
    }
  }, []);

  const goToPage = useCallback((page) => {
    fetchData(page);
  }, [fetchData]);

  return { 
    data: { reports }, 
    pagination, 
    loading, 
    error, 
    refresh: () => fetchData(pagination.page),
    updateStatus,
    goToPage,
  };
}

/**
 * Hook for fetching and managing users
 * @param {Object} filters - User filters
 * @param {Object} paginationOptions - Pagination options
 */
export function useUsers(filters = {}, paginationOptions = {}) {
  const [users, setUsers] = useState([]);
  const [pagination, setPagination] = useState({
    page: paginationOptions.page || 1,
    limit: paginationOptions.limit || 50,
    total: 0,
    totalPages: 0,
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchData = useCallback(async (page = pagination.page) => {
    try {
      setLoading(true);
      setError(null);
      
      const res = await getUsers({
        ...filters,
        page,
        limit: pagination.limit,
      });
      
      if (res.success) {
        setUsers(res.data.users);
        setPagination({
          page: res.data.page,
          limit: res.data.limit,
          total: res.data.total,
          totalPages: res.data.total_pages,
        });
      }
    } catch (err) {
      setError(err.message || 'Failed to fetch users');
    } finally {
      setLoading(false);
    }
  }, [filters, pagination.limit]);

  useEffect(() => {
    fetchData(1); // Reset to page 1 when filters change
  }, [filters.search, filters.role, filters.isActive, filters.isVerified]);

  const deleteUser = useCallback(async (userId, hardDelete = false) => {
    try {
      const res = await apiDeleteUser(userId, hardDelete);
      if (res.success) {
        setUsers(prev => prev.filter(u => u.id !== userId));
        setPagination(prev => ({ ...prev, total: prev.total - 1 }));
        return { success: true };
      }
      return { success: false, error: 'Delete failed' };
    } catch (err) {
      return { success: false, error: err.message };
    }
  }, []);

  const resetPassword = useCallback(async (userId, newPassword) => {
    try {
      const res = await apiResetPassword(userId, newPassword);
      return { success: res.success, message: res.message };
    } catch (err) {
      return { success: false, error: err.message };
    }
  }, []);

  const updateStatus = useCallback(async (userId, newStatus) => {
    try {
      const res = await apiUpdateUserStatus(userId, newStatus);
      if (res.success) {
        setUsers(prev => 
          prev.map(u => u.id === userId ? { 
            ...u, 
            status: newStatus,
            is_active: newStatus === 'active',
          } : u)
        );
        return { success: true };
      }
      return { success: false, error: 'Update failed' };
    } catch (err) {
      return { success: false, error: err.message };
    }
  }, []);

  const updateRoles = useCallback(async (userId, roles) => {
    try {
      const res = await apiUpdateUserRoles(userId, roles);
      if (res.success) {
        setUsers(prev => 
          prev.map(u => u.id === userId ? { ...u, roles } : u)
        );
        return { success: true };
      }
      return { success: false, error: 'Update failed' };
    } catch (err) {
      return { success: false, error: err.message };
    }
  }, []);

  const goToPage = useCallback((page) => {
    fetchData(page);
  }, [fetchData]);

  return {
    data: { users, pagination },
    loading,
    error,
    refresh: () => fetchData(pagination.page),
    deleteUser,
    resetPassword,
    updateStatus,
    updateRoles,
    goToPage,
  };
}

/**
 * Hook for fetching single user details
 * @param {string} userId - User ID
 */
export function useUserDetails(userId) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchData = useCallback(async () => {
    if (!userId) {
      setLoading(false);
      return;
    }
    
    try {
      setLoading(true);
      setError(null);
      
      const res = await getUser(userId);
      if (res.success) setUser(res.data);
    } catch (err) {
      setError(err.message || 'Failed to fetch user details');
    } finally {
      setLoading(false);
    }
  }, [userId]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { user, loading, error, refresh: fetchData };
}

/**
 * Hook for fetching website analytics
 * @param {string} period - Time period (day, week, month)
 * @param {number} refreshInterval - Auto-refresh interval in ms (0 to disable)
 */
export function useAnalytics(period = 'week', refreshInterval = 60000) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const intervalRef = useRef(null);

  const fetchData = useCallback(async () => {
    try {
      setError(null);
      
      const [summaryRes, recentRes] = await Promise.all([
        getAnalyticsSummary({ period }),
        getRecentVisits({ limit: 20 }),
      ]);
      
      if (summaryRes.success) {
        setData({
          ...summaryRes.data,
          recent: recentRes.success ? recentRes.data : [],
        });
      }
    } catch (err) {
      setError(err.message || 'Failed to fetch analytics');
    } finally {
      setLoading(false);
    }
  }, [period]);

  useEffect(() => {
    setLoading(true);
    fetchData();

    if (refreshInterval > 0) {
      intervalRef.current = setInterval(fetchData, refreshInterval);
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [fetchData, refreshInterval]);

  return { data, loading, error, refresh: fetchData };
}
