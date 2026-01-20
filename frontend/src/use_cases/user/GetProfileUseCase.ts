import { userApi } from '../../infrastructure/api';
import { UserStorage } from '../../infrastructure/storage';
import { User } from '../../domain/entities';
import type { UserProfile } from '../../domain/types';

/**
 * Use case for retrieving user profile
 * Fetches current user data and updates local storage
 */
export class GetProfileUseCase {
  async execute(): Promise<{ success: boolean; user: User }> {
    // Call profile API
    const profile: UserProfile = await userApi.getProfile();

    // Create User domain entity
    const user = new User(
      profile.id,
      profile.email,
      profile.roles,
      profile.isActive,
      profile.isVerified,
      new Date(profile.createdAt),
      profile.username,
      profile.lastLogin ? new Date(profile.lastLogin) : undefined
    );

    // Update local storage with fresh data
    await UserStorage.storeUser(profile);

    return {
      success: true,
      user,
    };
  }

  /**
   * Get profile from local storage without API call
   * Useful for quick access to cached user data
   */
  async getFromCache(): Promise<User | null> {
    const cachedProfile = await UserStorage.getUser();
    
    if (!cachedProfile) {
      return null;
    }

    return new User(
      cachedProfile.id,
      cachedProfile.email,
      cachedProfile.roles,
      cachedProfile.isActive,
      cachedProfile.isVerified,
      new Date(cachedProfile.createdAt),
      cachedProfile.username,
      cachedProfile.lastLogin ? new Date(cachedProfile.lastLogin) : undefined
    );
  }
}

// Export singleton instance
export const getProfileUseCase = new GetProfileUseCase();
