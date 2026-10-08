import { useRef, useState } from 'react';
import { sendEmailVerificationCodeRequest, verifyEmailCodeRequest } from '../../api/client';

function AlertIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
      <path
        d="M12 9v4m0 4h.01M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0Z"
        stroke="currentColor"
        strokeWidth="1.6"
        strokeLinejoin="round"
      />
    </svg>
  );
}

/**
 * Shared 6-digit email verification code screen.
 * Reused wherever a user needs to verify their email before continuing
 * (fresh signup, signup retry on an unverified email, login on an unverified email).
 */
function EmailVerificationCode({ email, initialMessage = '', onVerified, onBack }) {
  const [code, setCode] = useState(['', '', '', '', '', '']);
  const [error, setError] = useState('');
  const [info, setInfo] = useState(initialMessage);
  const [loading, setLoading] = useState(false);
  const [resending, setResending] = useState(false);
  const codeRefs = useRef([]);

  const handleCodeChange = (index, value) => {
    if (!/^\d*$/.test(value)) return;
    const next = [...code];
    next[index] = value.slice(-1);
    setCode(next);
    if (value && index < 5) {
      codeRefs.current[index + 1]?.focus();
    }
  };

  const handleCodeKeyDown = (index, e) => {
    if (e.key === 'Backspace' && !code[index] && index > 0) {
      codeRefs.current[index - 1]?.focus();
    }
  };

  const handleCodePaste = (e) => {
    e.preventDefault();
    const pasted = e.clipboardData.getData('text').replace(/\D/g, '').slice(0, 6);
    if (!pasted) return;
    const next = [...code];
    for (let i = 0; i < 6; i++) {
      next[i] = pasted[i] || '';
    }
    setCode(next);
    codeRefs.current[Math.min(pasted.length, 5)]?.focus();
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError('');
    const joined = code.join('');
    if (joined.length < 6) {
      setError('Please enter the full 6-digit code');
      return;
    }
    setLoading(true);
    try {
      await verifyEmailCodeRequest({ email, code: joined });
      onVerified?.();
    } catch (err) {
      setError(err.message || 'Invalid or expired code');
    } finally {
      setLoading(false);
    }
  };

  const handleResend = async () => {
    setError('');
    setInfo('');
    setResending(true);
    try {
      await sendEmailVerificationCodeRequest(email);
      setInfo('A new code has been sent to your email.');
    } catch (err) {
      setError(err.message || 'Failed to resend code');
    } finally {
      setResending(false);
    }
  };

  return (
    <>
      <h1 className="auth__title">Verify Your Email</h1>
      <p className="auth__subtitle auth__subtitle--mfa">
        We&apos;ve sent a 6-digit code to <strong>{email}</strong>.
        <br />
        Enter it below to verify your account.
      </p>

      <form className="auth__form" onSubmit={handleSubmit}>
        <div className="mfa-code-container">
          <div className="mfa-code-inputs" onPaste={handleCodePaste}>
            {code.map((digit, i) => (
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

        {info && (
          <p className="auth__subtitle" style={{ textAlign: 'center', color: '#4CAF50' }}>
            {info}
          </p>
        )}

        {error && (
          <div className="auth__error-banner" role="alert" aria-live="assertive">
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
              <span>Verify Email</span>
              <span className="auth__submit-arrow">→</span>
            </>
          )}
        </button>

        <p className="auth__subtitle" style={{ textAlign: 'center', marginTop: 8 }}>
          Didn&apos;t receive the code?{' '}
          <button
            type="button"
            className="auth__link auth__link--button"
            onClick={handleResend}
            disabled={resending}
          >
            {resending ? 'Sending…' : 'Resend Code'}
          </button>
        </p>

        {onBack && (
          <p style={{ textAlign: 'center', marginTop: 8 }}>
            <button type="button" className="auth__link auth__link--button" onClick={onBack}>
              ← Back
            </button>
          </p>
        )}
      </form>
    </>
  );
}

export default EmailVerificationCode;
