import React from 'react';

interface CorrectlyClassifiedFraudScamCardProps {
  title?: string;
  totalValue?: string;
  chartData?: Array<{
    date: string;
    value: number;
    percentage: string;
  }>;
  yLabels?: string[];
}

export const CorrectlyClassifiedFraudScamCard: React.FC<CorrectlyClassifiedFraudScamCardProps> = ({
  title = "Correctly Classified Fraud/Scam",
  totalValue = "128,7K",
  chartData = [
    { date: "29 July", value: 220342.76, percentage: "+3.4%" },
    { date: "28 July", value: 185234.12, percentage: "+2.1%" },
    { date: "27 July", value: 198456.89, percentage: "+1.8%" },
    { date: "26 July", value: 176234.45, percentage: "+0.9%" },
    { date: "25 July", value: 165123.78, percentage: "-0.5%" }
  ],
  yLabels = ["$100", "$200", "$500", "$1000"]
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
      
      {/* Main value */}
      <div className="mb-6">
        <span className="text-4xl font-bold text-gray-900">{totalValue}</span>
      </div>
      
      {/* Line Chart */}
      <div className="relative h-48 mb-4">
        {/* Y-axis labels */}
        <div className="absolute left-0 top-0 bottom-0 w-12 flex flex-col justify-between text-xs text-gray-500">
          {yLabels.map((label, index) => (
            <span key={index}>{label}</span>
          ))}
        </div>
        
        {/* Chart area */}
        <div className="ml-12 h-full relative">
          {/* Grid lines */}
          <div className="absolute inset-0 flex flex-col justify-between">
            {[...Array(4)].map((_, index) => (
              <div key={index} className="border-b border-gray-200"></div>
            ))}
          </div>
          
          {/* Line */}
          <svg className="absolute inset-0 w-full h-full" viewBox="0 0 100 100" preserveAspectRatio="none">
            <defs>
              <linearGradient id="purpleGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                <stop offset="0%" stopColor="#8b5cf6" stopOpacity="0.3" />
                <stop offset="100%" stopColor="#8b5cf6" stopOpacity="0.1" />
              </linearGradient>
            </defs>
            <path
              d="M 0,80 L 20,60 L 40,45 L 60,30 L 80,20 L 100,10"
              fill="url(#purpleGradient)"
              stroke="#8b5cf6"
              strokeWidth="2"
            />
          </svg>
          
          {/* Tooltip */}
          <div className="absolute top-4 right-4 bg-gray-900 text-white p-2 rounded-lg text-xs">
            <div className="font-semibold">29 July 00:00</div>
            <div className="text-purple-300">220,342.76</div>
            <div className="text-green-400">+3.4%</div>
          </div>
        </div>
      </div>
    </div>
  );
};
