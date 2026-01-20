import { useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { detectScamRequest } from '../api/client';

function Detection() {
  const navigate = useNavigate();
  const [text, setText] = useState('');
  const [isFocused, setIsFocused] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);
  const [isDetecting, setIsDetecting] = useState(false);

  const isLoggedIn = useMemo(
    () => Boolean(window.localStorage.getItem('access_token')),
    [],
  );

  const handleTextChange = (e) => {
    setText(e.target.value);
    // Auto-expand when text grows
    if (e.target.value.length > 50 && !isExpanded) {
      setIsExpanded(true);
    } else if (e.target.value.length === 0) {
      setIsExpanded(false);
    }
  };

  const handleDetect = async () => {
    if (!text.trim() || isDetecting) return;

    setIsDetecting(true);
    try {
      const result = await detectScamRequest(text);
      console.log('[DETECTION RESULT]', result);
      // TODO: Display results in UI (for now just logging to console)
    } catch (error) {
      console.error('[DETECTION ERROR]', error);
      alert(`Error: ${error.message || 'Failed to detect scam'}`);
    } finally {
      setIsDetecting(false);
    }
  };

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

          <div 
            className={`detect__inputRow ${isFocused ? 'detect__inputRow--focused' : ''} ${isExpanded ? 'detect__inputRow--expanded' : ''}`}
          >
            <button className="detect__plus" type="button" aria-label="Upload">
              +
            </button>
            <textarea
              className="detect__input"
              value={text}
              onChange={handleTextChange}
              onFocus={() => setIsFocused(true)}
              onBlur={() => setIsFocused(false)}
              placeholder="Paste suspicious message or email here..."
              rows={1}
            />
            <button 
              className={`detect__cta ${text.trim() ? 'detect__cta--active' : ''}`}
              type="button"
              disabled={!text.trim() || isDetecting}
              onClick={handleDetect}
            >
              {isDetecting ? 'Analyzing...' : 'Detect'}
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


