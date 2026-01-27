import { useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { placeholderChats } from '../responses/placeholder_chat.js';

function Detection() {
  const navigate = useNavigate();
  const [text, setText] = useState('');
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const isLoggedIn = useMemo(
    () => Boolean(window.localStorage.getItem('access_token')),
    [],
  );

  const toggleSidebar = () => {
    setSidebarOpen(!sidebarOpen);
  };

  const formatTimestamp = (timestamp) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffInHours = Math.floor((now - date) / (1000 * 60 * 60));

    if (diffInHours < 24) {
      return `${diffInHours}h ago`;
    } else {
      const diffInDays = Math.floor(diffInHours / 24);
      return `${diffInDays}d ago`;
    }
  };

  return (
    <div className={`detect ${sidebarOpen ? 'detect--sidebar-open' : ''}`}>
      <aside className={`detect__sidebar ${sidebarOpen ? 'detect__sidebar--open' : ''}`}>
        <button
          className="detect__sidebtn detect__sidebtn--menu"
          type="button"
          onClick={toggleSidebar}
          aria-label="Toggle menu"
        >
          {sidebarOpen ? '✕' : '☰'}
        </button>

        {sidebarOpen && (
          <div className="detect__chat-history">
            <h3 className="detect__chat-title">Chat History</h3>
            <div className="detect__chat-list">
              {placeholderChats.map((chat) => (
                <div key={chat.id} className="detect__chat-item">
                  <div className="detect__chat-item-title">{chat.title}</div>
                  <div className="detect__chat-item-preview">{chat.preview}</div>
                  <div className="detect__chat-item-time">{formatTimestamp(chat.timestamp)}</div>
                </div>
              ))}
            </div>
          </div>
        )}

        {!sidebarOpen && (
          <>
            <button className="detect__sidebtn" type="button" aria-label="New chat">
              ✎
            </button>
            <div className="detect__spacer" />
            <button className="detect__sidebtn" type="button" aria-label="Settings">
              ⚙
            </button>
          </>
        )}
      </aside>

      <div className="detect__main">
        <header className="nav nav--detect">
          <div className="brand brand--small">[INSERT LOGO / Verf AI] Fraud Detection</div>
          <nav className="nav__links">
            <button className="nav__link nav__btn" type="button" onClick={() => navigate('/')}>
              About us
            </button>
            <button className="nav__link nav__btn nav__btn--active" type="button">
              Detection
            </button>
            <button
              className="nav__link nav__btn"
              type="button"
              onClick={() => navigate('/chatbot')}
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
            onClick={() => navigate(isLoggedIn ? '/' : '/login')}
          >
            {isLoggedIn ? 'Profile' : 'Login/Signup'}
          </button>
        </header>

        <main className="detect__content">
          <h1 className="detect__title">Welcome to VerfAI fraud detection</h1>
          <p className="detect__subtitle">
            Write the promo/message you want to analyze, or press the plus button to submit a file
          </p>

          <div className="detect__inputRow">
            <button className="detect__plus" type="button" aria-label="Upload">
              +
            </button>
            <input
              className="detect__input"
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="Paste suspicious message or email here"
            />
            <button className="detect__cta" type="button">
              Detect
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

export default Detection;