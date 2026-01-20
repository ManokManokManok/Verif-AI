import { authApi } from '../../infrastructure/api';
import { validationService } from '../../domain/services';
import type { RegisterData, RegisterResult } from '../../domain/types';

/**
 * Use case for user registration
 * Handles user signup with validation
 */
export class RegisterUseCase {
  async execute(data: RegisterData): Promise<{
    success: boolean;
    message: string;
    userId: string;
    email: string;
  }> {
    // Validate email format
    if (!validationService.validateEmail(data.email)) {
      throw new Error('Invalid email format');
    }

    // Validate password strength
    const passwordValidation = validationService.validatePassword(data.password);
    if (!passwordValidation.isValid) {
      throw new Error(passwordValidation.errors.join(', '));
    }

    // Validate password confirmation
    const matchValidation = validationService.validatePasswordMatch(
      data.password,
      data.confirmPassword
    );
    if (!matchValidation.isValid) {
      throw new Error(matchValidation.errors[0]);
    }

    // Call registration API
    const response: RegisterResult = await authApi.register(data);

    return {
      success: true,
      message: response.message || 'Registration successful. Please check your email for verification.',
      userId: response.user.id,
      email: response.user.email,
    };
  }
}

// Export singleton instance
export const registerUseCase = new RegisterUseCase();
