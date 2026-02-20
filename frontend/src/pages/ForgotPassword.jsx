import { useState } from 'react';
import { Link } from 'react-router-dom';
import { requestPasswordResetRequest } from '../api/client';

function ForgotPassword() {
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await requestPasswordResetRequest(email);
      setSent(true);
    } catch (err) {
      setError(err.message || 'Failed to send reset email');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth auth--single page-enter">
      <div className="auth__panel auth__panel--right auth__panel--single">
        <div className="auth__single-card">
          <h1 className="auth__title auth__title--compact">Forgot Password</h1>

          {!sent ? (
            <>
              <p className="auth__subtitle">
                Enter your email address and we&apos;ll send you a link to reset your password.
              </p>

              <form className="auth__form" onSubmit={handleSubmit}>
                <label className="auth__field">
                  <span>Email</span>
                  <input
                    type="email"
                    placeholder="Enter your email address"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                  />
                </label>

                {error && (
                  <div className="auth__error-container">
                    <p className="auth__error">{error}</p>
                  </div>
                )}

                <button type="submit" className="auth__primary" disabled={loading}>
                  <strong>{loading ? 'Sending…' : 'Send Reset Link'}</strong>
                </button>
              </form>
            </>
          ) : (
            <div className="auth__single-center auth__single-center--spaced">
              <div className="verify-icon verify-icon--success">✓</div>
              <p className="auth__subtitle auth__subtitle--spaced">
                If an account exists for <strong>{email}</strong>, you&apos;ll receive a password reset email shortly.
              </p>
              <p className="auth__subtitle auth__subtitle--tight">
                Check your inbox and click the link to reset your password.
              </p>
            </div>
          )}

          <p className="auth__single-footer-link">
            <Link to="/login" className="auth__link">← Back to Login</Link>
          </p>
        </div>
      </div>
    </div>
  );
}

export default ForgotPassword;
