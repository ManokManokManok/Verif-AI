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
import { AdminDashboard } from './pages/admin';
import TermsAndConditions from './pages/TermsAndConditions.jsx';
import SessionExpiredModal from './components/auth/SessionExpiredModal';
import MobileHeader from './components/MobileHeader';
import { useEffect, useState } from 'react';

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

function App() {
  const location = useLocation();
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
  const showMobileHeader = isMobile && !hideMobileHeaderOnRoutes.has(location.pathname) && !location.pathname.startsWith('/admin');

  return (
    <ThemeProvider>
      <AuthProvider>
        {showMobileHeader && <MobileHeader />}
        <SessionExpiredModal />
        <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/detection" element={<Detection />} />
        <Route path="/chatbot" element={<AIChatbot />} />
        <Route path="/login" element={<Login />} />
        <Route path="/signup" element={<Signup />} />
        <Route path="/verify-email" element={<VerifyEmail />} />
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
          path="/admin" 
          element={
            <ProtectedRoute requireAdmin>
              <AdminDashboard />
            </ProtectedRoute>
          } 
        />
      </Routes>
      </AuthProvider>
    </ThemeProvider>
  );
}

export default App;

