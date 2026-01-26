import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ProtectedRoute } from './ProtectedRoute';
import { LoginPage } from '../pages/auth/LoginPage';
import { RegisterPage } from '../pages/auth/RegisterPage';
import { LandingPage } from '../pages/LandingPage';
import { DashboardLayout } from '../components/layout/DashboardLayout';
import { DashboardHomePage } from '../components/dashboard/DashboardHomePage';
import { UsersPage } from '../pages/dashboard/UsersPage';
import { StatisticsPage } from '../pages/dashboard/StatisticsPage';
import { BlockchainPage } from '../pages/dashboard/BlockchainPage';

/**
 * Main application router
 * Defines all routes and navigation structure
 */
export const AppRouter: React.FC = () => {
  return (
    <BrowserRouter>
      <Routes>
        {/* Public routes */}
        <Route path="/" element={<LandingPage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        
        {/* Protected routes with dashboard layout */}
        <Route element={<ProtectedRoute />}>
          <Route element={<DashboardLayout />}>
            <Route path="/dashboard" element={<DashboardHomePage />} />
            <Route path="/dashboard/users" element={<UsersPage />} />
            <Route path="/dashboard/statistics" element={<StatisticsPage />} />
            <Route path="/dashboard/blockchain" element={<BlockchainPage />} />
          </Route>
        </Route>
        
        {/* Catch all - redirect to landing */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
};
