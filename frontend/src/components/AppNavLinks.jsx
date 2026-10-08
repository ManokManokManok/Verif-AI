import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const LINKS = [
  { key: 'about', label: 'About us', path: '/' },
  { key: 'journey', label: 'Your Verif-AI Journey', path: '/analytics', requiresLogin: true },
  { key: 'detection', label: 'Detection', path: '/detection' },
  { key: 'chatbot', label: 'AI Chatbot', path: '/chatbot' },
  { key: 'admin', label: 'Admin', path: '/admin', requiresAdmin: true },
];

export default function AppNavLinks({ active }) {
  const navigate = useNavigate();
  const { isLoggedIn, isAdmin } = useAuth();

  return (
    <>
      <div className="brand brand--small">Verif-AI</div>
      <nav className="nav__links">
        {LINKS.filter((l) => (!l.requiresLogin || isLoggedIn) && (!l.requiresAdmin || isAdmin)).map((l) => (
          <button
            key={l.key}
            className={`nav__link nav__btn${active === l.key ? ' nav__btn--active' : ''}`}
            type="button"
            onClick={active === l.key ? undefined : () => navigate(l.path)}
          >
            {l.label}
          </button>
        ))}
      </nav>
    </>
  );
}
