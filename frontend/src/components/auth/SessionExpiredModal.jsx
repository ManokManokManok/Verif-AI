import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';

/**
 * Modal overlay shown when the user's session has expired.
 * Prompts the user to log in again and redirects to the login page.
 */
export default function SessionExpiredModal() {
  const { sessionExpired, dismissSessionExpired } = useAuth();
  const navigate = useNavigate();

  if (!sessionExpired) return null;

  const handleLogin = () => {
    dismissSessionExpired();
    navigate('/login');
  };

  return (
    <div style={overlayStyle}>
      <div style={modalStyle}>
        <div style={iconContainerStyle}>
          <svg
            width="48"
            height="48"
            viewBox="0 0 24 24"
            fill="none"
            stroke="#f59e0b"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <circle cx="12" cy="12" r="10" />
            <line x1="12" y1="8" x2="12" y2="12" />
            <line x1="12" y1="16" x2="12.01" y2="16" />
          </svg>
        </div>
        <h2 style={titleStyle}>Session Expired</h2>
        <p style={messageStyle}>
          Your session has expired due to inactivity. Please log in again to continue.
        </p>
        <button onClick={handleLogin} style={buttonStyle}>
          Log In Again
        </button>
      </div>
    </div>
  );
}

const overlayStyle = {
  position: 'fixed',
  top: 0,
  left: 0,
  right: 0,
  bottom: 0,
  backgroundColor: 'rgba(0, 0, 0, 0.7)',
  display: 'flex',
  justifyContent: 'center',
  alignItems: 'center',
  zIndex: 10000,
  backdropFilter: 'blur(4px)',
};

const modalStyle = {
  background: '#1a1a2e',
  borderRadius: '12px',
  padding: '32px 40px',
  maxWidth: '420px',
  width: '90%',
  textAlign: 'center',
  border: '1px solid rgba(245, 158, 11, 0.3)',
  boxShadow: '0 20px 60px rgba(0, 0, 0, 0.5)',
};

const iconContainerStyle = {
  marginBottom: '16px',
};

const titleStyle = {
  color: '#f59e0b',
  fontSize: '1.5rem',
  fontWeight: '600',
  margin: '0 0 12px 0',
};

const messageStyle = {
  color: '#cbd5e1',
  fontSize: '0.95rem',
  lineHeight: '1.6',
  margin: '0 0 24px 0',
};

const buttonStyle = {
  background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
  color: '#fff',
  border: 'none',
  borderRadius: '8px',
  padding: '12px 32px',
  fontSize: '1rem',
  fontWeight: '600',
  cursor: 'pointer',
  transition: 'transform 0.15s, box-shadow 0.15s',
  boxShadow: '0 4px 12px rgba(99, 102, 241, 0.4)',
};
