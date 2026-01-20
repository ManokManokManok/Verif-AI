import React from 'react';
import { CorrectlyClassifiedFraudScamCard } from '../../components/dashboard/CorrectlyClassifiedFraudScamCard';
import { TodaysResultsCard } from '../../components/dashboard/TodaysResultsCard';

export const StatisticsPage: React.FC = () => {
  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">Statistics</h1>
        <p className="text-slate-300">View detailed analytics and system statistics</p>
      </div>
      
      {/* Dashboard Cards Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Correctly Classified Fraud/Scam Card */}
        <div className="lg:col-span-1">
          <CorrectlyClassifiedFraudScamCard />
        </div>
        
        {/* Todays Results Card */}
        <div className="lg:col-span-1">
          <TodaysResultsCard />
        </div>
      </div>
    </div>
  );
};
