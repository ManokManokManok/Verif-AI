import React from 'react';
import { HealthCard } from './HealthCard';
import { AnalyticsCard } from './AnalyticsCard';

export const DashboardHomePage: React.FC = () => {
  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">VerifAI Admin</h1>
        <p className="text-gray-600">Monitor your system health and analytics</p>
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
