import { userApi } from '../../infrastructure/api';
import type { CheckPermissionRequest } from '../../domain/types';

/**
 * Use case for checking user permissions
 * Verifies if current user has specific permissions
 */
export class CheckPermissionUseCase {
  async execute(permission: string, resource?: string): Promise<{
    hasPermission: boolean;
    permission: string;
  }> {
    const request: CheckPermissionRequest = {
      permission,
      resource,
    };

    const response = await userApi.checkPermission(request);

    return {
      hasPermission: response.hasPermission,
      permission: response.permission,
    };
  }

  /**
   * Check multiple permissions at once
   */
  async checkMultiple(permissions: string[]): Promise<{
    [permission: string]: boolean;
  }> {
    const results: { [permission: string]: boolean } = {};

    // Execute all permission checks in parallel
    await Promise.all(
      permissions.map(async (permission) => {
        try {
          const result = await this.execute(permission);
          results[permission] = result.hasPermission;
        } catch (error) {
          // If check fails, assume no permission
          results[permission] = false;
        }
      })
    );

    return results;
  }
}

// Export singleton instance
export const checkPermissionUseCase = new CheckPermissionUseCase();
