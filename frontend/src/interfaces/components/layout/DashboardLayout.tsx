import React, { useState } from 'react';
import { Link, Outlet, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../../hooks/useAuth';
import { Button } from '../../../components/ui/button';
import {
  Home,
  User,
  Settings,
  LogOut,
  Menu,
  X,
  Bell,
  ChevronDown,
  Shield
} from 'lucide-react';

export const DashboardLayout: React.FC = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [userMenuOpen, setUserMenuOpen] = useState(false);

  const handleLogout = async () => {
    await logout();
    navigate('/');
  };

  const navItems = [
    { path: '/dashboard', icon: Home, label: 'Model Health' },
    { path: '/dashboard/users', icon: User, label: 'Users' },
    { path: '/dashboard/statistics', icon: Settings, label: 'Statistics' },
    { path: '/dashboard/blockchain', icon: Shield, label: 'Blockchain' },
  ];

  const isActive = (path: string) => {
    if (path === '/dashboard') {
      return location.pathname === path;
    }
    return location.pathname.startsWith(path);
  };

  return (
    <div className="min-h-screen bg-slate-900">
      {/* Top Navigation Bar */}
      <header className="bg-slate-800 border-b border-slate-700 fixed top-0 left-0 right-0 z-30">
        <div className="flex items-center justify-between px-4 py-3">
          {/* Mobile menu button */}
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="lg:hidden p-2 rounded-md hover:bg-slate-700 text-white"
          >
            {sidebarOpen ? <X size={24} /> : <Menu size={24} />}
          </button>

          {/* Logo */}
          <Link to="/dashboard" className="flex items-center space-x-2">
            <span className="text-xl font-bold text-white hidden sm:block">VerifAI Admin</span>
          </Link>

          {/* Right side - notifications and user menu */}
          <div className="flex items-center space-x-4">
            {/* Notifications */}
            <button className="p-2 rounded-md hover:bg-slate-700 relative text-white">
              <Bell size={20} />
              <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full"></span>
            </button>

            {/* User menu */}
            <div className="relative">
              <button
                onClick={() => setUserMenuOpen(!userMenuOpen)}
                className="flex items-center space-x-3 p-2 rounded-md hover:bg-slate-700 text-white"
              >
                <div className="w-8 h-8 rounded-full bg-indigo-600 flex items-center justify-center text-white font-semibold">
                  {user?.email.charAt(0).toUpperCase()}
                </div>
                <span className="hidden md:block text-sm font-medium text-white">
                  {user?.email}
                </span>
                <ChevronDown size={16} />
              </button>

              {/* User dropdown menu */}
              {userMenuOpen && (
                <>
                  <div
                    className="fixed inset-0 z-30"
                    onClick={() => setUserMenuOpen(false)}
                  ></div>
                  <div className="absolute right-0 mt-2 w-48 bg-slate-700 rounded-md shadow-lg py-1 z-40 border border-slate-600">
                    <div className="px-4 py-2 border-b border-slate-600">
                      <p className="text-sm font-medium text-white truncate">{user?.email}</p>
                      <p className="text-xs text-slate-300">
                        {user?.roles.join(', ') || 'User'}
                      </p>
                    </div>
                    <Link
                      to="/dashboard/users"
                      className="block px-4 py-2 text-sm text-white hover:bg-slate-600"
                      onClick={() => setUserMenuOpen(false)}
                    >
                      <User size={16} className="inline mr-2" />
                      Your Profile
                    </Link>
                    <Link
                      to="/dashboard/statistics"
                      className="block px-4 py-2 text-sm text-white hover:bg-slate-600"
                      onClick={() => setUserMenuOpen(false)}
                    >
                      <Settings size={16} className="inline mr-2" />
                      Settings
                    </Link>
                    <button
                      onClick={handleLogout}
                      className="block w-full text-left px-4 py-2 text-sm text-red-400 hover:bg-slate-600"
                    >
                      <LogOut size={16} className="inline mr-2" />
                      Sign out
                    </button>
                  </div>
                </>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Sidebar */}
      <aside
        className={`
          fixed top-16 left-0 bottom-0 w-64 bg-slate-800 border-r border-slate-700 z-20
          transform transition-transform duration-300 ease-in-out
          ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}
          lg:translate-x-0
        `}
      >
        <nav className="p-4 space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const active = isActive(item.path);
            
            return (
              <Link
                key={item.path}
                to={item.path}
                onClick={() => setSidebarOpen(false)}
                className={`
                  flex items-center space-x-3 px-4 py-3 rounded-lg transition-colors
                  ${active
                    ? 'bg-slate-700 text-white font-medium'
                    : 'text-slate-300 hover:bg-slate-700 hover:text-white'
                  }
                `}
              >
                <Icon size={20} />
                <span>{item.label}</span>
              </Link>
            );
          })}
        </nav>

        {/* Sidebar footer */}
        <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-slate-700">
          <div className="bg-slate-700 rounded-lg p-3">
            <p className="text-sm font-medium text-white mb-1">Need Help?</p>
            <p className="text-xs text-slate-300 mb-2">
              Check our documentation or contact support
            </p>
            <Button size="sm" variant="outline" className="w-full text-slate-300 border-slate-600 hover:bg-slate-600">
              View Docs
            </Button>
          </div>
        </div>
      </aside>

      {/* Mobile sidebar overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 z-10 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        ></div>
      )}

      {/* Main content */}
      <main className="pt-16 lg:pl-64 min-h-screen">
        <div className="p-6">
          <Outlet />
        </div>
      </main>
    </div>
  );
};
