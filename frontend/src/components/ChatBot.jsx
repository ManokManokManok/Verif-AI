import { useState, useRef, useEffect } from 'react';
import { sendChatMessage, clearChatHistory } from '../api/chatbot';

/**
 * Simple Chatbot Component
 * Works for both logged-in and anonymous users
 */
export default function ChatBot({ accessToken = null }) {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [disclaimer, setDisclaimer] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const messagesEndRef = useRef(null);

  // Auto-scroll to bottom when new messages arrive
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Handle sending a message
  const handleSendMessage = async (e) => {
    e.preventDefault();
    
    if (!inputMessage.trim() || isLoading) return;

    const userMessage = inputMessage.trim();
    setInputMessage('');

    // Add user message to UI immediately
    const newUserMessage = {
      role: 'user',
      content: userMessage,
      timestamp: new Date().toISOString(),
    };
    setMessages(prev => [...prev, newUserMessage]);

    setIsLoading(true);

    try {
      // Send to backend
      const response = await sendChatMessage(userMessage, accessToken);

      // Add bot response
      const botMessage = {
        role: 'assistant',
        content: response.response,
        timestamp: new Date().toISOString(),
      };
      setMessages(prev => [...prev, botMessage]);

      // Show disclaimer if present (first message for anonymous users)
      if (response.disclaimer) {
        setDisclaimer(response.disclaimer);
      }

      setIsAuthenticated(response.is_authenticated);

    } catch (error) {
      console.error('Chat error:', error);
      // Add error message
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

  // Handle clearing chat
  const handleClearChat = async () => {
    if (!window.confirm('Are you sure you want to clear this conversation?')) {
      return;
    }

    try {
      await clearChatHistory(accessToken);
      setMessages([]);
      setDisclaimer(null);
      alert('Conversation cleared!');
    } catch (error) {
      console.error('Clear error:', error);
      alert('Failed to clear conversation');
    }
  };

  return (
    <div className="chatbot-container" style={styles.container}>
      {/* Header */}
      <div style={styles.header}>
        <h2 style={styles.title}>🛡️ Bimby - Scam Prevention Assistant</h2>
        <button 
          onClick={handleClearChat}
          style={styles.clearButton}
          title="Clear conversation"
        >
          🗑️ Clear
        </button>
      </div>

      {/* Auth Status Badge */}
      <div style={styles.statusBadge}>
        {isAuthenticated ? (
          <span style={styles.authenticatedBadge}>✅ Logged In - Conversation Saved</span>
        ) : (
          <span style={styles.anonymousBadge}>👤 Anonymous - Not Saved</span>
        )}
      </div>

      {/* Disclaimer for anonymous users */}
      {disclaimer && (
        <div style={styles.disclaimer}>
          ℹ️ {disclaimer}
        </div>
      )}

      {/* Messages Area */}
      <div style={styles.messagesArea}>
        {messages.length === 0 && (
          <div style={styles.emptyState}>
            <p>👋 Hi! I'm Bimby, your scam prevention assistant.</p>
            <p>Ask me about:</p>
            <ul style={styles.suggestedTopics}>
              <li>Common phishing tactics</li>
              <li>How to spot scams</li>
              <li>What to do if you've been scammed</li>
              <li>Romance scam red flags</li>
            </ul>
          </div>
        )}

        {messages.map((msg, index) => (
          <div
            key={index}
            style={{
              ...styles.message,
              ...(msg.role === 'user' ? styles.userMessage : styles.botMessage),
              ...(msg.isError ? styles.errorMessage : {}),
            }}
          >
            <div style={styles.messageHeader}>
              <strong>{msg.role === 'user' ? '👤 You' : '🤖 Bimby'}</strong>
              <span style={styles.timestamp}>
                {new Date(msg.timestamp).toLocaleTimeString()}
              </span>
            </div>
            <div style={styles.messageContent}>{msg.content}</div>
          </div>
        ))}

        {isLoading && (
          <div style={{ ...styles.message, ...styles.botMessage }}>
            <div style={styles.messageHeader}>
              <strong>🤖 Bimby</strong>
            </div>
            <div style={styles.messageContent}>
              <span style={styles.typing}>Thinking...</span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <form onSubmit={handleSendMessage} style={styles.inputForm}>
        <input
          type="text"
          value={inputMessage}
          onChange={(e) => setInputMessage(e.target.value)}
          placeholder="Ask me about scam prevention..."
          style={styles.input}
          disabled={isLoading}
          maxLength={2000}
        />
        <button
          type="submit"
          style={{
            ...styles.sendButton,
            ...(isLoading || !inputMessage.trim() ? styles.sendButtonDisabled : {}),
          }}
          disabled={isLoading || !inputMessage.trim()}
        >
          {isLoading ? '⏳' : '📤'} Send
        </button>
      </form>
    </div>
  );
}

// Inline styles (you can move these to CSS if preferred)
const styles = {
  container: {
    display: 'flex',
    flexDirection: 'column',
    height: '600px',
    maxWidth: '800px',
    margin: '0 auto',
    border: '1px solid #ddd',
    borderRadius: '12px',
    overflow: 'hidden',
    boxShadow: '0 4px 6px rgba(0,0,0,0.1)',
    backgroundColor: '#fff',
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '16px 20px',
    backgroundColor: '#4F46E5',
    color: 'white',
  },
  title: {
    margin: 0,
    fontSize: '18px',
    fontWeight: 'bold',
  },
  clearButton: {
    padding: '6px 12px',
    backgroundColor: 'rgba(255,255,255,0.2)',
    border: 'none',
    borderRadius: '6px',
    color: 'white',
    cursor: 'pointer',
    fontSize: '14px',
  },
  statusBadge: {
    padding: '8px 20px',
    backgroundColor: '#F9FAFB',
    borderBottom: '1px solid #E5E7EB',
    fontSize: '13px',
  },
  authenticatedBadge: {
    color: '#059669',
    fontWeight: 'bold',
  },
  anonymousBadge: {
    color: '#D97706',
    fontWeight: 'bold',
  },
  disclaimer: {
    padding: '12px 20px',
    backgroundColor: '#FEF3C7',
    borderBottom: '1px solid #FDE68A',
    fontSize: '13px',
    lineHeight: '1.5',
    color: '#92400E',
  },
  messagesArea: {
    flex: 1,
    overflowY: 'auto',
    padding: '20px',
    backgroundColor: '#F9FAFB',
  },
  emptyState: {
    textAlign: 'center',
    color: '#6B7280',
    marginTop: '40px',
  },
  suggestedTopics: {
    textAlign: 'left',
    display: 'inline-block',
    marginTop: '10px',
  },
  message: {
    marginBottom: '16px',
    padding: '12px 16px',
    borderRadius: '12px',
    maxWidth: '80%',
  },
  userMessage: {
    marginLeft: 'auto',
    backgroundColor: '#4F46E5',
    color: 'white',
  },
  botMessage: {
    marginRight: 'auto',
    backgroundColor: 'white',
    border: '1px solid #E5E7EB',
    color: '#1F2937',
  },
  errorMessage: {
    backgroundColor: '#FEE2E2',
    borderColor: '#FCA5A5',
  },
  messageHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    marginBottom: '6px',
    fontSize: '12px',
    opacity: 0.8,
  },
  timestamp: {
    fontSize: '11px',
  },
  messageContent: {
    lineHeight: '1.6',
    whiteSpace: 'pre-wrap',
    wordBreak: 'break-word',
  },
  typing: {
    fontStyle: 'italic',
    opacity: 0.7,
  },
  inputForm: {
    display: 'flex',
    padding: '16px 20px',
    borderTop: '1px solid #E5E7EB',
    backgroundColor: 'white',
  },
  input: {
    flex: 1,
    padding: '12px 16px',
    border: '1px solid #D1D5DB',
    borderRadius: '8px',
    fontSize: '14px',
    outline: 'none',
  },
  sendButton: {
    marginLeft: '12px',
    padding: '12px 24px',
    backgroundColor: '#4F46E5',
    color: 'white',
    border: 'none',
    borderRadius: '8px',
    fontSize: '14px',
    fontWeight: 'bold',
    cursor: 'pointer',
  },
  sendButtonDisabled: {
    opacity: 0.5,
    cursor: 'not-allowed',
  },
};
