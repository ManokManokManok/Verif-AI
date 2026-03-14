import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { signupRequest } from '../api/client.js';
import { useTheme } from '../context/ThemeContext';
import { getPasswordRequirements, validateUsername } from '../utils/validation.js';
import signupImage from '../../assets/image/signup.png';

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
    return error.split('. ').filter(Boolean).map((e) => (e.endsWith('.') ? e : e));
  }
  if (typeof error === 'object') {
    return Object.values(error).flat().filter(Boolean);
  }
  return [String(error)];
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

function UserIcon() {
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
        d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"
        stroke="currentColor"
        strokeWidth="1.6"
        strokeLinejoin="round"
      />
      <circle
        cx="12"
        cy="7"
        r="4"
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

function Signup() {
  const navigate = useNavigate();
  const { theme, toggleTheme } = useTheme();
  const [email, setEmail] = useState('');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [fieldErrors, setFieldErrors] = useState({});
  const [registered, setRegistered] = useState(false);
  const [agreed, setAgreed] = useState(false);

  // Dynamic password requirements
  const passwordRequirements = getPasswordRequirements(password);
  const showPasswordReqs = password.length > 0;
  const allPasswordReqsMet = passwordRequirements.every((r) => r.met);
  const unmetReqs = passwordRequirements.filter((r) => !r.met);

  // Dynamic username validation
  const usernameError = username.length > 0 ? validateUsername(username) : null;

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError('');
    setFieldErrors({});

    if (!agreed) {
      setError('You must agree to the Terms and Conditions to sign up.');
      return;
    }

    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    setLoading(true);

    try {
      await signupRequest({ email, username, password });
      setRegistered(true);
    } catch (err) {
      // Store structured validation errors if available
      if (err.isValidationError && err.validationErrors) {
        setFieldErrors(err.validationErrors);
      }
      setError(err.message || 'Failed to register');
    } finally {
      setLoading(false);
    }
  };

  // Parse error message into list for multi-error display
  // Filter out password/username validation errors already shown inline
  const errorList = parseErrors(error).filter((msg) => {
    const lower = msg.toLowerCase();
    // Skip messages already covered by inline password requirements
    if (lower.includes('at least one uppercase')) return false;
    if (lower.includes('at least one lowercase')) return false;
    if (lower.includes('at least one digit')) return false;
    if (lower.includes('at least one special character')) return false;
    if (lower.includes('at least') && lower.includes('characters')) return false;
    if (lower.includes('too common')) return false;
    if (lower.includes('choose a stronger password')) return false;
    if (lower.includes('must not contain spaces')) return false;
    // Skip username errors shown inline
    if (lower.includes('at least one letter') && lower.includes('username')) return false;
    return true;
  });
  const hasMultipleErrors = errorList.length > 1;

  return (
    <div className="auth auth--signup page-enter">
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
          <p className="auth__tagline">Keeping you Safe</p>
          <p className="auth__brand">Verif-AI</p>
        </div>
        <img src={signupImage} alt="Signup illustration" className="auth__image" />
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

        {registered ? (
          <div style={{ textAlign: 'center', marginTop: 32 }}>
            <div className="verify-icon verify-icon--success">✓</div>
            <h1 className="auth__title" style={{ marginTop: 20 }}>Check Your Email</h1>
            <p className="auth__subtitle" style={{ marginTop: 12, lineHeight: 1.6 }}>
              We&apos;ve sent a verification link to <strong>{email}</strong>.
              <br />
              Please click the link in your email to verify your account before logging in.
            </p>
            <button
              className="auth__submit"
              style={{ marginTop: 28 }}
              onClick={() => navigate('/login')}
            >
              <span>Go to Login</span>
              <span className="auth__submit-arrow">→</span>
            </button>
            <p className="auth__subtitle" style={{ marginTop: 16, fontSize: 12 }}>
              Didn&apos;t receive the email? Check your spam folder.
            </p>
          </div>
        ) : (
        <>
        <h1 className="auth__title">Sign up</h1>
        <p className="auth__subtitle">
          If you already have an account register
          <br />
          You can{' '}
          <Link to="/login" className="auth__link">
            Login here !
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
            <span>Username</span>
            <div className="auth__input-wrapper">
              <input
                type="text"
                placeholder="Enter your User name"
                required
                value={username}
                onChange={(e) => setUsername(e.target.value)}
              />
              <span className="auth__input-icon">
                <UserIcon />
              </span>
            </div>
            {usernameError && !usernameError.valid && (
              <span className="auth__field-hint auth__field-hint--error">{usernameError.error}</span>
            )}
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
            <div className="auth__password-wrapper">
              <input
                type={showConfirmPassword ? 'text' : 'password'}
                placeholder="Confirm your Password"
                required
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
              />
              <span className="auth__input-icon auth__input-icon--left">
                <LockIcon />
              </span>
              <button
                type="button"
                className="auth__password-toggle"
                onClick={() => setShowConfirmPassword((prev) => !prev)}
                aria-label={
                  showConfirmPassword ? 'Hide password' : 'Show password'
                }
              >
                <span className="auth__password-icon">
                  <EyeIcon slashed={!showConfirmPassword} />
                </span>
              </button>
            </div>
          </label>

          {errorList.length > 0 && (
            <div className="auth__error-container">
              {hasMultipleErrors ? (
                <ul className="auth__error-list">
                  {errorList.map((err, index) => (
                    <li key={index} className="auth__error-item">{err}</li>
                  ))}
                </ul>
              ) : (
                <p className="auth__error">{error}</p>
              )}
            </div>
          )}

          <label className="auth__checkbox-label" style={{ display: 'flex', alignItems: 'center', margin: '16px 0 8px 0', fontSize: 14 }}>
            <input
              type="checkbox"
              checked={agreed}
              onChange={e => setAgreed(e.target.checked)}
              required
              style={{ marginRight: 8 }}
            />
            I agree to the{' '}
            <a
              href="/terms-and-conditions"
              target="_blank"
              rel="noopener noreferrer"
              style={{ color: '#2563eb', textDecoration: 'underline', marginLeft: 4 }}
              onClick={e => { e.stopPropagation(); }}
            >
              Verif-AI Terms and Conditions
            </a>
          </label>

          <button type="submit" className="auth__submit" disabled={loading}>
            {loading ? (
              <>
                <span className="auth__submit-spinner"></span>
                <span>Registering…</span>
              </>
            ) : (
              <>
                <span>Register</span>
                <span className="auth__submit-arrow">→</span>
              </>
            )}
          </button>
        </form>
        </>
        )}
      </div>
    </div>
  );
}

export default Signup;

