import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { requestPasswordResetRequest } from '../api/client';

const RESET_EMAIL_KEY = 'passwordResetEmail';
const RESET_RESEND_AT_KEY = 'passwordResetResendAt';

function ForgotPassword() {
  const [email, setEmail] = useState(() => window.sessionStorage.getItem(RESET_EMAIL_KEY) || '');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError('');
    setLoading(true);

    const normalizedEmail = email.trim().toLowerCase();
    try {
      const result = await requestPasswordResetRequest(normalizedEmail);
      window.sessionStorage.setItem(RESET_EMAIL_KEY, normalizedEmail);
      const retryAfter = Math.max(0, Number(result?.retry_after_seconds) || 60);
      window.sessionStorage.setItem(
        RESET_RESEND_AT_KEY,
        String(Date.now() + retryAfter * 1000),
      );
      navigate('/reset-password-code');
    } catch (requestError) {
      setError(requestError.message || 'Unable to request a password reset code');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth auth--single page-enter">
      <div className="auth__panel auth__panel--right auth__panel--single">
        <div className="auth__single-card">
          <h1 className="auth__title auth__title--compact">Forgot Password</h1>
          <p className="auth__subtitle">
            Enter your email address and we&apos;ll send you a six-digit password reset code.
          </p>

          <form className="auth__form" onSubmit={handleSubmit}>
            <label className="auth__field">
              <span>Email</span>
              <input
                type="email"
                autoComplete="email"
                placeholder="Enter your email address"
                required
                value={email}
                onChange={(event) => setEmail(event.target.value)}
              />
            </label>
            {error && (
              <div className="auth__error-container" role="alert">
                <p className="auth__error">{error}</p>
              </div>
            )}
            <button type="submit" className="auth__primary" disabled={loading}>
              <strong>{loading ? 'Sending…' : 'Send Verification Code'}</strong>
            </button>
          </form>

          <p className="auth__single-footer-link">
            <Link to="/login" className="auth__link">← Back to Login</Link>
          </p>
        </div>
      </div>
    </div>
  );
}

export default ForgotPassword;
