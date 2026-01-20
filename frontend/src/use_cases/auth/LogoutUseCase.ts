import { authApi } from '../../infrastructure/api';
import { TokenStorage, UserStorage } from '../../infrastructure/storage';

/**
 * Use case for user logout
 * Handles token blacklisting and local session cleanup
 */
export class LogoutUseCase {
  async execute(): Promise<{ success: boolean; message: string }> {
    try {
      // Call logout API to blacklist tokens
      await authApi.logout();
    } catch (error) {
      // Even if API call fails, clear local storage
      console.error('Logout API call failed:', error);
    } finally {
      // Always clear local storage
      await TokenStorage.clearTokens();
      await UserStorage.clearUser();
    }

    return {
      success: true,
      message: 'Logged out successfully',
    };
  }
}

// Export singleton instance
export const logoutUseCase = new LogoutUseCase();
