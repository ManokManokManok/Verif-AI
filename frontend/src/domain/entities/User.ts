// Domain entity representing a user in the system
export class User {
  public readonly id: string;
  public readonly email: string;
  public readonly username?: string;
  public readonly roles: string[];
  public readonly isActive: boolean;
  public readonly isVerified: boolean;
  public readonly createdAt: Date;
  public readonly lastLogin?: Date;

  constructor(
    id: string,
    email: string,
    roles: string[],
    isActive: boolean,
    isVerified: boolean,
    createdAt: Date,
    username?: string,
    lastLogin?: Date
  ) {
    this.id = id;
    this.email = email;
    this.username = username;
    this.roles = roles;
    this.isActive = isActive;
    this.isVerified = isVerified;
    this.createdAt = createdAt;
    this.lastLogin = lastLogin;
  }

  /**
   * Check if user can access a specific permission
   */
  canAccess(permission: string): boolean {
    return this.roles.includes('admin') || this.hasPermission(permission);
  }

  /**
   * Check if user has a specific permission based on their roles
   */
  private hasPermission(permission: string): boolean {
    return this.roles.some(role => this.roleHasPermission(role, permission));
  }

  /**
   * Map roles to their permissions
   */
  private roleHasPermission(role: string, permission: string): boolean {
    const rolePermissions: Record<string, string[]> = {
      'admin': [
        'create_user',
        'delete_user',
        'update_user',
        'create_post',
        'delete_post',
        'update_post',
        'view_analytics',
        'manage_system'
      ],
      'user': [
        'view_profile',
        'update_profile',
        'create_post',
        'update_own_post'
      ],
      'moderator': [
        'view_analytics',
        'moderate_content',
        'delete_post',
        'update_post'
      ]
    };
    return rolePermissions[role]?.includes(permission) || false;
  }

  /**
   * Check if user has a specific role
   */
  hasRole(role: string): boolean {
    return this.roles.includes(role);
  }

  /**
   * Check if user is fully activated (active and verified)
   */
  isFullyActivated(): boolean {
    return this.isActive && this.isVerified;
  }

  /**
   * Get all permissions for the user based on their roles
   */
  getAllPermissions(): string[] {
    const allPermissions = new Set<string>();
    
    const rolePermissions: Record<string, string[]> = {
      'admin': [
        'create_user',
        'delete_user',
        'update_user',
        'create_post',
        'delete_post',
        'update_post',
        'view_analytics',
        'manage_system'
      ],
      'user': [
        'view_profile',
        'update_profile',
        'create_post',
        'update_own_post'
      ],
      'moderator': [
        'view_analytics',
        'moderate_content',
        'delete_post',
        'update_post'
      ]
    };

    this.roles.forEach(role => {
      const permissions = rolePermissions[role] || [];
      permissions.forEach(permission => allPermissions.add(permission));
    });

    return Array.from(allPermissions);
  }
}
