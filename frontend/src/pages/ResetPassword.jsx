import { useState } from 'react';
import { useSearchParams, useNavigate, Link } from 'react-router-dom';
import { resetPasswordRequest } from '../api/client';

function ResetPassword() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const token = searchParams.get('token');

  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (password !== confirm) {
      setError('Passwords do not match');
      return;
    }

    if (password.length < 8) {
      setError('Password must be at least 8 characters');
      return;
    }

    setLoading(true);

    try {
      await resetPasswordRequest({ token, new_password: password });
      setSuccess(true);
    } catch (err) {
      setError(err.message || 'Failed to reset password');
    } finally {
      setLoading(false);
    }
  };

  if (!token) {
    return (
      <div className="auth auth--single page-enter">
        <div className="auth__panel auth__panel--right auth__panel--single">
          <div className="auth__single-card auth__single-card--center">
            <h1 className="auth__title auth__title--compact">Invalid Link</h1>
            <p className="auth__error auth__error--single">
              No reset token provided. Please request a new reset link.
            </p>
            <Link to="/forgot-password" className="auth__link auth__link--inline">
              Request New Link
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="auth auth--single page-enter">
      <div className="auth__panel auth__panel--right auth__panel--single">
        <div className="auth__single-card">
          <h1 className="auth__title auth__title--compact">Reset Password</h1>

          {!success ? (
            <>
              <p className="auth__subtitle">
                Enter your new password below.
              </p>

              <form className="auth__form" onSubmit={handleSubmit}>
                <label className="auth__field">
                  <span>New Password</span>
                  <input
                    type="password"
                    placeholder="Enter new password"
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                  />
                </label>

                <label className="auth__field">
                  <span>Confirm Password</span>
                  <input
                    type="password"
                    placeholder="Confirm new password"
                    required
                    value={confirm}
                    onChange={(e) => setConfirm(e.target.value)}
                  />
                </label>

                {error && (
                  <div className="auth__error-container">
                    <p className="auth__error">{error}</p>
                  </div>
                )}

                <button type="submit" className="auth__primary" disabled={loading}>
                  <strong>{loading ? 'Resetting…' : 'Reset Password'}</strong>
                </button>
              </form>
            </>
          ) : (
            <div className="auth__single-center auth__single-center--spaced">
              <div className="verify-icon verify-icon--success">✓</div>
              <p className="auth__subtitle auth__subtitle--spaced">
                Your password has been reset successfully!
              </p>
              <button
                className="auth__primary"
                onClick={() => navigate('/login')}
              >
                <strong>Go to Login</strong>
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default ResetPassword;
