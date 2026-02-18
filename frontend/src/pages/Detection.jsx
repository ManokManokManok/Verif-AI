import { useState, useEffect, useRef } from 'react';
import { getChatHistory, detectScamRequest } from '../api/client';
import { getAnalysisDetail } from '../api/analysis';
import { anchorAnalysis, verifyAnalysis } from '../api/blockchain';
import { getAnalysisConversation } from '../api/chatbot';
import mockChatHistory from '../mock_chat_history.json';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { validateMessage, escapeHtml, CONSTRAINTS } from '../utils/validation';
import { ReportModal } from '../components/reports';
import LogoutConfirmModal from '../components/auth/LogoutConfirmModal';

const ANALYSIS_STEPS = [
  'Analyzing message...',
  'Running classifier...',
  'Generating summary...',
];

function Detection() {
  const navigate = useNavigate();
  const { isLoggedIn, isAdmin, logout, user, accessToken } = useAuth();
  const [text, setText] = useState('');
  const [isFocused, setIsFocused] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);
  const [isDetecting, setIsDetecting] = useState(false);
  const [detectionResult, setDetectionResult] = useState(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [chatHistory, setChatHistory] = useState([]);
  const [validationError, setValidationError] = useState(null);
  const [rateLimitError, setRateLimitError] = useState(null);
  const [analysisStep, setAnalysisStep] = useState(0);
  const [analysisProgress, setAnalysisProgress] = useState(0);
  const [graphScamWidth, setGraphScamWidth] = useState(0);
  const [graphLegitWidth, setGraphLegitWidth] = useState(0);
  const [isAnchoring, setIsAnchoring] = useState(false);
  const [isVerifying, setIsVerifying] = useState(false);
  const [verificationResult, setVerificationResult] = useState(null);
  const [isOpeningGuidance, setIsOpeningGuidance] = useState(false);
  const [isReportModalOpen, setIsReportModalOpen] = useState(false);
  const [showLogoutModal, setShowLogoutModal] = useState(false);
  const progressIntervalRef = useRef(null);
  const stepIntervalRef = useRef(null);

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

  // Analyzing animation: step labels + simulated progress
  useEffect(() => {
    if (!isDetecting) {
      setAnalysisStep(0);
      setAnalysisProgress(0);
      if (progressIntervalRef.current) clearInterval(progressIntervalRef.current);
      if (stepIntervalRef.current) clearInterval(stepIntervalRef.current);
      return;
    }
    setAnalysisStep(0);
    setAnalysisProgress(0);

    const STEP_MS = 1400;
    const PROGRESS_MS = 120;
    const MAX_PROGRESS = 92;

    stepIntervalRef.current = setInterval(() => {
      setAnalysisStep((prev) => (prev + 1) % ANALYSIS_STEPS.length);
    }, STEP_MS);

    progressIntervalRef.current = setInterval(() => {
      setAnalysisProgress((prev) => {
        if (prev >= MAX_PROGRESS) return prev;
        return prev + 2;
      });
    }, PROGRESS_MS);

    return () => {
      if (progressIntervalRef.current) clearInterval(progressIntervalRef.current);
      if (stepIntervalRef.current) clearInterval(stepIntervalRef.current);
    };
  }, [isDetecting]);

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
    setGraphScamWidth(0);
    setGraphLegitWidth(0);
  };

  // Animate graph bar from 0 to result values when result appears
  useEffect(() => {
    if (!detectionResult) return;
    setGraphScamWidth(0);
    setGraphLegitWidth(0);
    const t = requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        setGraphScamWidth(detectionResult.scam_score ?? 0);
        setGraphLegitWidth(detectionResult.legit_score ?? 0);
      });
    });
    return () => cancelAnimationFrame(t);
  }, [detectionResult]);

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

  const handleAskAIGuidance = async () => {
    if (!detectionResult?.ref_id || !isLoggedIn || isOpeningGuidance) return;

    setIsOpeningGuidance(true);
    try {
      // Get or create the analysis-guided conversation
      const conversation = await getAnalysisConversation(detectionResult.ref_id, accessToken);
      console.log('[GUIDANCE CONVERSATION]', conversation);
      
      // Navigate to chatbot page with conversation ID and analysis context
      navigate('/chatbot', {
        state: {
          conversationId: conversation.conversation_id,
          conversationType: 'analysis_guided',
          analysisContext: conversation.analysis_context,
          isNew: conversation.is_new
        }
      });
    } catch (error) {
      console.error('[GUIDANCE ERROR]', error);
      alert(`Error opening guidance: ${error.message || 'Failed to open AI guidance'}`);
    } finally {
      setIsOpeningGuidance(false);
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

        <main className={`detect__content ${detectionResult ? 'detect__content--results' : ''}`}>
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

              {/* Analyzing progress animation */}
              {isDetecting && (
                <div className="detect__analyzing" role="status" aria-live="polite">
                  <div className="detect__analyzing-step">
                    {ANALYSIS_STEPS[analysisStep]}
                  </div>
                  <div className="detect__analyzing-bar">
                    <div
                      className="detect__analyzing-fill"
                      style={{ width: `${analysisProgress}%` }}
                    />
                    <div className="detect__analyzing-shine" aria-hidden="true" />
                  </div>
                  <div className="detect__analyzing-dots">
                    <span className="detect__analyzing-dot" />
                    <span className="detect__analyzing-dot" />
                    <span className="detect__analyzing-dot" />
                  </div>
                </div>
              )}

              {/* Character count */}
              {text.length > 0 && (
                <div className={`detect__charCount ${text.length > CONSTRAINTS.message.maxLength * 0.9 ? 'detect__charCount--warning' : ''}`}>
                  {text.length} / {CONSTRAINTS.message.maxLength}
                </div>
              )}
            </>
          ) : (
            <div className="detect__results" role="region" aria-label="Analysis results">
              <div className="detect__resultsHeader detect__resultsHeader--animate">
                <h2 className="detect__resultsTitle">Analysis Results</h2>
                <div className="detect__resultsActions">
                  {isLoggedIn && (
                    <>
                      <button 
                        className="detect__reportBtn" 
                        type="button"
                        onClick={() => setIsReportModalOpen(true)}
                        title="Report an issue with this analysis"
                      >
                        🚩 Report Issue
                      </button>
                      <button
                        className="detect__newAnalysis"
                        type="button"
                        onClick={handleAskAIGuidance}
                        disabled={isOpeningGuidance}
                        title="Get personalized guidance based on this analysis"
                      >
                        {isOpeningGuidance ? 'Opening...' : '💬 Ask AI for Guidance'}
                      </button>
                    </>
                  )}
                  <button 
                    className="detect__newAnalysis" 
                    type="button"
                    onClick={handleNewAnalysis}
                  >
                    ✨ New Analysis
                  </button>
                </div>
              </div>

              <div className="detect__resultsGrid">
                {/* Summary & Original Message */}
                <div className="detect__resultCard detect__resultCard--summary detect__resultCard--animate">
                  <h3 className="detect__cardTitle">Summary</h3>
                  <p className="detect__summary">{detectionResult.summary}</p>
                  <h4 className="detect__cardSubtitle">Analyzed Message</h4>
                  <div className="detect__originalMessage">
                    {detectionResult.message}
                  </div>
                </div>

                {/* Likelihood Graph */}
                <div className="detect__resultCard detect__resultCard--graph detect__resultCard--animate">
                  <h3 className="detect__cardTitle">Scam Likelihood</h3>
                  <div className="detect__graph">
                    <div className="detect__graphBar">
                      <div
                        className="detect__graphFill detect__graphFill--scam"
                        style={{ width: `${graphScamWidth}%` }}
                      />
                      <div
                        className="detect__graphFill detect__graphFill--legit"
                        style={{ width: `${graphLegitWidth}%` }}
                      />
                    </div>
                    <div className="detect__graphLabels">
                      <div className="detect__graphLabel detect__graphLabel--scam">
                        <span className="detect__graphDot detect__graphDot--scam" />
                        Scam: {(detectionResult.scam_score ?? 0).toFixed(1)}%
                      </div>
                      <div className="detect__graphLabel detect__graphLabel--legit">
                        <span className="detect__graphDot detect__graphDot--legit" />
                        Legit: {(detectionResult.legit_score ?? 0).toFixed(1)}%
                      </div>
                    </div>
                  </div>
                  <div className="detect__verdict detect__verdict--animate">
                    <span className={`detect__verdictLabel ${detectionResult.is_scam ? 'detect__verdictLabel--scam' : 'detect__verdictLabel--legit'}`}>
                      {detectionResult.label}
                    </span>
                  </div>
                </div>

                {/* Details & Markers */}
                <div className="detect__resultCard detect__resultCard--details detect__resultCard--animate">
                  <h3 className="detect__cardTitle">Details</h3>
                  {detectionResult.is_scam && (
                    <div className="detect__scamType detect__scamType--animate">
                      <div className="detect__detailLabel">Scam Type</div>
                      <div className="detect__detailValue">{detectionResult.scam_type}</div>
                      <div className="detect__confidence">
                        Confidence: {(detectionResult.type_confidence ?? 0).toFixed(1)}%
                      </div>
                    </div>
                  )}
                  {detectionResult.key_markers && detectionResult.key_markers.length > 0 && (
                    <div className="detect__markers">
                      <h4 className="detect__markersTitle">Key Linguistic Markers</h4>
                      <ul className="detect__markersList">
                        {detectionResult.key_markers.map((marker, idx) => (
                          <li key={idx} className="detect__markerItem detect__markerItem--animate" style={{ animationDelay: `${0.35 + idx * 0.06}s` }}>
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

      {/* Report Modal */}
      <ReportModal
        isOpen={isReportModalOpen}
        onClose={() => setIsReportModalOpen(false)}
        analysisId={detectionResult?.id}
        analysisRefId={detectionResult?.ref_id}
      />

      {/* Logout Confirmation Modal */}
      <LogoutConfirmModal
        isOpen={showLogoutModal}
        onConfirm={confirmLogout}
        onCancel={cancelLogout}
      />
    </div>
  );
}

export default Detection;


