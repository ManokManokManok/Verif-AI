import { authApi } from '../../infrastructure/api';
import { TokenStorage, UserStorage } from '../../infrastructure/storage';
import { validationService } from '../../domain/services';
import { User, AuthToken } from '../../domain/entities';
import type { LoginCredentials, LoginResult } from '../../domain/types';

/**
 * Use case for user login
 * Handles authentication, token storage, and user session management
 */
export class LoginUseCase {
  async execute(credentials: LoginCredentials): Promise<{
    success: boolean;
    user: User;
    token: AuthToken;
  }> {
    // Validate email format
    if (!validationService.validateEmail(credentials.email)) {
      throw new Error('Invalid email format');
    }

    // Validate password is provided
    const passwordValidation = validationService.validateRequired(
      credentials.password,
      'Password'
    );
    if (!passwordValidation.isValid) {
      throw new Error(passwordValidation.errors[0]);
    }

    // Call authentication API
    const response: LoginResult = await authApi.login(credentials);

    // Calculate token expiry (15 minutes from now)
    const expiresAt = new Date(Date.now() + 15 * 60 * 1000);

    // Create domain entities
    const authToken = new AuthToken(
      response.tokens.access_token,
      response.tokens.refresh_token,
      expiresAt
    );

    const user = new User(
      response.user.id,
      response.user.email,
      response.user.roles,
      response.user.is_active,
      response.user.is_verified,
      new Date(response.user.created_at),
      response.user.username,
      response.user.last_login ? new Date(response.user.last_login) : undefined
    );

    // Store tokens and user data
    await TokenStorage.storeTokens(authToken);
    await UserStorage.storeUser({
      id: user.id,
      email: user.email,
      username: user.username,
      roles: user.roles,
      permissions: user.getAllPermissions(),
      isActive: user.isActive,
      isVerified: user.isVerified,
      createdAt: user.createdAt.toISOString(),
      lastLogin: user.lastLogin?.toISOString(),
    });

    return {
      success: true,
      user,
      token: authToken,
    };
  }
}

// Export singleton instance
export const loginUseCase = new LoginUseCase();
