import type { ValidationResult } from '../types';

/**
 * Domain service for validating user input
 * Matches backend validation rules
 */
export class ValidationService {
  /**
   * Validate email format
   */
  validateEmail(email: string): boolean {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  }

  /**
   * Validate password strength
   * Requirements:
   * - Minimum 8 characters
   * - At least one uppercase letter
   * - At least one lowercase letter
   * - At least one digit
   * - At least one special character
   */
  validatePassword(password: string): ValidationResult {
    const errors: string[] = [];
    
    if (password.length < 8) {
      errors.push('Password must be at least 8 characters long');
    }
    if (!/[A-Z]/.test(password)) {
      errors.push('Password must contain at least one uppercase letter');
    }
    if (!/[a-z]/.test(password)) {
      errors.push('Password must contain at least one lowercase letter');
    }
    if (!/\d/.test(password)) {
      errors.push('Password must contain at least one digit');
    }
    if (!/[!@#$%^&*(),.?":{}|<>]/.test(password)) {
      errors.push('Password must contain at least one special character');
    }
    
    return {
      isValid: errors.length === 0,
      errors
    };
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
