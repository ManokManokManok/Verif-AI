import React from 'react';

interface TodaysResultsCardProps {
  title?: string;
  score?: number;
  subtitle?: string;
  lastCheck?: string;
  status?: string;
  segments?: Array<{
    value: number;
    color: string;
  }>;
}

export const TodaysResultsCard: React.FC<TodaysResultsCardProps> = ({
  title = "Todays Results",
  score = 660,
  subtitle = "660 Scams Identified",
  lastCheck = "Last Check on 21 Apr",
  status = "High amount of entries for 21 Apr",
  segments = [
    { value: 30, color: "bg-red-500" },
    { value: 45, color: "bg-orange-500" },
    { value: 25, color: "bg-green-500" }
  ]
}) => {
  return (
    <div className="bg-gray-50 rounded-xl shadow-sm p-6 border border-gray-200">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
        
        {/* Menu Icon */}
        <button className="p-2 rounded-md hover:bg-gray-100">
          <svg className="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        </button>
      </div>
      
      {/* Semi-circular Gauge */}
      <div className="flex justify-center mb-6">
        <div className="relative w-40 h-32">
          <svg className="w-full h-full" viewBox="0 0 160 120">
            {/* Background arc */}
            <path
              d="M 20,100 A 60,60 0 0,1 140,100"
              fill="none"
              stroke="#e5e7eb"
              strokeWidth="12"
              strokeLinecap="round"
            />
            
            {/* Colored segments */}
            {segments.map((segment, index) => {
              const startAngle = segments.slice(0, index).reduce((sum, s) => sum + s.value, 0);
              const endAngle = startAngle + segment.value;
              const x1 = 80 + 60 * Math.cos((startAngle - 90) * Math.PI / 180);
              const y1 = 100 + 60 * Math.sin((startAngle - 90) * Math.PI / 180);
              const x2 = 80 + 60 * Math.cos((endAngle - 90) * Math.PI / 180);
              const y2 = 100 + 60 * Math.sin((endAngle - 90) * Math.PI / 180);
              
              return (
                <path
                  key={index}
                  d={`M ${x1},${y1} A 60,60 0 0,1 ${x2},${y2}`}
                  fill="none"
                  stroke={segment.color.replace('bg-', '#').replace('500', '600')}
                  strokeWidth="12"
                  strokeLinecap="round"
                />
              );
            })}
          </svg>
          
          {/* Center text */}
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <span className="text-3xl font-bold text-gray-900">{score}</span>
            <span className="text-sm text-gray-600">{subtitle}</span>
          </div>
        </div>
      </div>
      
      {/* Info text */}
      <div className="text-center mb-4">
        <p className="text-sm text-gray-600">{lastCheck}</p>
      </div>
      
      {/* Status tag */}
      <div className="flex justify-center">
        <span className="inline-flex items-center px-3 py-1.5 rounded-full text-xs font-medium bg-gray-200 text-gray-700">
          {status}
        </span>
      </div>
    </div>
  );
};
