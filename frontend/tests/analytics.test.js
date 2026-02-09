/**
 * Analytics API Tests
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import apiClient from '../src/api/client';
import {
  getVisitStatistics,
  getPageAnalytics,
  getDeviceBreakdown,
  getVisitsTimeSeries,
  getHourlyPattern,
  getReferrerStats,
  getRecentVisits,
  getAnalyticsSummary,
} from '../src/api/analytics';

// Mock the API client
vi.mock('../src/api/client', () => ({
  default: {
    get: vi.fn(),
  },
}));

describe('Analytics API', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('getVisitStatistics', () => {
    it('calls the correct endpoint', async () => {
      apiClient.get.mockResolvedValue({
        data: {
          success: true,
          data: {
            total_visits: 100,
            unique_visitors: 50,
          },
        },
      });

      await getVisitStatistics();

      expect(apiClient.get).toHaveBeenCalledWith('/analytics/visits/');
    });

    it('passes date parameters', async () => {
      apiClient.get.mockResolvedValue({ data: { success: true } });

      await getVisitStatistics({
        startDate: '2024-01-01',
        endDate: '2024-01-31',
      });

      expect(apiClient.get).toHaveBeenCalledWith(
        '/analytics/visits/?start_date=2024-01-01&end_date=2024-01-31'
      );
    });

    it('returns visit statistics', async () => {
      const mockData = {
        success: true,
        data: {
          total_visits: 100,
          unique_visitors: 50,
          authenticated_visits: 30,
          anonymous_visits: 70,
        },
      };
      apiClient.get.mockResolvedValue({ data: mockData });

      const result = await getVisitStatistics();

      expect(result).toEqual(mockData);
      expect(result.data.total_visits).toBe(100);
    });
  });

  describe('getPageAnalytics', () => {
    it('calls the correct endpoint', async () => {
      apiClient.get.mockResolvedValue({ data: { success: true, data: [] } });

      await getPageAnalytics();

      expect(apiClient.get).toHaveBeenCalledWith('/analytics/pages/');
    });

    it('passes limit parameter', async () => {
      apiClient.get.mockResolvedValue({ data: { success: true, data: [] } });

      await getPageAnalytics({ limit: 20 });

      expect(apiClient.get).toHaveBeenCalledWith('/analytics/pages/?limit=20');
    });

    it('returns page analytics data', async () => {
      const mockData = {
        success: true,
        data: [
          { path: '/api/analysis', visit_count: 500 },
          { path: '/api/chat', visit_count: 300 },
        ],
      };
      apiClient.get.mockResolvedValue({ data: mockData });

      const result = await getPageAnalytics();

      expect(result.data).toHaveLength(2);
      expect(result.data[0].path).toBe('/api/analysis');
    });
  });

  describe('getDeviceBreakdown', () => {
    it('calls the correct endpoint', async () => {
      apiClient.get.mockResolvedValue({ data: { success: true } });

      await getDeviceBreakdown();

      expect(apiClient.get).toHaveBeenCalledWith('/analytics/devices/');
    });

    it('returns device breakdown', async () => {
      const mockData = {
        success: true,
        data: {
          desktop: 60,
          mobile: 30,
          tablet: 10,
          unknown: 0,
          percentages: {
            desktop: 60.0,
            mobile: 30.0,
            tablet: 10.0,
          },
        },
      };
      apiClient.get.mockResolvedValue({ data: mockData });

      const result = await getDeviceBreakdown();

      expect(result.data.desktop).toBe(60);
      expect(result.data.percentages.mobile).toBe(30.0);
    });
  });

  describe('getVisitsTimeSeries', () => {
    it('calls the correct endpoint with parameters', async () => {
      apiClient.get.mockResolvedValue({ data: { success: true, data: [] } });

      await getVisitsTimeSeries({
        startDate: '2024-01-01',
        endDate: '2024-01-31',
        granularity: 'day',
      });

      expect(apiClient.get).toHaveBeenCalledWith(
        '/analytics/time-series/?start_date=2024-01-01&end_date=2024-01-31&granularity=day'
      );
    });

    it('returns time series data', async () => {
      const mockData = {
        success: true,
        data: [
          { date: '2024-01-01T00:00:00', count: 50 },
          { date: '2024-01-02T00:00:00', count: 75 },
        ],
      };
      apiClient.get.mockResolvedValue({ data: mockData });

      const result = await getVisitsTimeSeries({
        startDate: '2024-01-01',
        endDate: '2024-01-02',
      });

      expect(result.data).toHaveLength(2);
    });
  });

  describe('getHourlyPattern', () => {
    it('calls the correct endpoint', async () => {
      apiClient.get.mockResolvedValue({ data: { success: true } });

      await getHourlyPattern();

      expect(apiClient.get).toHaveBeenCalledWith('/analytics/hourly/');
    });

    it('returns hourly pattern data', async () => {
      const mockData = {
        success: true,
        data: {
          0: 10,
          1: 5,
          12: 100,
          18: 80,
        },
      };
      apiClient.get.mockResolvedValue({ data: mockData });

      const result = await getHourlyPattern();

      expect(result.data[12]).toBe(100);
    });
  });

  describe('getReferrerStats', () => {
    it('calls the correct endpoint', async () => {
      apiClient.get.mockResolvedValue({ data: { success: true, data: [] } });

      await getReferrerStats();

      expect(apiClient.get).toHaveBeenCalledWith('/analytics/referrers/');
    });

    it('passes limit parameter', async () => {
      apiClient.get.mockResolvedValue({ data: { success: true, data: [] } });

      await getReferrerStats({ limit: 5 });

      expect(apiClient.get).toHaveBeenCalledWith('/analytics/referrers/?limit=5');
    });

    it('returns referrer statistics', async () => {
      const mockData = {
        success: true,
        data: [
          { referrer: 'https://google.com', count: 50 },
          { referrer: 'https://twitter.com', count: 30 },
        ],
      };
      apiClient.get.mockResolvedValue({ data: mockData });

      const result = await getReferrerStats();

      expect(result.data[0].referrer).toBe('https://google.com');
    });
  });

  describe('getRecentVisits', () => {
    it('calls the correct endpoint', async () => {
      apiClient.get.mockResolvedValue({ data: { success: true, data: [] } });

      await getRecentVisits();

      expect(apiClient.get).toHaveBeenCalledWith('/analytics/recent/');
    });

    it('passes limit and path parameters', async () => {
      apiClient.get.mockResolvedValue({ data: { success: true, data: [] } });

      await getRecentVisits({ limit: 100, path: '/api' });

      expect(apiClient.get).toHaveBeenCalledWith('/analytics/recent/?limit=100&path=%2Fapi');
    });

    it('returns recent visits', async () => {
      const mockData = {
        success: true,
        data: [
          { path: '/api/analysis', timestamp: '2024-01-15T10:30:00' },
          { path: '/api/chat', timestamp: '2024-01-15T10:29:00' },
        ],
      };
      apiClient.get.mockResolvedValue({ data: mockData });

      const result = await getRecentVisits();

      expect(result.data).toHaveLength(2);
    });
  });

  describe('getAnalyticsSummary', () => {
    it('calls the correct endpoint', async () => {
      apiClient.get.mockResolvedValue({ data: { success: true } });

      await getAnalyticsSummary();

      expect(apiClient.get).toHaveBeenCalledWith('/analytics/summary/');
    });

    it('passes period parameter', async () => {
      apiClient.get.mockResolvedValue({ data: { success: true } });

      await getAnalyticsSummary({ period: 'month' });

      expect(apiClient.get).toHaveBeenCalledWith('/analytics/summary/?period=month');
    });

    it('returns comprehensive summary', async () => {
      const mockData = {
        success: true,
        data: {
          period: 'week',
          visits: { total_visits: 100, unique_visitors: 50 },
          devices: { desktop: 60, mobile: 30, tablet: 10 },
          top_pages: [{ path: '/api/analysis', visit_count: 500 }],
          hourly_pattern: { 12: 100 },
        },
      };
      apiClient.get.mockResolvedValue({ data: mockData });

      const result = await getAnalyticsSummary({ period: 'week' });

      expect(result.data.period).toBe('week');
      expect(result.data.visits.total_visits).toBe(100);
      expect(result.data.top_pages).toHaveLength(1);
    });
  });

  describe('Error handling', () => {
    it('propagates API errors', async () => {
      apiClient.get.mockRejectedValue(new Error('Network error'));

      await expect(getVisitStatistics()).rejects.toThrow('Network error');
    });

    it('handles 401 unauthorized', async () => {
      apiClient.get.mockRejectedValue({
        response: { status: 401, data: { error: 'Authentication required' } },
      });

      await expect(getAnalyticsSummary()).rejects.toBeDefined();
    });

    it('handles 403 forbidden', async () => {
      apiClient.get.mockRejectedValue({
        response: { status: 403, data: { error: 'Admin access required' } },
      });

      await expect(getPageAnalytics()).rejects.toBeDefined();
    });
  });
});
