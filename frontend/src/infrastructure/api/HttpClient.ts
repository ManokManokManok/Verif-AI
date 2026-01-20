import axios from 'axios';
import type { AxiosInstance, AxiosError, InternalAxiosRequestConfig } from 'axios';
import { TokenStorage } from '../storage';
import { AuthToken } from '../../domain/entities';

/**
 * HTTP client with automatic token refresh and request/response interceptors
 */
export class HttpClient {
  private axiosInstance: AxiosInstance;
  private isRefreshing = false;
  private refreshSubscribers: Array<(token: string) => void> = [];

  constructor(baseURL: string = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000/api') {
    this.axiosInstance = axios.create({
      baseURL,
      timeout: Number(import.meta.env.VITE_API_TIMEOUT) || 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.setupInterceptors();
  }

  /**
   * Get the axios instance
   */
  getInstance(): AxiosInstance {
    return this.axiosInstance;
  }

  /**
   * Setup request and response interceptors
   */
  private setupInterceptors(): void {
    // Request interceptor - Add authorization header
    this.axiosInstance.interceptors.request.use(
      async (config: InternalAxiosRequestConfig) => {
        const token = await TokenStorage.getAccessToken();
        if (token && config.headers) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor - Handle token refresh
    this.axiosInstance.interceptors.response.use(
      (response) => response,
      async (error: AxiosError) => {
        const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

        // Skip token refresh for login/register endpoints
        const isAuthEndpoint = originalRequest.url?.includes('/auth/login') || 
                               originalRequest.url?.includes('/auth/register');

        // Handle 401 errors (unauthorized) - but not for auth endpoints
        if (error.response?.status === 401 && !originalRequest._retry && !isAuthEndpoint) {
          if (this.isRefreshing) {
            // Wait for the refresh to complete
            return new Promise((resolve) => {
              this.refreshSubscribers.push((token: string) => {
                if (originalRequest.headers) {
                  originalRequest.headers.Authorization = `Bearer ${token}`;
                }
                resolve(this.axiosInstance(originalRequest));
              });
            });
          }

          originalRequest._retry = true;
          this.isRefreshing = true;

          try {
            await this.refreshToken();
            const newToken = await TokenStorage.getAccessToken();
            
            if (newToken) {
              // Notify all waiting requests
              this.refreshSubscribers.forEach(callback => callback(newToken));
              this.refreshSubscribers = [];

              // Retry the original request with new token
              if (originalRequest.headers) {
                originalRequest.headers.Authorization = `Bearer ${newToken}`;
              }
              return this.axiosInstance(originalRequest);
            }
          } catch (refreshError) {
            // Refresh failed, clear tokens and redirect to login
            await this.handleAuthFailure();
            return Promise.reject(refreshError);
          } finally {
            this.isRefreshing = false;
          }
        }

        return Promise.reject(error);
      }
    );
  }

  /**
   * Refresh the access token using the refresh token
   */
  private async refreshToken(): Promise<void> {
    const refreshToken = await TokenStorage.getRefreshToken();
    
    if (!refreshToken) {
      throw new Error('No refresh token available');
    }

    try {
      const response = await axios.post(
        `${this.axiosInstance.defaults.baseURL}/auth/refresh`,
        { refresh_token: refreshToken }
      );

      const { access_token, refresh_token } = response.data;
      
      // Calculate expiry (15 minutes for access token)
      const expiresAt = new Date(Date.now() + 15 * 60 * 1000);
      
      const newToken = new AuthToken(
        access_token,
        refresh_token || refreshToken,
        expiresAt
      );

      await TokenStorage.storeTokens(newToken);
    } catch (error) {
      console.error('Token refresh failed:', error);
      throw error;
    }
  }

  /**
   * Handle authentication failure
   */
  private async handleAuthFailure(): Promise<void> {
    await TokenStorage.clearTokens();
    
    // Redirect to login page
    if (typeof window !== 'undefined') {
      window.location.href = '/login';
    }
  }
}

// Export singleton instance
export const httpClient = new HttpClient();
