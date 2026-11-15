import React from 'react';
import { describe, expect, it, vi } from 'vitest';
import { act, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import Settings from '../src/pages/Settings';
import { changePasswordRequest } from '../src/api/client';

vi.mock('../src/context/AuthContext', () => ({
  useAuth: () => ({
    user: { username: 'test-user', email: 'user@example.com' },
    isLoggedIn: true,
    logout: vi.fn(),
    refreshUser: vi.fn(),
  }),
}));

vi.mock('../src/context/ThemeContext', () => ({
  useTheme: () => ({ theme: 'light', toggleTheme: vi.fn(), setTheme: vi.fn() }),
}));

vi.mock('../src/api/client', () => ({
  changePasswordRequest: vi.fn().mockResolvedValue({}),
  deleteAccountRequest: vi.fn(),
  sendPasswordChangeCodeRequest: vi.fn(),
  updateUsernameRequest: vi.fn(),
}));

vi.mock('../src/api/reports', async (importOriginal) => ({
  ...await importOriginal(),
  getMyReports: vi.fn().mockResolvedValue({ success: true, data: { reports: [] } }),
}));

describe('Settings password change', () => {
  it('accepts and submits a six-digit verification code including a leading zero', async () => {
    const user = userEvent.setup();
    render(<MemoryRouter><Settings /></MemoryRouter>);

    await act(async () => user.click(screen.getByRole('button', { name: /change password/i })));
    await act(async () => user.type(screen.getByLabelText('Verification code'), '0123457'));
    expect(screen.getByLabelText('Verification code')).toHaveValue('012345');
    await act(async () => user.type(screen.getByLabelText('Current password'), 'CurrentPass1!'));
    await act(async () => user.type(screen.getByLabelText('New password'), 'ExamplePass1!'));
    await act(async () => user.type(screen.getByLabelText('Confirm new password'), 'ExamplePass1!'));
    await act(async () => user.click(screen.getByRole('button', { name: 'Change password', exact: true })));

    await waitFor(() => expect(changePasswordRequest).toHaveBeenCalledWith({
      code: '012345',
      current_password: 'CurrentPass1!',
      new_password: 'ExamplePass1!',
      confirm_password: 'ExamplePass1!',
    }));
  });
});
