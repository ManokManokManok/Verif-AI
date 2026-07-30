import { useState, useEffect } from 'react';
import './Settings.css';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { updateUsernameRequest, deleteAccountRequest } from '../api/client';
import { getMyReports, getReportTypeLabel, getReportStatusLabel } from '../api/reports';
import { validateUsername } from '../utils/validation';

export default function Settings() {
  const navigate = useNavigate();
  const { user, isLoggedIn, logout, refreshUser } = useAuth();

  // Username update state
  const [newUsername, setNewUsername] = useState('');
  const [usernameError, setUsernameError] = useState('');
  const [usernameSuccess, setUsernameSuccess] = useState('');
  const [usernameLoading, setUsernameLoading] = useState(false);

  // Delete account state
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [deletePassword, setDeletePassword] = useState('');
  const [deleteError, setDeleteError] = useState('');
  const [deleteLoading, setDeleteLoading] = useState(false);

  // User reports state
  const [reports, setReports] = useState([]);
  const [reportsLoading, setReportsLoading] = useState(true);
  const [reportsError, setReportsError] = useState('');

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
      await updateUsernameRequest({ username: trimmed });
      refreshUser();
      setUsernameSuccess('Username updated successfully.');
    } catch (err) {
      setUsernameError(err.message || 'Failed to update username.');
    } finally {
      setUsernameLoading(false);
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

  if (!user) return null;

  const usernameChanged = newUsername.trim() !== (user?.username || '');

  return (
    <div className="settings page-enter">
      <header className="settings__header">
        <button className="settings__back" type="button" onClick={() => navigate(-1)}>
          ← Back
        </button>
        <h1 className="settings__title">Account Settings</h1>
      </header>

      <div className="settings__content">
        {/* Account Information Section */}
        <section className="settings__section">
          <h2 className="settings__section-title">Account Information</h2>
          <div className="settings__card">
            <div className="settings__field">
              <label className="settings__label">Email</label>
              <input
                className="settings__input settings__input--readonly"
                type="email"
                value={user.email || ''}
                readOnly
                disabled
              />
              <span className="settings__hint">Email cannot be changed.</span>
            </div>
          </div>
        </section>

        {/* Update Username Section */}
        <section className="settings__section">
          <h2 className="settings__section-title">Update Username</h2>
          <div className="settings__card">
            <form onSubmit={handleUsernameUpdate} className="settings__form">
              <div className="settings__field">
                <label className="settings__label" htmlFor="settings-username">Username</label>
                <input
                  id="settings-username"
                  className={`settings__input${usernameError ? ' settings__input--error' : ''}`}
                  type="text"
                  value={newUsername}
                  onChange={(e) => {
                    setNewUsername(e.target.value);
                    setUsernameSuccess('');
                  }}
                  maxLength={30}
                  autoComplete="username"
                />
                {usernameError && (
                  <span className="settings__error">{usernameError}</span>
                )}
                {usernameSuccess && (
                  <span className="settings__success">{usernameSuccess}</span>
                )}
              </div>
              <button
                className="settings__btn settings__btn--primary"
                type="submit"
                disabled={usernameLoading || !usernameChanged || !!usernameError}
              >
                {usernameLoading ? 'Updating...' : 'Update Username'}
              </button>
            </form>
          </div>
        </section>

        {/* My Submitted Reports Section */}
        <section className="settings__section">
          <h2 className="settings__section-title">My Submitted Reports</h2>
          <div className="settings__card settings__card--reports">
            {reportsLoading ? (
              <div className="settings__loading">Loading reports...</div>
            ) : reportsError ? (
              <div className="settings__error">{reportsError}</div>
            ) : reports.length === 0 ? (
              <p className="settings__empty">You haven't submitted any reports yet.</p>
            ) : (
              <div className="settings__reports-list">
                {reports.map((report) => (
                  <div key={report.id || report.report_id} className="settings__report-item">
                    <div className="settings__report-header">
                      <span className="settings__report-title">{report.title || 'Untitled Report'}</span>
                      <span className={`settings__report-status settings__report-status--${report.status}`}>
                        {getReportStatusLabel(report.status)}
                      </span>
                    </div>
                    <div className="settings__report-meta">
                      <span className="settings__report-type">{getReportTypeLabel(report.report_type)}</span>
                      <span className="settings__report-date">
                        {new Date(report.created_at).toLocaleDateString()}
                      </span>
                    </div>
                    {report.description && (
                      <p className="settings__report-desc">
                        {report.description.length > 100 
                          ? `${report.description.substring(0, 100)}...` 
                          : report.description}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </section>

        {/* Danger Zone — Delete Account */}
        <section className="settings__section settings__section--danger">
          <h2 className="settings__section-title settings__section-title--danger">Danger Zone</h2>
          <div className="settings__card settings__card--danger">
            <p className="settings__danger-text">
              Permanently delete your account and all associated data. This action cannot be undone.
            </p>

            {!showDeleteConfirm ? (
              <button
                className="settings__btn settings__btn--danger"
                type="button"
                onClick={() => setShowDeleteConfirm(true)}
              >
                Delete Account
              </button>
            ) : (
              <form onSubmit={handleDeleteAccount} className="settings__form">
                <div className="settings__field">
                  <label className="settings__label" htmlFor="settings-delete-pw">
                    Enter your password to confirm
                  </label>
                  <input
                    id="settings-delete-pw"
                    className="settings__input"
                    type="password"
                    value={deletePassword}
                    onChange={(e) => {
                      setDeletePassword(e.target.value);
                      setDeleteError('');
                    }}
                    autoComplete="current-password"
                    placeholder="Your password"
                  />
                  {deleteError && (
                    <span className="settings__error">{deleteError}</span>
                  )}
                </div>
                <div className="settings__btn-group">
                  <button
                    className="settings__btn settings__btn--danger"
                    type="submit"
                    disabled={deleteLoading || !deletePassword}
                  >
                    {deleteLoading ? 'Deleting...' : 'Confirm Delete'}
                  </button>
                  <button
                    className="settings__btn settings__btn--secondary"
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
        </section>
      </div>
    </div>
  );
}
