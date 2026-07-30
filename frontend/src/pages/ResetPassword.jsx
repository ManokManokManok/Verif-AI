import { useEffect, useState } from 'react';
import { useSearchParams, useNavigate, Link } from 'react-router-dom';
import {
  getPasswordResetTokenStatusRequest,
  resendPasswordResetLinkRequest,
  resetPasswordRequest,
} from '../api/client';
import { getPasswordRequirements, validatePassword } from '../utils/validation';

function ResetPassword() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const token = searchParams.get('token');

  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [tokenStatus, setTokenStatus] = useState('checking');
  const [statusMessage, setStatusMessage] = useState('');
  const [resendLoading, setResendLoading] = useState(false);
  const [resendMessage, setResendMessage] = useState('');

  const passwordRequirements = getPasswordRequirements(password);
  const showPasswordReqs = password.length > 0;
  const allPasswordReqsMet = passwordRequirements.every((r) => r.met);
  const unmetReqs = passwordRequirements.filter((r) => !r.met);

  useEffect(() => {
    if (!token) {
      setTokenStatus('invalid');
      return;
    }

    let active = true;

    const checkToken = async () => {
      try {
        const result = await getPasswordResetTokenStatusRequest(token);
        if (!active) return;

        const status = result?.status || 'invalid';
        setTokenStatus(status);

        if (status === 'expired') {
          setStatusMessage(result?.message || 'This password reset link has expired.');
        } else if (status === 'invalid') {
          setStatusMessage(result?.message || 'Invalid password reset link.');
        } else {
          setStatusMessage('');
        }
      } catch {
        if (!active) return;
        setTokenStatus('invalid');
        setStatusMessage('Unable to validate reset link. Please request a new one.');
      }
    };

    checkToken();
    return () => {
      active = false;
    };
  }, [token]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (password !== confirm) {
      setError('Passwords do not match');
      return;
    }

    const passwordValidation = validatePassword(password);
    if (!passwordValidation.valid) {
      setError(passwordValidation.errors.join('. '));
      return;
    }

    setLoading(true);

    try {
      await resetPasswordRequest({ token, new_password: password });
      setSuccess(true);
    } catch (err) {
      if (err?.payload?.error?.code === 'INVALID_TOKEN') {
        setTokenStatus('expired');
        setStatusMessage('This password reset link has expired.');
      }
      setError(err.message || 'Failed to reset password');
    } finally {
      setLoading(false);
    }
  };

  const handleResend = async () => {
    setResendLoading(true);
    setResendMessage('');

    try {
      await resendPasswordResetLinkRequest(token);
      setResendMessage('If this request is valid, a new password reset email has been sent.');
    } catch (err) {
      if (err?.isRateLimited) {
        setResendMessage(err.message || 'Too many requests. Please try again later.');
      } else {
        setResendMessage('Unable to resend now. Please try again shortly.');
      }
    } finally {
      setResendLoading(false);
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

  if (tokenStatus === 'checking') {
    return (
      <div className="auth auth--single page-enter">
        <div className="auth__panel auth__panel--right auth__panel--single">
          <div className="auth__single-card auth__single-card--center">
            <h1 className="auth__title auth__title--compact">Reset Password</h1>
            <p className="auth__subtitle auth__subtitle--spaced">Checking your reset link…</p>
          </div>
        </div>
      </div>
    );
  }

  if (tokenStatus === 'invalid') {
    return (
      <div className="auth auth--single page-enter">
        <div className="auth__panel auth__panel--right auth__panel--single">
          <div className="auth__single-card auth__single-card--center">
            <h1 className="auth__title auth__title--compact">Invalid Link</h1>
            <p className="auth__error auth__error--single">
              {statusMessage || 'Invalid password reset link.'}
            </p>
            <Link to="/forgot-password" className="auth__link auth__link--inline">
              Request New Link
            </Link>
          </div>
        </div>
      </div>
    );
  }

  if (tokenStatus === 'expired') {
    return (
      <div className="auth auth--single page-enter">
        <div className="auth__panel auth__panel--right auth__panel--single">
          <div className="auth__single-card auth__single-card--center">
            <h1 className="auth__title auth__title--compact">Reset Password</h1>
            <p className="auth__error auth__error--single">
              {statusMessage || 'This password reset link has expired.'}
            </p>
            <button
              type="button"
              className="auth__primary"
              onClick={handleResend}
              disabled={resendLoading}
            >
              <strong>{resendLoading ? 'Sending…' : 'Resend Reset Link'}</strong>
            </button>
            {resendMessage && (
              <p className="auth__subtitle auth__subtitle--tight">{resendMessage}</p>
            )}
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
                  {showPasswordReqs && (
                    <div className="password-requirements">
                      {allPasswordReqsMet ? (
                        <span className="password-requirements__success">✓ Password meets all requirements</span>
                      ) : (
                        <div className="password-requirements__grid">
                          {unmetReqs.map((req) => (
                            <span key={req.key} className="password-requirements__item password-requirements__item--unmet">
                              <span className="password-requirements__icon">✗</span>
                              {req.label}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
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
