import { useEffect, useState } from 'react';
import { Link, Navigate, useNavigate } from 'react-router-dom';
import {
  requestPasswordResetRequest,
  resetPasswordWithCodeRequest,
} from '../api/client';
import { getPasswordRequirements, validatePassword } from '../utils/validation';

const RESET_EMAIL_KEY = 'passwordResetEmail';
const RESET_RESEND_AT_KEY = 'passwordResetResendAt';

function ResetPasswordCode() {
  const navigate = useNavigate();
  const email = window.sessionStorage.getItem(RESET_EMAIL_KEY);
  const [code, setCode] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [resendAt, setResendAt] = useState(
    () => Number(window.sessionStorage.getItem(RESET_RESEND_AT_KEY)) || 0,
  );
  const [secondsLeft, setSecondsLeft] = useState(
    () => Math.max(0, Math.ceil((resendAt - Date.now()) / 1000)),
  );
  const [sendLimitReached, setSendLimitReached] = useState(false);
  const [resetComplete, setResetComplete] = useState(false);
  const requirements = getPasswordRequirements(password);

  useEffect(() => {
    if (secondsLeft <= 0) return undefined;
    const timer = window.setTimeout(() => {
      setSecondsLeft(Math.max(0, Math.ceil((resendAt - Date.now()) / 1000)));
    }, 1000);
    return () => window.clearTimeout(timer);
  }, [resendAt, secondsLeft]);

  useEffect(() => {
    if (!resetComplete) return undefined;
    const timer = window.setTimeout(() => navigate('/login', { replace: true }), 2500);
    return () => window.clearTimeout(timer);
  }, [navigate, resetComplete]);

  if (!email) {
    return <Navigate to="/forgot-password" replace />;
  }

  const startCountdown = (retryAfter, limited) => {
    const nextResendAt = Date.now() + Math.max(0, Number(retryAfter) || 60) * 1000;
    window.sessionStorage.setItem(RESET_RESEND_AT_KEY, String(nextResendAt));
    setResendAt(nextResendAt);
    setSecondsLeft(Math.max(0, Math.ceil((nextResendAt - Date.now()) / 1000)));
    setSendLimitReached(Boolean(limited));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError('');

    if (password !== confirmPassword) {
      setError('Passwords do not match.');
      return;
    }
    const validation = validatePassword(password);
    if (!validation.valid) {
      setError(validation.errors.join('. '));
      return;
    }

    setLoading(true);
    try {
      await resetPasswordWithCodeRequest({ email, code, new_password: password });
      setResetComplete(true);
      window.sessionStorage.removeItem(RESET_EMAIL_KEY);
      window.sessionStorage.removeItem(RESET_RESEND_AT_KEY);
    } catch (requestError) {
      setError(
        requestError.message
        || 'That code is invalid, expired, or has reached its attempt limit. Request a new code and try again.',
      );
    } finally {
      setLoading(false);
    }
  };

  const handleResend = async () => {
    setError('');
    setLoading(true);
    try {
      const result = await requestPasswordResetRequest(email);
      startCountdown(result?.retry_after_seconds, result?.send_limit_reached);
      setCode('');
      setPassword('');
      setConfirmPassword('');
      if (result?.send_limit_reached) {
        setError('You have reached the hourly code limit. Try again when the countdown ends.');
      }
    } catch (requestError) {
      if (requestError?.isRateLimited) {
        const retryAfter = Number(requestError?.payload?.error?.retry_after);
        if (retryAfter > 0) {
          startCountdown(retryAfter, true);
        }
      }
      setError(requestError.message || 'Unable to request another code right now.');
    } finally {
      setLoading(false);
    }
  };

  const countdownLabel = `${Math.floor(secondsLeft / 60)}:${String(secondsLeft % 60).padStart(2, '0')}`;

  if (resetComplete) {
    return (
      <div className="auth auth--single page-enter">
        <div className="auth__panel auth__panel--right auth__panel--single">
          <div className="auth__single-card auth__single-card--center">
            <h1 className="auth__title auth__title--compact">Password Reset</h1>
            <div className="auth__single-center auth__single-center--spaced">
              <div className="verify-icon verify-icon--success">✓</div>
              <p className="auth__subtitle auth__subtitle--spaced">
                Your password has been reset successfully. Taking you to login…
              </p>
              <Link to="/login" className="auth__link auth__link--inline">
                Back to Login
              </Link>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="auth auth--single page-enter">
      <div className="auth__panel auth__panel--right auth__panel--single">
        <div className="auth__single-card reset-code">
          <p className="reset-code__step">ACCOUNT RECOVERY <span>STEP 2 OF 2</span></p>
          <h1 className="auth__title auth__title--compact">Verify your email</h1>
          <p className="auth__subtitle reset-code__intro">
            If an account exists for this address, we sent a six-digit code to:
          </p>
          <p className="reset-code__email">{email}</p>
          <p className="reset-code__expiry">The code expires 10 minutes after it was sent.</p>

          <form className="auth__form" onSubmit={handleSubmit}>
            <label className="auth__field reset-code__field">
              <span>Verification code</span>
              <input
                className="reset-code__input"
                type="text"
                inputMode="numeric"
                autoComplete="one-time-code"
                pattern="[0-9]{6}"
                maxLength={6}
                placeholder="000000"
                required
                value={code}
                onChange={(event) => setCode(event.target.value.replace(/\D/g, '').slice(0, 6))}
                aria-describedby="reset-code-hint"
              />
              <span className="reset-code__hint" id="reset-code-hint">
                Check your inbox and spam folder.
              </span>
            </label>
            <div className="reset-code__password-heading">
              <span>Choose a new password</span>
              <span>Use a password you haven&apos;t used before.</span>
            </div>
            <label className="auth__field">
              <span>New password</span>
              <div className="reset-code__password-control">
                <input
                  type={showPassword ? 'text' : 'password'}
                  autoComplete="new-password"
                  placeholder="Enter new password"
                  required
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
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
            </label>
            {password.length > 0 && (
              <div className="password-requirements">
                <div className="password-requirements__grid">
                  {requirements.map((requirement) => (
                    <span
                      key={requirement.key}
                      className={`password-requirements__item${requirement.met ? ' password-requirements__item--met' : ' password-requirements__item--unmet'}`}
                    >
                      <span className="password-requirements__icon">{requirement.met ? '✓' : '✗'}</span>
                      {requirement.label}
                    </span>
                  ))}
                </div>
              </div>
            )}
            <label className="auth__field">
              <span>Confirm new password</span>
              <div className="reset-code__password-control">
                <input
                  type={showConfirmPassword ? 'text' : 'password'}
                  autoComplete="new-password"
                  placeholder="Confirm new password"
                  required
                  value={confirmPassword}
                  onChange={(event) => setConfirmPassword(event.target.value)}
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
              <div className="auth__error-container" role="alert">
                <p className="auth__error">{error}</p>
              </div>
            )}
            <button type="submit" className="auth__primary" disabled={loading || code.length !== 6}>
              <strong>{loading ? 'Resetting…' : 'Reset Password'}</strong>
            </button>
          </form>

          <div className="reset-code__actions" aria-live="polite">
            <button
              type="button"
              className="auth__link reset-code__resend"
              disabled={loading || secondsLeft > 0}
              onClick={handleResend}
            >
              {secondsLeft > 0
                ? `${sendLimitReached ? 'Hourly limit — try again in' : 'Resend code in'} ${countdownLabel}`
                : 'Resend code'}
            </button>
            <Link to="/forgot-password" className="auth__link reset-code__change-email">
              Use a different email
            </Link>
          </div>

          <p className="auth__single-footer-link">
            <Link to="/login" className="auth__link">← Back to Login</Link>
          </p>
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

export default ResetPasswordCode;
