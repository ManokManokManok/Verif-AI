/**
 * Admin Dashboard Page
 * 
 * Main container for all admin sections with modular sidebar navigation.
 */

import React, { useState } from 'react';
import { Alert, AdminSidebar } from '../../../components/admin';
import { useAuth } from '../../../context/AuthContext';
import ModelHealth from '../ModelHealth';
import AnalysisStats from '../AnalysisStats';
import UserStats from '../UserStats';
import UserManagement from '../UserManagement';
import WebsiteAnalytics from '../WebsiteAnalytics';
import BlockchainVerification from '../BlockchainVerification';
import './AdminDashboard.css';
import '../WebsiteAnalytics/WebsiteAnalytics.css';

const SECTION_LABELS = {
  'model-health': 'Model Health',
  'analysis-stats': 'Analysis Stats',
  'user-stats': 'User Stats',
  'user-management': 'User Management',
  'website-analytics': 'Website Analytics',
  'blockchain': 'Blockchain',
};

export default function AdminDashboard() {
  const { user, isAdmin } = useAuth();
  const [activeSection, setActiveSection] = useState('model-health');
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [notification, setNotification] = useState(null);

  // Show notification and auto-dismiss after 5 seconds
  const showNotification = (type, message) => {
    setNotification({ type, message });
    setTimeout(() => setNotification(null), 5000);
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
      case 'blockchain':
        return <BlockchainVerification onNotify={showNotification} />;
      default:
        return null;
    }
  };

  return (
    <div className="admin-dashboard">
      {/* Sidebar Navigation Component */}
      <AdminSidebar
        isOpen={sidebarOpen}
        onToggle={() => setSidebarOpen(!sidebarOpen)}
        activeSection={activeSection}
        onSectionChange={setActiveSection}
        onClose={() => setSidebarOpen(false)}
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
        </div>
      </div>
    </div>
  );
}
