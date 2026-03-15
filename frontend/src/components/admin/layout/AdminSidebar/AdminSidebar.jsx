/**
 * AdminSidebar Component
 * 
 * Collapsible sidebar navigation for admin dashboard.
 * Matches user-facing Detection page sidebar design.
 */

import React from 'react';
import PropTypes from 'prop-types';
import './AdminSidebar.css';
import modelHealthIcon from '../../../../../assets/image/modelhealthPage.svg';
import analysisStatsIcon from '../../../../../assets/image/analysisstatspage.svg';
import userStatsIcon from '../../../../../assets/image/userstatsPage.svg';
import userManagementIcon from '../../../../../assets/image/usermanagementPage.svg';
import websiteAnalyticsIcon from '../../../../../assets/image/websiteanalyticsPage.svg';
import blockchainIcon from '../../../../../assets/image/blockchainPage.svg';

const ADMIN_SECTIONS = [
  { id: 'model-health', label: 'Model Health', icon: modelHealthIcon },
  { id: 'analysis-stats', label: 'Analysis Stats', icon: analysisStatsIcon },
  { id: 'user-stats', label: 'User Stats', icon: userStatsIcon },
  { id: 'user-management', label: 'User Management', icon: userManagementIcon },
  { id: 'website-analytics', label: 'Website Analytics', icon: websiteAnalyticsIcon },
  { id: 'blockchain', label: 'Blockchain', icon: blockchainIcon },
];

export default function AdminSidebar({ 
  isOpen, 
  onToggle, 
  activeSection, 
  onSectionChange,
  onClose 
}) {
  const handleSectionClick = (sectionId) => {
    onSectionChange(sectionId);
    
    // Auto-close on mobile
    if (window.innerWidth <= 768 && onClose) {
      onClose();
    }
  };

  return (
    <>
      {/* Overlay for mobile when sidebar is open */}
      {isOpen && (
        <div 
          className="admin-sidebar__overlay"
          onClick={onClose}
        />
      )}

      {/* Sidebar Navigation */}
      <aside className={`admin-sidebar${isOpen ? ' admin-sidebar--open' : ''}`}>
        {/* Menu Toggle Button */}
        <button
          className="admin-sidebar__toggle"
          type="button"
          aria-label="Toggle Menu"
          onClick={onToggle}
        >
          {isOpen ? '✕' : '☰'}
        </button>

        {/* Expanded Sidebar - Navigation List */}
        {isOpen && (
          <nav className="admin-sidebar__nav">
            <div className="admin-sidebar__title">Admin Panel</div>
            <ul className="admin-sidebar__list">
              {ADMIN_SECTIONS.map((section) => (
                <li key={section.id} className="admin-sidebar__item">
                  <button
                    className={`admin-sidebar__button ${
                      activeSection === section.id ? 'admin-sidebar__button--active' : ''
                    }`}
                    onClick={() => handleSectionClick(section.id)}
                  >
                    <span className="admin-sidebar__icon">
                      <img
                        src={section.icon}
                        alt={`${section.label} icon`}
                        className="admin-sidebar__icon-image"
                      />
                    </span>
                    <span className="admin-sidebar__label">{section.label}</span>
                  </button>
                </li>
              ))}
            </ul>
          </nav>
        )}

        {/* Collapsed Sidebar - Icon Buttons */}
        {!isOpen && (
          <>
            {ADMIN_SECTIONS.map((section) => (
              <button
                key={section.id}
                className={`admin-sidebar__iconbtn ${
                  activeSection === section.id ? 'admin-sidebar__iconbtn--active' : ''
                }`}
                type="button"
                aria-label={section.label}
                title={section.label}
                onClick={() => handleSectionClick(section.id)}
              >
                <img
                  src={section.icon}
                  alt={`${section.label} icon`}
                  className="admin-sidebar__icon-image"
                />
              </button>
            ))}
          </>
        )}
      </aside>
    </>
  );
}

AdminSidebar.propTypes = {
  isOpen: PropTypes.bool.isRequired,
  onToggle: PropTypes.func.isRequired,
  activeSection: PropTypes.string.isRequired,
  onSectionChange: PropTypes.func.isRequired,
  onClose: PropTypes.func,
};
