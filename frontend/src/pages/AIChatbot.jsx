import { useEffect, useRef, useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { 
  sendChatMessage, 
  getConversations, 
  getChatHistory, 
  deleteConversation,
  sendAnalysisGuidedMessage,
  getAnalysisGuidedHistory
} from '../api/chatbot';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';
import LogoutConfirmModal from '../components/auth/LogoutConfirmModal';

function AIChatbot() {
    const [showUserMenu, setShowUserMenu] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const { isLoggedIn, isAdmin, logout, user, accessToken } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const [text, setText] = useState('');
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [conversations, setConversations] = useState([]);
  const [currentConversationId, setCurrentConversationId] = useState(null);
  const [currentTitle, setCurrentTitle] = useState('New Conversation');
  const [conversationType, setConversationType] = useState('general'); // 'general' or 'analysis_guided'
  const [analysisContext, setAnalysisContext] = useState(null);
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingConversations, setIsLoadingConversations] = useState(false);
  const [disclaimer, setDisclaimer] = useState(null);
  const [showLogoutModal, setShowLogoutModal] = useState(false);
  const [showSettingsModal, setShowSettingsModal] = useState(false);
  const [autoScroll, setAutoScroll] = useState(() => localStorage.getItem('chatbot-autoscroll') !== 'false');
  const [soundEnabled, setSoundEnabled] = useState(() => localStorage.getItem('chatbot-sound') !== 'false');
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    if (autoScroll) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, autoScroll]);

  // Save settings to localStorage
  useEffect(() => {
    localStorage.setItem('chatbot-autoscroll', autoScroll);
  }, [autoScroll]);

  useEffect(() => {
    localStorage.setItem('chatbot-sound', soundEnabled);
  }, [soundEnabled]);

  const handleSettingsClick = () => {
    setShowSettingsModal(true);
  };

  const closeSettingsModal = () => {
    setShowSettingsModal(false);
  };

  // Handle navigation state for analysis-guided mode
  useEffect(() => {
    if (location.state) {
      const { conversationId, conversationType: navType, analysisContext: navContext, isNew } = location.state;
      
      if (navType === 'analysis_guided' && conversationId) {
        console.log('[CHATBOT] Opening analysis-guided conversation:', conversationId);
        setConversationType('analysis_guided');
        setAnalysisContext(navContext);
        setCurrentConversationId(conversationId);
        
        // Load the conversation history
        loadAnalysisGuidedConversation(conversationId);
        
        // Clear navigation state to prevent reloading on refresh
        window.history.replaceState({}, document.title);
      }
    }
  }, [location.state]);

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
      setConversationType('general');
      setAnalysisContext(null);
      setSidebarOpen(false);
    } catch (error) {
      console.error('Failed to load conversation:', error);
    } finally {
      setIsLoading(false);
    }
  };

  // Load analysis-guided conversation
  const loadAnalysisGuidedConversation = async (conversationId) => {
    if (!accessToken) return;
    
    setIsLoading(true);
    try {
      const response = await getAnalysisGuidedHistory(conversationId, accessToken);
      setMessages(response.messages || []);
      setCurrentConversationId(conversationId);
      setCurrentTitle(response.title || 'Analysis Guidance');
      setConversationType('analysis_guided');
      setAnalysisContext(response.analysis_context);
      setSidebarOpen(false);
    } catch (error) {
      console.error('Failed to load analysis-guided conversation:', error);
    } finally {
      setIsLoading(false);
    }
  };

  // Start a new conversation
  const startNewConversation = () => {
    setMessages([]);
    setCurrentConversationId(null);
    setCurrentTitle('New Conversation');
    setConversationType('general');
    setAnalysisContext(null);
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

  const handleLogout = () => {
    setShowLogoutModal(true);
  };

  const confirmLogout = async () => {
    setShowLogoutModal(false);
    await logout();
    navigate('/');
  };

  const cancelLogout = () => {
    setShowLogoutModal(false);
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
      let response;
      
      // Use different API based on conversation type
      if (conversationType === 'analysis_guided') {
        // Analysis-guided conversation
        if (!currentConversationId) {
          throw new Error('Analysis conversation ID required');
        }
        response = await sendAnalysisGuidedMessage(currentConversationId, userMessage, accessToken);
      } else {
        // General conversation
        response = await sendChatMessage(userMessage, accessToken, currentConversationId);
        
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
    <div className="detect detect--chatbot page-enter" style={{ height: '100vh', overflow: 'hidden' }}>
      <aside className={`detect__sidebar detect__sidebar--chatbot${sidebarOpen ? ' detect__sidebar--open' : ''}`} style={{ width: sidebarOpen ? 320 : 72 }}>
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
          <div className="chatbot__history-panel">
            <div className="chatbot__history-title">
              Chat History
            </div>
            
            {isLoadingConversations ? (
              <div className="chatbot__history-empty">
                Loading...
              </div>
            ) : conversations.length === 0 ? (
              <div className="chatbot__history-empty">
                No conversations yet
              </div>
            ) : (
              conversations.map((conv) => (
                <div
                  key={conv.id}
                  onClick={() => {
                    // Load analysis-guided conversations differently
                    if (conv.conversation_type === 'analysis_guided') {
                      loadAnalysisGuidedConversation(conv.id);
                    } else {
                      loadConversation(conv.id);
                    }
                  }}
                  className={`chatbot__history-item${conv.id === currentConversationId ? ' chatbot__history-item--active' : ''}`}
                >
                  <div className="chatbot__history-item-header">
                    <div className="chatbot__history-item-title">
                      {conv.title || 'Untitled'}
                    </div>
                    <button
                      onClick={(e) => handleDeleteConversation(conv.id, e)}
                      className="chatbot__history-delete"
                      title="Delete conversation"
                    >
                      🗑️
                    </button>
                  </div>
                  <div className="chatbot__history-meta">
                    {conv.message_count || 0} messages · {formatDate(conv.updated_at)}
                  </div>
                </div>
              ))
            )}
          </div>
        )}
        
        {/* Anonymous user message when sidebar is open */}
        {sidebarOpen && !isLoggedIn && (
          <div className="chatbot__anonymous-box">
            <div className="chatbot__anonymous-icon">💬</div>
            <div className="chatbot__anonymous-text">
              Login to save your conversations
            </div>
            <button
              onClick={() => navigate('/login')}
              className="chatbot__anonymous-login"
            >
              Login
            </button>
          </div>
        )}
        
        <div className="detect__spacer" />
        <button 
          className="detect__sidebtn" 
          type="button" 
          aria-label="Settings"
          onClick={handleSettingsClick}
          title="Settings"
        >
          ⚙
        </button>
      </aside>

      <div className="detect__main" style={{ 
        transition: 'margin-left 0.3s cubic-bezier(.4,2,.6,1)', 
        marginLeft: sidebarOpen ? 320 : 72,
        display: 'flex',
        flexDirection: 'column',
        height: '100vh',
      }}>
        <header className="nav nav--detect" style={{ flexShrink: 0 }}>
          <div className="brand brand--small">
            Verif-AI Assistant
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
            <div className="nav__user-menu" onClick={e => e.stopPropagation()}>
              <button
                className="nav__login"
                type="button"
                onClick={() => setShowUserMenu(v => !v)}
              >
                {user?.username || user?.email || 'Profile'}
              </button>
              {showUserMenu && (
                <div className="nav__dropdown">
                  <button
                    className="nav__dropdown-item"
                    type="button"
                    onClick={() => { navigate('/settings'); setShowUserMenu(false); }}
                  >
                    Settings
                  </button>
                  {isAdmin && (
                    <button
                      className="nav__dropdown-item nav__dropdown-item--admin"
                      type="button"
                      onClick={() => { navigate('/admin'); setShowUserMenu(false); }}
                    >
                      Admin Panel
                    </button>
                  )}
                  <button
                    className="nav__dropdown-item nav__dropdown-item--logout"
                    type="button"
                    onClick={handleLogout}
                  >
                    Logout
                  </button>
                </div>
              )}
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

        <main className="detect__content detect__content--chatbot" style={{
          display: 'flex',
          flexDirection: 'column',
          flex: 1,
          overflow: 'hidden',
          marginBottom: '-30px',
          padding: '20px',
        }}>
          {disclaimer && (
            <div className="chatbot__disclaimer">
              ℹ️ {disclaimer}
            </div>
          )}
          <div className="chatbot__panel page-enter">
            <div className="chatbot__messages-wrap" style={{ 
              flex: 1,
              minHeight: 0,
              overflowY: 'auto',
              padding: '16px',
              display: 'flex',
              flexDirection: 'column',
            }}>
              {messages.length === 0 && (
                <div className="chatbot__empty-state">
                  {conversationType === 'analysis_guided' && analysisContext ? (
                    <>
                      <h2 className="chatbot__empty-title">Analysis Guidance</h2>
                      <p className="chatbot__empty-subtitle">Ask me about the analysis results and what to do next!</p>
                    </>
                  ) : (
                    <>
                      <h2 className="chatbot__empty-title">Welcome to Verif-AI Guidance</h2>
                      <p className="chatbot__empty-subtitle">Ask me anything about scam prevention!</p>
                      <div className="chatbot__empty-hints">
                        <p>Try asking about:</p>
                        <ul>
                          <li>• Common phishing tactics</li>
                          <li>• How to spot fake emails</li>
                          <li>• What to do if you've been scammed</li>
                          <li>• Romance scam red flags</li>
                        </ul>
                      </div>
                    </>
                  )}
                </div>
              )}
              
              {/* Analysis Context Card - shown for analysis-guided conversations */}
              {conversationType === 'analysis_guided' && analysisContext && (
                <div className={`chatbot__analysis-card${analysisContext.is_scam ? ' chatbot__analysis-card--scam' : ' chatbot__analysis-card--safe'}`}>
                  <div className="chatbot__analysis-header">
                    <h3 className="chatbot__analysis-title">
                      {analysisContext.is_scam ? 'High Likelihood' : 'Low Likelihood'}
                    </h3>
                  </div>
                  
                  {analysisContext.is_scam && analysisContext.scam_type && (
                    <div className="chatbot__analysis-line">
                      <strong>Type:</strong>{' '}
                      <span>{analysisContext.scam_type}</span>
                    </div>
                  )}
                  
                  <div className="chatbot__analysis-line">
                    <strong>Confidence:</strong> Scam {analysisContext.scam_score?.toFixed(1)}% / Legitimate {analysisContext.legit_score?.toFixed(1)}%
                  </div>
                  
                  {analysisContext.summary && (
                    <div className="chatbot__analysis-summary">
                      <strong>Summary:</strong> {analysisContext.summary}
                    </div>
                  )}
                  
                  <div className="chatbot__analysis-hint">
                    Ask me anything about these results and what steps to take!
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
      className={`chatbot__message-wrap${isUser ? ' chatbot__message-wrap--user' : ''}`}
    >
      
      <div className={`chatbot__message-name${isUser ? ' chatbot__message-name--user' : ''}`}>
        {displayName}
      </div>

      {/* Bubble – only contains the message text */}
      <div
        className={`chatbot__message-bubble${isUser ? ' chatbot__message-bubble--user' : ''}${msg.isError ? ' chatbot__message-bubble--error' : ''}`}
      >
        <div className="chatbot__message-content">
          {msg.content}
        </div>
      </div>


      <div className="chatbot__message-time">
        {timeStr}
      </div>
    </div>
  );
})}

              {isLoading && (
                <div className="chatbot__message-wrap">
                  <div className="chatbot__message-name">
                    VerifAI
                  </div>
                  <div className="chatbot__message-bubble">
                    <div className="chatbot__typing-indicator">
                      <span className="chatbot__typing-dot"></span>
                      <span className="chatbot__typing-dot"></span>
                      <span className="chatbot__typing-dot"></span>
                    </div>
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>
          </div>

          <form onSubmit={handleSendMessage} className="detect__inputRow detect__inputRow--chatbot" style={{ flexShrink: 0 }}>
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

      {/* Logout Confirmation Modal */}
      <LogoutConfirmModal
        isOpen={showLogoutModal}
        onConfirm={confirmLogout}
        onCancel={cancelLogout}
      />

      {/* Settings Modal */}
      {showSettingsModal && (
        <div className="chatbot__settings-overlay" onClick={closeSettingsModal}>
          <div className="chatbot__settings-modal" onClick={(e) => e.stopPropagation()}>
            <div className="chatbot__settings-header">
              <h2 className="chatbot__settings-title">Settings</h2>
              <button 
                className="chatbot__settings-close" 
                onClick={closeSettingsModal}
                aria-label="Close"
              >
                ✕
              </button>
            </div>

            <div className="chatbot__settings-content">
              {/* Theme Setting */}
              <div className="chatbot__settings-item">
                <div className="chatbot__settings-item-header">
                  <div className="chatbot__settings-item-icon">{theme === 'dark' ? '🌙' : '☀️'}</div>
                  <div className="chatbot__settings-item-info">
                    <div className="chatbot__settings-item-label">Theme</div>
                    <div className="chatbot__settings-item-desc">
                      {theme === 'dark' ? 'Dark mode' : 'Light mode'}
                    </div>
                  </div>
                </div>
                <button 
                  className={`chatbot__settings-toggle${theme === 'light' ? ' chatbot__settings-toggle--active' : ''}`}
                  onClick={toggleTheme}
                  aria-label="Toggle theme"
                >
                  <div className="chatbot__settings-toggle-slider"></div>
                </button>
              </div>

              {/* Auto-scroll Setting */}
              <div className="chatbot__settings-item">
                <div className="chatbot__settings-item-header">
                  <div className="chatbot__settings-item-icon">📜</div>
                  <div className="chatbot__settings-item-info">
                    <div className="chatbot__settings-item-label">Auto-scroll</div>
                    <div className="chatbot__settings-item-desc">
                      Automatically scroll to new messages
                    </div>
                  </div>
                </div>
                <button 
                  className={`chatbot__settings-toggle${autoScroll ? ' chatbot__settings-toggle--active' : ''}`}
                  onClick={() => setAutoScroll(prev => !prev)}
                  aria-label="Toggle auto-scroll"
                >
                  <div className="chatbot__settings-toggle-slider"></div>
                </button>
              </div>

              {/* Sound Setting */}
              <div className="chatbot__settings-item">
                <div className="chatbot__settings-item-header">
                  <div className="chatbot__settings-item-icon">{soundEnabled ? '🔔' : '🔕'}</div>
                  <div className="chatbot__settings-item-info">
                    <div className="chatbot__settings-item-label">Sound Effects</div>
                    <div className="chatbot__settings-item-desc">
                      Play sound on new messages
                    </div>
                  </div>
                </div>
                <button 
                  className={`chatbot__settings-toggle${soundEnabled ? ' chatbot__settings-toggle--active' : ''}`}
                  onClick={() => setSoundEnabled(prev => !prev)}
                  aria-label="Toggle sound"
                >
                  <div className="chatbot__settings-toggle-slider"></div>
                </button>
              </div>

              {/* User Info */}
              {isLoggedIn && (
                <div className="chatbot__settings-section">
                  <div className="chatbot__settings-section-title">Account</div>
                  <div className="chatbot__settings-user-info">
                    <div className="chatbot__settings-user-avatar">
                      {(user?.username || user?.email || 'U').charAt(0).toUpperCase()}
                    </div>
                    <div className="chatbot__settings-user-details">
                      <div className="chatbot__settings-user-name">
                        {user?.username || user?.email}
                      </div>
                      <div className="chatbot__settings-user-email">
                        {user?.email}
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>

            <div className="chatbot__settings-footer">
              <button 
                className="chatbot__settings-btn chatbot__settings-btn--primary"
                onClick={closeSettingsModal}
              >
                Done
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default AIChatbot;


