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

/** Request timeout: 2 minutes only */
const REQUEST_TIMEOUT_MS = 2 * 60 * 1000;

/** Flag to prevent multiple concurrent refresh attempts */
let isRefreshing = false;
/** Queue of requests waiting for token refresh */
let refreshQueue = [];

/**
 * Decode a JWT payload without verification (for client-side expiry checks only).
 * @param {string} token - JWT token string
 * @returns {object|null} Decoded payload or null
 */
function decodeTokenPayload(token) {
  try {
    const base64Url = token.split('.')[1];
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
    const payload = JSON.parse(atob(base64));
    return payload;
  } catch {
    return null;
  }
}

/**
 * Check if a JWT token is expired or about to expire.
 * @param {string} token - JWT token string
 * @param {number} bufferSeconds - Consider token expired this many seconds early (default: 30)
 * @returns {boolean} True if expired or will expire within buffer window
 */
export function isTokenExpired(token, bufferSeconds = 30) {
  if (!token) return true;
  const payload = decodeTokenPayload(token);
  if (!payload || !payload.exp) return true;
  const now = Math.floor(Date.now() / 1000);
  return payload.exp - now <= bufferSeconds;
}

/**
 * Attempt to refresh the access token using the stored refresh token.
 * @returns {Promise<string|null>} New access token or null on failure
 */
async function refreshAccessToken() {
  const refreshToken = window.localStorage.getItem('refresh_token');
  if (!refreshToken || isTokenExpired(refreshToken, 0)) {
    return null;
  }

  try {
    const url = `${API_BASE}/auth/refresh/`;
    const response = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });

    if (!response.ok) return null;

    const data = await response.json();
    if (data?.tokens?.access_token) {
      window.localStorage.setItem('access_token', data.tokens.access_token);
      if (data.tokens.refresh_token) {
        window.localStorage.setItem('refresh_token', data.tokens.refresh_token);
      }
      return data.tokens.access_token;
    }
    // Some backends return { access_token } directly
    if (data?.access_token) {
      window.localStorage.setItem('access_token', data.access_token);
      if (data.refresh_token) {
        window.localStorage.setItem('refresh_token', data.refresh_token);
      }
      return data.access_token;
    }
    return null;
  } catch {
    return null;
  }
}

/**
 * Handle token refresh with queuing to avoid multiple concurrent refresh calls.
 * @returns {Promise<string|null>} New access token or null
 */
function handleTokenRefresh() {
  if (isRefreshing) {
    // Another refresh is in progress — queue this request
    return new Promise((resolve) => {
      refreshQueue.push(resolve);
    });
  }

  isRefreshing = true;
  return refreshAccessToken()
    .then((newToken) => {
      // Resolve all queued requests
      refreshQueue.forEach((cb) => cb(newToken));
      refreshQueue = [];
      return newToken;
    })
    .finally(() => {
      isRefreshing = false;
    });
}

/**
 * Dispatch a custom event to notify the app that the session has expired.
 * AuthContext listens for this to show the re-login prompt.
 */
function dispatchSessionExpired() {
  window.dispatchEvent(new CustomEvent('session-expired'));
}

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

  const controller = new AbortController();
  const timeoutId = options.signal
    ? null
    : setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

  let response;
  try {
    response = await fetch(url, {
      ...options,
      headers,
      signal: options.signal ?? controller.signal,
    });
  } catch (err) {
    if (err.name === 'AbortError' && !options.signal) {
      const timeoutErr = new Error('Request timed out after 2 minutes');
      timeoutErr.name = 'TimeoutError';
      throw timeoutErr;
    }
    throw err;
  } finally {
    if (timeoutId) clearTimeout(timeoutId);
  }

  const isJson = response.headers
    .get('content-type')
    ?.includes('application/json');
  const data = isJson ? await response.json() : null;

  if (!response.ok) {
    // Handle 401 Unauthorized — attempt token refresh
    if (response.status === 401) {
      const error = new Error(
        data?.error?.message || data?.message || 'Invalid email or password'
      );
      error.status = 401;
      error.payload = data;
      error.isUnauthorized = true;
      throw error;
    }

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
 * Make an authenticated API request.
 * Automatically handles token refresh on 401 responses.
 */
export async function authApiRequest(path, options = {}) {
  // Pre-check: if access token is about to expire, refresh proactively
  const currentToken = window.localStorage.getItem('access_token');
  if (currentToken && isTokenExpired(currentToken)) {
    const newToken = await handleTokenRefresh();
    if (!newToken) {
      // Refresh failed — session is expired
      dispatchSessionExpired();
      const error = new Error('Session expired. Please log in again.');
      error.status = 401;
      error.isSessionExpired = true;
      throw error;
    }
  }

  try {
    return await apiRequest(path, {
      ...options,
      headers: {
        ...getAuthHeaders(),
        ...(options.headers || {}),
      },
    });
  } catch (err) {
    // If 401, attempt one token refresh and retry
    if (err.status === 401 && !options._retried) {
      const newToken = await handleTokenRefresh();
      if (newToken) {
        return apiRequest(path, {
          ...options,
          _retried: true,
          headers: {
            Authorization: `Bearer ${newToken}`,
            ...(options.headers || {}),
          },
        });
      }
      // Refresh failed — notify user
      dispatchSessionExpired();
      err.isSessionExpired = true;
    }
    throw err;
  }
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

/**
 * Step 1 of MFA login: verify credentials and send MFA code to email.
 */
export async function sendMfaCodeRequest({ email, password }) {
  const validation = validateLoginForm({ email, password });
  if (!validation.valid) {
    const error = new Error(Object.values(validation.errors).join(', '));
    error.isValidationError = true;
    error.validationErrors = validation.errors;
    throw error;
  }

  return apiRequest('/auth/mfa/send/', {
    method: 'POST',
    body: JSON.stringify({
      email: email.trim().toLowerCase(),
      password,
    }),
  });
}

/**
 * Step 2 of MFA login: verify the 6-digit code and get tokens.
 */
export async function verifyMfaCodeRequest({ email, code }) {
  const data = await apiRequest('/auth/mfa/verify/', {
    method: 'POST',
    body: JSON.stringify({
      email: email.trim().toLowerCase(),
      code: code.trim(),
    }),
  });

  // Store tokens and user info (same as loginRequest)
  if (data?.tokens) {
    window.localStorage.setItem('access_token', data.tokens.access_token);
    window.localStorage.setItem('refresh_token', data.tokens.refresh_token);
  }
  if (data?.user) {
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

/**
 * Verify email using token from verification link.
 */
export async function verifyEmailRequest(token) {
  return apiRequest('/auth/verify-email/', {
    method: 'POST',
    body: JSON.stringify({ token }),
  });
}

/**
 * Request a password reset email.
 */
export async function requestPasswordResetRequest(email) {
  return apiRequest('/auth/request-reset/', {
    method: 'POST',
    body: JSON.stringify({ email: email.trim().toLowerCase() }),
  });
}

/**
 * Reset password using token from reset link.
 */
export async function resetPasswordRequest({ token, new_password }) {
  return apiRequest('/auth/reset-password/', {
    method: 'POST',
    body: JSON.stringify({ token, new_password }),
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

/**
 * API Client object with REST methods for convenience
 * Provides axios-like interface: apiClient.get(), apiClient.post(), etc.
 */
const apiClient = {
  async get(path, config = {}) {
    const response = await authApiRequest(path, { method: 'GET', ...config });
    return { data: response };
  },
  async post(path, data, config = {}) {
    const response = await authApiRequest(path, {
      method: 'POST',
      body: JSON.stringify(data),
      ...config,
    });
    return { data: response };
  },
  async put(path, data, config = {}) {
    const response = await authApiRequest(path, {
      method: 'PUT',
      body: JSON.stringify(data),
      ...config,
    });
    return { data: response };
  },
  async patch(path, data, config = {}) {
    const response = await authApiRequest(path, {
      method: 'PATCH',
      body: JSON.stringify(data),
      ...config,
    });
    return { data: response };
  },
  async delete(path, config = {}) {
    const response = await authApiRequest(path, { method: 'DELETE', ...config });
    return { data: response };
  },
};

export default apiClient;
