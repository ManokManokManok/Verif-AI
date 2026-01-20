import { httpClient } from './HttpClient';
import type {
  UserProfile,
  UpdateProfileRequest,
  UpdateProfileResult,
  CheckPermissionRequest,
  CheckPermissionResult,
} from '../../domain/types';

/**
 * API service for user management endpoints
 */
export class UserApi {
  private client = httpClient.getInstance();

  /**
   * Get current user profile
   */
  async getProfile(): Promise<UserProfile> {
    const response = await this.client.get<{ user: UserProfile }>('/users/profile/');
    return response.data.user;
  }

  /**
   * Update user profile
   */
  async updateProfile(data: UpdateProfileRequest): Promise<UpdateProfileResult> {
    const response = await this.client.put<UpdateProfileResult>('/users/profile/', data);
    return response.data;
  }

  /**
   * Check user permission
   */
  async checkPermission(request: CheckPermissionRequest): Promise<CheckPermissionResult> {
    const response = await this.client.post<CheckPermissionResult>(
      '/users/check-permission/',
      {
        permission: request.permission,
        resource: request.resource,
      }
    );
    return response.data;
  }
}

// Export singleton instance
export const userApi = new UserApi();
