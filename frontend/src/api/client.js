const API_BASE =
  import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, '') ||
  'http://localhost:8000/api';

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

export async function loginRequest({ email, password }) {
  return apiRequest('/auth/login/', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  });
}

export async function signupRequest({ email, username, password }) {
  return apiRequest('/auth/register/', {
    method: 'POST',
    body: JSON.stringify({ email, username, password }),
  });
}


