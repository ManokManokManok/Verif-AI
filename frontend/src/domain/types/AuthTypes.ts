// Authentication-related types

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterData {
  email: string;
  password: string;
  confirmPassword: string;
  username: string;
}

export interface LoginResult {
  success: boolean;
  user: {
    id: string;
    email: string;
    username?: string;
    roles: string[];
    is_active: boolean;
    is_verified: boolean;
    created_at: string;
    last_login?: string;
  };
  tokens: {
    access_token: string;
    refresh_token: string;
    token_type: string;
  };
}

export interface RegisterResult {
  success: boolean;
  message: string;
  user: {
    id: string;
    email: string;
    username?: string;
    roles: string[];
    is_active: boolean;
    is_verified: boolean;
    created_at: string;
  };
}

export interface RefreshTokenResult {
  success: boolean;
  tokens: {
    access_token: string;
    refresh_token: string;
    token_type: string;
  };
}

export interface LogoutResult {
  success: boolean;
  message: string;
}

export interface VerifyEmailRequest {
  token: string;
}

export interface VerifyEmailResult {
  success: boolean;
  message: string;
}

export interface RequestPasswordResetRequest {
  email: string;
}

export interface RequestPasswordResetResult {
  success: boolean;
  message: string;
}

export interface ResetPasswordRequest {
  token: string;
  newPassword: string;
  confirmPassword: string;
}

export interface ResetPasswordResult {
  success: boolean;
  message: string;
}

// API Error Response
export interface ApiErrorResponse {
  error: {
    code: string;
    message: string;
    details?: Record<string, string[]>;
  };
}

// Validation Result
export interface ValidationResult {
  isValid: boolean;
  errors: string[];
}
