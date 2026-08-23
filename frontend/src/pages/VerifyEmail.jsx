import { useEffect, useState, useRef } from 'react';
import { useSearchParams, useNavigate, Link } from 'react-router-dom';
import { verifyEmailRequest } from '../api/client';

function VerifyEmail() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const token = searchParams.get('token');

  const [status, setStatus] = useState('verifying'); // verifying | success | error
  const [message, setMessage] = useState('');
  const calledRef = useRef(false);

  useEffect(() => {
    if (!token) {
      setStatus('error');
      setMessage('No verification token provided.');
      return;
    }

    // Prevent double-call from React StrictMode
    if (calledRef.current) return;
    calledRef.current = true;

    async function verify() {
      try {
        const data = await verifyEmailRequest(token);
        setStatus('success');
        setMessage(data?.message || 'Email verified successfully!');
      } catch (err) {
        setStatus('error');
        setMessage(err.message || 'Verification failed. The token may be invalid or expired.');
      }
    }

    verify();
  }, [token]);

  return (
    <div className="auth auth--single auth--mobile page-enter">
      <div className="auth__panel auth__panel--right auth__panel--single">
        <div className="auth__single-card auth__single-card--center">
          <h1 className="auth__title auth__title--compact">Email Verification</h1>

          {status === 'verifying' && (
            <div className="auth__single-center auth__single-center--spaced">
              <div className="verify-spinner" />
              <p className="auth__subtitle auth__subtitle--spaced">
                Verifying your email address…
              </p>
            </div>
          )}

          {status === 'success' && (
            <div className="auth__single-center auth__single-center--spaced">
              <div className="verify-icon verify-icon--success">✓</div>
              <p className="auth__subtitle auth__subtitle--spaced">
                {message}
              </p>
              <button
                className="auth__primary"
                onClick={() => navigate('/login')}
              >
                <strong>Go to Login</strong>
              </button>
            </div>
          )}

          {status === 'error' && (
            <div className="auth__single-center auth__single-center--spaced">
              <div className="verify-icon verify-icon--error">✕</div>
              <p className="auth__error auth__error--single">
                {message}
              </p>
              <Link to="/login" className="auth__link auth__link--inline">
                Back to Login
              </Link>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default VerifyEmail;
