/**
 * Chatbot API Service
 * Handles communication with the general chatbot endpoint
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

/**
 * Send a message to the chatbot
 * @param {string} message - User's message
 * @param {string} accessToken - JWT access token (optional for anonymous users)
<<<<<<< HEAD
 * @param {string} conversationId - Optional conversation ID to continue existing conversation
 * @returns {Promise<object>} Response with bot's reply
 */
export async function sendChatMessage(message, accessToken = null, conversationId = null) {
=======
 * @returns {Promise<object>} Response with bot's reply
 */
export async function sendChatMessage(message, accessToken = null) {
>>>>>>> origin/josh-admin-feat
  const headers = {
    'Content-Type': 'application/json',
  };

  // Add auth header if user is logged in
  if (accessToken) {
    headers['Authorization'] = `Bearer ${accessToken}`;
  }

  // Add session ID for anonymous users (optional but helps maintain session)
  if (!accessToken) {
    const sessionId = getOrCreateSessionId();
    headers['X-Session-ID'] = sessionId;
  }

<<<<<<< HEAD
  const body = { message };
  if (conversationId) {
    body.conversation_id = conversationId;
  }

  const response = await fetch(`${API_BASE_URL}/api/chat/message/`, {
    method: 'POST',
    headers,
    body: JSON.stringify(body),
=======
  const response = await fetch(`${API_BASE_URL}/chat/message/`, {
    method: 'POST',
    headers,
    body: JSON.stringify({ message }),
>>>>>>> origin/josh-admin-feat
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.error?.message || 'Failed to send message');
  }

  return await response.json();
}

/**
<<<<<<< HEAD
 * Get chat history for a specific conversation
 * @param {string} accessToken - JWT access token (optional)
 * @param {string} conversationId - Optional specific conversation ID
 * @returns {Promise<object>} Chat history
 */
export async function getChatHistory(accessToken = null, conversationId = null) {
=======
 * Get chat history
 * @param {string} accessToken - JWT access token (optional)
 * @returns {Promise<object>} Chat history
 */
export async function getChatHistory(accessToken = null) {
>>>>>>> origin/josh-admin-feat
  const headers = {};

  if (accessToken) {
    headers['Authorization'] = `Bearer ${accessToken}`;
  } else {
    const sessionId = getOrCreateSessionId();
    headers['X-Session-ID'] = sessionId;
  }

<<<<<<< HEAD
  let url = `${API_BASE_URL}/api/chat/history/`;
  if (conversationId) {
    url += `?conversation_id=${conversationId}`;
  }

  const response = await fetch(url, {
=======
  const response = await fetch(`${API_BASE_URL}/api/chat/history/`, {
>>>>>>> origin/josh-admin-feat
    method: 'GET',
    headers,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.error?.message || 'Failed to get history');
  }

  return await response.json();
}

/**
<<<<<<< HEAD
 * Get all conversations for logged in user
 * @param {string} accessToken - JWT access token
 * @param {number} limit - Maximum number of conversations to return
 * @returns {Promise<object>} List of conversations
 */
export async function getConversations(accessToken, limit = 50) {
  if (!accessToken) {
    return { conversations: [], is_authenticated: false };
  }

  const headers = {
    'Authorization': `Bearer ${accessToken}`,
  };

  const response = await fetch(`${API_BASE_URL}/api/chat/conversations/?limit=${limit}`, {
    method: 'GET',
    headers,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.error?.message || 'Failed to get conversations');
  }

  return await response.json();
}

/**
 * Delete a specific conversation
 * @param {string} conversationId - Conversation ID to delete
 * @param {string} accessToken - JWT access token
 * @returns {Promise<object>} Success message
 */
export async function deleteConversation(conversationId, accessToken) {
  if (!accessToken) {
    throw new Error('Authentication required');
  }

  const headers = {
    'Authorization': `Bearer ${accessToken}`,
  };

  const response = await fetch(`${API_BASE_URL}/api/chat/conversations/${conversationId}/`, {
    method: 'DELETE',
    headers,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.error?.message || 'Failed to delete conversation');
  }

  return await response.json();
}

/**
=======
>>>>>>> origin/josh-admin-feat
 * Clear chat history (start fresh)
 * @param {string} accessToken - JWT access token (optional)
 * @returns {Promise<object>} Success message
 */
export async function clearChatHistory(accessToken = null) {
  const headers = {};

  if (accessToken) {
    headers['Authorization'] = `Bearer ${accessToken}`;
  } else {
    const sessionId = getOrCreateSessionId();
    headers['X-Session-ID'] = sessionId;
  }

  const response = await fetch(`${API_BASE_URL}/api/chat/history/`, {
    method: 'DELETE',
    headers,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.error?.message || 'Failed to clear history');
  }

  return await response.json();
}

/**
 * Get or create a session ID for anonymous users
 * Stored in localStorage to maintain session across page reloads
 */
function getOrCreateSessionId() {
  let sessionId = localStorage.getItem('chatbot_session_id');
  
  if (!sessionId) {
    // Create a simple session ID
    sessionId = `anon_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    localStorage.setItem('chatbot_session_id', sessionId);
  }
  
  return sessionId;
}

/**
 * Clear the session ID (useful when user logs in)
 */
export function clearSessionId() {
  localStorage.removeItem('chatbot_session_id');
}
<<<<<<< HEAD


// ============================================================
// ANALYSIS-GUIDED CHATBOT API
// ============================================================

/**
 * Get or create analysis-guided conversation for a specific analysis
 * @param {string} analysisRefId - UUID of the analysis result
 * @param {string} accessToken - JWT access token (required)
 * @returns {Promise<object>} Conversation data with analysis context
 */
export async function getAnalysisConversation(analysisRefId, accessToken) {
  if (!accessToken) {
    throw new Error('Authentication required for analysis-guided conversations');
  }

  const headers = {
    'Authorization': `Bearer ${accessToken}`,
  };

  const response = await fetch(`${API_BASE_URL}/api/chat/analysis-guided/${analysisRefId}/`, {
    method: 'GET',
    headers,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.error?.message || 'Failed to get analysis conversation');
  }

  return await response.json();
}

/**
 * Send a message in an analysis-guided conversation
 * @param {string} conversationId - Conversation MongoDB ID
 * @param {string} message - User's message
 * @param {string} accessToken - JWT access token (required)
 * @returns {Promise<object>} Response with bot's guidance
 */
export async function sendAnalysisGuidedMessage(conversationId, message, accessToken) {
  if (!accessToken) {
    throw new Error('Authentication required for analysis-guided conversations');
  }

  const headers = {
    'Authorization': `Bearer ${accessToken}`,
    'Content-Type': 'application/json',
  };

  const response = await fetch(`${API_BASE_URL}/api/chat/analysis-guided/message/`, {
    method: 'POST',
    headers,
    body: JSON.stringify({
      conversation_id: conversationId,
      message,
    }),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.error?.message || 'Failed to send analysis-guided message');
  }

  return await response.json();
}

/**
 * Get full history of an analysis-guided conversation
 * @param {string} conversationId - Conversation MongoDB ID
 * @param {string} accessToken - JWT access token (required)
 * @returns {Promise<object>} Full conversation with analysis context
 */
export async function getAnalysisGuidedHistory(conversationId, accessToken) {
  if (!accessToken) {
    throw new Error('Authentication required for analysis-guided conversations');
  }

  const headers = {
    'Authorization': `Bearer ${accessToken}`,
  };

  const response = await fetch(`${API_BASE_URL}/api/chat/analysis-guided/history/${conversationId}/`, {
    method: 'GET',
    headers,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.error?.message || 'Failed to get analysis-guided history');
  }

  return await response.json();
}
=======
>>>>>>> origin/josh-admin-feat
