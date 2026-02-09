import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { sendChatMessage, getConversations, getChatHistory, deleteConversation } from '../api/chatbot';
import { useAuth } from '../context/AuthContext';

function AIChatbot() {
  const navigate = useNavigate();
  const { isLoggedIn, isAdmin, logout, user, accessToken } = useAuth();
  const [text, setText] = useState('');
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [conversations, setConversations] = useState([]);
  const [currentConversationId, setCurrentConversationId] = useState(null);
  const [currentTitle, setCurrentTitle] = useState('New Conversation');
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingConversations, setIsLoadingConversations] = useState(false);
  const [disclaimer, setDisclaimer] = useState(null);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Fetch conversations list when logged in
  useEffect(() => {
    if (isLoggedIn && accessToken) {
      fetchConversations();
    } else {
      setConversations([]);
    }
  }, [isLoggedIn, accessToken]);

  const fetchConversations = async () => {
    if (!accessToken) return;
    
    setIsLoadingConversations(true);
    try {
      const response = await getConversations(accessToken);
      setConversations(response.conversations || []);
    } catch (error) {
      console.error('Failed to fetch conversations:', error);
    } finally {
      setIsLoadingConversations(false);
    }
  };

  // Load a specific conversation
  const loadConversation = async (conversationId) => {
    if (!accessToken) return;
    
    setIsLoading(true);
    try {
      const response = await getChatHistory(accessToken, conversationId);
      setMessages(response.messages || []);
      setCurrentConversationId(conversationId);
      setCurrentTitle(response.title || 'Conversation');
      setSidebarOpen(false);
    } catch (error) {
      console.error('Failed to load conversation:', error);
    } finally {
      setIsLoading(false);
    }
  };

  // Start a new conversation
  const startNewConversation = () => {
    setMessages([]);
    setCurrentConversationId(null);
    setCurrentTitle('New Conversation');
    setDisclaimer(null);
    setSidebarOpen(false);
  };

  // Delete a conversation
  const handleDeleteConversation = async (conversationId, e) => {
    e.stopPropagation();
    if (!window.confirm('Delete this conversation?')) return;
    
    try {
      await deleteConversation(conversationId, accessToken);
      await fetchConversations();
      
      // If we deleted the current conversation, start fresh
      if (conversationId === currentConversationId) {
        startNewConversation();
      }
    } catch (error) {
      console.error('Failed to delete conversation:', error);
      alert('Failed to delete conversation');
    }
  };

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
      const response = await sendChatMessage(userMessage, accessToken, currentConversationId);
      
      if (response.disclaimer) {
        setDisclaimer(response.disclaimer);
      }

      // Update conversation ID if this is a new conversation
      if (response.is_new_conversation || !currentConversationId) {
        setCurrentConversationId(response.conversation_id);
        setCurrentTitle(response.title || userMessage.substring(0, 50));
        // Refresh conversations list
        if (isLoggedIn) {
          fetchConversations();
        }
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

  // Format date for sidebar
  const formatDate = (dateString) => {
    if (!dateString) return '';
    const date = new Date(dateString);
    const now = new Date();
    const diffDays = Math.floor((now - date) / (1000 * 60 * 60 * 24));
    
    if (diffDays === 0) return 'Today';
    if (diffDays === 1) return 'Yesterday';
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString();
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
        <button 
          className="detect__sidebtn" 
          type="button" 
          aria-label="New Chat"
          onClick={startNewConversation}
          title="New Conversation"
        >
          ✎
        </button>
        
        {/* Conversation History - Only shown when sidebar is open and logged in */}
        {sidebarOpen && isLoggedIn && (
          <div style={{
            flex: 1,
            overflowY: 'auto',
            padding: '12px',
            marginTop: '8px',
          }}>
            <div style={{
              fontSize: '12px',
              fontWeight: '600',
              color: '#94a3b8',
              marginBottom: '12px',
              textTransform: 'uppercase',
              letterSpacing: '0.5px',
            }}>
              Chat History
            </div>
            
            {isLoadingConversations ? (
              <div style={{ color: '#64748b', fontSize: '13px', padding: '8px' }}>
                Loading...
              </div>
            ) : conversations.length === 0 ? (
              <div style={{ color: '#64748b', fontSize: '13px', padding: '8px' }}>
                No conversations yet
              </div>
            ) : (
              conversations.map((conv) => (
                <div
                  key={conv.id}
                  onClick={() => loadConversation(conv.id)}
                  style={{
                    padding: '10px 12px',
                    borderRadius: '8px',
                    marginBottom: '6px',
                    cursor: 'pointer',
                    backgroundColor: conv.id === currentConversationId ? '#312e81' : 'transparent',
                    border: conv.id === currentConversationId ? '1px solid #4338ca' : '1px solid transparent',
                    transition: 'all 0.15s ease',
                  }}
                  onMouseEnter={(e) => {
                    if (conv.id !== currentConversationId) {
                      e.currentTarget.style.backgroundColor = '#1e1b4b';
                    }
                  }}
                  onMouseLeave={(e) => {
                    if (conv.id !== currentConversationId) {
                      e.currentTarget.style.backgroundColor = 'transparent';
                    }
                  }}
                >
                  <div style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'flex-start',
                  }}>
                    <div style={{
                      fontSize: '13px',
                      fontWeight: '500',
                      color: '#e2e8f0',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap',
                      flex: 1,
                      marginRight: '8px',
                    }}>
                      {conv.title || 'Untitled'}
                    </div>
                    <button
                      onClick={(e) => handleDeleteConversation(conv.id, e)}
                      style={{
                        background: 'none',
                        border: 'none',
                        color: '#64748b',
                        cursor: 'pointer',
                        fontSize: '12px',
                        padding: '2px 4px',
                        borderRadius: '4px',
                        opacity: 0.6,
                        transition: 'opacity 0.15s ease',
                      }}
                      onMouseEnter={(e) => e.currentTarget.style.opacity = '1'}
                      onMouseLeave={(e) => e.currentTarget.style.opacity = '0.6'}
                      title="Delete conversation"
                    >
                      🗑️
                    </button>
                  </div>
                  <div style={{
                    fontSize: '11px',
                    color: '#64748b',
                    marginTop: '4px',
                  }}>
                    {conv.message_count || 0} messages · {formatDate(conv.updated_at)}
                  </div>
                </div>
              ))
            )}
          </div>
        )}
        
        {/* Anonymous user message when sidebar is open */}
        {sidebarOpen && !isLoggedIn && (
          <div style={{
            flex: 1,
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'center',
            alignItems: 'center',
            padding: '20px',
            textAlign: 'center',
          }}>
            <div style={{ fontSize: '24px', marginBottom: '12px' }}>💬</div>
            <div style={{ color: '#94a3b8', fontSize: '13px', marginBottom: '16px' }}>
              Login to save your conversations
            </div>
            <button
              onClick={() => navigate('/login')}
              style={{
                padding: '8px 16px',
                borderRadius: '6px',
                border: 'none',
                backgroundColor: '#4f46e5',
                color: 'white',
                fontSize: '13px',
                cursor: 'pointer',
              }}
            >
              Login
            </button>
          </div>
        )}
        
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


