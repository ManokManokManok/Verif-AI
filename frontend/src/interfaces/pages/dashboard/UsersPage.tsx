import React from 'react';
import { UserIncreaseCard } from '../../components/dashboard/UserIncreaseCard';
import { UserReportsCard } from '../../components/dashboard/UserReportsCard';

export const UsersPage: React.FC = () => {
  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">Users</h1>
        <p className="text-slate-300">Manage and monitor user accounts</p>
      </div>
      
      {/* Dashboard Cards Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* User Increase Card */}
        <div className="lg:col-span-1">
          <UserIncreaseCard />
        </div>
        
        {/* User Reports Card */}
        <div className="lg:col-span-1">
          <UserReportsCard />
        </div>
      </div>
    </div>
  );
};
