import { useState, useRef, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';
import loginImage from '../../assets/image/login.png';
import { isAdmin as checkIsAdmin, sendMfaCodeRequest, verifyMfaCodeRequest } from '../api/client';

/**
 * Format error message for display.
 * Handles both string errors and structured validation errors.
 *
 * @param {string|object} error - Error message or validation errors object
 * @returns {string[]} Array of error messages
 */
function parseErrors(error) {
  if (!error) return [];
  if (typeof error === 'string') {
    return error.split('. ').filter(Boolean);
  }
  if (typeof error === 'object') {
    return Object.values(error).flat().filter(Boolean);
  }
  return [String(error)];
}

function EyeIcon({ slashed }) {
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
        <path
          d="M4 20L20 4"
          stroke="currentColor"
          strokeWidth="1.8"
          strokeLinecap="round"
        />
      )}
    </svg>
  );
}

function EmailIcon() {
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
        d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"
        stroke="currentColor"
        strokeWidth="1.6"
        strokeLinejoin="round"
      />
      <polyline
        points="22,6 12,13 2,6"
        stroke="currentColor"
        strokeWidth="1.6"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function LockIcon() {
  return (
    <svg
      width="18"
      height="18"
      viewBox="0 0 24 24"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
    >
      <rect
        x="3"
        y="11"
        width="18"
        height="11"
        rx="2"
        ry="2"
        stroke="currentColor"
        strokeWidth="1.6"
        strokeLinejoin="round"
      />
      <circle
        cx="12"
        cy="16"
        r="1"
        stroke="currentColor"
        strokeWidth="1.6"
        strokeLinejoin="round"
      />
      <path
        d="M7 11V7a5 5 0 0 1 10 0v4"
        stroke="currentColor"
        strokeWidth="1.6"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function FacebookIcon() {
  return (
    <svg
      width="16"
      height="16"
      viewBox="0 0 24 24"
      fill="currentColor"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
    >
      <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/>
    </svg>
  );
}

function AppleIcon() {
  return (
    <svg
      width="16"
      height="16"
      viewBox="0 0 24 24"
      fill="currentColor"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
    >
      <path d="M18.71 19.5c-.83 1.24-1.71 2.45-3.05 2.47-1.34.03-1.77-.79-3.29-.79-1.53 0-2 .77-3.27.82-1.31.05-2.3-1.32-3.14-2.53C4.25 17 2.94 12.45 4.7 9.39c.87-1.52 2.43-2.48 4.12-2.51 1.28-.02 2.5.87 3.29.87.78 0 2.26-1.07 3.81-.91.65.03 2.47.26 3.64 1.98-.09.06-2.17 1.28-2.15 3.81.03 3.02 2.65 4.03 2.68 4.04-.03.07-.42 1.44-1.38 2.83M13 3.5c.73-.83 1.94-1.46 2.94-1.5.13 1.17-.34 2.35-1.04 3.19-.69.85-1.83 1.51-2.95 1.42-.15-1.15.41-2.35 1.05-3.11z"/>
    </svg>
  );
}

function GoogleIcon() {
  return (
    <svg
      width="16"
      height="16"
      viewBox="0 0 24 24"
      fill="currentColor"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
    >
      <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
      <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
      <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
      <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
    </svg>
  );
}

function AlertIcon() {
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
        d="M12 9v4m0 4h.01M10.615 3.892 2.39 18.098c-.456.789.113 1.777 1.016 1.902h16.39c.902-.125 1.471-1.113 1.015-1.902L12.585 3.892a1.127 1.127 0 0 0-1.97 0Z"
        stroke="currentColor"
        strokeWidth="1.6"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function Login() {
  const navigate = useNavigate();
  const { refreshUser } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [rememberMe, setRememberMe] = useState(false);

  // MFA state
  const [mfaStep, setMfaStep] = useState(false);
  const [mfaCode, setMfaCode] = useState(['', '', '', '', '', '']);
  const codeRefs = useRef([]);

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError('');
    setLoading(true);

    try {
      // Step 1: Send MFA code (validates credentials on the backend)
      await sendMfaCodeRequest({ email, password });
      setMfaStep(true);
    } catch (err) {
      setError(err.message || 'Failed to log in');
    } finally {
      setLoading(false);
    }
  };

  const handleMfaSubmit = async (event) => {
    event.preventDefault();
    setError('');
    const code = mfaCode.join('');
    if (code.length < 6) {
      setError('Please enter the full 6-digit code');
      return;
    }
    setLoading(true);

    try {
      await verifyMfaCodeRequest({ email, code });
      // Refresh user state from stored data
      refreshUser();
      if (checkIsAdmin()) {
        navigate('/admin');
      } else {
        navigate('/detection');
      }
    } catch (err) {
      setError(err.message || 'Invalid verification code');
    } finally {
      setLoading(false);
    }
  };

  const handleCodeChange = (index, value) => {
    if (!/^\d*$/.test(value)) return;
    const next = [...mfaCode];
    next[index] = value.slice(-1);
    setMfaCode(next);
    // Auto-focus next input
    if (value && index < 5) {
      codeRefs.current[index + 1]?.focus();
    }
  };

  const handleCodeKeyDown = (index, e) => {
    if (e.key === 'Backspace' && !mfaCode[index] && index > 0) {
      codeRefs.current[index - 1]?.focus();
    }
  };

  const handleCodePaste = (e) => {
    e.preventDefault();
    const pasted = e.clipboardData.getData('text').replace(/\D/g, '').slice(0, 6);
    if (!pasted) return;
    const next = [...mfaCode];
    for (let i = 0; i < 6; i++) {
      next[i] = pasted[i] || '';
    }
    setMfaCode(next);
    const focusIdx = Math.min(pasted.length, 5);
    codeRefs.current[focusIdx]?.focus();
  };

  const handleResendCode = async () => {
    setError('');
    setLoading(true);
    try {
      await sendMfaCodeRequest({ email, password });
      setError('');
    } catch (err) {
      setError(err.message || 'Failed to resend code');
    } finally {
      setLoading(false);
    }
  };

  // Parse error message into list for multi-error display
  const errorList = parseErrors(error);
  const hasMultipleErrors = errorList.length > 1;

  return (
    <div className="auth auth--login auth--mobile">
      {/* Theme Toggle Button */}
      <button 
        className="auth__theme-toggle" 
        onClick={toggleTheme}
        aria-label="Toggle theme"
        title={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
      >
        {theme === 'dark' ? '☀️' : '🌙'}
      </button>

      <div className="auth__panel auth__panel--left">
        <div className="auth__overlay">
          <p className="auth__tagline">Know What&apos;s Real</p>
          <p className="auth__brand">Verif-AI</p>
        </div>
        <img src={loginImage} alt="Login illustration" className="auth__image" />
      </div>

      <div className="auth__panel auth__panel--right">
        <div className="auth__header-row">
          <button
            type="button"
            className="auth__logo-link"
            onClick={() => navigate('/')}
          >
            Verif-AI
          </button>
        </div>

        {!mfaStep ? (
          <>
            <h1 className="auth__title">Log in</h1>
            <p className="auth__subtitle">
              If you don&apos;t have an account register
              <br />
              You can{' '}
              <Link to="/signup" className="auth__link">
                Register here !
              </Link>
            </p>

            <form
              className="auth__form"
              onSubmit={handleSubmit}
            >
              <label className="auth__field">
                <span>Email</span>
                <div className="auth__input-wrapper">
                  <input
                    type="email"
                    placeholder="Enter your email address"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                  />
                  <span className="auth__input-icon">
                    <EmailIcon />
                  </span>
                </div>
              </label>

              <label className="auth__field">
                <span>Password</span>
                <div className="auth__password-wrapper">
                  <input
                    type={showPassword ? 'text' : 'password'}
                    placeholder="Enter your Password"
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                  />
                  <span className="auth__input-icon auth__input-icon--left">
                    <LockIcon />
                  </span>
                  <button
                    type="button"
                    className="auth__password-toggle"
                    onClick={() => setShowPassword((prev) => !prev)}
                    aria-label={showPassword ? 'Hide password' : 'Show password'}
                  >
                    <span className="auth__password-icon">
                      <EyeIcon slashed={!showPassword} />
                    </span>
                  </button>
                </div>
              </label>

              <div className="auth__row auth__row--between">
                <label className="auth__checkbox">
                  <input 
                    type="checkbox" 
                    checked={rememberMe}
                    onChange={(e) => setRememberMe(e.target.checked)}
                  />
                  <span>Remember me</span>
                </label>
                <Link to="/forgot-password" className="auth__link" style={{ fontSize: 12 }}>
                  Forgot Password ?
                </Link>
              </div>

              {error && (
                <div
                  className="auth__error-banner"
                  role="alert"
                  aria-live="assertive"
                >
                  <span className="auth__error-icon"><AlertIcon /></span>
                  <div className="auth__error-body">
                    {hasMultipleErrors ? (
                      <ul className="auth__error-list">
                        {errorList.map((err, index) => (
                          <li key={index} className="auth__error-item">{err}</li>
                        ))}
                      </ul>
                    ) : (
                      <p className="auth__error-text">{error}</p>
                    )}
                  </div>
                  <button
                    type="button"
                    className="auth__error-dismiss"
                    onClick={() => setError('')}
                    aria-label="Dismiss error"
                  >
                    ×
                  </button>
                </div>
              )}

              <button type="submit" className="auth__submit" disabled={loading}>
                {loading ? (
                  <>
                    <span className="auth__submit-spinner"></span>
                    <span>Sending code…</span>
                  </>
                ) : (
                  <>
                    <span>Login</span>
                    <span className="auth__submit-arrow">→</span>
                  </>
                )}
              </button>

              <p className="auth__or">or continue with</p>
              <div className="auth__socials">
                <button type="button" className="auth__social">
                  <FacebookIcon />
                </button>
                <button type="button" className="auth__social">
                  <AppleIcon />
                </button>
                <button type="button" className="auth__social">
                  <GoogleIcon />
                </button>
              </div>
            </form>
          </>
        ) : (
          <>
            <h1 className="auth__title">Verification Code</h1>
            <p className="auth__subtitle auth__subtitle--mfa">
              {window.matchMedia && window.matchMedia('(max-width: 600px)').matches ? (
                <>Enter the 6-digit code we sent to <strong>{email}</strong>.</>
              ) : (
                <>
                  We&apos;ve sent a 6-digit code to <strong>{email}</strong>.
                  <br />
                  Enter it below to complete login.
                </>
              )}
            </p>

            <form className="auth__form" onSubmit={handleMfaSubmit}>
              <div className="mfa-code-container">
                <div className="mfa-code-inputs" onPaste={handleCodePaste}>
                  {mfaCode.map((digit, i) => (
                    <input
                      key={i}
                      ref={(el) => (codeRefs.current[i] = el)}
                      type="text"
                      inputMode="numeric"
                      maxLength={1}
                      className="mfa-code-input"
                      value={digit}
                      onChange={(e) => handleCodeChange(i, e.target.value)}
                      onKeyDown={(e) => handleCodeKeyDown(i, e)}
                      autoFocus={i === 0}
                    />
                  ))}
                </div>
              </div>

              {error && (
                <div
                  className="auth__error-banner"
                  role="alert"
                  aria-live="assertive"
                >
                  <span className="auth__error-icon"><AlertIcon /></span>
                  <div className="auth__error-body">
                    <p className="auth__error-text">{error}</p>
                  </div>
                  <button
                    type="button"
                    className="auth__error-dismiss"
                    onClick={() => setError('')}
                    aria-label="Dismiss error"
                  >
                    ×
                  </button>
                </div>
              )}

              <button type="submit" className="auth__submit" disabled={loading}>
                {loading ? (
                  <>
                    <span className="auth__submit-spinner"></span>
                    <span>Verifying…</span>
                  </>
                ) : (
                  <>
                    <span>Verify & Login</span>
                    <span className="auth__submit-arrow">→</span>
                  </>
                )}
              </button>

              <p className="auth__subtitle" style={{ textAlign: 'center', marginTop: 8 }}>
                Didn&apos;t receive the code?{' '}
                <button
                  type="button"
                  className="auth__link auth__link--button"
                  onClick={handleResendCode}
                  disabled={loading}
                >
                  Resend Code
                </button>
              </p>

              <p style={{ textAlign: 'center', marginTop: 8 }}>
                <button
                  type="button"
                  className="auth__link auth__link--button"
                  onClick={() => { setMfaStep(false); setError(''); setMfaCode(['', '', '', '', '', '']); }}
                >
                  ← Back to Login
                </button>
              </p>
            </form>
          </>
        )}
      </div>
    </div>
  );
}

export default Login;

