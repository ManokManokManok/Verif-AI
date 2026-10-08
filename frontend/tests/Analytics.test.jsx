import React from 'react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import Analytics from '../src/pages/Analytics';
import {
  getGlobalSafetySummary,
  getUserAiSummaryCached,
  getUserSafetySummary,
} from '../src/api/analytics';

vi.mock('../src/context/AuthContext', () => ({
  useAuth: () => ({
    user: { username: 'test-user' },
    isLoggedIn: true,
    isAdmin: false,
    logout: vi.fn(),
  }),
}));

vi.mock('../src/api/analytics', () => ({
  getGlobalSafetySummary: vi.fn(),
  getUserSafetySummary: vi.fn(),
  getUserAiSummary: vi.fn(),
  getUserAiSummaryCached: vi.fn(),
}));

vi.mock('../src/components/AppNavLinks', () => ({
  default: () => <nav />,
}));

describe('Analytics', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    getUserSafetySummary.mockRejectedValue(new Error('Failed to fetch'));
    getGlobalSafetySummary.mockResolvedValue({});
    getUserAiSummaryCached.mockResolvedValue({});
  });

  it('shows a friendly message when analytics cannot be loaded', async () => {
    render(
      <MemoryRouter>
        <Analytics />
      </MemoryRouter>,
    );

    expect(await screen.findByText(
      'We are having trouble contacting Verif-AI right now. Please refresh the page to try again.',
    )).toBeInTheDocument();
    expect(screen.queryByText('Failed to fetch')).not.toBeInTheDocument();
  });

  it('distinguishes no recent checks from a zero high-risk rate', async () => {
    getUserSafetySummary.mockResolvedValue({
      data: {
        success: true,
        data: {
          total_checks: 0,
          total_scam_checks: 0,
          high_risk_count: 0,
          activity: {
            as_of_date: '2026-10-08',
            recent_30_days: { total_checks: 0, high_risk_count: 0, high_risk_rate: null },
            previous_30_days: { total_checks: 0, high_risk_count: 0, high_risk_rate: null },
            risk_mix: { not_scam: 0, suspicious: 0, high_risk: 0 },
            monthly_risk: [],
            calendar_days: [],
            weekday_activity: [],
            days_since_last_high_risk: null,
          },
        },
      },
    });
    getGlobalSafetySummary.mockResolvedValue({
      data: {
        success: true,
        data: {
          total_checks: 0,
          community_analytics: {
            distinct_users: 0,
            minimum_users: 5,
            total_scam_checks: 0,
            top_types_all_time: [],
            top_types_this_month: [],
            category_monthly_series: [],
            rising_scams: [],
          },
        },
      },
    });

    render(
      <MemoryRouter>
        <Analytics />
      </MemoryRouter>,
    );

    expect(await screen.findByText('No recent checks')).toBeInTheDocument();
    expect(screen.getByText('No checks')).toBeInTheDocument();
    expect(screen.getByText('0 of 0 checks were high-risk')).toBeInTheDocument();
    expect(screen.queryByText('0%')).not.toBeInTheDocument();
  });
});
