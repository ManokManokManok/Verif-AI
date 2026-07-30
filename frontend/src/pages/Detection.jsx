import { useState, useEffect, useRef } from 'react';
import { getChatHistory, detectScamRequest } from '../api/client';
import { getAnalysisDetail, deleteAnalysisHistoryItem, deleteAllAnalysisHistory } from '../api/analysis';
import { getAnalysisConversation } from '../api/chatbot';
import mockChatHistory from '../mock_chat_history.json';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { validateMessage, escapeHtml, CONSTRAINTS } from '../utils/validation';
import { ReportModal } from '../components/reports';
import LogoutConfirmModal from '../components/auth/LogoutConfirmModal';
import ReactCrop from 'react-image-crop';
import 'react-image-crop/dist/ReactCrop.css';
import Tesseract from 'tesseract.js';

const ANALYSIS_STEPS = [
  'Analyzing message...',
  'Running classifier...',
  'Generating summary...',
];

function Detection() {
  const navigate = useNavigate();
  const { isLoggedIn, isAdmin, logout, user, accessToken } = useAuth();
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [text, setText] = useState('');
  const [isFocused, setIsFocused] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);
  const [isDetecting, setIsDetecting] = useState(false);
  const [detectionResult, setDetectionResult] = useState(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [chatHistory, setChatHistory] = useState([]);
  const [isDeletingHistoryId, setIsDeletingHistoryId] = useState(null);
  const [isDeletingAllHistory, setIsDeletingAllHistory] = useState(false);
  const [validationError, setValidationError] = useState(null);
  const [rateLimitError, setRateLimitError] = useState(null);
  const [analysisStep, setAnalysisStep] = useState(0);
  const [analysisProgress, setAnalysisProgress] = useState(0);
  const [graphScamWidth, setGraphScamWidth] = useState(0);
  const [graphLegitWidth, setGraphLegitWidth] = useState(0);
  const [isOpeningGuidance, setIsOpeningGuidance] = useState(false);
  const [isReportModalOpen, setIsReportModalOpen] = useState(false);
  const [showLogoutModal, setShowLogoutModal] = useState(false);
  const progressIntervalRef = useRef(null);
  const stepIntervalRef = useRef(null);
  
  // Image OCR states
  const [selectedImage, setSelectedImage] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);
  const [isExtractingText, setIsExtractingText] = useState(false);
  const [ocrProgress, setOcrProgress] = useState(0);
  const [showCropModal, setShowCropModal] = useState(false);
  const [crop, setCrop] = useState({ unit: '%', x: 5, y: 5, width: 90, height: 90 });
  const [completedCrop, setCompletedCrop] = useState(null);
  const [cropImageElement, setCropImageElement] = useState(null);
  const fileInputRef = useRef(null);

  const refreshHistory = async () => {
    if (!isLoggedIn) {
      setChatHistory([]);
      return;
    }

    try {
      const res = await getChatHistory();
      if (Array.isArray(res?.history)) {
        // For authenticated users, respect empty history (do not fall back to mock data).
        setChatHistory(res.history);
        return;
      }
    } catch (err) {
      // Fall through to fallback behavior below.
    }

    setChatHistory([]);
  };

  useEffect(() => {
    refreshHistory();
  }, [isLoggedIn]);

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
      console.log('[HISTORY DETAIL]', detail);
      console.log('[HISTORY DETAIL needs_review]', detail.needs_review);
      setDetectionResult(detail);
      setSidebarOpen(false);
    } catch (err) {
      alert('Failed to load analysis details.');
    }
  };

  const handleDeleteHistoryItem = async (analysisId) => {
    if (!isLoggedIn || !analysisId || isDeletingHistoryId === analysisId) return;

    const confirmed = window.confirm('Delete this detection history item?');
    if (!confirmed) return;

    setIsDeletingHistoryId(analysisId);
    try {
      await deleteAnalysisHistoryItem(analysisId);
      if (detectionResult?.id === analysisId) {
        setDetectionResult(null);
      }
      await refreshHistory();
    } catch (err) {
      alert('Failed to delete history item. Please try again.');
    } finally {
      setIsDeletingHistoryId(null);
    }
  };

  const handleDeleteAllHistory = async () => {
    if (!isLoggedIn || isDeletingAllHistory) return;

    const confirmed = window.confirm('Delete all detection history? This will remove it from your view.');
    if (!confirmed) return;

    setIsDeletingAllHistory(true);
    try {
      await deleteAllAnalysisHistory();
      setDetectionResult(null);
      await refreshHistory();
    } catch (err) {
      alert('Failed to delete detection history. Please try again.');
    } finally {
      setIsDeletingAllHistory(false);
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
      
      // Refresh history list to include the new detection
      await refreshHistory();
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
    // Clear image states
    setSelectedImage(null);
    setImagePreview(null);
    setIsExtractingText(false);
    setOcrProgress(0);
    setShowCropModal(false);
    setCropImageElement(null);
    setCompletedCrop(null);
  };

  // Handle image file selection
  const handleImageSelect = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Validate file type
    if (!file.type.startsWith('image/')) {
      setValidationError('Please select a valid image file (PNG, JPG, etc.)');
      return;
    }

    // Validate file size (max 10MB)
    const maxSize = 10 * 1024 * 1024;
    if (file.size > maxSize) {
      setValidationError('Image file is too large. Maximum size is 10MB.');
      return;
    }

    setSelectedImage(file);
    setValidationError(null);
    setRateLimitError(null);

    // Create preview
    const reader = new FileReader();
    reader.onload = (event) => {
      setImagePreview(event.target.result);
      setCrop({ unit: '%', x: 5, y: 5, width: 90, height: 90 });
      setCompletedCrop(null);
      setShowCropModal(true);
    };
    reader.readAsDataURL(file);
  };

  const getCroppedImageBlob = async () => {
    if (!selectedImage) return null;

    if (!cropImageElement || !completedCrop?.width || !completedCrop?.height) {
      return selectedImage;
    }

    const scaleX = cropImageElement.naturalWidth / cropImageElement.width;
    const scaleY = cropImageElement.naturalHeight / cropImageElement.height;
    const canvas = document.createElement('canvas');

    canvas.width = Math.max(1, Math.floor(completedCrop.width * scaleX));
    canvas.height = Math.max(1, Math.floor(completedCrop.height * scaleY));

    const ctx = canvas.getContext('2d');
    if (!ctx) return selectedImage;

    ctx.drawImage(
      cropImageElement,
      completedCrop.x * scaleX,
      completedCrop.y * scaleY,
      completedCrop.width * scaleX,
      completedCrop.height * scaleY,
      0,
      0,
      canvas.width,
      canvas.height,
    );

    return new Promise((resolve, reject) => {
      canvas.toBlob((blob) => {
        if (blob) {
          resolve(blob);
          return;
        }
        reject(new Error('Failed to crop image'));
      }, 'image/png');
    });
  };

  const handleCropAndExtract = async () => {
    if (!selectedImage) return;

    try {
      const croppedBlob = await getCroppedImageBlob();
      setShowCropModal(false);
      await extractTextFromImage(croppedBlob || selectedImage);
    } catch (error) {
      console.error('[CROP ERROR]', error);
      setValidationError('Failed to crop image. Please try again.');
      setShowCropModal(false);
    }
  };

  // Extract text from image using Tesseract.js
  const extractTextFromImage = async (imageFile) => {
    setIsExtractingText(true);
    setOcrProgress(0);
    setText(''); // Clear existing text

    try {
      const result = await Tesseract.recognize(
        imageFile,
        'eng', // Language
        {
          logger: (m) => {
            // Update progress
            if (m.status === 'recognizing text') {
              setOcrProgress(Math.round(m.progress * 100));
            }
          },
        }
      );

      const extractedText = (result.data.text || '')
        .replace(/\s+/g, ' ')
        .trim();
      
      if (!extractedText) {
        setValidationError('No text found in the image. Please try another image or enter text manually.');
        setIsExtractingText(false);
        return;
      }

      // Set the extracted text
      setText(extractedText);
      setIsExpanded(true);
      setIsExtractingText(false);
      setOcrProgress(100);
      
      console.log('[OCR] Extracted text:', extractedText);
    } catch (error) {
      console.error('[OCR ERROR]', error);
      setValidationError('Failed to extract text from image. Please try again or enter text manually.');
      setIsExtractingText(false);
      setOcrProgress(0);
    }
  };

  // Trigger file input click
  const handlePlusButtonClick = () => {
    if (isDetecting || isExtractingText) return;
    fileInputRef.current?.click();
  };

  // Remove selected image
  const handleRemoveImage = () => {
    setSelectedImage(null);
    setImagePreview(null);
    setIsExtractingText(false);
    setOcrProgress(0);
    setShowCropModal(false);
    setCropImageElement(null);
    setCompletedCrop(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
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

  const handleAskAIGuidance = async () => {
    if (!detectionResult || isOpeningGuidance) return;

    setIsOpeningGuidance(true);
    try {
      if (isLoggedIn && accessToken && detectionResult.ref_id) {
        // Get or create the analysis-guided conversation for authenticated user
        const conversation = await getAnalysisConversation(detectionResult.ref_id, accessToken);
        console.log('[GUIDANCE CONVERSATION]', conversation);
        
        navigate('/chatbot', {
          state: {
            conversationId: conversation.conversation_id,
            conversationType: 'analysis_guided',
            analysisContext: conversation.analysis_context,
            isNew: conversation.is_new
          }
        });
      } else {
        // Guest mode: Navigate directly to chatbot page with analysis context
        navigate('/chatbot', {
          state: {
            conversationType: 'analysis_guided',
            analysisContext: {
              ref_id: detectionResult.ref_id || 'guest-temp-ref',
              is_scam: detectionResult.is_scam,
              scam_type: detectionResult.scam_type || 'Scam Detection',
              scam_score: detectionResult.scam_score,
              legit_score: detectionResult.legit_score,
              summary: detectionResult.summary,
              key_markers: detectionResult.key_markers || [],
            }
          }
        });
      }
    } catch (error) {
      console.error('[GUIDANCE ERROR]', error);
      // Fallback: navigate directly with context
      navigate('/chatbot', {
        state: {
          conversationType: 'analysis_guided',
          analysisContext: {
            ref_id: detectionResult.ref_id || 'guest-temp-ref',
            is_scam: detectionResult.is_scam,
            scam_type: detectionResult.scam_type || 'Scam Detection',
            scam_score: detectionResult.scam_score,
            legit_score: detectionResult.legit_score,
            summary: detectionResult.summary,
            key_markers: detectionResult.key_markers || [],
          }
        }
      });
    } finally {
      setIsOpeningGuidance(false);
    }
  };

  return (
    <div className="detect page-enter">
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
            {isLoggedIn ? (
              <>
                {chatHistory.length > 0 && (
                  <div className="detect__chat-actions">
                    <button
                      className="detect__chat-clear"
                      type="button"
                      onClick={handleDeleteAllHistory}
                      disabled={isDeletingAllHistory}
                    >
                      {isDeletingAllHistory ? 'Deleting...' : 'Clear All'}
                    </button>
                  </div>
                )}
                <div className="detect__chat-list">
                  {chatHistory.map((chat) => (
                    <div
                      className="detect__chat-item"
                      key={chat.id}
                      onClick={() => handleChatClick(chat)}
                      style={{ cursor: 'pointer' }}
                    >
                      <div className="detect__chat-item-header">
                        <div className="detect__chat-item-title">{chat.title}</div>
                        {chat.id && (
                          <button
                            className="detect__chat-delete"
                            type="button"
                            onClick={(event) => {
                              event.stopPropagation();
                              handleDeleteHistoryItem(chat.id);
                            }}
                            disabled={isDeletingHistoryId === chat.id}
                          >
                            {isDeletingHistoryId === chat.id ? '...' : 'Delete'}
                          </button>
                        )}
                      </div>
                      <div className="detect__chat-item-preview">{chat.description}</div>
                      <div className="detect__chat-item-time">{chat.timestamp}</div>
                    </div>
                  ))}
                </div>
              </>
            ) : (
              <div className="chatbot__anonymous-box" style={{ margin: '15px' }}>
                <div className="chatbot__anonymous-icon">🛡️</div>
                <div className="chatbot__anonymous-text">
                  You are using guest mode. Log in to save your analysis history across devices.
                </div>
                <button
                  className="chatbot__anonymous-login"
                  type="button"
                  onClick={() => navigate('/login')}
                >
                  Login / Sign Up
                </button>
              </div>
            )}
          </div>
        )}
        {!sidebarOpen && (
          <>
            <button className="detect__sidebtn" type="button" aria-label="Edit">
              ✎
            </button>
            <div className="detect__spacer" />
            <button className="detect__sidebtn" type="button" aria-label="Settings" onClick={() => navigate('/settings')}>
              ⚙
            </button>
          </>
        )}
      </aside>

      <div className="detect__main" style={{ transition: 'margin-left 0.3s cubic-bezier(.4,2,.6,1)', marginLeft: sidebarOpen ? 320 : 72 }}>
        <header className="nav nav--detect">
          <div className="brand brand--small">Verif-AI Detection</div>
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
                onClick={() => navigate('/admin')}
              >
                Admin
              </button>
            )}
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

        <main className={`detect__content ${detectionResult ? 'detect__content--results' : ''}`}>
          {!detectionResult ? (
            <>
              <h1 className="detect__title">Welcome to VerifAI</h1>
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

              {/* Image preview */}
              {imagePreview && (
                <div className="detect__imagePreview">
                  <div className="detect__imagePreview-header">
                    <span className="detect__imagePreview-title">📷 Selected Image</span>
                    <div className="detect__imagePreview-actions">
                      <button
                        className="detect__imagePreview-crop"
                        onClick={() => setShowCropModal(true)}
                        type="button"
                        disabled={isExtractingText}
                      >
                        {showCropModal ? 'Cropping...' : 'Crop'}
                      </button>
                      <button
                        className="detect__imagePreview-remove"
                        onClick={handleRemoveImage}
                        type="button"
                        disabled={isExtractingText}
                      >
                        ✕
                      </button>
                    </div>
                  </div>

                  {showCropModal ? (
                    <div className="detect__cropInline">
                      <div className="detect__cropHeader">
                        <h3 className="detect__cropTitle">Crop Before OCR</h3>
                        <p className="detect__cropHint">Select only the text area for better extraction quality.</p>
                      </div>
                      <div className="detect__cropBody">
                        <ReactCrop
                          crop={crop}
                          onChange={(nextCrop) => setCrop(nextCrop)}
                          onComplete={(nextCompletedCrop) => setCompletedCrop(nextCompletedCrop)}
                          keepSelection
                        >
                          <img
                            src={imagePreview}
                            alt="Crop selection"
                            className="detect__cropImage"
                            onLoad={(event) => setCropImageElement(event.currentTarget)}
                          />
                        </ReactCrop>
                      </div>
                      <div className="detect__cropActions">
                        <button
                          type="button"
                          className="detect__cropBtn detect__cropBtn--ghost"
                          onClick={() => setShowCropModal(false)}
                          disabled={isExtractingText}
                        >
                          Cancel
                        </button>
                        <button
                          type="button"
                          className="detect__cropBtn detect__cropBtn--primary"
                          onClick={handleCropAndExtract}
                          disabled={isExtractingText}
                        >
                          {isExtractingText ? 'Extracting...' : 'Crop & Extract'}
                        </button>
                      </div>
                    </div>
                  ) : (
                    <img src={imagePreview} alt="Selected for OCR" className="detect__imagePreview-img" />
                  )}

                  {isExtractingText && (
                    <div className="detect__imagePreview-progress">
                      <div className="detect__imagePreview-progressBar">
                        <div 
                          className="detect__imagePreview-progressFill"
                          style={{ width: `${ocrProgress}%` }}
                        />
                      </div>
                      <p className="detect__imagePreview-progressText">
                        Extracting text... {ocrProgress}%
                      </p>
                    </div>
                  )}
                </div>
              )}

              <div
                className={`detect__inputRow ${isFocused ? 'detect__inputRow--focused' : ''} ${isExpanded ? 'detect__inputRow--expanded' : ''}`}
              >
                {/* Hidden file input */}
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/*"
                  onChange={handleImageSelect}
                  style={{ display: 'none' }}
                />
                
                <button 
                  className="detect__plus" 
                  type="button" 
                  aria-label="Upload image"
                  onClick={handlePlusButtonClick}
                  disabled={isDetecting || isExtractingText}
                  title="Upload image to extract text"
                >
                  {isExtractingText ? '⏳' : '+'}
                </button>
                <textarea
                  className="detect__input"
                  value={text}
                  onChange={handleTextChange}
                  onFocus={() => setIsFocused(true)}
                  onBlur={() => setIsFocused(false)}
                  placeholder={isExtractingText ? 'Extracting text from image...' : 'Paste suspicious message or email here, or click + to upload an image...'}
                  rows={1}
                  maxLength={CONSTRAINTS.message.maxLength}
                  disabled={isExtractingText}
                />
                <button
                  className={`detect__cta ${text.trim() && !validationError ? 'detect__cta--active' : ''}`}
                  type="button"
                  disabled={!text.trim() || isDetecting || validationError || isExtractingText}
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
                    <button 
                      className="detect__reportBtn" 
                      type="button"
                      onClick={() => setIsReportModalOpen(true)}
                      title="Report an issue with this analysis"
                    >
                      Report Issue
                    </button>
                  )}
                  <button
                    className="detect__newAnalysis"
                    type="button"
                    onClick={handleAskAIGuidance}
                    disabled={isOpeningGuidance}
                    title="Get personalized guidance based on this analysis"
                  >
                    {isOpeningGuidance ? 'Opening...' : 'Ask AI for Guidance'}
                  </button>
                  <button 
                    className="detect__newAnalysis" 
                    type="button"
                    onClick={handleNewAnalysis}
                  >
                    New Analysis
                  </button>
                </div>
              </div>

              <div className="detect__resultsGrid">
                {/* Low Confidence Review Notice */}
                {detectionResult.needs_review && (
                  <div className="detect__resultCard detect__resultCard--review detect__resultCard--animate">
                    <div className="detect__reviewBanner">
                      <div className="detect__reviewIcon">🔍</div>
                      <div className="detect__reviewContent">
                        <h3 className="detect__reviewTitle">This result is under review</h3>
                        <p className="detect__reviewText">
                          Our AI model wasn&apos;t fully confident about this analysis. We&apos;ve flagged it for human review to ensure accuracy.
                        </p>
                        <p className="detect__reviewNote">
                          Verif-AI is constantly learning and improving. Your patience helps us achieve even more accurate scam detection for everyone.
                        </p>
                      </div>
                    </div>
                  </div>
                )}

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


