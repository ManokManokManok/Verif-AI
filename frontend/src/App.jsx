import { Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { ThemeProvider } from './context/ThemeContext';
import Landing from './pages/Landing.jsx';
import Login from './pages/Login.jsx';
import Signup from './pages/Signup.jsx';
import Detection from './pages/Detection.jsx';
import AIChatbot from './pages/AIChatbot.jsx';
import VerifyEmail from './pages/VerifyEmail.jsx';
import ForgotPassword from './pages/ForgotPassword.jsx';
import ResetPassword from './pages/ResetPassword.jsx';
import Settings from './pages/Settings.jsx';
import Analytics from './pages/Analytics.jsx';
import { AdminDashboard } from './pages/admin';
import TermsAndConditions from './pages/TermsAndConditions.jsx';
import SessionExpiredModal from './components/auth/SessionExpiredModal';
import MobileHeader from './components/MobileHeader';
import { useEffect, useRef, useState } from 'react';

/**
 * Protected Route Component
 * 
 * Wraps routes that require authentication and optionally admin role.
 */
function ProtectedRoute({ children, requireAdmin = false }) {
  const { isLoggedIn, isAdmin, loading } = useAuth();

  // Show loading state while checking auth
  if (loading) {
    return (
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        minHeight: '100vh',
        background: '#0f0f0f',
        color: '#fff'
      }}>
        Loading...
      </div>
    );
  }

  // Redirect to login if not authenticated
  if (!isLoggedIn) {
    return <Navigate to="/login" replace />;
  }

  // Redirect to home if admin is required but user is not admin
  if (requireAdmin && !isAdmin) {
    return <Navigate to="/" replace />;
  }

  return children;
}

function GuestRoute({ children }) {
  const { isLoggedIn } = useAuth();

  if (isLoggedIn) {
    return <Navigate to="/" replace />;
  }

  return children;
}

function App() {
  const location = useLocation();
  const [routeLoading, setRouteLoading] = useState(false);
  const isFirstRoute = useRef(true);

  useEffect(() => {
    if (isFirstRoute.current) {
      isFirstRoute.current = false;
      return undefined;
    }
    setRouteLoading(true);
    const timer = setTimeout(() => setRouteLoading(false), 700);
    return () => clearTimeout(timer);
  }, [location.pathname]);
  const [isMobile, setIsMobile] = useState(
    typeof window !== 'undefined' && window.matchMedia
      ? window.matchMedia('(max-width: 600px)').matches
      : false
  );

  useEffect(() => {
    if (!window.matchMedia) return undefined;
    const mq = window.matchMedia('(max-width: 600px)');
    const handler = (e) => setIsMobile(e.matches);
    if (mq.addEventListener) mq.addEventListener('change', handler);
    else mq.addListener(handler);
    return () => {
      if (mq.removeEventListener) mq.removeEventListener('change', handler);
      else mq.removeListener(handler);
    };
  }, []);

  const hideMobileHeaderOnRoutes = new Set(['/login', '/signup', '/verify-email']);
  const showMobileHeader = isMobile && !hideMobileHeaderOnRoutes.has(location.pathname);

  return (
    <ThemeProvider>
      <AuthProvider>
        {showMobileHeader && <MobileHeader />}
        <SessionExpiredModal />
        <div key={location.pathname} className={`route-fade${!isFirstRoute.current ? ' route-fade--delayed' : ''}`}>
        <Routes location={location}>
        <Route path="/" element={<Landing />} />
        <Route path="/detection" element={<Detection />} />
        <Route path="/chatbot" element={<AIChatbot />} />
        <Route path="/login" element={<GuestRoute><Login /></GuestRoute>} />
        <Route path="/signup" element={<GuestRoute><Signup /></GuestRoute>} />
        <Route path="/verify-email" element={<GuestRoute><VerifyEmail /></GuestRoute>} />
        <Route path="/forgot-password" element={<ForgotPassword />} />
        <Route path="/reset-password" element={<ResetPassword />} />
        <Route path="/terms-and-conditions" element={<TermsAndConditions />} />
        <Route
          path="/settings"
          element={
            <ProtectedRoute>
              <Settings />
            </ProtectedRoute>
          }
        />
        <Route
          path="/analytics"
          element={
            <ProtectedRoute>
              <Analytics />
            </ProtectedRoute>
          }
        />
        <Route path="/journey" element={<Navigate to="/analytics" replace />} />
        <Route 
          path="/admin" 
          element={
            <ProtectedRoute requireAdmin>
              <AdminDashboard />
            </ProtectedRoute>
          } 
        />
      </Routes>
        </div>
        {routeLoading && (
          <div className="detect__navigation-loading route-loader" role="status" aria-live="polite">
            <div className="detect__navigation-card">
              <div className="detect__navigation-mark" aria-hidden="true">
                <span />
                <span />
                <span />
              </div>
              <div className="detect__navigation-copy">
                <strong>Loading</strong>
                <span>Just a moment...</span>
              </div>
              <div className="detect__navigation-progress" aria-hidden="true">
                <span />
              </div>
            </div>
          </div>
        )}
      </AuthProvider>
    </ThemeProvider>
  );
}

export default App;
