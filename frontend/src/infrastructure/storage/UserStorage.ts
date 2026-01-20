import type { UserProfile } from '../../domain/types';

/**
 * Service for managing user data storage
 */
export class UserStorage {
  private static readonly USER_KEY = 'verfai_user';

  /**
   * Store user profile
   */
  static async storeUser(user: UserProfile): Promise<void> {
    if (typeof window !== 'undefined') {
      try {
        localStorage.setItem(this.USER_KEY, JSON.stringify(user));
      } catch (error) {
        console.error('Error storing user:', error);
        throw new Error('Failed to store user data');
      }
    }
  }

  /**
   * Get stored user profile
   */
  static async getUser(): Promise<UserProfile | null> {
    if (typeof window !== 'undefined') {
      try {
        const userJson = localStorage.getItem(this.USER_KEY);
        return userJson ? JSON.parse(userJson) : null;
      } catch (error) {
        console.error('Error retrieving user:', error);
        return null;
      }
    }
    return null;
  }

  /**
   * Clear stored user
   */
  static async clearUser(): Promise<void> {
    if (typeof window !== 'undefined') {
      try {
        localStorage.removeItem(this.USER_KEY);
      } catch (error) {
        console.error('Error clearing user:', error);
      }
    }
  }

  /**
   * Check if user exists in storage
   */
  static async hasUser(): Promise<boolean> {
    const user = await this.getUser();
    return user !== null;
  }
}
