/**
 * API Client with Security Enhancements
 * 
 * Features:
 * - Rate limit handling with graceful 429 responses
 * - Input validation before sending requests
 * - Secure token storage
 * - No sensitive data in URLs
 */

import { 
  validateLoginForm, 
  validateSignupForm, 
  validateDetectionForm,
  handleRateLimitError,
  sanitizeInput 
} from '../utils/validation';

export async function getChatHistory() {
  return authApiRequest('/history/', {
    method: 'GET',
  });
}

// API base URL from environment - NEVER include API keys here
const API_BASE =
  import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, '') ||
  'http://localhost:8000/api';

/**
 * Get auth headers with access token.
 * Tokens are stored in localStorage (consider sessionStorage for higher security).
 */
function getAuthHeaders() {
  const token = window.localStorage.getItem('access_token');
  return token ? { Authorization: `Bearer ${token}` } : {};
}

/**
 * Core API request function with security enhancements.
 * 
 * @param {string} path - API endpoint path
 * @param {RequestInit} options - Fetch options
 * @returns {Promise<any>} Response data
 * @throws {Error} With status and payload on failure
 */
async function apiRequest(path, options = {}) {
  const url = `${API_BASE}${path.startsWith('/') ? path : `/${path}`}`;

  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {}),
  };

  const response = await fetch(url, {
    ...options,
    headers,
  });

  const isJson = response.headers
    .get('content-type')
    ?.includes('application/json');
  const data = isJson ? await response.json() : null;

  if (!response.ok) {
    // Handle rate limiting gracefully
    if (response.status === 429) {
      const rateLimitInfo = handleRateLimitError({ status: 429, payload: data });
      const error = new Error(rateLimitInfo.message);
      error.status = 429;
      error.payload = data;
      error.isRateLimited = true;
      error.retryAfter = rateLimitInfo.retryAfter;
      throw error;
    }
    
    // Extract error message and validation details from API response
    let message = data?.error?.message || data?.message || `Request failed with status ${response.status}`;
    
    // If the API returned validation error details, format them nicely
    if (data?.error?.details) {
      const details = data.error.details;
      // Handle both array and object error details
      if (Array.isArray(details)) {
        message = details.join('. ');
      } else if (typeof details === 'object') {
        // Format field-specific errors: { email: ["error1"], password: ["error1", "error2"] }
        const errorMessages = Object.values(details)
          .flat()
          .filter(Boolean);
        if (errorMessages.length > 0) {
          message = errorMessages.join('. ');
        }
      }
    }
    
    const error = new Error(message);
    error.status = response.status;
    error.payload = data;
    
    // Mark validation errors for specific handling
    if (data?.error?.code === 'VALIDATION_ERROR') {
      error.isValidationError = true;
      error.validationErrors = data.error.details;
    }
    
    throw error;
  }

  return data;
}

/**
 * Make an authenticated API request
 */
export async function authApiRequest(path, options = {}) {
  return apiRequest(path, {
    ...options,
    headers: {
      ...getAuthHeaders(),
      ...(options.headers || {}),
    },
  });
}

export async function loginRequest({ email, password }) {
  // Client-side validation (defense in depth)
  const validation = validateLoginForm({ email, password });
  if (!validation.valid) {
    const error = new Error(Object.values(validation.errors).join(', '));
    error.isValidationError = true;
    error.validationErrors = validation.errors;
    throw error;
  }
  
  const data = await apiRequest('/auth/login/', {
    method: 'POST',
    body: JSON.stringify({ 
      email: email.trim().toLowerCase(), 
      password 
    }),
  });
  
  // Store tokens and user info securely
  if (data?.tokens) {
    window.localStorage.setItem('access_token', data.tokens.access_token);
    window.localStorage.setItem('refresh_token', data.tokens.refresh_token);
  }
  if (data?.user) {
    // Don't store sensitive data - only what's needed for UI
    const safeUser = {
      id: data.user.id,
      email: data.user.email,
      username: data.user.username,
      roles: data.user.roles,
    };
    window.localStorage.setItem('user', JSON.stringify(safeUser));
  }
  
  return data;
}

export async function signupRequest({ email, username, password }) {
  // Client-side validation (defense in depth)
  const validation = validateSignupForm({ email, username, password });
  if (!validation.valid) {
    // Flatten all validation errors into a readable message
    const allErrors = Object.values(validation.errors).flat();
    const error = new Error(allErrors.join('. '));
    error.isValidationError = true;
    error.validationErrors = validation.errors;
    throw error;
  }
  
  return apiRequest('/auth/register/', {
    method: 'POST',
    body: JSON.stringify({ 
      email: email.trim().toLowerCase(), 
      username: username.trim(),
      password 
    }),
  });
}

export async function logoutRequest() {
  const refreshToken = window.localStorage.getItem('refresh_token');
  
  try {
    await authApiRequest('/auth/logout/', {
      method: 'POST',
      body: JSON.stringify({ refresh_token: refreshToken || '' }),
    });
  } finally {
    // Always clear local storage, even if request fails
    window.localStorage.removeItem('access_token');
    window.localStorage.removeItem('refresh_token');
    window.localStorage.removeItem('user');
  }
}

export async function detectScamRequest(message) {
  // Client-side validation
  const validation = validateDetectionForm({ message });
  if (!validation.valid) {
    const error = new Error(validation.errors.message || 'Invalid message');
    error.isValidationError = true;
    error.validationErrors = validation.errors;
    throw error;
  }
  
  return apiRequest('/detect/', {
    method: 'POST',
    headers: {
      ...getAuthHeaders(),
    },
    body: JSON.stringify({ message: message.trim() }),
  });
}

/**
 * Get stored user info
 */
export function getStoredUser() {
  try {
    const userStr = window.localStorage.getItem('user');
    return userStr ? JSON.parse(userStr) : null;
  } catch {
    return null;
  }
}

/**
 * Check if user is logged in
 */
export function isLoggedIn() {
  return Boolean(window.localStorage.getItem('access_token'));
}

/**
 * Check if user has a specific role
 */
export function hasRole(roleName) {
  const user = getStoredUser();
  if (!user || !user.roles) return false;
  return user.roles.includes(roleName);
}

/**
 * Check if user is admin
 */
export function isAdmin() {
  return hasRole('admin');
}


