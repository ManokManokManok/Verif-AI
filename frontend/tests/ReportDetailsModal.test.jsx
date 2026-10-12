import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import ReportDetailsModal from '../src/pages/admin/UserStats/components/ReportDetailsModal';

const createReport = () => ({
  id: 'report-1',
  report_id: 'report-1',
  report_type: 'false_positive',
  status: 'pending',
  title: 'False positive',
  description: 'This message is from my bank.',
  analysis_ref_id: 'analysis-1',
  analysis: {
    ref_id: 'analysis-1',
    is_scam: true,
    scam_type: 'Banking Access & Payment',
    scam_score: 82,
    legit_score: 18,
    type_confidence: 75,
    message: 'Please verify your account.',
    needs_review: false,
    review_history: [],
  },
});

describe('ReportDetailsModal', () => {
  it('shows linked analysis and submits a complete human scam review', () => {
    const onSaveChanges = vi.fn();
    const report = createReport();

    render(
      <ReportDetailsModal
        isOpen
        report={report}
        loading={false}
        onClose={vi.fn()}
        onSaveChanges={onSaveChanges}
      />,
    );

    expect(screen.getByText('Please verify your account.')).toBeInTheDocument();
    expect(screen.getByText('Model flagged as scam')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: /Confirmed scam/ }));
    const scamType = screen.getByLabelText('Scam type');
    expect(scamType.options).toHaveLength(16);
    fireEvent.change(scamType, { target: { value: 'Banking Access & Payment' } });
    fireEvent.change(screen.getByLabelText('Human risk estimate number'), {
      target: { value: '84' },
    });
    fireEvent.change(screen.getByLabelText(/Human-written result summary/), {
      target: { value: 'This message is a high-risk attempt to steal bank credentials.' },
    });
    fireEvent.change(screen.getByLabelText(/Additional human-reviewed details/), {
      target: { value: 'The link opens a credential collection page.' },
    });
    fireEvent.change(screen.getByLabelText(/Reviewer rationale/), {
      target: { value: 'The message impersonates the bank and requests credentials.' },
    });
    fireEvent.change(screen.getByLabelText(/Human-verified red flags/), {
      target: { value: 'Requests a password using an unverified link' },
    });
    fireEvent.keyDown(screen.getByLabelText(/Human-verified red flags/), { key: 'Enter' });
    fireEvent.click(screen.getByRole('button', { name: 'Save report and review' }));

    expect(onSaveChanges).toHaveBeenCalledWith(
      report,
      'pending',
      undefined,
      {
        decision: 'confirmed_scam',
        risk_score: 84,
        scam_type: 'Banking Access & Payment',
        summary: 'This message is a high-risk attempt to steal bank credentials.',
        details: 'The link opens a credential collection page.',
        key_markers: ['Requests a password using an unverified link'],
        explanation: 'The message impersonates the bank and requests credentials.',
      },
    );
  });

  it('sets confirmed legitimate reviews to zero human risk', () => {
    const onSaveChanges = vi.fn();
    const report = createReport();
    render(
      <ReportDetailsModal
        isOpen
        report={report}
        loading={false}
        onClose={vi.fn()}
        onSaveChanges={onSaveChanges}
      />,
    );

    fireEvent.click(screen.getByRole('button', { name: /Confirmed legitimate/ }));
    fireEvent.change(screen.getByLabelText(/Human-written result summary/), {
      target: { value: 'Verified as a legitimate bank notification.' },
    });
    fireEvent.change(screen.getByLabelText(/Reviewer rationale/), {
      target: { value: 'The sender and destination were verified as authentic.' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Save report and review' }));

    expect(onSaveChanges).toHaveBeenCalledWith(
      report,
      'pending',
      undefined,
      expect.objectContaining({
        decision: 'confirmed_legitimate',
        risk_score: 0,
      }),
    );
  });

  it('shows who resolved a report and preserves the admin activity history', () => {
    const report = {
      ...createReport(),
      status: 'resolved',
      is_resolved: true,
      activity_history: [
        {
          admin_user_id: 'admin-1',
          admin_email: 'first.admin@example.com',
          status: 'in_progress',
          action: 'support_response',
          actions: ['status_updated', 'support_response'],
          resolution_notes: 'We are investigating your report.',
          created_at: '2026-10-12T04:00:00Z',
        },
        {
          admin_user_id: 'admin-2',
          admin_email: 'second.admin@example.com',
          status: 'resolved',
          action: 'status_updated',
          actions: ['status_updated', 'resolved'],
          resolution_notes: 'Confirmed and corrected.',
          created_at: '2026-10-12T05:00:00Z',
        },
      ],
    };

    render(
      <ReportDetailsModal
        isOpen
        report={report}
        loading={false}
        onClose={vi.fn()}
      />,
    );

    expect(screen.getByText('Admin activity history')).toBeInTheDocument();
    expect(screen.getByText('Admin responded to support request')).toBeInTheDocument();
    expect(screen.getByText('Report resolved')).toBeInTheDocument();
    expect(screen.getByText(/first\.admin@example\.com/)).toBeInTheDocument();
    expect(screen.getAllByText(/second\.admin@example\.com/)).toHaveLength(2);
    expect(screen.getByText('We are investigating your report.')).toBeInTheDocument();
    expect(screen.getByText('Confirmed and corrected.')).toBeInTheDocument();
  });
});
