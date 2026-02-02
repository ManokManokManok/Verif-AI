import { useState, useEffect, useRef } from 'react';
import chatHistoryData from '../mock_chat_history.json';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { sendChatMessage, getChatHistory } from '../api/chatbot';

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
        content: '❌ Sorry, I encountered an error. Please try again.',
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

      <div className="detect__main" style={{ 
        transition: 'margin-left 0.3s cubic-bezier(.4,2,.6,1)', 
        marginLeft: sidebarOpen ? 320 : 72,
        display: 'flex',
        flexDirection: 'column',
        height: '100vh',
        overflow: 'hidden',
      }}>
        <header className="nav nav--detect" style={{ flexShrink: 0 }}>
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

        <main className="detect__content" style={{
          display: 'flex',
          flexDirection: 'column',
          flex: 1,
          overflow: 'hidden',
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
            overflowY: 'auto',
            marginBottom: '16px',
            paddingRight: '8px',
          }}>
            {messages.length === 0 && (
              <div style={{ textAlign: 'center', padding: '40px 20px', color: '#64748b' }}>
                <h1 className="detect__title">🛡️ Welcome to VerfAI Guidance</h1>
                <p className="detect__subtitle">Ask me anything about scam prevention!</p>
                <div style={{ marginTop: '20px', fontSize: '14px' }}>
                  <p>💡 Try asking about:</p>
                  <ul style={{ listStyle: 'none', padding: 0, marginTop: '10px' }}>
                    <li>• Common phishing tactics</li>
                    <li>• How to spot fake emails</li>
                    <li>• What to do if you've been scammed</li>
                    <li>• Romance scam red flags</li>
                  </ul>
                </div>
              </div>
            )}

            {messages.map((msg, index) => (
              <div
                key={index}
                style={{
                  display: 'flex',
                  justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start',
                  marginBottom: '16px',
                }}
              >
                <div
                  style={{
                    maxWidth: '70%',
                    padding: '12px 16px',
                    borderRadius: '12px',
                    backgroundColor: msg.role === 'user' ? '#4F46E5' : msg.isError ? '#FEE2E2' : '#f1f5f9',
                    color: msg.role === 'user' ? 'white' : msg.isError ? '#991B1B' : '#1e293b',
                  }}
                >
                  <div style={{ 
                    fontSize: '11px', 
                    marginBottom: '4px', 
                    opacity: 0.7,
                    fontWeight: 'bold',
                  }}>
                    {msg.role === 'user' ? 'You' : 'VerifAI'}
                    <span style={{ marginLeft: '8px', fontWeight: 'normal' }}>
                      {new Date(msg.timestamp).toLocaleTimeString()}
                    </span>
                  </div>
                  <div style={{ whiteSpace: 'pre-wrap', lineHeight: '1.5' }}>
                    {msg.content}
                  </div>
                </div>
              </div>
            ))}

            {isLoading && (
              <div style={{ display: 'flex', justifyContent: 'flex-start', marginBottom: '16px' }}>
                <div style={{
                  maxWidth: '70%',
                  padding: '12px 16px',
                  borderRadius: '12px',
                  backgroundColor: '#f1f5f9',
                  color: '#1e293b',
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


