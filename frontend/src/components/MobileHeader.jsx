import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function MobileHeader() {
  const [open, setOpen] = useState(false);
  const navigate = useNavigate();
  const { isLoggedIn, isAdmin, logout, user } = useAuth();
  const menuRef = useRef(null);
  const firstItemRef = useRef(null);
  const hamburgerRef = useRef(null);

  useEffect(() => {
    const handleRoute = () => setOpen(false);
    window.addEventListener('popstate', handleRoute);
    return () => window.removeEventListener('popstate', handleRoute);
  }, []);

  // Focus trap + keyboard handling + scroll lock when menu is open
  useEffect(() => {
    if (!open) {
      // restore body scroll
      document.body.style.overflow = '';
      return;
    }

    document.body.style.overflow = 'hidden';

    // Focus the first menu item after open animation
    const t = setTimeout(() => firstItemRef.current?.focus(), 160);

    const onKeyDown = (e) => {
      if (e.key === 'Escape') {
        setOpen(false);
        hamburgerRef.current?.focus();
        return;
      }

      if (e.key === 'Tab') {
        // trap focus inside the menu
        const menu = menuRef.current;
        if (!menu) return;
        const focusable = Array.from(menu.querySelectorAll('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'))
          .filter((el) => !el.hasAttribute('disabled'));
        if (focusable.length === 0) return;
        const first = focusable[0];
        const last = focusable[focusable.length - 1];

        if (e.shiftKey && document.activeElement === first) {
          e.preventDefault();
          last.focus();
        } else if (!e.shiftKey && document.activeElement === last) {
          e.preventDefault();
          first.focus();
        }
      }
    };

    document.addEventListener('keydown', onKeyDown);

    return () => {
      clearTimeout(t);
      document.removeEventListener('keydown', onKeyDown);
      document.body.style.overflow = '';
    };
  }, [open]);

  const go = (path) => {
    setOpen(false);
    navigate(path);
  };

  const scrollToSection = (id) => {
    setOpen(false);
    if (window.location.pathname !== '/') {
      navigate(`/#${id}`);
      return;
    }

    const target = document.getElementById(id);
    if (target) {
      target.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  };

  const handleLogout = async () => {
    setOpen(false);
    try {
      await logout();
      navigate('/');
    } catch (err) {
      // ignore
    }
  };

  return (
    <div className="mobile-header">
      <div className="mobile-header__bar">
        <button
          type="button"
          className="mobile-header__hamburger"
          aria-label="Menu"
          aria-expanded={open}
          aria-controls="mobile-menu"
          onClick={() => setOpen((v) => !v)}
          ref={hamburgerRef}
        >
          {open ? (
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M6 18L18 6M6 6l12 12" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/></svg>
          ) : (
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M3 12h18M3 6h18M3 18h18" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/></svg>
          )}
        </button>

        <button
          type="button"
          className="mobile-header__brand"
          onClick={() => go('/')}
        >
          Verif-AI
        </button>
        <div className="mobile-header__spacer" />

        {isLoggedIn ? (
          <button
            type="button"
            className="mobile-header__account"
            onClick={() => go('/settings')}
            aria-label="Open profile settings"
          >
            <span className="mobile-header__account-label">{user?.username || user?.email || 'Profile'}</span>
          </button>
        ) : (
          <button
            type="button"
            className="mobile-header__account mobile-header__account--auth"
            onClick={() => go('/login')}
            aria-label="Login or sign up"
          >
            Login / Signup
          </button>
        )}
      </div>

      <div id="mobile-menu" ref={menuRef} className={`mobile-header__menu ${open ? 'mobile-header__menu--open' : ''}`} role="menu" aria-hidden={!open}>
        <button className="mobile-header__item" onClick={() => scrollToSection('features')}>
          <span className="mobile-header__item-icon">ℹ️</span>
          About us
        </button>
        <button ref={firstItemRef} className="mobile-header__item" onClick={() => go('/')}>
          <span className="mobile-header__item-icon">🏠</span>
          Home
        </button>
        <button className="mobile-header__item" onClick={() => go('/detection')}>
          <span className="mobile-header__item-icon">🔎</span>
          Detection
        </button>
        <button className="mobile-header__item" onClick={() => go('/chatbot')}>
          <span className="mobile-header__item-icon">💬</span>
          AI Chatbot
        </button>

        {!isLoggedIn && (
          <button className="mobile-header__item" onClick={() => go('/login')}>
            <span className="mobile-header__item-icon">🔐</span>
            Login / Signup
          </button>
        )}

        {isLoggedIn && (
          <>
            <button className="mobile-header__item" onClick={() => go('/settings')}>
              <span className="mobile-header__item-icon">⚙️</span>
              Settings
            </button>
            {isAdmin && (
              <button className="mobile-header__item" onClick={() => go('/admin')}>
                <span className="mobile-header__item-icon">🛠️</span>
                Admin
              </button>
            )}
            <button className="mobile-header__item mobile-header__item--logout" onClick={handleLogout}>
              <span className="mobile-header__item-icon">🚪</span>
              Logout
            </button>
          </>
        )}

        <div className="mobile-header__footer">{isLoggedIn ? (user?.username || user?.email) : 'Guest'}</div>
      </div>
    </div>
  );
}
