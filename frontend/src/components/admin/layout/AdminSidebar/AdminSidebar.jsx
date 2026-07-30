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

const ADMIN_SECTIONS = [
  { id: 'model-health', label: 'Model Health', icon: modelHealthIcon },
  { id: 'analysis-stats', label: 'Analysis Stats', icon: analysisStatsIcon },
  { id: 'user-stats', label: 'User Stats', icon: userStatsIcon },
  { id: 'user-management', label: 'User Management', icon: userManagementIcon },
  { id: 'website-analytics', label: 'Website Analytics', icon: websiteAnalyticsIcon },
];

export default function AdminSidebar({ 
  isOpen, 
  onToggle, 
  activeSection, 
  onSectionChange,
  onClose,
  onLogout,
}) {
  const getSectionHref = (sectionId) => `/admin?section=${encodeURIComponent(sectionId)}`;

  const handleSectionClick = (sectionId) => {
    onSectionChange(sectionId);
    
    // Auto-close on mobile
    if (window.innerWidth <= 768 && onClose) {
      onClose();
    }
  };

  const handleSectionLinkClick = (event, sectionId) => {
    const isPlainLeftClick =
      event.button === 0 &&
      !event.metaKey &&
      !event.ctrlKey &&
      !event.shiftKey &&
      !event.altKey;

    if (!isPlainLeftClick) {
      return;
    }

    event.preventDefault();
    handleSectionClick(sectionId);
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
                  <a
                    className={`admin-sidebar__button ${
                      activeSection === section.id ? 'admin-sidebar__button--active' : ''
                    }`}
                    href={getSectionHref(section.id)}
                    onClick={(event) => handleSectionLinkClick(event, section.id)}
                    aria-current={activeSection === section.id ? 'page' : undefined}
                  >
                    <span className="admin-sidebar__icon">
                      <img
                        src={section.icon}
                        alt={`${section.label} icon`}
                        className="admin-sidebar__icon-image"
                      />
                    </span>
                    <span className="admin-sidebar__label">{section.label}</span>
                  </a>
                </li>
              ))}
            </ul>

            <div className="admin-sidebar__footer">
              <button
                className="admin-sidebar__button admin-sidebar__button--logout"
                type="button"
                onClick={onLogout}
              >
                <span className="admin-sidebar__icon" aria-hidden="true">↩</span>
                <span className="admin-sidebar__label">Logout</span>
              </button>
            </div>
          </nav>
        )}

        {/* Collapsed Sidebar - Icon Buttons */}
        {!isOpen && (
          <>
            {ADMIN_SECTIONS.map((section) => (
              <a
                key={section.id}
                className={`admin-sidebar__iconbtn ${
                  activeSection === section.id ? 'admin-sidebar__iconbtn--active' : ''
                }`}
                aria-label={section.label}
                title={section.label}
                href={getSectionHref(section.id)}
                onClick={(event) => handleSectionLinkClick(event, section.id)}
                aria-current={activeSection === section.id ? 'page' : undefined}
              >
                <img
                  src={section.icon}
                  alt={`${section.label} icon`}
                  className="admin-sidebar__icon-image"
                />
              </a>
            ))}

            <button
              className="admin-sidebar__iconbtn admin-sidebar__iconbtn--logout"
              type="button"
              aria-label="Logout"
              title="Logout"
              onClick={onLogout}
            >
              ↩
            </button>
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
  onLogout: PropTypes.func.isRequired,
};
