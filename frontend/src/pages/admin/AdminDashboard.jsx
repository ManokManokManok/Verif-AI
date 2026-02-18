/**
 * Admin Dashboard Page
 * 
 * Main container with tab navigation for all admin sections.
 */

import React, { useState } from 'react';
import { TabNavigation, Alert } from '../../components/admin';
import { useAuth } from '../../context/AuthContext';
import ModelHealth from './ModelHealth';
import AnalysisStats from './AnalysisStats';
import UserStats from './UserStats';
import UserManagement from './UserManagement';
import WebsiteAnalytics from './WebsiteAnalytics';
import BlockchainVerification from './BlockchainVerification';
import './AdminDashboard.css';
import './WebsiteAnalytics.css';

const ADMIN_TABS = [
  { id: 'model-health', label: 'Model Health' },
  { id: 'analysis-stats', label: 'Analysis Statistics' },
  { id: 'user-stats', label: 'User Statistics' },
  { id: 'user-management', label: 'User Management' },
  { id: 'website-analytics', label: 'Website Analytics' },
  { id: 'blockchain', label: 'Blockchain' },
];

export default function AdminDashboard() {
  const { user, isAdmin } = useAuth();
  const [activeTab, setActiveTab] = useState('model-health');
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

  // Render active tab content
  const renderTabContent = () => {
    switch (activeTab) {
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
      <div className="admin-dashboard__container">
        {/* Header */}
        <header className="admin-dashboard__header">
          <div className="admin-dashboard__title-section">
            <h1 className="admin-dashboard__title">Admin Dashboard</h1>
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

        {/* Tab Navigation */}
        <TabNavigation
          tabs={ADMIN_TABS}
          activeTab={activeTab}
          onTabChange={setActiveTab}
        />

        {/* Tab Content */}
        <main className="admin-dashboard__content">
          {renderTabContent()}
        </main>
      </div>
    </div>
  );
}
