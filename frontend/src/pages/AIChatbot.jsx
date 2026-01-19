import { useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';

function AIChatbot() {
  const navigate = useNavigate();
  const [text, setText] = useState('');

  const isLoggedIn = useMemo(
    () => Boolean(window.localStorage.getItem('access_token')),
    [],
  );

  return (
    <div className="detect">
      <aside className="detect__sidebar">
        <button className="detect__sidebtn" type="button" aria-label="Menu">
          ☰
        </button>
        <button className="detect__sidebtn" type="button" aria-label="Edit">
          ✎
        </button>
        <div className="detect__spacer" />
        <button className="detect__sidebtn" type="button" aria-label="Settings">
          ⚙
        </button>
      </aside>

      <div className="detect__main">
        <header className="nav nav--detect">
          <div className="brand brand--small">
            [INSERT LOGO / Verf AI] Fraud Detection
          </div>
          <nav className="nav__links">
            <button
              className="nav__link nav__btn"
              type="button"
              onClick={() => navigate('/')}
            >
              About us
            </button>
            <button
              className="nav__link nav__btn"
              type="button"
              onClick={() => navigate('/detection')}
            >
              Detection
            </button>
            <button
              className="nav__link nav__btn nav__btn--active"
              type="button"
            >
              AI Chatbot
            </button>
            <button className="nav__link nav__btn" type="button">
              Membership
            </button>
          </nav>
          <button
            className="nav__login"
            type="button"
            onClick={() => navigate(isLoggedIn ? '/detection' : '/login')}
          >
            {isLoggedIn ? 'Profile' : 'Login/Signup'}
          </button>
        </header>

        <main className="detect__content">
          <h1 className="detect__title">Welcome to VerfAI Guidance</h1>
          <p className="detect__subtitle">What do you need help with?</p>

          <div className="detect__inputRow">
            <button className="detect__plus" type="button" aria-label="Upload">
              +
            </button>
            <input
              className="detect__input"
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="Ask VerifAI"
            />
            <button className="detect__cta" type="button">
              Send
            </button>
          </div>
        </main>

        <footer className="detect__footer">
          <div className="detect__copyright">
            © 2026 VerifAI Technologies Inc. All rights reserved.
          </div>
        </footer>
      </div>
    </div>
  );
}

export default AIChatbot;


