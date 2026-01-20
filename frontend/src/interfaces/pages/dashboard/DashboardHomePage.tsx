import React, { useEffect, useState } from 'react';
import { useAuth } from '../../../hooks/useAuth';
import { HealthCard } from '../../components/dashboard/HealthCard';
import { AnalyticsCard } from '../../components/dashboard/AnalyticsCard';


export const DashboardHomePage: React.FC = () => {
  const { user } = useAuth();
  const [stats, setStats] = useState({
    totalLogins: 0,
    lastLogin: '',
    accountAge: 0,
    verificationStatus: false
  });

  useEffect(() => {
    // Calculate account statistics
    if (user) {
      const createdAt = new Date(user.createdAt);
      const now = new Date();
      const daysSinceCreation = Math.floor((now.getTime() - createdAt.getTime()) / (1000 * 60 * 60 * 24));
      
      setStats({
        totalLogins: Math.floor(Math.random() * 50) + 10, // Mock data
        lastLogin: user.lastLogin 
          ? new Date(user.lastLogin).toLocaleDateString('en-US', {
              year: 'numeric',
              month: 'long',
              day: 'numeric',
              hour: '2-digit',
              minute: '2-digit'
            })
          : 'First login',
        accountAge: daysSinceCreation,
        verificationStatus: user.isVerified
      });
    }
  }, [user]);

  if (!user) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Page Header - Updated to match landing page theme */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">VerifAI Admin</h1>
        <p className="text-slate-300">Monitor your system health and analytics</p>
      </div>
      
      {/* User Welcome Section */}
      <div className="bg-gray-50 rounded-xl shadow-sm p-6 border border-gray-200">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-semibold text-gray-900 mb-1">
              Welcome back, {user.email.split('@')[0]}! 👋
            </h2>
            <p className="text-gray-600">Here's what's happening with your account today.</p>
          </div>
          <div className="text-right">
            <div className="text-sm text-gray-500">Account Status</div>
            <div className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
              stats.verificationStatus 
                ? 'bg-green-100 text-green-800' 
                : 'bg-yellow-100 text-yellow-800'
            }`}>
              {stats.verificationStatus ? 'Verified' : 'Unverified'}
            </div>
          </div>
        </div>
        
        {/* User Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6">
          <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
            <div className="text-sm text-gray-500">Total Logins</div>
            <div className="text-2xl font-bold text-gray-900">{stats.totalLogins}</div>
          </div>
          <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
            <div className="text-sm text-gray-500">Account Age</div>
            <div className="text-2xl font-bold text-gray-900">{stats.accountAge} days</div>
          </div>
          <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
            <div className="text-sm text-gray-500">Last Login</div>
            <div className="text-sm font-medium text-gray-900 truncate">{stats.lastLogin}</div>
          </div>
        </div>
      </div>
      
      {/* Dashboard Cards Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Health Card */}
        <div className="lg:col-span-1">
          <HealthCard />
        </div>
        
        {/* Analytics Card */}
        <div className="lg:col-span-1">
          <AnalyticsCard />
        </div>
      </div>
    </div>
  );
};
