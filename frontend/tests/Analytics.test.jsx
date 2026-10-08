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
});
