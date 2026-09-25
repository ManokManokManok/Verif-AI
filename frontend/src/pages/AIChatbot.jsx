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
import DetectionSidebarFrame from '../components/DetectionSidebarFrame';
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
  const [expandedAnalysisImage, setExpandedAnalysisImage] = useState(null);
  const [isStartingDetection, setIsStartingDetection] = useState(false);
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingConversations, setIsLoadingConversations] = useState(false);
  const [disclaimer, setDisclaimer] = useState(null);
  const [showLogoutModal, setShowLogoutModal] = useState(false);
  const [showSettingsModal, setShowSettingsModal] = useState(false);
  const [autoScroll, setAutoScroll] = useState(() => localStorage.getItem('chatbot-autoscroll') !== 'false');
  const [soundEnabled, setSoundEnabled] = useState(() => localStorage.getItem('chatbot-sound') !== 'false');
  const [copiedIndex, setCopiedIndex] = useState(null);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    if (autoScroll) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  };

  const handleCopyMessage = (content, index) => {
    if (!content) return;
    navigator.clipboard.writeText(content);
    setCopiedIndex(index);
    setTimeout(() => setCopiedIndex(null), 2000);
  };

  const handlePromptSubmit = (promptText) => {
    if (!promptText || isLoading) return;
    setText(promptText);
    
    // Auto send prompt
    const fakeEvent = { preventDefault: () => {} };
    setTimeout(() => {
      handleSendMessageDirect(promptText);
    }, 50);
  };

  const renderFormattedContent = (content) => {
    if (!content) return null;

    const lines = content.split('\n');

    return lines.map((line, lineIndex) => {
      if (!line.trim() && lines.length > 1) {
        return <div key={lineIndex} className="chatbot__text-spacer" />;
      }

      const isBullet = /^\s*[\*\-•]\s+/.test(line);
      const cleanLine = isBullet ? line.replace(/^\s*[\*\-•]\s+/, '') : line;

      // Split bold markers **bold text**
      const parts = cleanLine.split(/(\*\*.*?\*\*)/g);
      const renderedParts = parts.map((part, pIdx) => {
        if (part.startsWith('**') && part.endsWith('**')) {
          return (
            <strong key={pIdx} className="chatbot__bold">
              {part.slice(2, -2)}
            </strong>
          );
        }
        return part;
      });

      if (isBullet) {
        return (
          <div key={lineIndex} className="chatbot__bullet-item">
            <span className="chatbot__bullet-dot">•</span>
            <span className="chatbot__bullet-text">{renderedParts}</span>
          </div>
        );
      }

      return (
        <div key={lineIndex} className="chatbot__text-line">
          {renderedParts}
        </div>
      );
    });
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

  const openDetection = () => {
    setIsStartingDetection(true);
    window.setTimeout(() => navigate('/detection'), 800);
  };

  // Handle navigation state for analysis-guided mode
  useEffect(() => {
    if (location.state) {
      const { conversationId, conversationType: navType, analysisContext: navContext, initialMessages } = location.state;

      if (location.state.imageAnalysis) {
        setConversationType('general');
        setCurrentConversationId(conversationId || null);
        setCurrentTitle('Image Scam Analysis');
        if (initialMessages) setMessages(initialMessages);
        fetchConversations();
        window.history.replaceState({}, document.title);
        return;
      }
      
      if (navType === 'analysis_guided' && conversationId) {
        console.log('[CHATBOT] Opening analysis-guided conversation:', conversationId);
        setConversationType('analysis_guided');
        setAnalysisContext(navContext);
        setCurrentConversationId(conversationId);
        
        // Load the conversation history
        loadAnalysisGuidedConversation(conversationId);
        
        // Clear navigation state to prevent reloading on refresh
        window.history.replaceState({}, document.title);
      } else if (conversationId) {
        console.log('[CHATBOT] Opening conversation:', conversationId);
        loadConversation(conversationId);
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

  const handleSendMessageDirect = async (messageText) => {
    const rawText = messageText || text;
    if (!rawText.trim() || isLoading) return;

    const userMessage = rawText.trim();
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
      if (conversationType === 'analysis_guided' && currentConversationId && accessToken) {
        // Analysis-guided conversation
        response = await sendAnalysisGuidedMessage(currentConversationId, userMessage, accessToken);
      } else {
        // General conversation (supports both logged-in and guest users)
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

  const handleSendMessage = (e) => {
    e.preventDefault();
    handleSendMessageDirect();
  };

  // Format time for message bubbles in user's local timezone
  const formatMessageTime = (timestamp) => {
    if (!timestamp) return '';
    let str = String(timestamp);
    if (!str.endsWith('Z') && !/[+-]\d{2}:\d{2}$/.test(str)) {
      str += 'Z';
    }
    const date = new Date(str);
    if (isNaN(date.getTime())) return '';
    return date.toLocaleTimeString([], {
      hour: '2-digit',
      minute: '2-digit',
      hour12: true,
    });
  };

  // Format date for sidebar
  const formatDate = (dateString) => {
    if (!dateString) return '';
    let str = String(dateString);
    if (!str.endsWith('Z') && !/[+-]\d{2}:\d{2}$/.test(str)) {
      str += 'Z';
    }
    const date = new Date(str);
    if (isNaN(date.getTime())) return '';
    const now = new Date();
    const diffDays = Math.floor((now - date) / (1000 * 60 * 60 * 24));
    
    if (diffDays === 0) return 'Today';
    if (diffDays === 1) return 'Yesterday';
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString();
  };

  return (
    <div className={`detect detect--chatbot page-enter${sidebarOpen ? ' detect--sidebar-open' : ''}`} style={{ height: '100vh', overflow: 'hidden' }}>
      <DetectionSidebarFrame
        variant="chatbot"
        isOpen={sidebarOpen}
        onToggle={() => setSidebarOpen((open) => !open)}
      >
        <button 
          className="detect__sidebtn" 
          type="button" 
          aria-label="New Detection"
          onClick={openDetection}
          title="New Detection"
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
      </DetectionSidebarFrame>

      <div className="detect__main" style={{
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
            {isLoggedIn && (
              <button className="nav__link nav__btn" type="button" onClick={() => navigate('/analytics')}>
                Your Verif-AI Journey
              </button>
            )}
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
          minHeight: 0,
          overflow: 'hidden',
          padding: '16px 20px 10px',
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
              padding: '20px 24px',
              display: 'flex',
              flexDirection: 'column',
            }}>
              {messages.length === 0 && (
                <div className="chatbot__empty-state">
                  {conversationType === 'analysis_guided' && analysisContext ? (
                    <div className="chatbot__empty-guided">
                      <div className="chatbot__empty-badge">
                        <span className="chatbot__empty-badge-dot"></span>
                        Analysis Guided Session
                      </div>
                      <h2 className="chatbot__empty-title">Inspection Guidance Ready</h2>
                      <p className="chatbot__empty-subtitle">
                        Ask any questions regarding the detection report below or request immediate next-step instructions.
                      </p>
                    </div>
                  ) : (
                    <>
                      <div className="chatbot__empty-header">
                        <div className="chatbot__empty-badge">
                          <span className="chatbot__empty-badge-dot"></span>
                          Verif-AI Security Assistant Active
                        </div>
                        <h2 className="chatbot__empty-title">How can I protect you today?</h2>
                        <p className="chatbot__empty-subtitle">
                          Ask any question or pick a suggested topic below to analyze security risks and spot scams.
                        </p>
                      </div>

                      <div className="chatbot__prompts-grid">
                        {[
                          {
                            icon: '🛡️',
                            title: 'Common Phishing Tactics',
                            desc: 'How do scammers use urgent SMS or email links to steal credentials?',
                            query: 'What are the most common phishing tactics used by scammers today?',
                          },
                          {
                            icon: '✉️',
                            title: 'Spotting Fake Emails',
                            desc: 'What key red flags identify spoofed email addresses and fake domain names?',
                            query: 'How can I spot a fake or spoofed email address?',
                          },
                          {
                            icon: '🚨',
                            title: 'Scam Recovery Steps',
                            desc: 'What immediate actions should I take if I accidentally clicked a phishing link?',
                            query: 'What should I do immediately if I entered my details on a suspicious website?',
                          },
                          {
                            icon: '💔',
                            title: 'Romance & Investment Scams',
                            desc: 'How do fake romance and crypto investment scams operate?',
                            query: 'What are the red flags of romance and crypto investment scams?',
                          },
                        ].map((prompt, idx) => (
                          <button
                            key={idx}
                            type="button"
                            className="chatbot__prompt-card"
                            onClick={() => handlePromptSubmit(prompt.query)}
                            disabled={isLoading}
                          >
                            <div className="chatbot__prompt-icon">{prompt.icon}</div>
                            <div className="chatbot__prompt-body">
                              <h4 className="chatbot__prompt-title">{prompt.title}</h4>
                              <p className="chatbot__prompt-desc">{prompt.desc}</p>
                            </div>
                            <span className="chatbot__prompt-arrow">&rarr;</span>
                          </button>
                        ))}
                      </div>
                    </>
                  )}
                </div>
              )}
              
              {/* Analysis Context Card - shown for analysis-guided conversations */}
              {conversationType === 'analysis_guided' && analysisContext && (
                <div className={`chatbot__analysis-card${analysisContext.is_scam ? ' chatbot__analysis-card--scam' : ' chatbot__analysis-card--safe'}`}>
                   {analysisContext.image_attachment?.data_url && (
                     <button
                       type="button"
                       className="chatbot__analysis-image-button"
                       onClick={() => setExpandedAnalysisImage(analysisContext.image_attachment.data_url)}
                       aria-label="View analyzed image larger"
                     >
                       <img
                         src={analysisContext.image_attachment.data_url}
                         alt="Analyzed submission"
                         className="chatbot__analysis-image"
                       />
                     </button>
                   )}

                  <div className="chatbot__analysis-top">
                    <div className="chatbot__analysis-header">
                      <span className={`chatbot__risk-pill ${analysisContext.is_scam ? 'chatbot__risk-pill--high' : 'chatbot__risk-pill--low'}`}>
                        {analysisContext.is_scam ? '🔴 High Risk Scam' : '🟢 Low Risk / Safe'}
                      </span>
                      {analysisContext.scam_type && (
                        <span className="chatbot__analysis-type-tag">
                          {analysisContext.scam_type}
                        </span>
                      )}
                    </div>

                    <div className="chatbot__analysis-confidence-row">
                      <div className="chatbot__confidence-bar-wrap">
                        <div className="chatbot__confidence-labels">
                          <span>Scam Likelihood</span>
                          <strong>{analysisContext.scam_score?.toFixed(1)}%</strong>
                        </div>
                        <div className="chatbot__confidence-track">
                          <div
                            className="chatbot__confidence-fill"
                            style={{ width: `${Math.min(100, Math.max(0, analysisContext.scam_score || 0))}%` }}
                          />
                        </div>
                      </div>
                    </div>
                  </div>

                  {expandedAnalysisImage && (
                    <div
                      className="chatbot__image-overlay"
                      role="dialog"
                      aria-modal="true"
                      aria-label="Enlarged analyzed image"
                      onClick={() => setExpandedAnalysisImage(null)}
                    >
                      <button
                        type="button"
                        className="chatbot__image-overlay-close"
                        onClick={() => setExpandedAnalysisImage(null)}
                        aria-label="Close enlarged image"
                      >
                        &times;
                      </button>
                      <img
                        src={expandedAnalysisImage}
                        alt="Enlarged analyzed submission"
                        className="chatbot__image-overlay-content"
                        onClick={(event) => event.stopPropagation()}
                      />
                    </div>
                  )}
                  
                  {analysisContext.summary && (
                    <div className="chatbot__analysis-summary">
                      <strong>Analysis Summary:</strong> {analysisContext.summary}
                    </div>
                  )}
                  
                  <div className="chatbot__analysis-quick-action">
                    <button
                      type="button"
                      className="chatbot__analysis-prompt-btn"
                      onClick={() => handlePromptSubmit('What immediate safety steps should I take based on this analysis?')}
                      disabled={isLoading}
                    >
                      ⚡ Quick Question: What immediate steps should I take next?
                    </button>
                  </div>
                </div>
              )}

              {messages.map((msg, index) => {
                const isUser = msg.role === 'user';
                const timeStr = formatMessageTime(msg.timestamp);

                const displayName = isUser
                  ? (user?.username || user?.email?.split('@')[0] || 'You')
                  : 'Verif-AI';

                return (
                  <div
                    key={index}
                    className={`chatbot__message-wrap${isUser ? ' chatbot__message-wrap--user' : ''}`}
                  >
                    <div className="chatbot__message-header">
                      <span className="chatbot__avatar">
                        {isUser ? '👤' : '🤖'}
                      </span>
                      <span className={`chatbot__message-name${isUser ? ' chatbot__message-name--user' : ''}`}>
                        {displayName}
                      </span>
                    </div>

                    {/* Bubble */}
                    <div
                      className={`chatbot__message-bubble${isUser ? ' chatbot__message-bubble--user' : ''}${msg.isError ? ' chatbot__message-bubble--error' : ''}`}
                    >
                      <div className="chatbot__message-content">
                        {msg.attachment?.data_url && (
                          <img
                            src={msg.attachment.data_url}
                            alt="Submitted for scam analysis"
                            className="chatbot__message-image"
                          />
                        )}
                        {renderFormattedContent(msg.content)}
                      </div>

                      {!isUser && !msg.isError && (
                        <div className="chatbot__message-actions">
                          <button
                            type="button"
                            className="chatbot__copy-btn"
                            onClick={() => handleCopyMessage(msg.content, index)}
                            title="Copy response to clipboard"
                          >
                            {copiedIndex === index ? '✓ Copied' : '📋 Copy'}
                          </button>
                        </div>
                      )}
                    </div>

                    <div className="chatbot__message-time">
                      {timeStr}
                    </div>
                  </div>
                );
              })}

              {isLoading && (
                <div className="chatbot__message-wrap">
                  <div className="chatbot__message-header">
                    <span className="chatbot__avatar">🤖</span>
                    <span className="chatbot__message-name">Verif-AI</span>
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

          {/* Quick Action Chips Bar above input */}
          <div className="chatbot__quick-chips">
            <button
              type="button"
              className="chatbot__chip"
              onClick={() => handlePromptSubmit('How do I verify if a link or message is safe?')}
              disabled={isLoading}
            >
              🛡️ How to verify links
            </button>
            <button
              type="button"
              className="chatbot__chip"
              onClick={() => handlePromptSubmit('What are signs of phishing emails?')}
              disabled={isLoading}
            >
              📧 Signs of fake emails
            </button>
            <button
              type="button"
              className="chatbot__chip"
              onClick={() => handlePromptSubmit('What should I do if my bank account details were compromised?')}
              disabled={isLoading}
            >
              🚨 Compromised account steps
            </button>
          </div>

          <form onSubmit={handleSendMessage} className="detect__inputRow detect__inputRow--chatbot" style={{ flexShrink: 0 }}>
            <button className="detect__plus" type="button" aria-label="Upload" title="Upload attachment (coming soon)">
              +
            </button>
            <input
              className="detect__input"
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="Ask Verif-AI about scam prevention, link safety, or suspicious messages..."
              disabled={isLoading}
              maxLength={2000}
            />
            <button 
              className={`detect__cta ${text.trim() ? 'detect__cta--active' : ''}`}
              type="submit"
              disabled={isLoading || !text.trim()}
            >
              {isLoading ? (
                <>
                  <span className="settings-spinner"></span>
                  Sending...
                </>
              ) : (
                <>
                  <span>Send</span>
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <line x1="22" y1="2" x2="11" y2="13"></line>
                    <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
                  </svg>
                </>
              )}
            </button>
          </form>
        </main>

        <footer className="detect__footer" style={{ flexShrink: 0 }}>
          <div className="detect__copyright">
            © 2026 VerifAI Technologies Inc. All rights reserved.
          </div>
        </footer>
      </div>

      {isStartingDetection && (
        <div className="detect__navigation-loading" role="status" aria-live="polite">
          <div className="detect__navigation-card">
            <div className="detect__navigation-mark" aria-hidden="true">
              <span />
              <span />
              <span />
            </div>
            <div className="detect__navigation-copy">
              <strong>Opening Detection</strong>
              <span>Loading the scam checker...</span>
            </div>
            <div className="detect__navigation-progress" aria-hidden="true">
              <span />
            </div>
          </div>
        </div>
      )}

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


