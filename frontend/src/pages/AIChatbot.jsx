import { useState, useEffect } from 'react';
import chatHistoryData from '../mock_chat_history.json';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

function AIChatbot() {
  const navigate = useNavigate();
  const { isLoggedIn, isAdmin, logout, user } = useAuth();
  const [text, setText] = useState('');
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [chatHistory, setChatHistory] = useState([]);

  useEffect(() => {
    // Simulate fetching chat history from backend
    setChatHistory(chatHistoryData);
  }, []);

  const handleLogout = async () => {
    await logout();
    navigate('/');
  };

  return (
    <div className="detect">
      <aside className={`detect__sidebar${sidebarOpen ? ' detect__sidebar--open' : ''}`} style={{ width: sidebarOpen ? 320 : 72 }}>
        <button
          className="detect__sidebtn detect__sidebtn--menu"
          type="button"
          aria-label="Menu"
          onClick={() => setSidebarOpen((open) => !open)}
        >
          {sidebarOpen ? '✕' : '☰'}
        </button>
        {sidebarOpen && (
          <div className="detect__chat-history">
            <div className="detect__chat-title">Chat History</div>
            <div className="detect__chat-list">
              {chatHistory.map((chat) => (
                <div className="detect__chat-item" key={chat.id}>
                  <div className="detect__chat-item-title">{chat.title}</div>
                  <div className="detect__chat-item-preview">{chat.description}</div>
                  <div className="detect__chat-item-time">{chat.timestamp}</div>
                </div>
              ))}
            </div>
          </div>
        )}
        {!sidebarOpen && (
          <>
            <button className="detect__sidebtn" type="button" aria-label="Edit">
              ✎
            </button>
            <div className="detect__spacer" />
            <button className="detect__sidebtn" type="button" aria-label="Settings">
              ⚙
            </button>
          </>
        )}
      </aside>

      <div className="detect__main" style={{ transition: 'margin-left 0.3s cubic-bezier(.4,2,.6,1)', marginLeft: sidebarOpen ? 320 : 72 }}>
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
            {isAdmin && (
              <button
                className="nav__link nav__btn"
                type="button"
                onClick={() => navigate('/blockchain')}
              >
                Admin
              </button>
            )}
          </nav>
          {isLoggedIn ? (
            <div className="nav__user-actions">
              <span className="nav__username">{user?.username || user?.email}</span>
              <button
                className="nav__login"
                type="button"
                onClick={handleLogout}
              >
                Logout
              </button>
            </div>
          ) : (
            <button
              className="nav__login"
              type="button"
              onClick={() => navigate('/login')}
            >
              Login/Signup
            </button>
          )}
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


