// User-related types

export interface UserProfile {
  id: string;
  email: string;
  username?: string;
  roles: string[];
  permissions: string[];
  isActive: boolean;
  isVerified: boolean;
  createdAt: string;
  lastLogin?: string;
}

export interface UpdateProfileRequest {
  email?: string;
  currentPassword?: string;
  newPassword?: string;
}

export interface UpdateProfileResult {
  success: boolean;
  message: string;
  user: UserProfile;
}

export interface CheckPermissionRequest {
  permission: string;
  resource?: string;
}

export interface CheckPermissionResult {
  hasPermission: boolean;
  permission: string;
}

// User state for UI
export interface UserState {
  user: UserProfile | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
}
