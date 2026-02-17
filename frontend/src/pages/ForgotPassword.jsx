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
    <div className="auth" style={{ gridTemplateColumns: '1fr' }}>
      <div className="auth__panel auth__panel--right" style={{ alignItems: 'center' }}>
        <div style={{ maxWidth: 440, width: '100%' }}>
          <h1 className="auth__title" style={{ marginTop: 0 }}>Forgot Password</h1>

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
            <div style={{ textAlign: 'center', marginTop: 24 }}>
              <div className="verify-icon verify-icon--success">✓</div>
              <p className="auth__subtitle" style={{ marginTop: 16 }}>
                If an account exists for <strong>{email}</strong>, you&apos;ll receive a password reset email shortly.
              </p>
              <p className="auth__subtitle" style={{ marginTop: 8 }}>
                Check your inbox and click the link to reset your password.
              </p>
            </div>
          )}

          <p style={{ marginTop: 24, fontSize: 13 }}>
            <Link to="/login" className="auth__link">← Back to Login</Link>
          </p>
        </div>
      </div>
    </div>
  );
}

export default ForgotPassword;
