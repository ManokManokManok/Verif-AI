import type { ValidationResult } from '../types';

/**
 * Domain service for validating user input
 * Matches backend validation rules (OWASP compliant)
 * 
 * IMPORTANT: Keep in sync with backend/src/infrastructure/input_validator.py
 */
export class ValidationService {
  /**
   * Validate email format (RFC 5322 simplified)
   * Max length: 254 characters (RFC 5321)
   */
  validateEmail(email: string): boolean {
    if (!email || email.length > 254) {
      return false;
    }
    const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
    return emailRegex.test(email);
  }

  /**
   * Validate password strength (OWASP compliant)
   * Requirements:
   * - Minimum 8 characters
   * - Maximum 128 characters (prevents DoS with bcrypt)
   * - At least one uppercase letter
   * - At least one lowercase letter
   * - At least one digit
   * - At least one special character
   * - No whitespace allowed
   * - No common weak patterns (sequential/repeated characters)
   */
  validatePassword(password: string): ValidationResult {
    const errors: string[] = [];
    
    // Length checks
    if (password.length < 8) {
      errors.push('Password must be at least 8 characters long');
    }
    
    if (password.length > 128) {
      errors.push('Password must not exceed 128 characters');
    }
    
    // Character type requirements
    if (!/[A-Z]/.test(password)) {
      errors.push('Password must contain at least one uppercase letter');
    }
    
    if (!/[a-z]/.test(password)) {
      errors.push('Password must contain at least one lowercase letter');
    }
    
    if (!/\d/.test(password)) {
      errors.push('Password must contain at least one digit');
    }
    
    // Extended special character set matching backend
    if (!/[!@#$%^&*(),.?":{}|<>\-_=+\[\]\\;'`~]/.test(password)) {
      errors.push('Password must contain at least one special character');
    }
    
    // SECURITY: No whitespace allowed (prevents confusion and potential issues)
    if (/\s/.test(password)) {
      errors.push('Password must not contain spaces or whitespace');
    }
    
    // SECURITY: Check for common weak patterns
    // Same character repeated 4+ times
    if (/(.)\1{3,}/.test(password)) {
      errors.push('Password contains weak patterns (repeated characters)');
    }
    
    // Sequential numbers
    if (/(012|123|234|345|456|567|678|789|890)/i.test(password)) {
      errors.push('Password contains weak patterns (sequential numbers)');
    }
    
    // Sequential letters (lowercase check)
    const sequentialLetters = /(?:abc|bcd|cde|def|efg|fgh|ghi|hij|ijk|jkl|klm|lmn|mno|nop|opq|pqr|qrs|rst|stu|tuv|uvw|vwx|wxy|xyz)/i;
    if (sequentialLetters.test(password)) {
      errors.push('Password contains weak patterns (sequential letters)');
    }
    
    return {
      isValid: errors.length === 0,
      errors
    };
  }

  /**
   * Get password strength indicator for UI
   */
  getPasswordStrength(password: string): {
    score: number;
    label: 'weak' | 'fair' | 'good' | 'strong';
    color: string;
  } {
    let score = 0;
    
    if (password.length >= 8) score++;
    if (password.length >= 12) score++;
    if (password.length >= 16) score++;
    if (/[A-Z]/.test(password)) score++;
    if (/[a-z]/.test(password)) score++;
    if (/\d/.test(password)) score++;
    if (/[!@#$%^&*(),.?":{}|<>\-_=+\[\]\\;'`~]/.test(password)) score++;
    if (!/\s/.test(password)) score++;
    if (!/(.)\1{2,}/.test(password)) score++; // No character repeated 3+ times
    
    if (score <= 3) {
      return { score, label: 'weak', color: 'text-red-500' };
    } else if (score <= 5) {
      return { score, label: 'fair', color: 'text-yellow-500' };
    } else if (score <= 7) {
      return { score, label: 'good', color: 'text-blue-500' };
    } else {
      return { score, label: 'strong', color: 'text-green-500' };
    }
  }

  /**
   * Validate password confirmation
   */
  validatePasswordMatch(password: string, confirmPassword: string): ValidationResult {
    if (password !== confirmPassword) {
      return {
        isValid: false,
        errors: ['Passwords do not match']
      };
    }
    
    return {
      isValid: true,
      errors: []
    };
  }

  /**
   * Validate username format
   * - 3-50 characters
   * - Alphanumeric, underscore, hyphen only
   */
  validateUsername(username: string): ValidationResult {
    const errors: string[] = [];
    
    if (!username || username.trim().length === 0) {
      errors.push('Username is required');
      return { isValid: false, errors };
    }
    
    if (username.length < 3) {
      errors.push('Username must be at least 3 characters');
    }
    
    if (username.length > 50) {
      errors.push('Username must not exceed 50 characters');
    }
    
    if (!/^[a-zA-Z0-9_-]+$/.test(username)) {
      errors.push('Username can only contain letters, numbers, underscores, and hyphens');
    }
    
    return {
      isValid: errors.length === 0,
      errors
    };
  }

  /**
   * Validate required field
   */
  validateRequired(value: string, fieldName: string): ValidationResult {
    if (!value || value.trim().length === 0) {
      return {
        isValid: false,
        errors: [`${fieldName} is required`]
      };
    }
    
    return {
      isValid: true,
      errors: []
    };
  }

  /**
   * Validate token format (hex string)
   */
  validateToken(token: string): ValidationResult {
    const errors: string[] = [];
    
    if (!token) {
      errors.push('Token is required');
      return { isValid: false, errors };
    }
    
    if (token.length < 16) {
      errors.push('Invalid token format');
    }
    
    if (token.length > 256) {
      errors.push('Invalid token format');
    }
    
    if (!/^[a-fA-F0-9]+$/.test(token)) {
      errors.push('Invalid token format');
    }
    
    return {
      isValid: errors.length === 0,
      errors
    };
  }

  /**
   * Sanitize string input (basic XSS prevention)
   */
  sanitizeString(value: string, maxLength: number = 10000): string {
    if (!value) return '';
    
    // Remove null bytes
    let sanitized = value.replace(/\0/g, '');
    
    // Trim whitespace
    sanitized = sanitized.trim();
    
    // Truncate to max length
    sanitized = sanitized.slice(0, maxLength);
    
    return sanitized;
  }

  /**
   * Sanitize email
   */
  sanitizeEmail(email: string): string {
    if (!email) return '';
    
    // Lowercase and trim
    let sanitized = email.toLowerCase().trim();
    
    // Remove dangerous characters (keep valid email chars)
    sanitized = sanitized.replace(/[^\w@.+-]/g, '');
    
    // Truncate to RFC max length
    return sanitized.slice(0, 254);
  }

  /**
   * Combine multiple validation results
   */
  combineValidationResults(...results: ValidationResult[]): ValidationResult {
    const allErrors = results.flatMap(result => result.errors);
    
    return {
      isValid: allErrors.length === 0,
      errors: allErrors
    };
  }
}

// Export singleton instance
export const validationService = new ValidationService();
