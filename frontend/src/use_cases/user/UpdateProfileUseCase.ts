import { userApi } from '../../infrastructure/api';
import { validationService } from '../../domain/services';
import { UserStorage } from '../../infrastructure/storage';
import type { UpdateProfileRequest, UserProfile } from '../../domain/types';

/**
 * Use case for updating user profile
 * Handles profile updates with validation
 */
export class UpdateProfileUseCase {
  async execute(data: UpdateProfileRequest): Promise<{
    success: boolean;
    message: string;
    user: UserProfile;
  }> {
    // Validate email if provided
    if (data.email && !validationService.validateEmail(data.email)) {
      throw new Error('Invalid email format');
    }

    // Validate new password if provided
    if (data.newPassword) {
      // Current password is required when changing password
      if (!data.currentPassword) {
        throw new Error('Current password is required to set a new password');
      }

      const passwordValidation = validationService.validatePassword(data.newPassword);
      if (!passwordValidation.isValid) {
        throw new Error(passwordValidation.errors.join(', '));
      }
    }

    // Call update API
    const response = await userApi.updateProfile(data);

    // Update local storage with new data
    await UserStorage.storeUser(response.user);

    return {
      success: true,
      message: response.message || 'Profile updated successfully',
      user: response.user,
    };
  }
}

// Export singleton instance
export const updateProfileUseCase = new UpdateProfileUseCase();
