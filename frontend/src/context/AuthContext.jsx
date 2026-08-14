import { createContext, useContext, useState, useCallback, useEffect, useRef } from 'react';
import { 
  loginRequest, 
  logoutRequest, 
  getStoredUser, 
  isLoggedIn as checkIsLoggedIn,
  isAdmin as checkIsAdmin,
  hasRole as checkHasRole,
  isTokenExpired
} from '../api/client';

// Create context
const AuthContext = createContext(null);

/**
 * Auth Provider Component
 * Wrap your app with this to provide auth state
 */
export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => getStoredUser());
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [sessionExpired, setSessionExpired] = useState(false);
  const sessionExpiredHandled = useRef(false);

  // Check if logged in (also verify token is not expired client-side)
  const accessToken = window.localStorage.getItem('access_token');
  const isLoggedIn = Boolean(user && checkIsLoggedIn() && !isTokenExpired(accessToken, 0));

  // Check if admin
  const isAdmin = isLoggedIn && checkIsAdmin();

  // Check role
  const hasRole = useCallback((roleName) => {
    return isLoggedIn && checkHasRole(roleName);
  }, [isLoggedIn]);

  // Login function
  const login = useCallback(async ({ email, password }) => {
    setIsLoading(true);
    setError(null);
    
    try {
      const data = await loginRequest({ email, password });
      setUser(data.user);
      setSessionExpired(false);
      sessionExpiredHandled.current = false;
      return data;
    } catch (err) {
      setError(err.message || 'Login failed');
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Logout function
  const logout = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      await logoutRequest();
    } catch (err) {
      console.error('Logout error:', err);
      // Still clear state even if API call fails
    } finally {
      setUser(null);
      setIsLoading(false);
    }
  }, []);

  // Refresh user from storage (useful after page reload)
  const refreshUser = useCallback(() => {
    const storedUser = getStoredUser();
    if (storedUser && checkIsLoggedIn()) {
      setUser(storedUser);
    } else {
      setUser(null);
    }
  }, []);

  // Listen for storage changes (e.g., logout in another tab)
  useEffect(() => {
    const handleStorageChange = (e) => {
      if (e.key === 'access_token' || e.key === 'user') {
        refreshUser();
      }
    };

    window.addEventListener('storage', handleStorageChange);
    return () => window.removeEventListener('storage', handleStorageChange);
  }, [refreshUser]);

  // Listen for session-expired events dispatched by the API client
  useEffect(() => {
    const handleSessionExpired = () => {
      if (sessionExpiredHandled.current) return;
      sessionExpiredHandled.current = true;
      setSessionExpired(true);
      // Clear auth state
      window.localStorage.removeItem('access_token');
      window.localStorage.removeItem('refresh_token');
      window.localStorage.removeItem('user');
      setUser(null);
    };

    window.addEventListener('session-expired', handleSessionExpired);
    return () => window.removeEventListener('session-expired', handleSessionExpired);
  }, []);

  // Periodically check token expiry while the user is on the app (every 60s)
  useEffect(() => {
    if (!user) return;

    const checkTokenExpiry = () => {
      const token = window.localStorage.getItem('access_token');
      if (token && isTokenExpired(token, 0)) {
        // Token expired — trigger session expired flow
        window.dispatchEvent(new CustomEvent('session-expired'));
      }
    };

    const intervalId = setInterval(checkTokenExpiry, 60 * 1000);
    return () => clearInterval(intervalId);
  }, [user]);

  // Reset sessionExpired flag on successful login
  const dismissSessionExpired = useCallback(() => {
    setSessionExpired(false);
    sessionExpiredHandled.current = false;
  }, []);

  // Get access token from localStorage
  const accessTokenValue = localStorage.getItem('access_token');

  const value = {
    user,
    isLoggedIn,
    isAdmin,
    isLoading,
    error,
    login,
    logout,
    hasRole,
    refreshUser,
    accessToken: accessTokenValue,
    sessionExpired,
    dismissSessionExpired,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

/**
 * Hook to use auth context
 */
export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

/**
 * Higher-order component for requiring authentication
 */
export function withAuth(Component, { requireAdmin = false } = {}) {
  return function AuthenticatedComponent(props) {
    const { isLoggedIn, isAdmin } = useAuth();
    
    if (!isLoggedIn) {
      return (
        <div className="auth-required">
          <h2>Authentication Required</h2>
          <p>Please log in to access this page.</p>
        </div>
      );
    }
    
    if (requireAdmin && !isAdmin) {
      return (
        <div className="auth-required">
          <h2>Admin Access Required</h2>
          <p>You do not have permission to access this page.</p>
        </div>
      );
    }
    
    return <Component {...props} />;
  };
}

export default AuthContext;
