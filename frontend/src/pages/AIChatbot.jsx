import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { sendChatMessage } from '../api/chatbot';
import { useAuth } from '../context/AuthContext';
import chatHistoryData from '../mock_chat_history.json';

function AIChatbot() {
  const navigate = useNavigate();
  const { isLoggedIn, isAdmin, logout, user, accessToken } = useAuth();
  const [text, setText] = useState('');
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [chatHistory, setChatHistory] = useState([]);
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [disclaimer, setDisclaimer] = useState(null);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    // Simulate fetching chat history from backend
    setChatHistory(chatHistoryData);
  }, []);

  const handleLogout = async () => {
    await logout();
    navigate('/');
  };

  const handleSendMessage = async (e) => {
    e.preventDefault();
    
    if (!text.trim() || isLoading) return;

    const userMessage = text.trim();
    setText('');

    const newUserMessage = {
      role: 'user',
      content: userMessage,
      timestamp: new Date().toISOString(),
    };
    setMessages(prev => [...prev, newUserMessage]);
    setIsLoading(true);

    try {
      const response = await sendChatMessage(userMessage, accessToken);
      
      if (response.disclaimer) {
        setDisclaimer(response.disclaimer);
      }

      const botMessage = {
        role: 'assistant',
        content: response.response,
        timestamp: new Date().toISOString(),
      };
      setMessages(prev => [...prev, botMessage]);

    } catch (error) {
      console.error('Chat error:', error);
      const errorMessage = {
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.',
        timestamp: new Date().toISOString(),
        isError: true,
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="detect" style={{ height: '100vh', overflow: 'hidden' }}>
      <aside className={`detect__sidebar${sidebarOpen ? ' detect__sidebar--open' : ''}`} style={{ width: sidebarOpen ? 320 : 72 }}>
        <button
          className="detect__sidebtn detect__sidebtn--menu"
          type="button"
          aria-label="Menu"
          onClick={() => setSidebarOpen((open) => !open)}
        >
          {sidebarOpen ? '✕' : '☰'}
        </button>
        <button className="detect__sidebtn" type="button" aria-label="Edit">
          ✎
        </button>
        <div className="detect__spacer" />
        <button className="detect__sidebtn" type="button" aria-label="Settings">
          ⚙
        </button>
      </aside>

      <div className="detect__main" style={{ 
        transition: 'margin-left 0.3s cubic-bezier(.4,0,.6,1)', 
        marginLeft: sidebarOpen ? 320 : 72,
        display: 'flex',
        flexDirection: 'column',
        height: '100vh',
      }}>
        <header className="nav nav--detect" style={{ flexShrink: 0 }}>
          <div className="brand brand--small">
            [INSERT LOGO / Verif-AI] Fraud Detection
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
              onClick={() => navigate(isLoggedIn ? '/detection' : '/login')}
            >
              Detection
            </button>
            <button
              className="nav__link nav__btn nav__btn--active"
              type="button"
            >
              AI Chatbot
            </button>
          </nav>
          {isLoggedIn ? (
            <div className="nav__user-actions">
              <span className="nav__username">{user?.username || user?.email}</span>
              <button
                className="nav__login"
                type="button"
                onClick={async () => { await logout(); navigate('/'); }}
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

        <main className="detect__content" style={{
          display: 'flex',
          flexDirection: 'column',
          flex: 1,
          overflow: 'hidden',
          marginBottom: '-30px',
          padding: '20px',
        }}>
          {disclaimer && (
            <div style={{
              padding: '12px 20px',
              backgroundColor: '#FEF3C7',
              border: '1px solid #FDE68A',
              borderRadius: '8px',
              fontSize: '13px',
              marginBottom: '16px',
              color: '#92400E',
              flexShrink: 0,
            }}>
              ℹ️ {disclaimer}
            </div>
          )}
          <div style={{
            flex: 1,
            display: 'flex',
            flexDirection: 'column',
            borderRadius: '12px #32314ba4',
            marginBottom: '-20px',
            overflow: 'visible',
            background: '#141327a4',
            boxShadow: '0 1px 5px #1c1b2b',
            minHeight: 0,
            width: '100%',
            maxWidth: '1050px',
            margin: '0 auto',
          }}>
            <div style={{ 
              flex: 1,
              minHeight: 0,
              overflowY: 'auto',
              padding: '16px',
              display: 'flex',
              flexDirection: 'column',
            }}>
              {messages.length === 0 && (
                <div style={{ textAlign: 'center', padding: '40px 20px', color: '#64748b', justifyContent: 'center', flex: 1, display: 'flex', flexDirection: 'column' }}>
                  <h2 style={{ fontSize: '24px', marginBottom: '8px', fontWeight: '600' }}>Welcome to VerifAI Guidance</h2>
                  <p style={{ fontSize: '14px', marginBottom: '20px' }}>Ask me anything about scam prevention!</p>
                  <div style={{ marginTop: '10px', fontSize: '13px' }}>
                    <p style={{ marginBottom: '10px' }}> Try asking about:</p>
                    <ul style={{ listStyle: 'none', padding: 0, marginTop: '10px' }}>
                      <li>• Common phishing tactics</li>
                      <li>• How to spot fake emails</li>
                      <li>• What to do if you've been scammed</li>
                      <li>• Romance scam red flags</li>
                    </ul>
                  </div>
                </div>
              )}
              

              {messages.map((msg, index) => {
  const isUser = msg.role === 'user';

  const timeStr = new Date(msg.timestamp).toLocaleTimeString([], {
    hour: '2-digit',
    minute: '2-digit',
    hour12: true,
  });

  const displayName = isUser
    ? (user?.username || user?.email?.split('@')[0] || 'You')
    : 'VerifAI';

  return (
    <div
      key={index}
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: isUser ? 'flex-end' : 'flex-start',
        marginBottom: '24px', // more space when labels are outside
      }}
    >
      
      <div
        style={{
          fontSize: '13px',
          fontWeight: '600',
          color: isUser ? '#c084fc' : '#60a5fa', // slightly colored to distinguish
          marginBottom: '4px',
          opacity: 0.95,
        }}
      >
        {displayName}
      </div>

      {/* Bubble – only contains the message text */}
      <div
  style={{
    maxWidth: '70%',
    width: 'fit-content',
    padding: '12px 16px',
    borderRadius: isUser ? '20px 20px 4px 20px' : '20px 20px 20px 4px', // asymmetric rounding
    backgroundColor: isUser ? '#25234b' : '#f0f4f8',
    color: isUser ? 'white' : '#1e293b',
    boxShadow: isUser 
      ? '0 2px 6px rgba(37, 35, 75, 0.25)' 
      : '0 2px 6px rgba(0, 0, 0, 0.12)',
    lineHeight: '1.48',
  }}
>
        <div style={{
          whiteSpace: 'pre-wrap',
          lineHeight: '1.5',
          wordBreak: 'break-word',
        }}>
          {msg.content}
        </div>
      </div>


      <div
        style={{
          fontSize: '11px',
          color: '#94a3b8',
          marginTop: '4px',
          opacity: 0.75,
        }}
      >
        {timeStr}
      </div>
    </div>
  );
})}

              {isLoading && (
                <div style={{ display: 'flex', justifyContent: 'flex-start', marginBottom: '12px' }}>
                  <div style={{
                    maxWidth: '70%',
                    padding: '12px 16px',
                    borderRadius: '12px',
                    backgroundColor: '#f0f4f8',
                    color: '#1e293b',
                    boxShadow: '0 1px 2px rgba(0, 0, 0, 0.05)',
                  }}>
                    <div style={{ fontSize: '11px', marginBottom: '4px', opacity: 0.7, fontWeight: 'bold' }}>
                      VerifAI
                    </div>
                    <div style={{ fontStyle: 'italic', opacity: 0.7 }}>
                      Thinking...
                    </div>
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>
          </div>

          <form onSubmit={handleSendMessage} className="detect__inputRow" style={{ flexShrink: 0 }}>
            <button className="detect__plus" type="button" aria-label="Upload">
              +
            </button>
            <input
              className="detect__input"
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="Ask about scam prevention..."
              disabled={isLoading}
              maxLength={2000}
            />
            <button 
              className={`detect__cta ${text.trim() ? 'detect__cta--active' : ''}`}
              type="submit"
              disabled={isLoading || !text.trim()}
            >
              {isLoading ? 'Sending...' : 'Send'}
            </button>
          </form>
        </main>

        <footer className="detect__footer" style={{ flexShrink: 0 }}>
          <div className="detect__copyright">
            © 2026 VerifAI Technologies Inc. All rights reserved.
          </div>
        </footer>
      </div>
    </div>
  );
}

export default AIChatbot;


