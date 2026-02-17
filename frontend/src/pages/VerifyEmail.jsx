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
    <div className="auth" style={{ gridTemplateColumns: '1fr' }}>
      <div className="auth__panel auth__panel--right" style={{ alignItems: 'center' }}>
        <div style={{ maxWidth: 440, width: '100%', textAlign: 'center' }}>
          <h1 className="auth__title" style={{ marginTop: 0 }}>Email Verification</h1>

          {status === 'verifying' && (
            <div style={{ marginTop: 32 }}>
              <div className="verify-spinner" />
              <p className="auth__subtitle" style={{ marginTop: 16 }}>
                Verifying your email address…
              </p>
            </div>
          )}

          {status === 'success' && (
            <div style={{ marginTop: 32 }}>
              <div className="verify-icon verify-icon--success">✓</div>
              <p className="auth__subtitle" style={{ marginTop: 16 }}>
                {message}
              </p>
              <button
                className="auth__primary"
                style={{ marginTop: 24 }}
                onClick={() => navigate('/login')}
              >
                <strong>Go to Login</strong>
              </button>
            </div>
          )}

          {status === 'error' && (
            <div style={{ marginTop: 32 }}>
              <div className="verify-icon verify-icon--error">✕</div>
              <p className="auth__error" style={{ marginTop: 16, fontSize: 14 }}>
                {message}
              </p>
              <Link to="/login" className="auth__link" style={{ display: 'inline-block', marginTop: 24 }}>
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
