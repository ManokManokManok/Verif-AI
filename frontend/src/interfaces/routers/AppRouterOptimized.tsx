import React, { lazy, Suspense } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ErrorBoundary } from '../../components/common/ErrorBoundary';
import { PageLoadingSkeleton } from '../../components/common/Skeleton';

// Eager load critical components
import { ProtectedRoute } from './ProtectedRoute';
import { LandingPage } from '../pages/LandingPage';

// Lazy load authentication pages
const LoginPage = lazy(() => import('../pages/auth/LoginPage').then(m => ({ default: m.LoginPage })));
const RegisterPage = lazy(() => import('../pages/auth/RegisterPage').then(m => ({ default: m.RegisterPage })));

// Lazy load dashboard components
const DashboardLayout = lazy(() => import('../components/layout/DashboardLayout').then(m => ({ default: m.DashboardLayout })));
const DashboardHomePage = lazy(() => import('../pages/dashboard/DashboardHomePage').then(m => ({ default: m.DashboardHomePage })));
const ProfilePage = lazy(() => import('../pages/ProfilePage').then(m => ({ default: m.ProfilePage })));
const SettingsPage = lazy(() => import('../pages/SettingsPage').then(m => ({ default: m.SettingsPage })));

/**
 * Main application router with code splitting
 * Defines all routes and navigation structure with lazy loading
 */
export const AppRouterOptimized: React.FC = () => {
  return (
    <ErrorBoundary>
      <BrowserRouter>
        <Suspense fallback={<PageLoadingSkeleton />}>
          <Routes>
            {/* Public routes - Landing page is eagerly loaded */}
            <Route path="/" element={<LandingPage />} />
            
            {/* Auth routes - Lazy loaded */}
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
            
            {/* Protected routes with dashboard layout - All lazy loaded */}
            <Route element={<ProtectedRoute />}>
              <Route element={<DashboardLayout />}>
                <Route path="/dashboard" element={<DashboardHomePage />} />
                <Route path="/dashboard/profile" element={<ProfilePage />} />
                <Route path="/dashboard/settings" element={<SettingsPage />} />
              </Route>
            </Route>
            
            {/* Catch all - redirect to landing */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Suspense>
      </BrowserRouter>
    </ErrorBoundary>
  );
};
