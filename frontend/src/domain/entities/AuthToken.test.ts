import { describe, it, expect } from 'vitest';
import { AuthToken } from './AuthToken';

describe('AuthToken Entity', () => {
  const mockAccessToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U';
  const mockRefreshToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwicmVmcmVzaCI6dHJ1ZX0.abc123';

  describe('constructor', () => {
    it('should create an auth token with all properties', () => {
      const expiresAt = new Date(Date.now() + 3600000); // 1 hour from now
      const token = new AuthToken(mockAccessToken, mockRefreshToken, expiresAt);
      expect(token.accessToken).toBe(mockAccessToken);
      expect(token.refreshToken).toBe(mockRefreshToken);
    });
  });

  describe('isValid', () => {
    it('should return true for valid token format', () => {
      const expiresAt = new Date(Date.now() + 3600000); // 1 hour from now
      const token = new AuthToken(mockAccessToken, mockRefreshToken, expiresAt);
      expect(token.isValid()).toBe(true);
    });

    it('should return false for empty access token', () => {
      const expiresAt = new Date(Date.now() + 3600000); // 1 hour from now
      const token = new AuthToken('', mockRefreshToken, expiresAt);
      expect(token.isValid()).toBe(false);
    });

    it('should return false for empty refresh token', () => {
      const expiresAt = new Date(Date.now() + 3600000); // 1 hour from now
      const token = new AuthToken(mockAccessToken, '', expiresAt);
      expect(token.isValid()).toBe(false);
    });

    it('should return false for both empty tokens', () => {
      const expiresAt = new Date(Date.now() + 3600000); // 1 hour from now
      const token = new AuthToken('', '', expiresAt);
      expect(token.isValid()).toBe(false);
    });

    it('should return false for whitespace-only tokens', () => {
      const expiresAt = new Date(Date.now() + 3600000); // 1 hour from now
      const token = new AuthToken('   ', '   ', expiresAt);
      expect(token.isValid()).toBe(false);
    });
  });
});
