import React from 'react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import Detection from '../src/pages/Detection';
import { getAnalysisDetail } from '../src/api/analysis';
import { analyzeImage, getAnalysisConversation } from '../src/api/chatbot';
import { getChatHistory } from '../src/api/client';

vi.mock('../src/context/AuthContext', () => ({
  useAuth: () => ({
    isLoggedIn: true,
    isAdmin: false,
    logout: vi.fn(),
    user: { username: 'test-user' },
    accessToken: 'test-token',
  }),
}));

vi.mock('../src/api/client', () => ({
  getChatHistory: vi.fn(),
  detectScamRequest: vi.fn(),
}));

vi.mock('../src/api/analysis', () => ({
  getAnalysisDetail: vi.fn(),
  deleteAnalysisHistoryItem: vi.fn(),
}));

vi.mock('../src/api/chatbot', () => ({
  analyzeImage: vi.fn(),
  getAnalysisConversation: vi.fn(),
  hasGuestFeatureBeenUsed: vi.fn(() => false),
  GUEST_USE_LIMIT_CODE: 'GUEST_USE_LIMIT_REACHED',
}));

vi.mock('../src/components/AppNavLinks', () => ({ default: () => <nav /> }));
vi.mock('../src/components/reports', () => ({ ReportModal: () => null }));
vi.mock('../src/components/auth/LogoutConfirmModal', () => ({ default: () => null }));
vi.mock('react-image-crop', () => ({
  default: ({ children }) => <div>{children}</div>,
}));

describe('Detection image analysis errors', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    getChatHistory.mockResolvedValue({ history: [] });
    getAnalysisConversation.mockResolvedValue({});
  });

  it('opens image review when an image is dropped onto the input bar', async () => {
    const { container } = render(
      <MemoryRouter>
        <Detection />
      </MemoryRouter>,
    );
    const row = container.querySelector('.detect__inputRow');
    const file = new File(['image'], 'dropped.png', { type: 'image/png' });

    fireEvent.drop(row, {
      dataTransfer: { files: [file], types: ['Files'] },
    });

    expect(await screen.findByRole('button', { name: 'Apply Crop' })).toBeInTheDocument();
  });

  it('loads an admin-verified analysis from history and displays its classification', async () => {
    getChatHistory.mockResolvedValue({
      history: [{
        id: 'analysis-123',
        title: 'Admin-reviewed: Banking Access & Payment',
        description: 'Admin assessment summary.',
        timestamp: '2026-10-12T04:00:00Z',
        reviewed_result: { is_published: true },
      }],
    });
    getAnalysisDetail.mockResolvedValue({
      id: 'analysis-123',
      ref_id: 'analysis-ref-123',
      is_scam: true,
      scam_type: 'Banking Access & Payment',
      scam_score: null,
      legit_score: null,
      summary: 'Admin assessment summary.',
      details: 'The link opens a credential collection page.',
      key_markers: ['Requests credentials through an unverified link'],
      reviewed_result: {
        is_published: true,
        is_scam: true,
        risk_score: 84,
        risk_level: 'high',
        scam_type: 'Banking Access & Payment',
        summary: 'Admin assessment summary.',
        details: 'The link opens a credential collection page.',
        key_markers: ['Requests credentials through an unverified link'],
        explanation: 'The sender impersonates a bank.',
      },
    });

    render(
      <MemoryRouter>
        <Detection />
      </MemoryRouter>,
    );

    fireEvent.click(screen.getByRole('button', { name: 'Menu' }));
    expect(await screen.findByText('Admin verified')).toBeInTheDocument();
    fireEvent.click(await screen.findByText('Admin-reviewed: Banking Access & Payment'));

    expect(await screen.findByText('Admin-verified: scam')).toBeInTheDocument();
    expect(screen.getByText('Banking Access & Payment')).toBeInTheDocument();
    expect(getAnalysisDetail).toHaveBeenCalledWith('analysis-123');
  });

  it('shows a retry action instead of presenting a failed history request as empty', async () => {
    getChatHistory.mockRejectedValueOnce(new Error('Request failed'));

    render(
      <MemoryRouter>
        <Detection />
      </MemoryRouter>,
    );

    fireEvent.click(screen.getByRole('button', { name: 'Menu' }));
    expect(await screen.findByRole('alert')).toHaveTextContent(
      'Failed to load analysis history. Please try again.',
    );

    getChatHistory.mockResolvedValueOnce({ history: [] });
    fireEvent.click(screen.getByRole('button', { name: 'Retry' }));

    await waitFor(() => expect(getChatHistory).toHaveBeenCalledTimes(2));
    expect(await screen.findByText('No analyses yet')).toBeInTheDocument();
  });

  it('refreshes history and the open analysis when the page regains focus', async () => {
    const analysisId = 'analysis-focus-123';
    const reviewedDetail = {
      id: analysisId,
      ref_id: 'analysis-focus-ref',
      is_scam: true,
      scam_type: 'Banking Access & Payment',
      scam_score: null,
      legit_score: null,
      summary: 'Admin assessment summary.',
      details: 'The link opens a credential collection page.',
      key_markers: ['Requests credentials through an unverified link'],
      reviewed_result: {
        is_published: true,
        is_scam: true,
        risk_score: 84,
        risk_level: 'high',
        scam_type: 'Banking Access & Payment',
        summary: 'Admin assessment summary.',
        details: 'The link opens a credential collection page.',
        key_markers: ['Requests credentials through an unverified link'],
        explanation: 'The sender impersonates a bank.',
      },
    };
    getChatHistory
      .mockResolvedValueOnce({
        history: [{
          id: analysisId,
          title: 'Banking Access & Payment',
          description: 'Model summary.',
          timestamp: '2026-10-12T04:00:00Z',
        }],
      })
      .mockResolvedValueOnce({
        history: [{
          id: analysisId,
          title: 'Admin-reviewed: Banking Access & Payment',
          description: 'Admin assessment summary.',
          timestamp: '2026-10-12T04:00:00Z',
          reviewed_result: { is_published: true },
        }],
      });
    getAnalysisDetail
      .mockResolvedValueOnce({
        id: analysisId,
        ref_id: 'analysis-focus-ref',
        is_scam: true,
        scam_type: 'Banking Access & Payment',
        scam_score: 80,
        legit_score: 20,
        type_confidence: 80,
        summary: 'Model summary.',
        details: 'Model detail.',
        key_markers: [],
      })
      .mockResolvedValueOnce(reviewedDetail);

    render(
      <MemoryRouter>
        <Detection />
      </MemoryRouter>,
    );

    fireEvent.click(screen.getByRole('button', { name: 'Menu' }));
    fireEvent.click(await screen.findByText('Banking Access & Payment'));
    expect(await screen.findByText('Likely to be a scam')).toBeInTheDocument();

    fireEvent.focus(window);

    expect(await screen.findByText('Admin-verified: scam')).toBeInTheDocument();
    expect(await screen.findByText('Admin verified')).toBeInTheDocument();
    expect(getChatHistory).toHaveBeenCalledTimes(2);
    expect(getAnalysisDetail).toHaveBeenCalledTimes(2);
  });

  it('opens image review when an image is pasted into the text input', async () => {
    render(
      <MemoryRouter>
        <Detection />
      </MemoryRouter>,
    );
    const textarea = screen.getByRole('textbox');
    const file = new File(['image'], 'pasted.png', { type: 'image/png' });

    fireEvent.paste(textarea, {
      clipboardData: {
        items: [{
          kind: 'file',
          type: 'image/png',
          getAsFile: () => file,
        }],
      },
    });

    expect(await screen.findByRole('button', { name: 'Apply Crop' })).toBeInTheDocument();
  });

  it('displays a friendly message when image analysis providers are unavailable', async () => {
    const message =
      'Verif-AI image analysis is currently unavailable. Please try again later or use text-based analysis.';
    analyzeImage.mockRejectedValue(Object.assign(new Error(message), { code: 'SERVICE_UNAVAILABLE' }));

    const { container } = render(
      <MemoryRouter>
        <Detection />
      </MemoryRouter>,
    );

    const upload = container.querySelector('input[type="file"]');
    fireEvent.change(upload, {
      target: { files: [new File(['image'], 'sample.png', { type: 'image/png' })] },
    });

    fireEvent.click(await screen.findByRole('button', { name: 'Apply Crop' }));
    fireEvent.click(await screen.findByRole('button', { name: 'Submit Image' }));

    expect(await screen.findByRole('alert')).toHaveTextContent(message);
  });
});
