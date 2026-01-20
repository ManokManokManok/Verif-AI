import { authApi } from '../../infrastructure/api';
import { TokenStorage } from '../../infrastructure/storage';
import { AuthToken } from '../../domain/entities';

/**
 * Use case for refreshing access token
 * Handles token refresh and storage update
 */
export class RefreshTokenUseCase {
  async execute(): Promise<{ success: boolean; token: AuthToken }> {
    // Get current refresh token
    const refreshToken = await TokenStorage.getRefreshToken();
    
    if (!refreshToken) {
      throw new Error('No refresh token available');
    }

    // Call refresh API
    const response = await authApi.refreshToken(refreshToken);

    // Calculate new expiry (15 minutes from now)
    const expiresAt = new Date(Date.now() + 15 * 60 * 1000);

    // Create new auth token
    const newToken = new AuthToken(
      response.tokens.access_token,
      response.tokens.refresh_token || refreshToken, // Use new refresh token if provided
      expiresAt
    );

    // Store new tokens
    await TokenStorage.storeTokens(newToken);

    return {
      success: true,
      token: newToken,
    };
  }

  /**
   * Check if token needs refresh and execute if necessary
   */
  async executeIfNeeded(): Promise<boolean> {
    const currentToken = await TokenStorage.getAuthToken();
    
    if (!currentToken) {
      return false;
    }

    // Refresh if token expires within 5 minutes
    if (currentToken.needsRefresh()) {
      try {
        await this.execute();
        return true;
      } catch (error) {
        console.error('Token refresh failed:', error);
        return false;
      }
    }

    return false;
  }
}

// Export singleton instance
export const refreshTokenUseCase = new RefreshTokenUseCase();
