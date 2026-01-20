import { AuthToken } from '../../domain/entities';

/**
 * Service for managing token storage in localStorage
 */
export class TokenStorage {
  private static readonly ACCESS_TOKEN_KEY = 'verfai_access_token';
  private static readonly REFRESH_TOKEN_KEY = 'verfai_refresh_token';
  private static readonly TOKEN_EXPIRY_KEY = 'verfai_token_expiry';

  /**
   * Store authentication tokens
   */
  static async storeTokens(token: AuthToken): Promise<void> {
    if (typeof window !== 'undefined') {
      try {
        localStorage.setItem(this.ACCESS_TOKEN_KEY, token.accessToken);
        localStorage.setItem(this.REFRESH_TOKEN_KEY, token.refreshToken);
        localStorage.setItem(this.TOKEN_EXPIRY_KEY, token.expiresAt.toISOString());
      } catch (error) {
        console.error('Error storing tokens:', error);
        throw new Error('Failed to store authentication tokens');
      }
    }
  }

  /**
   * Get access token
   */
  static async getAccessToken(): Promise<string | null> {
    if (typeof window !== 'undefined') {
      try {
        return localStorage.getItem(this.ACCESS_TOKEN_KEY);
      } catch (error) {
        console.error('Error retrieving access token:', error);
        return null;
      }
    }
    return null;
  }

  /**
   * Get refresh token
   */
  static async getRefreshToken(): Promise<string | null> {
    if (typeof window !== 'undefined') {
      try {
        return localStorage.getItem(this.REFRESH_TOKEN_KEY);
      } catch (error) {
        console.error('Error retrieving refresh token:', error);
        return null;
      }
    }
    return null;
  }

  /**
   * Get token expiry date
   */
  static async getTokenExpiry(): Promise<Date | null> {
    if (typeof window !== 'undefined') {
      try {
        const expiry = localStorage.getItem(this.TOKEN_EXPIRY_KEY);
        return expiry ? new Date(expiry) : null;
      } catch (error) {
        console.error('Error retrieving token expiry:', error);
        return null;
      }
    }
    return null;
  }

  /**
   * Get complete auth token object
   */
  static async getAuthToken(): Promise<AuthToken | null> {
    const accessToken = await this.getAccessToken();
    const refreshToken = await this.getRefreshToken();
    const expiresAt = await this.getTokenExpiry();

    if (!accessToken || !refreshToken || !expiresAt) {
      return null;
    }

    return new AuthToken(accessToken, refreshToken, expiresAt);
  }

  /**
   * Clear all stored tokens
   */
  static async clearTokens(): Promise<void> {
    if (typeof window !== 'undefined') {
      try {
        localStorage.removeItem(this.ACCESS_TOKEN_KEY);
        localStorage.removeItem(this.REFRESH_TOKEN_KEY);
        localStorage.removeItem(this.TOKEN_EXPIRY_KEY);
      } catch (error) {
        console.error('Error clearing tokens:', error);
      }
    }
  }

  /**
   * Check if tokens exist in storage
   */
  static async hasTokens(): Promise<boolean> {
    const accessToken = await this.getAccessToken();
    const refreshToken = await this.getRefreshToken();
    return !!(accessToken && refreshToken);
  }
}
