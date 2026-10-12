import React from 'react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import Detection from '../src/pages/Detection';
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
vi.mock('../src/components/ChatHistoryList', () => ({ default: () => <div /> }));
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
