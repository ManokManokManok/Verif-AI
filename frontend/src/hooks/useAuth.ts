import { useState, useEffect, useCallback } from 'react';
import { User } from '../domain/entities';
import { TokenStorage, UserStorage } from '../infrastructure/storage';
import { 
  loginUseCase, 
  logoutUseCase, 
  registerUseCase,
  refreshTokenUseCase 
} from '../use_cases/auth';
import { getProfileUseCase } from '../use_cases/user';
import type { LoginCredentials, RegisterData } from '../domain/types';

/**
 * Custom hook for authentication management
 * Provides user state and authentication methods
 */
export const useAuth = () => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Check authentication status on mount
  useEffect(() => {
    checkAuthStatus();
  }, []);

  /**
   * Check if user is authenticated and restore session
   */
  const checkAuthStatus = async () => {
    try {
      const token = await TokenStorage.getAccessToken();
      if (token) {
        // Try to get user profile to verify token is valid
        const profileResult = await getProfileUseCase.execute();
        setUser(profileResult.user);
      }
    } catch (error) {
      // Token is invalid, clear storage
      await TokenStorage.clearTokens();
      await UserStorage.clearUser();
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Login user with credentials
   */
  const login = useCallback(async (credentials: LoginCredentials) => {
    setIsLoading(true);
    setError(null);
    
    try {
      const result = await loginUseCase.execute(credentials);
      setUser(result.user);
      return result;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Login failed';
      setError(errorMessage);
      throw error;
    } finally {
      setIsLoading(false);
    }
  }, []);

  /**
   * Register new user
   */
  const register = useCallback(async (userData: RegisterData) => {
    setIsLoading(true);
    setError(null);
    
    try {
      const result = await registerUseCase.execute(userData);
      return result;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Registration failed';
      setError(errorMessage);
      throw error;
    } finally {
      setIsLoading(false);
    }
  }, []);

  /**
   * Logout user and clear session
   */
  const logout = useCallback(async () => {
    try {
      await logoutUseCase.execute();
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      setUser(null);
      await TokenStorage.clearTokens();
      await UserStorage.clearUser();
    }
  }, []);

  /**
   * Refresh authentication token
   */
  const refreshAuth = useCallback(async () => {
    try {
      const result = await refreshTokenUseCase.execute();
      return result;
    } catch (error) {
      // Refresh failed, logout user
      await logout();
      throw error;
    }
  }, [logout]);

  /**
   * Clear error state
   */
  const clearError = useCallback(() => {
    setError(null);
  }, []);

  return {
    user,
    isLoading,
    error,
    login,
    register,
    logout,
    refreshAuth,
    clearError,
    isAuthenticated: !!user,
  };
};
