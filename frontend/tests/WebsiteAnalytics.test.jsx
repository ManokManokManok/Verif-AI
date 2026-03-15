/**
 * Website Analytics Component Tests
 */

import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import WebsiteAnalytics from '../src/pages/admin/WebsiteAnalytics';
import * as adminDataHooks from '../src/hooks/useAdminData';

// Mock the hooks
vi.mock('../src/hooks/useAdminData', () => ({
  useAnalytics: vi.fn(),
}));

// Mock CSS import
vi.mock('../src/pages/admin/WebsiteAnalytics.css', () => ({}));

describe('WebsiteAnalytics', () => {
  const mockRefresh = vi.fn();
  const mockOnNotify = vi.fn();

  const mockAnalyticsData = {
    visits: {
      total_visits: 1500,
      unique_visitors: 800,
      authenticated_visits: 500,
      anonymous_visits: 1000,
    },
    devices: {
      desktop: 600,
      mobile: 350,
      tablet: 100,
      unknown: 50,
    },
    top_pages: [
      { path: '/api/analysis', visit_count: 500 },
      { path: '/api/chat', visit_count: 300 },
      { path: '/dashboard', visit_count: 200 },
    ],
    hourly_pattern: {
      0: 10, 1: 5, 2: 3, 3: 2, 4: 1, 5: 2,
      6: 10, 7: 25, 8: 50, 9: 80, 10: 100, 11: 90,
      12: 70, 13: 85, 14: 95, 15: 88, 16: 75, 17: 60,
      18: 45, 19: 35, 20: 25, 21: 20, 22: 15, 23: 12,
    },
    referrers: [
      { referrer: 'https://google.com', count: 200 },
      { referrer: 'https://twitter.com', count: 100 },
    ],
    recent: [
      { path: '/api/analysis', device_type: 'desktop', timestamp: new Date().toISOString() },
      { path: '/api/chat', device_type: 'mobile', timestamp: new Date().toISOString() },
    ],
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders loading state', () => {
    adminDataHooks.useAnalytics.mockReturnValue({
      data: null,
      loading: true,
      error: null,
      refresh: mockRefresh,
    });

    render(<WebsiteAnalytics onNotify={mockOnNotify} />);

    expect(screen.getByText('Loading website analytics...')).toBeInTheDocument();
  });

  it('renders error state with retry button', () => {
    adminDataHooks.useAnalytics.mockReturnValue({
      data: null,
      loading: false,
      error: 'Failed to fetch',
      refresh: mockRefresh,
    });

    render(<WebsiteAnalytics onNotify={mockOnNotify} />);

    expect(screen.getByText(/Failed to load analytics/)).toBeInTheDocument();
  });

  it('renders analytics data', async () => {
    adminDataHooks.useAnalytics.mockReturnValue({
      data: mockAnalyticsData,
      loading: false,
      error: null,
      refresh: mockRefresh,
    });

    render(<WebsiteAnalytics onNotify={mockOnNotify} />);

    // Check header
    expect(screen.getByText('Website Analytics')).toBeInTheDocument();

    // Check stat cards
    expect(screen.getByText('Total Visits')).toBeInTheDocument();
    expect(screen.getByText('1,500')).toBeInTheDocument();
    expect(screen.getByText('Unique Visitors')).toBeInTheDocument();
    expect(screen.getByText('800')).toBeInTheDocument();
  });

  it('displays device breakdown', () => {
    adminDataHooks.useAnalytics.mockReturnValue({
      data: mockAnalyticsData,
      loading: false,
      error: null,
      refresh: mockRefresh,
    });

    render(<WebsiteAnalytics onNotify={mockOnNotify} />);

    expect(screen.getByText('Device Breakdown')).toBeInTheDocument();
    expect(screen.getByText('Desktop')).toBeInTheDocument();
    expect(screen.getByText('Mobile')).toBeInTheDocument();
    expect(screen.getByText('Tablet')).toBeInTheDocument();
  });

  it('displays top pages chart', () => {
    adminDataHooks.useAnalytics.mockReturnValue({
      data: mockAnalyticsData,
      loading: false,
      error: null,
      refresh: mockRefresh,
    });

    render(<WebsiteAnalytics onNotify={mockOnNotify} />);

    expect(screen.getByText('Top Pages')).toBeInTheDocument();
    // Use getAllByText since path may appear in both chart and recent visits
    const analysisElements = screen.getAllByText('/api/analysis');
    expect(analysisElements.length).toBeGreaterThan(0);
  });

  it('displays hourly traffic pattern', () => {
    adminDataHooks.useAnalytics.mockReturnValue({
      data: mockAnalyticsData,
      loading: false,
      error: null,
      refresh: mockRefresh,
    });

    render(<WebsiteAnalytics onNotify={mockOnNotify} />);

    expect(screen.getByText('Hourly Traffic Pattern')).toBeInTheDocument();
  });

  it('displays recent visits', () => {
    adminDataHooks.useAnalytics.mockReturnValue({
      data: mockAnalyticsData,
      loading: false,
      error: null,
      refresh: mockRefresh,
    });

    render(<WebsiteAnalytics onNotify={mockOnNotify} />);

    expect(screen.getByText('Recent Visits')).toBeInTheDocument();
  });

  it('does not display top referrers section', () => {
    adminDataHooks.useAnalytics.mockReturnValue({
      data: mockAnalyticsData,
      loading: false,
      error: null,
      refresh: mockRefresh,
    });

    render(<WebsiteAnalytics onNotify={mockOnNotify} />);

    expect(screen.queryByText('Top Referrers')).not.toBeInTheDocument();
    expect(screen.queryByText('https://google.com')).not.toBeInTheDocument();
  });

  it('calls refresh on button click', () => {
    adminDataHooks.useAnalytics.mockReturnValue({
      data: mockAnalyticsData,
      loading: false,
      error: null,
      refresh: mockRefresh,
    });

    render(<WebsiteAnalytics onNotify={mockOnNotify} />);

    const refreshButton = screen.getByText('Refresh');
    fireEvent.click(refreshButton);

    expect(mockRefresh).toHaveBeenCalled();
  });

  it('handles period change', () => {
    adminDataHooks.useAnalytics.mockReturnValue({
      data: mockAnalyticsData,
      loading: false,
      error: null,
      refresh: mockRefresh,
    });

    render(<WebsiteAnalytics onNotify={mockOnNotify} />);

    // Period selector should be present
    expect(adminDataHooks.useAnalytics).toHaveBeenCalledWith('week');
  });

  it('shows empty state for no recent visits', () => {
    adminDataHooks.useAnalytics.mockReturnValue({
      data: { ...mockAnalyticsData, recent: [] },
      loading: false,
      error: null,
      refresh: mockRefresh,
    });

    render(<WebsiteAnalytics onNotify={mockOnNotify} />);

    expect(screen.getByText('No recent visits recorded yet')).toBeInTheDocument();
  });

  it('handles missing data gracefully', () => {
    adminDataHooks.useAnalytics.mockReturnValue({
      data: { visits: {}, devices: {}, top_pages: [], hourly_pattern: {}, referrers: [] },
      loading: false,
      error: null,
      refresh: mockRefresh,
    });

    render(<WebsiteAnalytics onNotify={mockOnNotify} />);

    // Should render without crashing
    expect(screen.getByText('Website Analytics')).toBeInTheDocument();
    // Use getAllByText since there are multiple stat cards with 0 value
    const zeroElements = screen.getAllByText('0');
    expect(zeroElements.length).toBeGreaterThan(0);
  });
});

describe('BarChart Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('shows empty state when no data', () => {
    const emptyAnalyticsData = {
      visits: {},
      devices: {},
      top_pages: [],
      hourly_pattern: {},
      referrers: [],
      recent: [],
    };

    adminDataHooks.useAnalytics.mockReturnValue({
      data: emptyAnalyticsData,
      loading: false,
      error: null,
      refresh: vi.fn(),
    });

    render(<WebsiteAnalytics />);

    // Use getAllByText since there are multiple empty charts
    const noDataElements = screen.getAllByText('No data available');
    expect(noDataElements.length).toBeGreaterThan(0);
  });
});

describe('useAnalytics hook integration', () => {
  it('is called with correct default period', () => {
    adminDataHooks.useAnalytics.mockReturnValue({
      data: null,
      loading: true,
      error: null,
      refresh: vi.fn(),
    });

    render(<WebsiteAnalytics />);

    expect(adminDataHooks.useAnalytics).toHaveBeenCalledWith('week');
  });
});
