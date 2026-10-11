import { useEffect, useState } from 'react';
import { useSearchParams, useNavigate, Link } from 'react-router-dom';
import {
  getPasswordResetTokenStatusRequest,
  resetPasswordRequest,
} from '../api/client';
import { getPasswordRequirements, validatePassword } from '../utils/validation';

function ResetPassword() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const token = searchParams.get('token');

  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [tokenStatus, setTokenStatus] = useState('checking');
  const [statusMessage, setStatusMessage] = useState('');

  useEffect(() => {
    if (!success) return undefined;
    const timer = window.setTimeout(() => navigate('/login', { replace: true }), 2500);
    return () => window.clearTimeout(timer);
  }, [navigate, success]);

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

  if (!token) {
    return (
      <div className="auth auth--single page-enter">
        <div className="auth__panel auth__panel--right auth__panel--single">
          <div className="auth__single-card auth__single-card--center">
            <h1 className="auth__title auth__title--compact">Invalid Link</h1>
            <p className="auth__error auth__error--single">
              No reset token provided. Request a password reset code instead.
            </p>
            <Link to="/forgot-password" className="auth__link auth__link--inline">
              Request a Reset Code
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
              Request a Reset Code
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
              {statusMessage || 'This password reset link has expired. Request a reset code instead.'}
            </p>
            <Link to="/forgot-password" className="auth__link auth__link--inline">
              Request a Reset Code
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
                  <div className="reset-password__password-control">
                    <input
                      type={showPassword ? 'text' : 'password'}
                      autoComplete="new-password"
                      placeholder="Enter new password"
                      required
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                    />
                    <button
                      type="button"
                      className="auth__password-toggle"
                      onClick={() => setShowPassword((visible) => !visible)}
                      aria-label={showPassword ? 'Hide new password' : 'Show new password'}
                    >
                      <PasswordEyeIcon slashed={!showPassword} />
                    </button>
                  </div>
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
                  <div className="reset-password__password-control">
                    <input
                      type={showConfirmPassword ? 'text' : 'password'}
                      autoComplete="new-password"
                      placeholder="Confirm new password"
                      required
                      value={confirm}
                      onChange={(e) => setConfirm(e.target.value)}
                    />
                    <button
                      type="button"
                      className="auth__password-toggle"
                      onClick={() => setShowConfirmPassword((visible) => !visible)}
                      aria-label={showConfirmPassword ? 'Hide confirmation password' : 'Show confirmation password'}
                    >
                      <PasswordEyeIcon slashed={!showConfirmPassword} />
                    </button>
                  </div>
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
                Your password has been reset successfully. Taking you to login…
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

function PasswordEyeIcon({ slashed }) {
  return (
    <svg
      width="18"
      height="18"
      viewBox="0 0 24 24"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
    >
      <path
        d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12Z"
        stroke="currentColor"
        strokeWidth="1.6"
        strokeLinejoin="round"
      />
      <path
        d="M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6Z"
        stroke="currentColor"
        strokeWidth="1.6"
        strokeLinejoin="round"
      />
      {slashed && (
        <path d="M4 20L20 4" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
      )}
    </svg>
  );
}

export default ResetPassword;
