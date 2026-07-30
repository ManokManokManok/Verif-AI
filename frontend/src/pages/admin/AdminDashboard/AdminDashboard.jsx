/**
 * Admin Dashboard Page
 * 
 * Main container for all admin sections with modular sidebar navigation.
 */

import React, { useEffect, useMemo, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { Alert, AdminSidebar } from '../../../components/admin';
import LogoutConfirmModal from '../../../components/auth/LogoutConfirmModal';
import { useAuth } from '../../../context/AuthContext';
import ModelHealth from '../ModelHealth';
import AnalysisStats from '../AnalysisStats';
import UserStats from '../UserStats';
import UserManagement from '../UserManagement';
import WebsiteAnalytics from '../WebsiteAnalytics';
import './AdminDashboard.css';
import '../WebsiteAnalytics/WebsiteAnalytics.css';

const SECTION_LABELS = {
  'model-health': 'Model Health',
  'analysis-stats': 'Analysis Stats',
  'user-stats': 'User Stats',
  'user-management': 'User Management',
  'website-analytics': 'Website Analytics',
};

export default function AdminDashboard() {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, isAdmin, logout } = useAuth();
  const validSectionIds = useMemo(() => new Set(Object.keys(SECTION_LABELS)), []);
  const resolveSection = (sectionId) => (
    sectionId && validSectionIds.has(sectionId) ? sectionId : 'model-health'
  );

  const [activeSection, setActiveSection] = useState(() => {
    const initialSection = new URLSearchParams(window.location.search).get('section');
    return resolveSection(initialSection);
  });
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [notification, setNotification] = useState(null);
  const [showLogoutModal, setShowLogoutModal] = useState(false);

  useEffect(() => {
    const sectionFromQuery = new URLSearchParams(location.search).get('section');
    setActiveSection(resolveSection(sectionFromQuery));
  }, [location.search]);

  const handleSectionChange = (sectionId) => {
    const nextSection = resolveSection(sectionId);
    setActiveSection(nextSection);

    const currentSection = new URLSearchParams(location.search).get('section');
    if (currentSection !== nextSection) {
      navigate(`/admin?section=${encodeURIComponent(nextSection)}`, { replace: true });
    }
  };

  // Show notification and auto-dismiss after 5 seconds
  const showNotification = (type, message) => {
    setNotification({ type, message });
    setTimeout(() => setNotification(null), 5000);
  };

  const handleLogout = () => {
    setShowLogoutModal(true);
  };

  const confirmLogout = async () => {
    setShowLogoutModal(false);
    await logout();
    navigate('/');
  };

  const cancelLogout = () => {
    setShowLogoutModal(false);
  };

  // Render access denied if not admin
  if (!isAdmin) {
    return (
      <div className="admin-dashboard">
        <div className="admin-dashboard__container">
          <Alert 
            type="error" 
            message="Access Denied. You need administrator privileges to view this page." 
          />
        </div>
      </div>
    );
  }

  // Render active section content
  const renderSectionContent = () => {
    switch (activeSection) {
      case 'model-health':
        return <ModelHealth onNotify={showNotification} />;
      case 'analysis-stats':
        return <AnalysisStats onNotify={showNotification} />;
      case 'user-stats':
        return <UserStats onNotify={showNotification} />;
      case 'user-management':
        return <UserManagement onNotify={showNotification} />;
      case 'website-analytics':
        return <WebsiteAnalytics onNotify={showNotification} />;
      default:
        return null;
    }
  };

  return (
    <div className="admin-dashboard page-enter">
      {/* Sidebar Navigation Component */}
      <AdminSidebar
        isOpen={sidebarOpen}
        onToggle={() => setSidebarOpen(!sidebarOpen)}
        activeSection={activeSection}
        onSectionChange={handleSectionChange}
        onClose={() => setSidebarOpen(false)}
        onLogout={handleLogout}
      />

      {/* Main Content Area */}
      <div className="admin-dashboard__main">
        <div className="admin-dashboard__container">
          {/* Mobile Menu Button */}
          <button
            className="admin-dashboard__mobile-menu"
            onClick={() => setSidebarOpen(true)}
            aria-label="Open Menu"
          >
            ☰
          </button>

          {/* Header */}
          <header className="admin-dashboard__header">
            <div className="admin-dashboard__title-section">
              <h1 className="admin-dashboard__title">
                {SECTION_LABELS[activeSection] || 'Admin Dashboard'}
              </h1>
              <p className="admin-dashboard__subtitle">
                Welcome back, {user?.username || 'Admin'}
              </p>
            </div>
          </header>

          {/* Notification */}
          {notification && (
            <Alert
              type={notification.type}
              message={notification.message}
              onClose={() => setNotification(null)}
            />
          )}

          {/* Section Content */}
          <main className="admin-dashboard__content">
            {renderSectionContent()}
          </main>

          <LogoutConfirmModal
            isOpen={showLogoutModal}
            onConfirm={confirmLogout}
            onCancel={cancelLogout}
          />
        </div>
      </div>
    </div>
  );
}
