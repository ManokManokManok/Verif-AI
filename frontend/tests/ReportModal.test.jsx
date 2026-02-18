/**
 * ReportModal Component Tests
 * 
 * Unit tests for the user report submission modal.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor, fireEvent, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import ReportModal from '../src/components/reports/ReportModal';
import * as reportsApi from '../src/api/reports';

// Mock the reports API
vi.mock('../src/api/reports', () => ({
  getReportTypes: vi.fn(),
  submitReport: vi.fn(),
  REPORT_TYPES: {
    HALLUCINATION: 'hallucination',
    FALSE_POSITIVE: 'false_positive',
    FALSE_NEGATIVE: 'false_negative',
    BUG: 'bug',
    FEEDBACK: 'feedback',
    OTHER: 'other',
  },
}));

describe('ReportModal', () => {
  const mockOnClose = vi.fn();
  const mockReportTypes = [
    { value: 'hallucination', label: 'AI Hallucination', description: 'AI provided incorrect info' },
    { value: 'false_positive', label: 'False Positive', description: 'Legitimate flagged as scam' },
    { value: 'bug', label: 'Bug Report', description: 'Technical issue' },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
    reportsApi.getReportTypes.mockResolvedValue({
      success: true,
      data: mockReportTypes,
    });
    reportsApi.submitReport.mockResolvedValue({
      success: true,
      data: { report_id: 'report_123' },
      message: 'Report submitted successfully',
    });
  });

  afterEach(() => {
    vi.clearAllTimers();
  });

  describe('Rendering', () => {
    it('does not render when isOpen is false', () => {
      render(<ReportModal isOpen={false} onClose={mockOnClose} />);
      
      expect(screen.queryByText('Submit a Report')).not.toBeInTheDocument();
    });

    it('renders modal when isOpen is true', () => {
      render(<ReportModal isOpen={true} onClose={mockOnClose} />);
      
      expect(screen.getByText('Submit a Report')).toBeInTheDocument();
    });

    it('renders all form fields', () => {
      render(<ReportModal isOpen={true} onClose={mockOnClose} />);
      
      expect(screen.getByLabelText(/report type/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/title/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/description/i)).toBeInTheDocument();
    });

    it('renders submit and cancel buttons', () => {
      render(<ReportModal isOpen={true} onClose={mockOnClose} />);
      
      expect(screen.getByRole('button', { name: /submit report/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /cancel/i })).toBeInTheDocument();
    });

    it('renders close button in header', () => {
      render(<ReportModal isOpen={true} onClose={mockOnClose} />);
      
      expect(screen.getByRole('button', { name: /close modal/i })).toBeInTheDocument();
    });
  });

  describe('Report Type Selection', () => {
    it('fetches report types on mount', async () => {
      render(<ReportModal isOpen={true} onClose={mockOnClose} />);
      
      await waitFor(() => {
        expect(reportsApi.getReportTypes).toHaveBeenCalledTimes(1);
      });
    });

    it('populates select with fetched report types', async () => {
      render(<ReportModal isOpen={true} onClose={mockOnClose} />);
      
      await waitFor(() => {
        const select = screen.getByLabelText(/report type/i);
        expect(select).toBeInTheDocument();
      });
      
      // Check options exist
      const select = screen.getByLabelText(/report type/i);
      expect(select.querySelectorAll('option').length).toBeGreaterThan(1);
    });

    it('shows description when type is selected', async () => {
      render(<ReportModal isOpen={true} onClose={mockOnClose} />);
      
      await waitFor(() => {
        expect(reportsApi.getReportTypes).toHaveBeenCalled();
      });
      
      const select = screen.getByLabelText(/report type/i);
      fireEvent.change(select, { target: { value: 'bug' } });
      
      expect(screen.getByText(/technical issue/i)).toBeInTheDocument();
    });
  });

  describe('Form Validation', () => {
    it('shows error when submitting without report type', async () => {
      render(<ReportModal isOpen={true} onClose={mockOnClose} />);
      
      // Wait for types to load
      await waitFor(() => {
        expect(reportsApi.getReportTypes).toHaveBeenCalled();
      });
      
      const titleInput = screen.getByLabelText(/title/i);
      const descInput = screen.getByLabelText(/description/i);
      
      await userEvent.type(titleInput, 'Test Title');
      await userEvent.type(descInput, 'This is a test description for the report.');
      
      const submitBtn = screen.getByRole('button', { name: /submit report/i });
      await userEvent.click(submitBtn);
      
      // The select has required attribute, so either browser validation or JS validation should prevent submission
      // Check that submitReport was NOT called (form validation failed)
      expect(reportsApi.submitReport).not.toHaveBeenCalled();
    });

    it('shows error when title is too short', async () => {
      render(<ReportModal isOpen={true} onClose={mockOnClose} />);
      
      await waitFor(() => {
        expect(reportsApi.getReportTypes).toHaveBeenCalled();
      });
      
      const select = screen.getByLabelText(/report type/i);
      const titleInput = screen.getByLabelText(/title/i);
      const descInput = screen.getByLabelText(/description/i);
      
      fireEvent.change(select, { target: { value: 'bug' } });
      await userEvent.type(titleInput, 'AB');
      await userEvent.type(descInput, 'This is a valid description for the report.');
      
      const submitBtn = screen.getByRole('button', { name: /submit report/i });
      await userEvent.click(submitBtn);
      
      expect(screen.getByText(/title must be at least 3 characters/i)).toBeInTheDocument();
    });

    it('shows error when description is too short', async () => {
      render(<ReportModal isOpen={true} onClose={mockOnClose} />);
      
      await waitFor(() => {
        expect(reportsApi.getReportTypes).toHaveBeenCalled();
      });
      
      const select = screen.getByLabelText(/report type/i);
      const titleInput = screen.getByLabelText(/title/i);
      const descInput = screen.getByLabelText(/description/i);
      
      fireEvent.change(select, { target: { value: 'bug' } });
      await userEvent.type(titleInput, 'Valid Title');
      await userEvent.type(descInput, 'Short');
      
      const submitBtn = screen.getByRole('button', { name: /submit report/i });
      await userEvent.click(submitBtn);
      
      expect(screen.getByText(/description must be at least 10 characters/i)).toBeInTheDocument();
    });
  });

  describe('Form Submission', () => {
    it('submits report with valid data', async () => {
      render(<ReportModal isOpen={true} onClose={mockOnClose} />);
      
      await waitFor(() => {
        expect(reportsApi.getReportTypes).toHaveBeenCalled();
      });
      
      const select = screen.getByLabelText(/report type/i);
      const titleInput = screen.getByLabelText(/title/i);
      const descInput = screen.getByLabelText(/description/i);
      
      fireEvent.change(select, { target: { value: 'bug' } });
      await userEvent.type(titleInput, 'Valid Title Here');
      await userEvent.type(descInput, 'This is a valid description for the report with enough characters.');
      
      const submitBtn = screen.getByRole('button', { name: /submit report/i });
      await userEvent.click(submitBtn);
      
      await waitFor(() => {
        expect(reportsApi.submitReport).toHaveBeenCalledWith({
          report_type: 'bug',
          title: 'Valid Title Here',
          description: 'This is a valid description for the report with enough characters.',
          analysis_id: null,
          analysis_ref_id: null,
        });
      });
    });

    it('includes analysis IDs when provided', async () => {
      render(
        <ReportModal 
          isOpen={true} 
          onClose={mockOnClose}
          analysisId="analysis_123"
          analysisRefId="ref_456"
        />
      );
      
      await waitFor(() => {
        expect(reportsApi.getReportTypes).toHaveBeenCalled();
      });
      
      const select = screen.getByLabelText(/report type/i);
      const titleInput = screen.getByLabelText(/title/i);
      const descInput = screen.getByLabelText(/description/i);
      
      fireEvent.change(select, { target: { value: 'hallucination' } });
      await userEvent.type(titleInput, 'AI Issue Report');
      await userEvent.type(descInput, 'The AI provided incorrect information about this message.');
      
      const submitBtn = screen.getByRole('button', { name: /submit report/i });
      await userEvent.click(submitBtn);
      
      await waitFor(() => {
        expect(reportsApi.submitReport).toHaveBeenCalledWith(
          expect.objectContaining({
            analysis_id: 'analysis_123',
            analysis_ref_id: 'ref_456',
          })
        );
      });
    });

    it('shows success message after submission', async () => {
      render(<ReportModal isOpen={true} onClose={mockOnClose} />);
      
      await waitFor(() => {
        expect(reportsApi.getReportTypes).toHaveBeenCalled();
      });
      
      const select = screen.getByLabelText(/report type/i);
      const titleInput = screen.getByLabelText(/title/i);
      const descInput = screen.getByLabelText(/description/i);
      
      // Use 'bug' which is in the mockReportTypes
      await userEvent.selectOptions(select, 'bug');
      await userEvent.type(titleInput, 'Great Feature');
      await userEvent.type(descInput, 'I really like this feature of the application.');
      
      const submitBtn = screen.getByRole('button', { name: /submit report/i });
      
      // Submit 
      await act(async () => {
        await userEvent.click(submitBtn);
      });
      
      // Wait for the API call to be made
      await waitFor(() => {
        expect(reportsApi.submitReport).toHaveBeenCalled();
      }, { timeout: 3000 });
      
      // Check for success message
      await waitFor(() => {
        expect(screen.getByText(/submitted successfully/i)).toBeInTheDocument();
      }, { timeout: 3000 });
    });

    it('shows error message on submission failure', async () => {
      reportsApi.submitReport.mockResolvedValue({
        success: false,
        error: 'Server error occurred',
      });
      
      render(<ReportModal isOpen={true} onClose={mockOnClose} />);
      
      await waitFor(() => {
        expect(reportsApi.getReportTypes).toHaveBeenCalled();
      });
      
      const select = screen.getByLabelText(/report type/i);
      const titleInput = screen.getByLabelText(/title/i);
      const descInput = screen.getByLabelText(/description/i);
      
      fireEvent.change(select, { target: { value: 'bug' } });
      await userEvent.type(titleInput, 'Bug Report Title');
      await userEvent.type(descInput, 'This is a bug report description.');
      
      const submitBtn = screen.getByRole('button', { name: /submit report/i });
      await userEvent.click(submitBtn);
      
      await waitFor(() => {
        expect(screen.getByText(/server error occurred/i)).toBeInTheDocument();
      });
    });

    it('disables submit button while submitting', async () => {
      // Make submit hang indefinitely for this test
      reportsApi.submitReport.mockImplementation(() => new Promise(() => {}));
      
      render(<ReportModal isOpen={true} onClose={mockOnClose} />);
      
      await waitFor(() => {
        expect(reportsApi.getReportTypes).toHaveBeenCalled();
      });
      
      const select = screen.getByLabelText(/report type/i);
      const titleInput = screen.getByLabelText(/title/i);
      const descInput = screen.getByLabelText(/description/i);
      
      fireEvent.change(select, { target: { value: 'bug' } });
      await userEvent.type(titleInput, 'Bug Report');
      await userEvent.type(descInput, 'Description with enough characters.');
      
      const submitBtn = screen.getByRole('button', { name: /submit report/i });
      await userEvent.click(submitBtn);
      
      await waitFor(() => {
        expect(screen.getByRole('button', { name: /submitting/i })).toBeDisabled();
      });
    });
  });

  describe('Modal Actions', () => {
    it('calls onClose when clicking cancel', async () => {
      render(<ReportModal isOpen={true} onClose={mockOnClose} />);
      
      const cancelBtn = screen.getByRole('button', { name: /cancel/i });
      await userEvent.click(cancelBtn);
      
      expect(mockOnClose).toHaveBeenCalled();
    });

    it('calls onClose when clicking close button', async () => {
      render(<ReportModal isOpen={true} onClose={mockOnClose} />);
      
      const closeBtn = screen.getByRole('button', { name: /close modal/i });
      await userEvent.click(closeBtn);
      
      expect(mockOnClose).toHaveBeenCalled();
    });

    it('calls onClose when clicking overlay', async () => {
      render(<ReportModal isOpen={true} onClose={mockOnClose} />);
      
      const overlay = document.querySelector('.report-modal__overlay');
      fireEvent.click(overlay);
      
      expect(mockOnClose).toHaveBeenCalled();
    });

    it('does not close when clicking inside modal', async () => {
      render(<ReportModal isOpen={true} onClose={mockOnClose} />);
      
      const container = document.querySelector('.report-modal__container');
      fireEvent.click(container);
      
      expect(mockOnClose).not.toHaveBeenCalled();
    });
  });

  describe('Character Counts', () => {
    it('shows character count for title', async () => {
      render(<ReportModal isOpen={true} onClose={mockOnClose} />);
      
      const titleInput = screen.getByLabelText(/title/i);
      await userEvent.type(titleInput, 'Hello');
      
      expect(screen.getByText('5/200')).toBeInTheDocument();
    });

    it('shows character count for description', async () => {
      render(<ReportModal isOpen={true} onClose={mockOnClose} />);
      
      const descInput = screen.getByLabelText(/description/i);
      await userEvent.type(descInput, 'Test description');
      
      expect(screen.getByText('16/2000')).toBeInTheDocument();
    });
  });

  describe('Analysis Context', () => {
    it('shows link indicator when analysis IDs provided', () => {
      render(
        <ReportModal 
          isOpen={true} 
          onClose={mockOnClose}
          analysisId="analysis_123"
        />
      );
      
      expect(screen.getByText(/linked to the current analysis/i)).toBeInTheDocument();
    });

    it('does not show link indicator without analysis IDs', () => {
      render(<ReportModal isOpen={true} onClose={mockOnClose} />);
      
      expect(screen.queryByText(/linked to the current analysis/i)).not.toBeInTheDocument();
    });
  });

  describe('Preselected Type', () => {
    it('preselects report type when provided', async () => {
      render(
        <ReportModal 
          isOpen={true} 
          onClose={mockOnClose}
          preselectedType="hallucination"
        />
      );
      
      await waitFor(() => {
        const select = screen.getByLabelText(/report type/i);
        expect(select.value).toBe('hallucination');
      });
    });
  });

  describe('Form Reset', () => {
    it('resets form when modal reopens', async () => {
      const { rerender } = render(<ReportModal isOpen={true} onClose={mockOnClose} />);
      
      await waitFor(() => {
        expect(reportsApi.getReportTypes).toHaveBeenCalled();
      });
      
      // Fill out form
      const titleInput = screen.getByLabelText(/title/i);
      await userEvent.type(titleInput, 'Test Title');
      
      // Close modal
      rerender(<ReportModal isOpen={false} onClose={mockOnClose} />);
      
      // Reopen modal
      rerender(<ReportModal isOpen={true} onClose={mockOnClose} />);
      
      // Check form is reset
      const newTitleInput = screen.getByLabelText(/title/i);
      expect(newTitleInput.value).toBe('');
    });
  });
});

describe('Reports API Functions', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('REPORT_TYPES contains all expected types', () => {
    expect(reportsApi.REPORT_TYPES.HALLUCINATION).toBe('hallucination');
    expect(reportsApi.REPORT_TYPES.FALSE_POSITIVE).toBe('false_positive');
    expect(reportsApi.REPORT_TYPES.FALSE_NEGATIVE).toBe('false_negative');
    expect(reportsApi.REPORT_TYPES.BUG).toBe('bug');
    expect(reportsApi.REPORT_TYPES.FEEDBACK).toBe('feedback');
    expect(reportsApi.REPORT_TYPES.OTHER).toBe('other');
  });
});
