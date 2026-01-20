import { httpClient } from './HttpClient';
import type {
  LoginCredentials,
  LoginResult,
  RegisterData,
  RegisterResult,
  RefreshTokenResult,
  LogoutResult,
  VerifyEmailRequest,
  VerifyEmailResult,
  RequestPasswordResetRequest,
  RequestPasswordResetResult,
  ResetPasswordRequest,
  ResetPasswordResult,
} from '../../domain/types';

/**
 * API service for authentication endpoints
 */
export class AuthApi {
  private client = httpClient.getInstance();

  /**
   * Register a new user
   */
  async register(data: RegisterData): Promise<RegisterResult> {
    const response = await this.client.post<RegisterResult>('/auth/register/', {
      email: data.email,
      password: data.password,
      username: data.username,
    });
    return response.data;
  }

  /**
   * Login user
   */
  async login(credentials: LoginCredentials): Promise<LoginResult> {
    const response = await this.client.post<LoginResult>('/auth/login/', {
      email: credentials.email,
      password: credentials.password,
    });
    return response.data;
  }

  /**
   * Refresh access token
   */
  async refreshToken(refreshToken: string): Promise<RefreshTokenResult> {
    const response = await this.client.post<RefreshTokenResult>('/auth/refresh/', {
      refresh_token: refreshToken,
    });
    return response.data;
  }

  /**
   * Logout user
   */
  async logout(): Promise<LogoutResult> {
    const response = await this.client.post<LogoutResult>('/auth/logout/');
    return response.data;
  }

  /**
   * Send email verification
   */
  async sendVerificationEmail(): Promise<{ success: boolean; message: string }> {
    const response = await this.client.post('/auth/send-verification/');
    return response.data;
  }

  /**
   * Verify email with token
   */
  async verifyEmail(request: VerifyEmailRequest): Promise<VerifyEmailResult> {
    const response = await this.client.post<VerifyEmailResult>('/auth/verify-email/', {
      token: request.token,
    });
    return response.data;
  }

  /**
   * Request password reset
   */
  async requestPasswordReset(
    request: RequestPasswordResetRequest
  ): Promise<RequestPasswordResetResult> {
    const response = await this.client.post<RequestPasswordResetResult>(
      '/auth/request-reset/',
      {
        email: request.email,
      }
    );
    return response.data;
  }

  /**
   * Reset password with token
   */
  async resetPassword(request: ResetPasswordRequest): Promise<ResetPasswordResult> {
    const response = await this.client.post<ResetPasswordResult>('/auth/reset-password/', {
      token: request.token,
      new_password: request.newPassword,
    });
    return response.data;
  }
}

// Export singleton instance
export const authApi = new AuthApi();
