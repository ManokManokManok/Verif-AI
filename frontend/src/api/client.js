const API_BASE =
  import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, '') ||
  'http://localhost:8000/api';

/**
 * Get auth headers with access token
 */
function getAuthHeaders() {
  const token = window.localStorage.getItem('access_token');
  return token ? { Authorization: `Bearer ${token}` } : {};
}

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
    const message =
      data?.error?.message ||
      data?.message ||
      `Request failed with status ${response.status}`;
    const error = new Error(message);
    error.status = response.status;
    error.payload = data;
    throw error;
  }

  return data;
}

/**
 * Make an authenticated API request
 */
async function authApiRequest(path, options = {}) {
  return apiRequest(path, {
    ...options,
    headers: {
      ...getAuthHeaders(),
      ...(options.headers || {}),
    },
  });
}

export async function loginRequest({ email, password }) {
  const data = await apiRequest('/auth/login/', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  });
  
  // Store tokens and user info
  if (data?.tokens) {
    window.localStorage.setItem('access_token', data.tokens.access_token);
    window.localStorage.setItem('refresh_token', data.tokens.refresh_token);
  }
  if (data?.user) {
    window.localStorage.setItem('user', JSON.stringify(data.user));
  }
  
  return data;
}

export async function signupRequest({ email, username, password }) {
  return apiRequest('/auth/register/', {
    method: 'POST',
    body: JSON.stringify({ email, username, password }),
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
  return apiRequest('/detect/', {
    method: 'POST',
    body: JSON.stringify({ message }),
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


