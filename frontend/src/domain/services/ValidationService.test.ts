import { describe, it, expect, beforeEach } from 'vitest';
import { ValidationService } from './ValidationService';

describe('ValidationService', () => {
  let validationService: ValidationService;

  beforeEach(() => {
    validationService = new ValidationService();
  });

  describe('validateEmail', () => {
    it('should return true for valid email addresses', () => {
      expect(validationService.validateEmail('test@example.com')).toBe(true);
      expect(validationService.validateEmail('user.name@domain.co.uk')).toBe(true);
      expect(validationService.validateEmail('user+tag@example.com')).toBe(true);
      expect(validationService.validateEmail('123@test.com')).toBe(true);
    });

    it('should return false for invalid email addresses', () => {
      expect(validationService.validateEmail('')).toBe(false);
      expect(validationService.validateEmail('invalid')).toBe(false);
      expect(validationService.validateEmail('no@domain')).toBe(false);
      expect(validationService.validateEmail('@example.com')).toBe(false);
      expect(validationService.validateEmail('user@')).toBe(false);
      expect(validationService.validateEmail('user @example.com')).toBe(false);
    });
  });

  describe('validatePassword', () => {
    it('should return valid result for strong passwords', () => {
      expect(validationService.validatePassword('StrongP@ss123').isValid).toBe(true);
      expect(validationService.validatePassword('MySecure#Pass1').isValid).toBe(true);
      expect(validationService.validatePassword('C0mplex!Pass').isValid).toBe(true);
    });

    it('should return invalid result for passwords shorter than 8 characters', () => {
      expect(validationService.validatePassword('Short1!').isValid).toBe(false);
      expect(validationService.validatePassword('P@ss1').isValid).toBe(false);
    });

    it('should return invalid result for passwords without uppercase letters', () => {
      expect(validationService.validatePassword('lowercase123!').isValid).toBe(false);
    });

    it('should return invalid result for passwords without lowercase letters', () => {
      expect(validationService.validatePassword('UPPERCASE123!').isValid).toBe(false);
    });

    it('should return invalid result for passwords without numbers', () => {
      expect(validationService.validatePassword('NoNumbers!@#').isValid).toBe(false);
    });

    it('should return invalid result for passwords without special characters', () => {
      expect(validationService.validatePassword('NoSpecial123').isValid).toBe(false);
    });

    it('should return invalid result for empty password', () => {
      expect(validationService.validatePassword('').isValid).toBe(false);
    });
  });

  describe('validateRequired', () => {
    it('should return valid result for non-empty strings', () => {
      expect(validationService.validateRequired('text', 'field').isValid).toBe(true);
      expect(validationService.validateRequired('a', 'field').isValid).toBe(true);
      expect(validationService.validateRequired('123', 'field').isValid).toBe(true);
    });

    it('should return invalid result for empty or whitespace strings', () => {
      expect(validationService.validateRequired('', 'field').isValid).toBe(false);
      expect(validationService.validateRequired('   ', 'field').isValid).toBe(false);
      expect(validationService.validateRequired('\t\n', 'field').isValid).toBe(false);
    });
  });
});
