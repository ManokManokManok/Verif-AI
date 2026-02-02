import { useState, useEffect } from 'react';
import { getChatHistory } from '../api/client';
import { getAnalysisDetail } from '../api/analysis';
import mockChatHistory from '../mock_chat_history.json';
import { useNavigate } from 'react-router-dom';
import { detectScamRequest } from '../api/client';
import { useAuth } from '../context/AuthContext';
import { validateMessage, escapeHtml, CONSTRAINTS } from '../utils/validation';

function Detection() {
  const navigate = useNavigate();
  const { isLoggedIn, isAdmin, logout, user } = useAuth();
  const [text, setText] = useState('');
  const [isFocused, setIsFocused] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);
  const [isDetecting, setIsDetecting] = useState(false);
  const [detectionResult, setDetectionResult] = useState(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [chatHistory, setChatHistory] = useState([]);
  const [validationError, setValidationError] = useState(null);
  const [rateLimitError, setRateLimitError] = useState(null);

  useEffect(() => {
    async function fetchHistory() {
      try {
        const res = await getChatHistory();
        if (res.history && res.history.length > 0) {
          setChatHistory(res.history);
        } else {
          setChatHistory(mockChatHistory);
        }
      } catch (err) {
        setChatHistory(mockChatHistory);
      }
    }
    fetchHistory();
  }, []);

  // Handle click on a chat history item
  const handleChatClick = async (chat) => {
    try {
      const detail = await getAnalysisDetail(chat.id);
      setDetectionResult(detail);
      setSidebarOpen(false);
    } catch (err) {
      alert('Failed to load analysis details.');
    }
  };

  const handleLogout = async () => {
    await logout();
    navigate('/');
  };

  const handleTextChange = (e) => {
    const newText = e.target.value;
    setText(newText);
    
    // Clear previous errors when user types
    setValidationError(null);
    setRateLimitError(null);
    
    // Validate on change for immediate feedback
    if (newText.length > CONSTRAINTS.message.maxLength) {
      setValidationError(`Message exceeds ${CONSTRAINTS.message.maxLength} character limit`);
    }
    
    // Auto-expand when text grows
    if (newText.length > 50 && !isExpanded) {
      setIsExpanded(true);
    } else if (newText.length === 0) {
      setIsExpanded(false);
    }
  };

  const handleDetect = async () => {
    if (!text.trim() || isDetecting) return;
    
    // Client-side validation
    const validation = validateMessage(text);
    if (!validation.valid) {
      setValidationError(validation.error);
      return;
    }

    setIsDetecting(true);
    setDetectionResult(null);
    setValidationError(null);
    setRateLimitError(null);
    
    try {
      const result = await detectScamRequest(text);
      console.log('[DETECTION RESULT]', result);
      setDetectionResult(result);
    } catch (error) {
      console.error('[DETECTION ERROR]', error);
      
      // Handle rate limiting gracefully
      if (error.isRateLimited) {
        setRateLimitError(`Too many requests. Please wait ${error.retryAfter} and try again.`);
      } else if (error.isValidationError) {
        setValidationError(error.message);
      } else {
        alert(`Error: ${error.message || 'Failed to detect scam'}`);
      }
    } finally {
      setIsDetecting(false);
    }
  };

  const handleNewAnalysis = () => {
    setDetectionResult(null);
    setText('');
    setIsExpanded(false);
    setValidationError(null);
    setRateLimitError(null);
  };

  const handleAnchor = async () => {
    if (!detectionResult?.ref_id || isAnchoring) return;
    
    setIsAnchoring(true);
    try {
      const result = await anchorAnalysis(detectionResult.ref_id);
      console.log('[ANCHOR RESULT]', result);
      // Update the detection result with anchored status
      setDetectionResult(prev => ({
        ...prev,
        is_anchored: true,
        tx_hash: result.tx_hash,
        block_number: result.block_number
      }));
      alert('Analysis anchored to blockchain successfully!');
    } catch (error) {
      console.error('[ANCHOR ERROR]', error);
      alert(`Error anchoring: ${error.message || 'Failed to anchor'}`);
    } finally {
      setIsAnchoring(false);
    }
  };

  const handleVerify = async () => {
    if (!detectionResult?.ref_id || isVerifying) return;
    
    setIsVerifying(true);
    setVerificationResult(null);
    try {
      const result = await verifyAnalysis(detectionResult.ref_id);
      console.log('[VERIFY RESULT]', result);
      setVerificationResult(result);
    } catch (error) {
      console.error('[VERIFY ERROR]', error);
      setVerificationResult({ verified: false, error: error.message });
    } finally {
      setIsVerifying(false);
    }
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
                <div
                  className="detect__chat-item"
                  key={chat.id}
                  onClick={() => handleChatClick(chat)}
                  style={{ cursor: 'pointer' }}
                >
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
          {!detectionResult ? (
            <>
              <h1 className="detect__title">Welcome to VerfAI fraud detection</h1>
              <p className="detect__subtitle">
                Write the promo/message you want to analyze, or press the plus button to submit a file
              </p>

              {/* Error messages */}
              {validationError && (
                <div className="detect__error detect__error--validation">
                  {validationError}
                </div>
              )}
              {rateLimitError && (
                <div className="detect__error detect__error--ratelimit">
                  {rateLimitError}
                </div>
              )}

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
                  maxLength={CONSTRAINTS.message.maxLength}
                />
                <button 
                  className={`detect__cta ${text.trim() && !validationError ? 'detect__cta--active' : ''}`}
                  type="button"
                  disabled={!text.trim() || isDetecting || validationError}
                  onClick={handleDetect}
                >
                  {isDetecting ? 'Analyzing...' : 'Detect'}
                </button>
              </div>
              
              {/* Character count */}
              {text.length > 0 && (
                <div className={`detect__charCount ${text.length > CONSTRAINTS.message.maxLength * 0.9 ? 'detect__charCount--warning' : ''}`}>
                  {text.length} / {CONSTRAINTS.message.maxLength}
                </div>
              )}
            </>
          ) : (
            <div className="detect__results">
              <div className="detect__resultsHeader">
                <h2 className="detect__resultsTitle">Analysis Results</h2>
                <button 
                  className="detect__newAnalysis" 
                  type="button"
                  onClick={handleNewAnalysis}
                >
                  PROTOTYPE ONLY | New Analysis
                </button>
              </div>

              <div className="detect__resultsGrid">
                {/* Left Column: Summary & Original Message */}
                <div className="detect__resultCard detect__resultCard--summary">
                  <h3 className="detect__cardTitle">Summary</h3>
                  <p className="detect__summary">{detectionResult.summary}</p>
                  
                  <h4 className="detect__cardSubtitle">Analyzed Message:</h4>
                  <div className="detect__originalMessage">
                    {detectionResult.message}
                  </div>
                </div>

                {/* Middle Column: Likelihood Graph */}
                <div className="detect__resultCard detect__resultCard--graph">
                  <h3 className="detect__cardTitle">Scam Likelihood</h3>
                  <div className="detect__graph">
                    <div className="detect__graphBar">
                      <div 
                        className="detect__graphFill detect__graphFill--scam"
                        style={{ width: `${detectionResult.scam_score}%` }}
                      />
                      <div 
                        className="detect__graphFill detect__graphFill--legit"
                        style={{ width: `${detectionResult.legit_score}%` }}
                      />
                    </div>
                    <div className="detect__graphLabels">
                      <div className="detect__graphLabel detect__graphLabel--scam">
                        <span className="detect__graphDot detect__graphDot--scam" />
                        Scam: {detectionResult.scam_score.toFixed(1)}%
                      </div>
                      <div className="detect__graphLabel detect__graphLabel--legit">
                        <span className="detect__graphDot detect__graphDot--legit" />
                        Legit: {detectionResult.legit_score.toFixed(1)}%
                      </div>
                    </div>
                  </div>
                  
                  <div className="detect__verdict">
                    <span className={`detect__verdictLabel ${detectionResult.is_scam ? 'detect__verdictLabel--scam' : 'detect__verdictLabel--legit'}`}>
                      {detectionResult.label}
                    </span>
                  </div>
                </div>

                {/* Right Column: Percentages & Key Factors */}
                <div className="detect__resultCard detect__resultCard--details">
                  <h3 className="detect__cardTitle">Details</h3>
                  
                  {detectionResult.is_scam && (
                    <div className="detect__scamType">
                      <div className="detect__detailLabel">Scam Type:</div>
                      <div className="detect__detailValue">{detectionResult.scam_type}</div>
                      <div className="detect__confidence">
                        Confidence: {detectionResult.type_confidence.toFixed(1)}%
                      </div>
                    </div>
                  )}

                  {detectionResult.key_markers && detectionResult.key_markers.length > 0 && (
                    <div className="detect__markers">
                      <h4 className="detect__markersTitle">Key Linguistic Markers:</h4>
                      <ul className="detect__markersList">
                        {detectionResult.key_markers.map((marker, idx) => (
                          <li key={idx} className="detect__markerItem">
                            {marker}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}
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


