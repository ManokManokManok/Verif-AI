/**
 * Input Validation & Sanitization Utilities
 * 
 * Client-side validation for defense in depth.
 * Note: Server-side validation is the primary security control.
 * 
 * OWASP References:
 * - Input Validation Cheat Sheet
 * - XSS Prevention Cheat Sheet
 */

// =============================================================================
// VALIDATION CONSTRAINTS (matching backend)
// =============================================================================

export const CONSTRAINTS = {
  email: {
    minLength: 5,
    maxLength: 254,
    pattern: /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/,
  },
  password: {
    minLength: 8,
    maxLength: 128,
    requireUppercase: true,
    requireLowercase: true,
    requireDigit: true,
    requireSpecial: true,
  },
  username: {
    minLength: 3,
    maxLength: 32,
    pattern: /^[a-zA-Z0-9_-]+$/,
    requireLetter: true,
  },
  message: {
    minLength: 1,
    maxLength: 10000, // 10KB limit for scam detection
  },
};

// Common password blacklist (matches backend common_passwords.txt)
const COMMON_PASSWORDS = new Set([
  'password', '123456', '12345678', '123456789', '1234567890',
  'qwerty', 'abc123', 'password1', 'password123', 'iloveyou',
  'admin', 'letmein', 'welcome', 'monkey', 'dragon',
  'master', 'login', 'princess', 'football', 'shadow',
  'sunshine', 'trustno1', '123123', '654321', 'superman',
  'qwerty123', 'michael', 'charlie', 'ashley', 'jessica',
  '121212', '000000', 'access', 'flower', 'whatever',
  'passw0rd', 'hello', 'donald', 'password1!', 'baseball',
  'soccer', 'hockey', 'killer', 'pepper', 'thomas',
  'summer', 'george', 'harley', 'batman', 'andrew',
  'ranger', 'daniel', 'starwars', 'klaster', '112233',
  'jordan', 'mustang', 'robert', 'taylor', 'jennifer',
  '123qwe', 'qwerty1', 'welcome1', '1q2w3e4r', 'qwertyuiop',
  'computer', 'internet', 'samsung', '1234qwer', 'nothing',
  'secret', 'zaq12wsx', 'pa$$w0rd', 'p@ssw0rd', 'p@ssword1',
  'qwerty123', 'password1!', 'welcome1!', 'changeme1!', 'admin123!',
  'letmein1!', 'test1234!', 'abc12345!', 'hello123!', 'pass1234',
  '12345qwert', '123abc', 'test123!', 'mypass123', 'user1234!',
  'default1!', 'temp1234!', 'guest123!',
]);

/**
 * Check if a password is in the common passwords blacklist.
 * @param {string} password
 * @returns {boolean}
 */
export function isCommonPassword(password) {
  if (!password) return false;
  return COMMON_PASSWORDS.has(password.toLowerCase());
}

// =============================================================================
// SANITIZATION FUNCTIONS
// =============================================================================

/**
 * Escape HTML entities to prevent XSS.
 * Use when displaying user input in the DOM.
 * 
 * @param {string} str - String to sanitize
 * @returns {string} Sanitized string with HTML entities escaped
 */
export function escapeHtml(str) {
  if (!str || typeof str !== 'string') return '';
  
  const htmlEntities = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#x27;',
    '/': '&#x2F;',
    '`': '&#x60;',
    '=': '&#x3D;',
  };
  
  return str.replace(/[&<>"'`=/]/g, (char) => htmlEntities[char]);
}

/**
 * Remove potentially dangerous content from strings.
 * More aggressive than escapeHtml - removes instead of escaping.
 * 
 * @param {string} str - String to sanitize
 * @returns {string} Sanitized string
 */
export function sanitizeInput(str) {
  if (!str || typeof str !== 'string') return '';
  
  // Remove null bytes
  let sanitized = str.replace(/\0/g, '');
  
  // Remove script tags and event handlers
  sanitized = sanitized.replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '');
  sanitized = sanitized.replace(/on\w+\s*=/gi, '');
  sanitized = sanitized.replace(/javascript:/gi, '');
  
  return sanitized;
}

/**
 * Trim and normalize whitespace.
 * 
 * @param {string} str - String to normalize
 * @returns {string} Normalized string
 */
export function normalizeWhitespace(str) {
  if (!str || typeof str !== 'string') return '';
  return str.trim().replace(/\s+/g, ' ');
}

// =============================================================================
// VALIDATION FUNCTIONS
// =============================================================================

/**
 * Validate email format.
 * 
 * @param {string} email - Email to validate
 * @returns {{ valid: boolean, error?: string }}
 */
export function validateEmail(email) {
  if (!email || typeof email !== 'string') {
    return { valid: false, error: 'Email is required' };
  }
  
  const trimmed = email.trim().toLowerCase();
  
  if (trimmed.length < CONSTRAINTS.email.minLength) {
    return { valid: false, error: 'Email is too short' };
  }
  
  if (trimmed.length > CONSTRAINTS.email.maxLength) {
    return { valid: false, error: 'Email is too long' };
  }
  
  if (!CONSTRAINTS.email.pattern.test(trimmed)) {
    return { valid: false, error: 'Invalid email format' };
  }
  
  return { valid: true };
}

/**
 * Validate password strength.
 * 
 * @param {string} password - Password to validate
 * @returns {{ valid: boolean, errors: string[] }}
 */
export function validatePassword(password) {
  const errors = [];
  
  if (!password) {
    return { valid: false, errors: ['Password is required'] };
  }
  
  // Check for whitespace characters (spaces, tabs, newlines, etc.)
  if (/\s/.test(password)) {
    errors.push('Password must not contain spaces or whitespace characters');
  }
  
  if (password.length < CONSTRAINTS.password.minLength) {
    errors.push(`Password must be at least ${CONSTRAINTS.password.minLength} characters`);
  }
  
  if (password.length > CONSTRAINTS.password.maxLength) {
    errors.push(`Password must not exceed ${CONSTRAINTS.password.maxLength} characters`);
  }
  
  if (CONSTRAINTS.password.requireUppercase && !/[A-Z]/.test(password)) {
    errors.push('Password must contain at least one uppercase letter');
  }
  
  if (CONSTRAINTS.password.requireLowercase && !/[a-z]/.test(password)) {
    errors.push('Password must contain at least one lowercase letter');
  }
  
  if (CONSTRAINTS.password.requireDigit && !/\d/.test(password)) {
    errors.push('Password must contain at least one digit');
  }
  
  if (CONSTRAINTS.password.requireSpecial && !/[!@#$%^&*(),.?":{}|<>\[\]\\;'`~_+=/\-]/.test(password)) {
    errors.push('Password must contain at least one special character');
  }
  
  if (isCommonPassword(password)) {
    errors.push('This password is too common. Please choose a stronger password.');
  }
  
  return { valid: errors.length === 0, errors };
}

/**
 * Get individual password requirement statuses for real-time UI feedback.
 * @param {string} password - Current password value
 * @returns {Array<{label: string, met: boolean}>}
 */
export function getPasswordRequirements(password) {
  const pw = password || '';
  return [
    { key: 'minLength', label: `At least ${CONSTRAINTS.password.minLength} characters`, met: pw.length >= CONSTRAINTS.password.minLength },
    { key: 'uppercase', label: 'At least one uppercase letter', met: /[A-Z]/.test(pw) },
    { key: 'lowercase', label: 'At least one lowercase letter', met: /[a-z]/.test(pw) },
    { key: 'digit', label: 'At least one digit', met: /\d/.test(pw) },
    { key: 'special', label: 'At least one special character', met: /[!@#$%^&*(),.?":{}|<>\[\]\\;'`~_+=/\-]/.test(pw) },
    { key: 'noWhitespace', label: 'No spaces or whitespace', met: pw.length > 0 && !/\s/.test(pw) },
    { key: 'notCommon', label: 'Not a commonly used password', met: pw.length > 0 && !isCommonPassword(pw) },
  ];
}

/**
 * Validate username format.
 * 
 * @param {string} username - Username to validate
 * @returns {{ valid: boolean, error?: string }}
 */
export function validateUsername(username) {
  if (!username || typeof username !== 'string') {
    return { valid: false, error: 'Username is required' };
  }
  
  const trimmed = username.trim();
  
  if (trimmed.length < CONSTRAINTS.username.minLength) {
    return { valid: false, error: `Username must be at least ${CONSTRAINTS.username.minLength} characters` };
  }
  
  if (trimmed.length > CONSTRAINTS.username.maxLength) {
    return { valid: false, error: `Username must not exceed ${CONSTRAINTS.username.maxLength} characters` };
  }
  
  if (!CONSTRAINTS.username.pattern.test(trimmed)) {
    return { valid: false, error: 'Username may only contain letters, numbers, underscores, and hyphens' };
  }
  
  if (!/[a-zA-Z]/.test(trimmed)) {
    return { valid: false, error: 'Username must contain at least one letter' };
  }
  
  return { valid: true };
}

/**
 * Validate message content for scam detection.
 * 
 * @param {string} message - Message to validate
 * @returns {{ valid: boolean, error?: string }}
 */
export function validateMessage(message) {
  if (!message || typeof message !== 'string') {
    return { valid: false, error: 'Message is required' };
  }
  
  const trimmed = message.trim();
  
  if (trimmed.length < CONSTRAINTS.message.minLength) {
    return { valid: false, error: 'Message is too short for analysis' };
  }
  
  if (trimmed.length > CONSTRAINTS.message.maxLength) {
    return { valid: false, error: `Message exceeds maximum length of ${CONSTRAINTS.message.maxLength} characters` };
  }
  
  return { valid: true };
}

// =============================================================================
// FORM VALIDATION HELPERS
// =============================================================================

/**
 * Validate login form data.
 * 
 * @param {{ email: string, password: string }} data
 * @returns {{ valid: boolean, errors: Record<string, string> }}
 */
export function validateLoginForm(data) {
  const errors = {};
  
  const emailResult = validateEmail(data.email);
  if (!emailResult.valid) {
    errors.email = emailResult.error;
  }
  
  // Don't validate password strength on login - just check it exists
  if (!data.password || data.password.length === 0) {
    errors.password = 'Password is required';
  } else if (data.password.length > CONSTRAINTS.password.maxLength) {
    errors.password = 'Invalid password';
  }
  
  return { valid: Object.keys(errors).length === 0, errors };
}

/**
 * Validate signup form data.
 * 
 * @param {{ email: string, username: string, password: string }} data
 * @returns {{ valid: boolean, errors: Record<string, string[]> }}
 */
export function validateSignupForm(data) {
  const errors = {};
  
  const emailResult = validateEmail(data.email);
  if (!emailResult.valid) {
    errors.email = [emailResult.error];
  }
  
  const usernameResult = validateUsername(data.username);
  if (!usernameResult.valid) {
    errors.username = [usernameResult.error];
  }
  
  const passwordResult = validatePassword(data.password);
  if (!passwordResult.valid) {
    errors.password = passwordResult.errors;
  }
  
  return { valid: Object.keys(errors).length === 0, errors };
}

/**
 * Validate scam detection form data.
 * 
 * @param {{ message: string }} data
 * @returns {{ valid: boolean, errors: Record<string, string> }}
 */
export function validateDetectionForm(data) {
  const errors = {};
  
  const messageResult = validateMessage(data.message);
  if (!messageResult.valid) {
    errors.message = messageResult.error;
  }
  
  return { valid: Object.keys(errors).length === 0, errors };
}

// =============================================================================
// RATE LIMIT HANDLING
// =============================================================================

/**
 * Parse rate limit headers from response.
 * 
 * @param {Response} response - Fetch response
 * @returns {{ limit: number, remaining: number, reset: number, retryAfter?: number } | null}
 */
export function parseRateLimitHeaders(response) {
  const limit = response.headers.get('X-RateLimit-Limit');
  const remaining = response.headers.get('X-RateLimit-Remaining');
  const reset = response.headers.get('X-RateLimit-Reset');
  const retryAfter = response.headers.get('Retry-After');
  
  if (!limit) return null;
  
  return {
    limit: parseInt(limit, 10),
    remaining: parseInt(remaining, 10),
    reset: parseInt(reset, 10),
    retryAfter: retryAfter ? parseInt(retryAfter, 10) : undefined,
  };
}

/**
 * Format retry-after seconds into human-readable string.
 * 
 * @param {number} seconds 
 * @returns {string}
 */
export function formatRetryAfter(seconds) {
  if (seconds < 60) {
    return `${seconds} seconds`;
  } else if (seconds < 3600) {
    const minutes = Math.ceil(seconds / 60);
    return `${minutes} minute${minutes > 1 ? 's' : ''}`;
  } else {
    const hours = Math.ceil(seconds / 3600);
    return `${hours} hour${hours > 1 ? 's' : ''}`;
  }
}

/**
 * Handle rate limit error (429 response).
 * 
 * @param {Error} error - Error with status and payload
 * @returns {{ isRateLimited: boolean, retryAfter?: string, message: string }}
 */
export function handleRateLimitError(error) {
  if (error.status !== 429) {
    return { isRateLimited: false, message: error.message };
  }
  
  const retryAfter = error.payload?.error?.retry_after;
  const humanReadable = error.payload?.error?.retry_after_human;
  
  return {
    isRateLimited: true,
    retryAfter: humanReadable || (retryAfter ? formatRetryAfter(retryAfter) : 'a moment'),
    message: `Too many requests. Please wait ${humanReadable || 'a moment'} and try again.`,
  };
}
