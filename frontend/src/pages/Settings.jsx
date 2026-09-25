import { useState, useEffect, useMemo } from 'react';
import './Settings.css';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';
import {
  changePasswordRequest,
  deleteAccountRequest,
  sendPasswordChangeCodeRequest,
  updateUsernameRequest,
} from '../api/client';
import { getMyReports, getReportTypeLabel, getReportStatusLabel } from '../api/reports';
import { getAnalysisDetail } from '../api/analysis';
import { getPasswordRequirements, validatePassword, validateUsername, CONSTRAINTS } from '../utils/validation';

export default function Settings() {
  const navigate = useNavigate();
  const { user, isLoggedIn, logout, refreshUser, accessToken } = useAuth();
  const { theme, toggleTheme, fontScale, setFontScale } = useTheme();

  // Navigation tab state
  const [activeTab, setActiveTab] = useState('account'); // 'account' | 'reports' | 'danger'

  // Username update state
  const [newUsername, setNewUsername] = useState('');
  const [usernameError, setUsernameError] = useState('');
  const [usernameSuccess, setUsernameSuccess] = useState('');
  const [usernameLoading, setUsernameLoading] = useState(false);
  const [showUsernameChange, setShowUsernameChange] = useState(false);
  const [usernamePassword, setUsernamePassword] = useState('');
  const [showUsernamePassword, setShowUsernamePassword] = useState(false);

  // Password change state
  const [showPasswordChange, setShowPasswordChange] = useState(false);
  const [passwordCode, setPasswordCode] = useState('');
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [passwordMessage, setPasswordMessage] = useState('');
  const [passwordError, setPasswordError] = useState('');
  const [codeLoading, setCodeLoading] = useState(false);
  const [passwordLoading, setPasswordLoading] = useState(false);
  const [codeCooldown, setCodeCooldown] = useState(0);
  const [visiblePasswords, setVisiblePasswords] = useState({});

  // Delete account state
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [deletePassword, setDeletePassword] = useState('');
  const [showDeletePassword, setShowDeletePassword] = useState(false);
  const [deleteError, setDeleteError] = useState('');
  const [deleteLoading, setDeleteLoading] = useState(false);

  // User reports state
  const [reports, setReports] = useState([]);
  const [reportsLoading, setReportsLoading] = useState(true);
  const [reportsError, setReportsError] = useState('');
  const [reportFilter, setReportFilter] = useState('all');
  const [selectedReport, setSelectedReport] = useState(null);
  const [navigatingAnalysisId, setNavigatingAnalysisId] = useState(null);

  useEffect(() => {
    if (!isLoggedIn) navigate('/login', { replace: true });
  }, [isLoggedIn, navigate]);

  useEffect(() => {
    if (isLoggedIn) {
      const fetchReports = async () => {
        try {
          const response = await getMyReports({ limit: 50 });
          if (response.success && response.data) {
            setReports(response.data.reports || []);
          }
        } catch (err) {
          setReportsError(err.message || 'Failed to load reports');
        } finally {
          setReportsLoading(false);
        }
      };
      fetchReports();
    }
  }, [isLoggedIn]);

  useEffect(() => {
    if (user?.username) setNewUsername(user.username);
  }, [user?.username]);

  useEffect(() => {
    if (codeCooldown <= 0) return undefined;
    const timer = window.setInterval(() => {
      setCodeCooldown((seconds) => Math.max(0, seconds - 1));
    }, 1000);
    return () => window.clearInterval(timer);
  }, [codeCooldown]);

  // Real-time username validation
  useEffect(() => {
    if (!newUsername || newUsername === user?.username) {
      setUsernameError('');
      return;
    }
    const result = validateUsername(newUsername);
    setUsernameError(result.valid ? '' : result.error || '');
  }, [newUsername, user?.username]);

  const handleUsernameUpdate = async (e) => {
    e.preventDefault();
    setUsernameSuccess('');
    setUsernameError('');

    const trimmed = newUsername.trim();
    if (!usernamePassword) {
      setUsernameError('Enter your current password to continue.');
      return;
    }

    if (trimmed === user?.username) {
      setUsernameError('Username is the same as your current one.');
      return;
    }

    const result = validateUsername(trimmed);
    if (!result.valid) {
      setUsernameError(result.error || 'Invalid username.');
      return;
    }

    setUsernameLoading(true);
    try {
      await updateUsernameRequest({ username: trimmed, currentPassword: usernamePassword });
      refreshUser();
      setUsernameSuccess('Username updated successfully.');
      setUsernamePassword('');
      setShowUsernameChange(false);
    } catch (err) {
      setUsernameError(err.message || 'Failed to update username.');
    } finally {
      setUsernameLoading(false);
    }
  };

  const handleSendPasswordCode = async () => {
    if (codeCooldown > 0) return;
    setPasswordError('');
    setPasswordMessage('');
    setCodeLoading(true);
    try {
      await sendPasswordChangeCodeRequest();
      setPasswordMessage(`A verification code was sent to ${user.email}.`);
      setCodeCooldown(60);
    } catch (err) {
      const retryAfter = err.payload?.error?.retry_after_seconds || err.retryAfter;
      if (retryAfter) setCodeCooldown(Number(retryAfter));
      setPasswordError(err.message || 'Failed to send verification code.');
    } finally {
      setCodeLoading(false);
    }
  };

  const handlePasswordChange = async (e) => {
    e.preventDefault();
    setPasswordError('');
    setPasswordMessage('');

    if (!passwordCode || !currentPassword) {
      setPasswordError('Verification code and current password are required.');
      return;
    }
    if (newPassword !== confirmPassword) {
      setPasswordError('New passwords do not match.');
      return;
    }

    const validation = validatePassword(newPassword);
    if (!validation.valid) {
      setPasswordError(validation.errors.join('. '));
      return;
    }

    setPasswordLoading(true);
    try {
      await changePasswordRequest({
        code: passwordCode,
        current_password: currentPassword,
        new_password: newPassword,
        confirm_password: confirmPassword,
      });
      setPasswordMessage('Password changed successfully.');
      setPasswordCode('');
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
      setCodeCooldown(0);
      setShowPasswordChange(false);
    } catch (err) {
      setPasswordError(err.message || 'Failed to change password.');
    } finally {
      setPasswordLoading(false);
    }
  };

  const handleDeleteAccount = async (e) => {
    e.preventDefault();
    setDeleteError('');

    if (!deletePassword) {
      setDeleteError('Please enter your password to confirm.');
      return;
    }

    setDeleteLoading(true);
    try {
      await deleteAccountRequest({ password: deletePassword });
      await logout();
      navigate('/', { replace: true });
    } catch (err) {
      setDeleteError(err.message || 'Failed to delete account.');
    } finally {
      setDeleteLoading(false);
    }
  };

  // Open Detection Analysis Result for a reported item
  const handleOpenReportAnalysis = async (report, e) => {
    if (e) e.stopPropagation();
    const targetId = report.id || report.report_id;
    const refId = report.analysis_ref_id || report.analysis_id;

    if (!refId) {
      navigate('/detection');
      return;
    }

    setNavigatingAnalysisId(targetId);
    try {
      const detail = await getAnalysisDetail(refId);
      if (detail) {
        navigate('/detection', {
          state: {
            analysisId: refId,
            analysisDetail: detail,
          },
        });
        return;
      }
    } catch (err) {
      console.warn('Could not fetch analysis detail directly, fallback to detection page:', err);
      navigate('/detection', {
        state: {
          analysisId: refId,
          analysisRefId: refId,
        },
      });
      return;
    } finally {
      setNavigatingAnalysisId(null);
    }

    navigate('/detection');
  };

  // Filter reports
  const filteredReports = useMemo(() => {
    if (reportFilter === 'all') return reports;
    return reports.filter((r) => r.status === reportFilter);
  }, [reports, reportFilter]);

  // Report statistics
  const reportStats = useMemo(() => {
    const total = reports.length;
    const pending = reports.filter((r) => r.status === 'pending').length;
    const inProgress = reports.filter((r) => r.status === 'in_progress').length;
    const resolved = reports.filter((r) => r.status === 'resolved').length;
    return { total, pending, inProgress, resolved };
  }, [reports]);

  if (!user) return null;

  const usernameChanged = newUsername.trim() !== (user?.username || '');
  const passwordRequirements = getPasswordRequirements(newPassword);
  const newPasswordValid = passwordRequirements.every((requirement) => requirement.met);
  const userInitial = (user.username || user.email || 'U').charAt(0).toUpperCase();

  return (
    <div className="settings-page page-enter">
      {/* Top Header & User Profile Bar */}
      <header className="settings-header">
        <button
          className="settings-header__back"
          type="button"
          onClick={() => navigate(-1)}
          aria-label="Go back"
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <line x1="19" y1="12" x2="5" y2="12"></line>
            <polyline points="12 19 5 12 12 5"></polyline>
          </svg>
          <span>Back</span>
        </button>

        <div className="settings-header__profile">
          <div className="settings-header__avatar">
            <span>{userInitial}</span>
          </div>
          <div className="settings-header__info">
            <h1 className="settings-header__title">{user.username || 'Account Settings'}</h1>
            <div className="settings-header__meta">
              <span className="settings-header__email">{user.email}</span>
              <span className="settings-header__badge">
                <span className="settings-header__dot"></span>
                Active Account
              </span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Settings Body Container */}
      <div className="settings-container">
        {/* Left / Top Section Navigation */}
        <nav className="settings-nav" aria-label="Settings categories">
          <button
            type="button"
            className={`settings-nav__item ${activeTab === 'account' ? 'settings-nav__item--active' : ''}`}
            onClick={() => setActiveTab('account')}
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
              <circle cx="12" cy="7" r="4"></circle>
            </svg>
            <span>Account &amp; Security</span>
          </button>

          <button
            type="button"
            className={`settings-nav__item ${activeTab === 'reports' ? 'settings-nav__item--active' : ''}`}
            onClick={() => setActiveTab('reports')}
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
              <polyline points="14 2 14 8 20 8"></polyline>
              <line x1="16" y1="13" x2="8" y2="13"></line>
              <line x1="16" y1="17" x2="8" y2="17"></line>
              <polyline points="10 9 9 9 8 9"></polyline>
            </svg>
            <span>Submitted Reports</span>
            {reports.length > 0 && (
              <span className="settings-nav__counter">{reports.length}</span>
            )}
          </button>

          <button
            type="button"
            className={`settings-nav__item ${activeTab === 'privacy' ? 'settings-nav__item--active' : ''}`}
            onClick={() => setActiveTab('privacy')}
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 3a9 9 0 0 0-9 9c0 4.97 4.03 9 9 9h1a2 2 0 0 0 2-2v-1a2 2 0 0 1 2-2h1a2 2 0 0 0 2-2v-2a9 9 0 0 0-9-9z"></path>
              <circle cx="7.5" cy="12" r="1"></circle>
              <circle cx="12" cy="7.5" r="1"></circle>
              <circle cx="16.5" cy="12" r="1"></circle>
            </svg>
            <span>Privacy &amp; Support</span>
          </button>
        </nav>

        {/* Content Panels */}
        <main className={`settings-content ${activeTab === 'account' ? 'settings-content--account' : ''}`}>
          {/* TAB 1: Account & Security */}
          {(activeTab === 'account' || activeTab === 'privacy') && (
            <div className={`settings-panel ${activeTab === 'account' ? 'settings-account-panel' : 'page-enter'}`}>
              <div className="settings-panel__header">
                <h2 className="settings-panel__title">
                  {activeTab === 'account' ? 'Account & Security' : 'Privacy & Support'}
                </h2>
                <p className="settings-panel__subtitle">
                  {activeTab === 'account'
                    ? 'Manage your account details, sign-in security, and account protection.'
                    : 'Review how your data is managed and find important support resources.'}
                </p>
              </div>

              {activeTab === 'account' && (
                <>
              {/* Email Section Card */}
              <div className="settings-card settings-account-card settings-account-card--email">
                <div className="settings-card__header">
                  <h3 className="settings-card__title">Email Address</h3>
                  <span className="settings-tag settings-tag--locked">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect>
                      <path d="M7 11V7a5 5 0 0 1 10 0v4"></path>
                    </svg>
                    Primary & Verified
                  </span>
                </div>
                <div className="settings-field">
                  <label className="settings-field__label" htmlFor="settings-email">Email Address</label>
                  <div className="settings-input-wrapper">
                    <input
                      id="settings-email"
                      className="settings-input settings-input--readonly"
                      type="email"
                      value={user.email || ''}
                      readOnly
                      disabled
                    />
                  </div>
                  <p className="settings-field__hint">
                    Your email address is linked to your authentication account and cannot be changed here.
                  </p>
                </div>
              </div>

              {/* Username Update Section Card */}
              <div className="settings-card settings-account-card settings-account-card--username">
                <div className="settings-card__header">
                  <h3 className="settings-card__title">Username</h3>
                </div>

                <div className="settings-username-summary">
                  <div className="settings-username-summary__identity">
                    <span className="settings-field__label">Current username</span>
                    <strong className="settings-username-summary__value">{user.username || 'Not set'}</strong>
                  </div>
                  <button
                    className="settings-username-summary__action"
                    type="button"
                    onClick={() => {
                      setUsernameError('');
                      setUsernameSuccess('');
                      setNewUsername(user.username || '');
                      setUsernamePassword('');
                      setShowUsernameChange(true);
                    }}
                  >
                    Change username
                  </button>
                </div>
                {usernameSuccess && (
                  <div className="settings-message settings-message--success">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <polyline points="20 6 9 17 4 12"></polyline>
                    </svg>
                    <span>{usernameSuccess}</span>
                  </div>
                )}
              </div>
                </>
              )}

              <div className="settings-feature-grid">
                {activeTab === 'account' && (
                <section className="settings-feature-section">
                  <div className="settings-feature-section__header">
                    <div>
                      <h3 className="settings-feature-section__title">Security</h3>
                      <p className="settings-feature-section__description">
                        Keep your account protected and manage sign-in options.
                      </p>
                    </div>
                  </div>
                  <div className="settings-feature-list">
                    <button
                      className="settings-feature-item"
                      type="button"
                      onClick={() => {
                        setPasswordError('');
                        setPasswordMessage('');
                        setShowPasswordChange(true);
                      }}
                    >
                      <span>
                        <strong>Change password</strong>
                        <small>Verify your email and current password before choosing a new one.</small>
                      </span>
                      <span className="settings-feature-item__arrow" aria-hidden="true">&rarr;</span>
                    </button>
                    <button className="settings-feature-item" type="button" disabled>
                      <span>
                        <strong>Two-factor authentication</strong>
                        <small>Add another layer of protection to your account.</small>
                      </span>
                      <span className="settings-feature-item__action">Coming soon</span>
                    </button>
                  </div>
                </section>
                )}

                {activeTab === 'privacy' && (
                <>
                  <section className="settings-feature-section settings-appearance-section">
                    <div className="settings-feature-section__header">
                      <div>
                        <h3 className="settings-feature-section__title">Appearance</h3>
                        <p className="settings-feature-section__description">
                          Adjust how VerifAI looks and reads across every page.
                        </p>
                      </div>
                    </div>
                    <div className="settings-appearance-controls">
                      <div className="settings-preference-row">
                        <div className="settings-preference-copy">
                          <strong>Theme</strong>
                          <small>{theme === 'dark' ? 'Dark mode' : 'Light mode'} is saved on this device.</small>
                        </div>
                        <button
                          className={`settings-theme-switch${theme === 'light' ? ' settings-theme-switch--light' : ''}`}
                          type="button"
                          role="switch"
                          aria-checked={theme === 'light'}
                          aria-label={`Theme: ${theme === 'dark' ? 'dark mode enabled' : 'light mode enabled'}. Activate to switch to ${theme === 'dark' ? 'light' : 'dark'} mode.`}
                          onClick={toggleTheme}
                        >
                          <span aria-hidden="true" />
                        </button>
                      </div>
                      <div className="settings-preference-row settings-preference-row--font">
                        <div className="settings-preference-copy">
                          <strong>Text size</strong>
                          <small>Scale interface text without changing your layout.</small>
                        </div>
                        <div className="settings-font-control">
                          <output htmlFor="settings-font-scale">{fontScale}%</output>
                          <input
                            id="settings-font-scale"
                            type="range"
                            min="90"
                            max="120"
                            step="10"
                            value={fontScale}
                            onChange={(event) => setFontScale(Number(event.target.value))}
                            aria-label="Global text size"
                          />
                          <div className="settings-font-scale-labels" aria-hidden="true"><span>A</span><span>A</span><span>A</span><span>A</span></div>
                        </div>
                      </div>
                    </div>
                  </section>

                  <section className="settings-feature-section">
                  <div className="settings-feature-section__header">
                    <div>
                      <h3 className="settings-feature-section__title">Privacy &amp; Data</h3>
                      <p className="settings-feature-section__description">
                        Review how your analyses and account data are managed.
                      </p>
                    </div>
                  </div>
                  <div className="settings-feature-list">
                    <button className="settings-feature-item" type="button" disabled>
                      <span>
                        <strong>Download your data</strong>
                        <small>Request a copy of your VerfAi account data.</small>
                      </span>
                      <span className="settings-feature-item__action">Coming soon</span>
                    </button>
                    <button className="settings-feature-item" type="button" disabled>
                      <span>
                        <strong>Analysis history</strong>
                        <small>Manage how long your submitted analyses are retained.</small>
                      </span>
                      <span className="settings-feature-item__action">Coming soon</span>
                    </button>
                  </div>
                  </section>

                  <section className="settings-feature-section">
                  <div className="settings-feature-section__header">
                    <div>
                      <h3 className="settings-feature-section__title">Support &amp; Legal</h3>
                      <p className="settings-feature-section__description">
                        Find help and review the documents that govern VerfAi.
                      </p>
                    </div>
                  </div>
                  <div className="settings-feature-list">
                    <button className="settings-feature-item" type="button" onClick={() => navigate('/terms-and-conditions')}>
                      <span>
                        <strong>Terms and Conditions</strong>
                        <small>Review the terms for using VerfAi.</small>
                      </span>
                      <span className="settings-feature-item__arrow" aria-hidden="true">&rarr;</span>
                    </button>
                    <button className="settings-feature-item" type="button" disabled>
                      <span>
                        <strong>Help and contact support</strong>
                        <small>Get assistance with your account or an analysis.</small>
                      </span>
                      <span className="settings-tag settings-tag--coming">Coming soon</span>
                    </button>
                  </div>
                  </section>
                </>
                )}
              </div>
            </div>
          )}

          {/* TAB 2: Submitted Reports Tracker */}
          {activeTab === 'reports' && (
            <div className="settings-panel page-enter">
              <div className="settings-panel__header">
                <h2 className="settings-panel__title">My Submitted Reports</h2>
                <p className="settings-panel__subtitle">
                  Track and inspect the status of issues or feedback you have submitted.
                </p>
              </div>

              {/* Reports Analytics Summary Pill Bar */}
              <div className="settings-reports-stats">
                <div className="settings-stat-pill">
                  <span className="settings-stat-pill__label">Total Reports</span>
                  <strong className="settings-stat-pill__value">{reportStats.total}</strong>
                </div>
                <div className="settings-stat-pill settings-stat-pill--warning">
                  <span className="settings-stat-pill__label">Pending</span>
                  <strong className="settings-stat-pill__value">{reportStats.pending}</strong>
                </div>
                <div className="settings-stat-pill settings-stat-pill--info">
                  <span className="settings-stat-pill__label">In Progress</span>
                  <strong className="settings-stat-pill__value">{reportStats.inProgress}</strong>
                </div>
                <div className="settings-stat-pill settings-stat-pill--success">
                  <span className="settings-stat-pill__label">Resolved</span>
                  <strong className="settings-stat-pill__value">{reportStats.resolved}</strong>
                </div>
              </div>

              {/* Reports Filter Controls */}
              <div className="settings-reports-filter">
                <span className="settings-reports-filter__label">Filter Status:</span>
                <div className="settings-filter-pills">
                  {['all', 'pending', 'in_progress', 'resolved', 'dismissed'].map((statusKey) => (
                    <button
                      key={statusKey}
                      type="button"
                      className={`settings-filter-btn ${reportFilter === statusKey ? 'settings-filter-btn--active' : ''}`}
                      onClick={() => setReportFilter(statusKey)}
                    >
                      {statusKey === 'all' ? 'All Reports' : getReportStatusLabel(statusKey)}
                    </button>
                  ))}
                </div>
              </div>

              {/* Reports List */}
              <div className="settings-card settings-card--reports">
                {reportsLoading ? (
                  <div className="settings-state">
                    <span className="settings-spinner settings-spinner--lg"></span>
                    <p>Loading your submitted reports...</p>
                  </div>
                ) : reportsError ? (
                  <div className="settings-state settings-state--error">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <circle cx="12" cy="12" r="10"></circle>
                      <line x1="12" y1="8" x2="12" y2="12"></line>
                      <line x1="12" y1="16" x2="12.01" y2="16"></line>
                    </svg>
                    <p>{reportsError}</p>
                  </div>
                ) : filteredReports.length === 0 ? (
                  <div className="settings-state settings-state--empty">
                    <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                      <polyline points="14 2 14 8 20 8"></polyline>
                      <line x1="12" y1="18" x2="12.01" y2="18"></line>
                      <line x1="12" y1="13" x2="12" y2="13"></line>
                    </svg>
                    <p>
                      {reportFilter === 'all'
                        ? "You haven't submitted any reports yet."
                        : `No reports matching "${getReportStatusLabel(reportFilter)}".`}
                    </p>
                  </div>
                ) : (
                  <div className="settings-reports-list">
                    {filteredReports.map((report) => {
                      const reportId = report.id || report.report_id;
                      const isNavigatingAnalysisThis = navigatingAnalysisId === reportId;
                      const hasRefId = Boolean(report.analysis_ref_id || report.analysis_id);

                      return (
                        <div
                          key={reportId}
                          className="settings-report-item"
                          onClick={() => setSelectedReport(report)}
                        >
                          <div className="settings-report-item__top">
                            <h4 className="settings-report-item__title">
                              {report.title || 'Untitled Report'}
                            </h4>
                            <span className={`settings-status-badge settings-status-badge--${report.status}`}>
                              {getReportStatusLabel(report.status)}
                            </span>
                          </div>

                          <div className="settings-report-item__meta">
                            <span className="settings-report-item__type">
                              {getReportTypeLabel(report.report_type)}
                            </span>
                            <span className="settings-report-item__bullet">•</span>
                            <span className="settings-report-item__date">
                              {new Date(report.created_at).toLocaleDateString(undefined, {
                                year: 'numeric',
                                month: 'short',
                                day: 'numeric',
                              })}
                            </span>
                          </div>

                          {report.description && (
                            <p className="settings-report-item__desc">
                              {report.description.length > 120
                                ? `${report.description.substring(0, 120)}...`
                                : report.description}
                            </p>
                          )}

                          <div className="settings-report-item__footer">
                            <div className="settings-report-item__actions">
                              {hasRefId && (
                                <button
                                  type="button"
                                  className="settings-report-item__action-btn settings-report-item__action-btn--analysis"
                                  onClick={(e) => handleOpenReportAnalysis(report, e)}
                                  disabled={isNavigatingAnalysisThis}
                                  title="Go to Detection Analysis Result for this report"
                                >
                                  {isNavigatingAnalysisThis ? (
                                    <>
                                      <span className="settings-spinner"></span>
                                      Opening Result...
                                    </>
                                  ) : (
                                    <>
                                      <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                        <circle cx="11" cy="11" r="8"></circle>
                                        <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
                                      </svg>
                                      <span>View Analysis Result</span>
                                    </>
                                  )}
                                </button>
                              )}
                            </div>
                            <span className="settings-report-item__link">View Details &rarr;</span>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Danger Zone stays separate within Account & Security. */}
          {activeTab === 'account' && (
            <div className="settings-panel settings-panel--danger">
              <div className="settings-panel__header">
                <h2 className="settings-panel__title settings-panel__title--danger">Danger Zone</h2>
                <p className="settings-panel__subtitle">
                  Irreversible and sensitive actions related to your account security and data.
                </p>
              </div>

              <div className="settings-card settings-card--danger settings-account-card settings-account-card--danger">
                <div className="settings-danger-box">
                  <div className="settings-danger-box__icon">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path>
                      <line x1="12" y1="9" x2="12" y2="13"></line>
                      <line x1="12" y1="17" x2="12.01" y2="17"></line>
                    </svg>
                  </div>
                  <div className="settings-danger-box__content">
                    <h3 className="settings-danger-box__title">Delete Account</h3>
                    <p className="settings-danger-box__desc">
                      Permanently remove your account profile, history, and all associated personal records.
                      This action is permanent and cannot be undone.
                    </p>

                    {!showDeleteConfirm ? (
                      <button
                        className="settings-btn settings-btn--danger"
                        type="button"
                        onClick={() => setShowDeleteConfirm(true)}
                      >
                        Delete My Account
                      </button>
                    ) : (
                      <form onSubmit={handleDeleteAccount} className="settings-form settings-danger-form page-enter">
                        <div className="settings-field">
                          <label className="settings-field__label" htmlFor="settings-delete-pw">
                            Enter your password to confirm deletion
                          </label>
                          <div className="settings-input-wrapper">
                            <input
                              id="settings-delete-pw"
                              className="settings-input settings-input--error"
                              type={showDeletePassword ? 'text' : 'password'}
                              value={deletePassword}
                              onChange={(e) => {
                                setDeletePassword(e.target.value);
                                setDeleteError('');
                              }}
                              autoComplete="current-password"
                              placeholder="Your current password"
                            />
                            <button
                              type="button"
                              className="settings-input-toggle"
                              onClick={() => setShowDeletePassword(!showDeletePassword)}
                              aria-label={showDeletePassword ? 'Hide password' : 'Show password'}
                            >
                              {showDeletePassword ? (
                                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                  <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path>
                                  <line x1="1" y1="1" x2="23" y2="23"></line>
                                </svg>
                              ) : (
                                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                  <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
                                  <circle cx="12" cy="12" r="3"></circle>
                                </svg>
                              )}
                            </button>
                          </div>

                          {deleteError && (
                            <div className="settings-message settings-message--error">
                              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                <circle cx="12" cy="12" r="10"></circle>
                                <line x1="12" y1="8" x2="12" y2="12"></line>
                                <line x1="12" y1="16" x2="12.01" y2="16"></line>
                              </svg>
                              <span>{deleteError}</span>
                            </div>
                          )}
                        </div>

                        <div className="settings-btn-group">
                          <button
                            className="settings-btn settings-btn--danger"
                            type="submit"
                            disabled={deleteLoading || !deletePassword}
                          >
                            {deleteLoading ? (
                              <>
                                <span className="settings-spinner"></span>
                                Deleting Account...
                              </>
                            ) : (
                              'Confirm Account Deletion'
                            )}
                          </button>
                          <button
                            className="settings-btn settings-btn--secondary"
                            type="button"
                            onClick={() => {
                              setShowDeleteConfirm(false);
                              setDeletePassword('');
                              setDeleteError('');
                            }}
                          >
                            Cancel
                          </button>
                        </div>
                      </form>
                    )}
                  </div>
                </div>
              </div>
            </div>
          )}
        </main>
      </div>

      {showPasswordChange && (
        <div className="settings-modal-overlay" onClick={() => !passwordLoading && setShowPasswordChange(false)}>
          <div className="settings-modal settings-modal--username page-enter" onClick={(e) => e.stopPropagation()}>
            <div className="settings-modal__header">
              <div>
                <span className="settings-tag settings-tag--locked">Account security</span>
                <h3 className="settings-modal__title">Change password</h3>
              </div>
              <button
                className="settings-modal__close"
                type="button"
                onClick={() => setShowPasswordChange(false)}
                disabled={passwordLoading}
                aria-label="Close password change dialog"
              >
                &times;
              </button>
            </div>

            <form className="settings-modal__body" onSubmit={handlePasswordChange}>
              <p className="settings-modal__intro">
                Send a verification code to {user.email}, then confirm your current password.
              </p>

              <div className="settings-field">
                <label className="settings-field__label" htmlFor="settings-password-code">Verification code</label>
                <div className="settings-input-wrapper">
                  <input
                    id="settings-password-code"
                    className="settings-input"
                    type="text"
                    inputMode="numeric"
                    maxLength={5}
                    value={passwordCode}
                    onChange={(e) => setPasswordCode(e.target.value.replace(/\D/g, ''))}
                    placeholder="Enter the 5-digit code"
                  />
                  <button
                    className="settings-input-toggle"
                    type="button"
                    onClick={handleSendPasswordCode}
                    disabled={codeLoading || codeCooldown > 0}
                  >
                    {codeLoading ? 'Sending...' : codeCooldown > 0 ? `${codeCooldown}s` : 'Send code'}
                  </button>
                </div>
              </div>

              <div className="settings-field">
                <label className="settings-field__label" htmlFor="settings-current-password">Current password</label>
                <div className="settings-input-wrapper">
                  <input
                    id="settings-current-password"
                    className="settings-input"
                    type={visiblePasswords.current ? 'text' : 'password'}
                    value={currentPassword}
                    onChange={(e) => setCurrentPassword(e.target.value)}
                    autoComplete="current-password"
                  />
                  <button
                    className="settings-input-toggle settings-input-toggle--text"
                    type="button"
                    onClick={() => setVisiblePasswords((current) => ({ ...current, current: !current.current }))}
                    aria-label={visiblePasswords.current ? 'Hide current password' : 'Show current password'}
                  >
                    {visiblePasswords.current ? 'Hide' : 'Show'}
                  </button>
                </div>
              </div>

              <div className="settings-field">
                <label className="settings-field__label" htmlFor="settings-new-password">New password</label>
                <div className="settings-input-wrapper">
                  <input
                    id="settings-new-password"
                    className="settings-input"
                    type={visiblePasswords.new ? 'text' : 'password'}
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    autoComplete="new-password"
                  />
                  <button
                    className="settings-input-toggle settings-input-toggle--text"
                    type="button"
                    onClick={() => setVisiblePasswords((current) => ({ ...current, new: !current.new }))}
                    aria-label={visiblePasswords.new ? 'Hide new password' : 'Show new password'}
                  >
                    {visiblePasswords.new ? 'Hide' : 'Show'}
                  </button>
                </div>
                <ul className="settings-password-requirements" aria-label="Password requirements">
                  {passwordRequirements.map((requirement) => (
                    <li className={requirement.met ? 'is-met' : ''} key={requirement.key}>
                      <span aria-hidden="true">{requirement.met ? '✓' : '○'}</span>
                      {requirement.label}
                    </li>
                  ))}
                </ul>
              </div>

              <div className="settings-field">
                <label className="settings-field__label" htmlFor="settings-confirm-password">Confirm new password</label>
                <div className="settings-input-wrapper">
                  <input
                    id="settings-confirm-password"
                    className={`settings-input ${confirmPassword && confirmPassword !== newPassword ? 'settings-input--error' : ''}`}
                    type={visiblePasswords.confirm ? 'text' : 'password'}
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    autoComplete="new-password"
                  />
                  <button
                    className="settings-input-toggle settings-input-toggle--text"
                    type="button"
                    onClick={() => setVisiblePasswords((current) => ({ ...current, confirm: !current.confirm }))}
                    aria-label={visiblePasswords.confirm ? 'Hide confirmed password' : 'Show confirmed password'}
                  >
                    {visiblePasswords.confirm ? 'Hide' : 'Show'}
                  </button>
                </div>
                {confirmPassword && confirmPassword !== newPassword && (
                  <span className="settings-field__error">Passwords do not match.</span>
                )}
              </div>

              {passwordMessage && <div className="settings-message settings-message--success"><span>{passwordMessage}</span></div>}
              {passwordError && <div className="settings-message settings-message--error"><span>{passwordError}</span></div>}

              <div className="settings-modal__actions">
                <button
                  className="settings-btn settings-btn--secondary"
                  type="button"
                  onClick={() => setShowPasswordChange(false)}
                  disabled={passwordLoading}
                >
                  Cancel
                </button>
                <button className="settings-btn settings-btn--primary" type="submit" disabled={passwordLoading || !newPasswordValid || newPassword !== confirmPassword}>
                  {passwordLoading ? 'Updating...' : 'Change password'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {showUsernameChange && (
        <div className="settings-modal-overlay" onClick={() => !usernameLoading && setShowUsernameChange(false)}>
          <div className="settings-modal settings-modal--username page-enter" onClick={(e) => e.stopPropagation()}>
            <div className="settings-modal__header">
              <div>
                <span className="settings-tag settings-tag--locked">Account security</span>
                <h3 className="settings-modal__title">Change username</h3>
              </div>
              <button
                className="settings-modal__close"
                type="button"
                onClick={() => setShowUsernameChange(false)}
                disabled={usernameLoading}
                aria-label="Close username change dialog"
              >
                &times;
              </button>
            </div>

            <form className="settings-modal__body" onSubmit={handleUsernameUpdate}>
              <p className="settings-modal__intro">
                Enter your current password to confirm this account change.
              </p>
              <p className="settings-field__hint settings-modal__username-hint">
                Usernames may contain letters, numbers, underscores, and hyphens (3-32 characters), and must include at least one letter.
              </p>

              <div className="settings-field">
                <label className="settings-field__label" htmlFor="settings-new-username">New username</label>
                <input
                  id="settings-new-username"
                  className={`settings-input ${usernameError ? 'settings-input--error' : ''}`}
                  type="text"
                  value={newUsername}
                  onChange={(e) => {
                    setNewUsername(e.target.value);
                    setUsernameError('');
                  }}
                  maxLength={CONSTRAINTS?.username?.maxLength || 32}
                  autoComplete="username"
                  autoFocus
                />
                <span className="settings-field__counter">
                  {newUsername.length} / {CONSTRAINTS?.username?.maxLength || 32} chars
                </span>
              </div>

              <div className="settings-field">
                <label className="settings-field__label" htmlFor="settings-username-password">Current password</label>
                <div className="settings-input-wrapper">
                  <input
                    id="settings-username-password"
                    className={`settings-input ${usernameError ? 'settings-input--error' : ''}`}
                    type={showUsernamePassword ? 'text' : 'password'}
                    value={usernamePassword}
                    onChange={(e) => {
                      setUsernamePassword(e.target.value);
                      setUsernameError('');
                    }}
                    autoComplete="current-password"
                  />
                  <button
                    className="settings-input-toggle"
                    type="button"
                    onClick={() => setShowUsernamePassword((visible) => !visible)}
                    aria-label={showUsernamePassword ? 'Hide password' : 'Show password'}
                  >
                    {showUsernamePassword ? 'Hide' : 'Show'}
                  </button>
                </div>
              </div>

              {usernameError && (
                <div className="settings-message settings-message--error">
                  <span>{usernameError}</span>
                </div>
              )}

              <div className="settings-modal__actions">
                <button
                  className="settings-btn settings-btn--secondary"
                  type="button"
                  onClick={() => setShowUsernameChange(false)}
                  disabled={usernameLoading}
                >
                  Cancel
                </button>
                <button
                  className="settings-btn settings-btn--primary"
                  type="submit"
                  disabled={usernameLoading || !usernamePassword || !usernameChanged}
                >
                  {usernameLoading ? 'Updating...' : 'Submit change'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Report Detail Modal */}
      {selectedReport && (
        <div className="settings-modal-overlay" onClick={() => setSelectedReport(null)}>
          <div className="settings-modal page-enter" onClick={(e) => e.stopPropagation()}>
            <div className="settings-modal__header">
              <div>
                <span className={`settings-status-badge settings-status-badge--${selectedReport.status}`}>
                  {getReportStatusLabel(selectedReport.status)}
                </span>
                <h3 className="settings-modal__title">{selectedReport.title || 'Untitled Report'}</h3>
              </div>
              <button
                className="settings-modal__close"
                onClick={() => setSelectedReport(null)}
                aria-label="Close report details"
              >
                &times;
              </button>
            </div>

            <div className="settings-modal__body">
              <div className="settings-modal__meta-grid">
                <div className="settings-modal__meta-item">
                  <span className="settings-modal__meta-label">Report Type</span>
                  <span className="settings-modal__meta-value">{getReportTypeLabel(selectedReport.report_type)}</span>
                </div>
                <div className="settings-modal__meta-item">
                  <span className="settings-modal__meta-label">Submitted On</span>
                  <span className="settings-modal__meta-value">
                    {new Date(selectedReport.created_at).toLocaleString()}
                  </span>
                </div>
                {selectedReport.analysis_ref_id && (
                  <div className="settings-modal__meta-item">
                    <span className="settings-modal__meta-label">Analysis Reference</span>
                    <span className="settings-modal__meta-value">{selectedReport.analysis_ref_id}</span>
                  </div>
                )}
              </div>

              <div className="settings-modal__section">
                <h4 className="settings-modal__section-label">Detailed Description</h4>
                <div className="settings-modal__desc-box">
                  {selectedReport.description || 'No detailed description provided.'}
                </div>
              </div>
            </div>

            <div className="settings-modal__footer">
              {(selectedReport.analysis_ref_id || selectedReport.analysis_id) && (
                <button
                  type="button"
                  className="settings-btn settings-btn--primary"
                  onClick={(e) => handleOpenReportAnalysis(selectedReport, e)}
                  disabled={navigatingAnalysisId === (selectedReport.id || selectedReport.report_id)}
                >
                  {navigatingAnalysisId === (selectedReport.id || selectedReport.report_id) ? (
                    <>
                      <span className="settings-spinner"></span>
                      Opening Result...
                    </>
                  ) : (
                    <>
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <circle cx="11" cy="11" r="8"></circle>
                        <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
                      </svg>
                      <span>View Analysis Result</span>
                    </>
                  )}
                </button>
              )}

              <button
                className="settings-btn settings-btn--secondary"
                onClick={() => setSelectedReport(null)}
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
