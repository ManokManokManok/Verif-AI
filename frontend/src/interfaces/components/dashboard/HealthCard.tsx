import React from 'react';

interface HealthCardProps {
  score?: number;
  subtitle?: string;
  lastCheck?: string;
}

export const HealthCard: React.FC<HealthCardProps> = ({
  score = 660,
  subtitle = "Your Credit Score is average",
  lastCheck = "Last Check on 21 Apr"
}) => {
  return (
    <div className="bg-gray-50 rounded-xl shadow-sm p-6 border border-gray-200">
      <h3 className="text-lg font-semibold text-gray-900 mb-6">Health</h3>
      
      {/* Circular Progress Indicator */}
      <div className="flex justify-center mb-6">
        <div className="relative w-32 h-32">
          <svg className="w-32 h-32 transform -rotate-90" viewBox="0 0 120 120">
            {/* Background circle */}
            <circle
              cx="60"
              cy="60"
              r="50"
              fill="none"
              stroke="#f3f4f6"
              strokeWidth="12"
            />
            
            {/* Progress segments */}
            <circle
              cx="60"
              cy="60"
              r="50"
              fill="none"
              stroke="#8b5cf6"
              strokeWidth="12"
              strokeDasharray="31.4 157"
              strokeLinecap="round"
            />
            <circle
              cx="60"
              cy="60"
              r="50"
              fill="none"
              stroke="#ec4899"
              strokeWidth="12"
              strokeDasharray="31.4 157"
              strokeDashoffset="-31.4"
              strokeLinecap="round"
            />
            <circle
              cx="60"
              cy="60"
              r="50"
              fill="none"
              stroke="#3b82f6"
              strokeWidth="12"
              strokeDasharray="31.4 157"
              strokeDashoffset="-62.8"
              strokeLinecap="round"
            />
            <circle
              cx="60"
              cy="60"
              r="50"
              fill="none"
              stroke="#eab308"
              strokeWidth="12"
              strokeDasharray="31.4 157"
              strokeDashoffset="-94.2"
              strokeLinecap="round"
            />
            
            {/* Indicator dot */}
            <circle
              cx="60"
              cy="10"
              r="4"
              fill="#3b82f6"
            />
          </svg>
          
          {/* Center text */}
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <span className="text-3xl font-bold text-gray-900">{score}</span>
          </div>
        </div>
      </div>
      
      {/* Health information */}
      <div className="text-center mb-4">
        <p className="text-sm text-gray-600 mb-1">{subtitle}</p>
        <p className="text-xs text-gray-500">{lastCheck}</p>
      </div>
      
      {/* Action button */}
      <button className="w-full bg-gray-50 hover:bg-gray-100 text-gray-700 text-sm font-medium py-2 px-4 rounded-lg transition-colors">
        What these stats mean?
      </button>
    </div>
  );
};
