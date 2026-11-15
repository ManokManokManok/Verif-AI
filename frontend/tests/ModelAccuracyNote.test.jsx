import React from 'react';
import { fireEvent, render, screen } from '@testing-library/react';
import { expect, it, vi } from 'vitest';
import ModelAccuracyNote from '../src/components/ModelAccuracyNote';

vi.mock('../src/api/client', () => ({
  getModelInfoRequest: vi.fn().mockResolvedValue({
    data: { accuracy: { accuracy: 94.7, margin_of_error: 4.4 }, dataset_updated: '2026-07' },
  }),
}));

it('shows the reported figures and explains the approximate margin', async () => {
  render(<ModelAccuracyNote />);

  expect(await screen.findByText('94.7%')).toBeInTheDocument();
  expect(screen.getByText('±4.4%')).toBeInTheDocument();
  fireEvent.click(screen.getByRole('button', { name: /Dataset was last updated/ }));
  fireEvent.click(screen.getByRole('button', { name: 'More about accuracy and margin of error' }));
  expect(screen.getByText(/not a statistically verified confidence interval/)).toBeInTheDocument();
});
