import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../../hooks/useAuth';
import { Button } from '../../../components/ui/button';

/**
 * Header/Navigation component
 * Main navigation bar for the application
 */
export const Header: React.FC = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const handleLogout = async () => {
    await logout();
    navigate('/');
  };

  return (
    <header className="fixed top-0 left-0 right-0 z-50 bg-slate-900/95 backdrop-blur-md border-b border-slate-800">
      <nav className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <Link to="/" className="flex items-center space-x-2">
            <span className="text-2xl font-bold text-white">VerifAI</span>
          </Link>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center space-x-8">
            <a href="#about" className="text-gray-400 hover:text-white transition-colors">
              About us
            </a>
            <a href="#detection" className="text-gray-400 hover:text-white transition-colors">
              Detection
            </a>
            <a href="#chatbot" className="text-gray-400 hover:text-white transition-colors">
              AI Chatbot
            </a>
            <a href="#membership" className="text-gray-400 hover:text-white transition-colors">
              Membership
            </a>
            
            {user ? (
              <div className="flex items-center space-x-4">
                <Link to="/dashboard">
                  <Button variant="outline" size="sm" className="border-gray-600 text-gray-300 hover:text-white hover:border-white">
                    Dashboard
                  </Button>
                </Link>
                <Button onClick={handleLogout} variant="ghost" size="sm" className="text-gray-300 hover:text-white">
                  Logout
                </Button>
              </div>
            ) : (
              <div className="flex items-center space-x-4">
                <Link to="/login">
                  <Button variant="ghost" size="sm" className="text-gray-400 hover:text-white">
                    Login/Signup
                  </Button>
                </Link>
              </div>
            )}
          </div>

          {/* Mobile menu button */}
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="md:hidden p-2 rounded-lg text-gray-300 hover:bg-slate-800"
          >
            {mobileMenuOpen ? (
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            ) : (
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            )}
          </button>
        </div>

        {/* Mobile Navigation */}
        {mobileMenuOpen && (
          <div className="md:hidden py-4 border-t border-slate-800">
            <div className="flex flex-col space-y-4">
              <a
                href="#about"
                className="text-gray-400 hover:text-white transition-colors"
                onClick={() => setMobileMenuOpen(false)}
              >
                About us
              </a>
              <a
                href="#detection"
                className="text-gray-400 hover:text-white transition-colors"
                onClick={() => setMobileMenuOpen(false)}
              >
                Detection
              </a>
              <a
                href="#chatbot"
                className="text-gray-400 hover:text-white transition-colors"
                onClick={() => setMobileMenuOpen(false)}
              >
                AI Chatbot
              </a>
              <a
                href="#membership"
                className="text-gray-400 hover:text-white transition-colors"
                onClick={() => setMobileMenuOpen(false)}
              >
                Membership
              </a>
              
              {user ? (
                <>
                  <Link to="/dashboard" onClick={() => setMobileMenuOpen(false)}>
                    <Button variant="outline" className="w-full border-gray-600 text-gray-300 hover:text-white hover:border-white">
                      Dashboard
                    </Button>
                  </Link>
                  <Button onClick={() => { handleLogout(); setMobileMenuOpen(false); }} variant="ghost" className="w-full text-gray-300 hover:text-white">
                    Logout
                  </Button>
                </>
              ) : (
                <>
                  <Link to="/login" onClick={() => setMobileMenuOpen(false)}>
                    <Button variant="outline" className="w-full border-gray-600 text-gray-300 hover:text-white hover:border-white">
                      Login/Signup
                    </Button>
                  </Link>
                </>
              )}
            </div>
          </div>
        )}
      </nav>
    </header>
  );
};
