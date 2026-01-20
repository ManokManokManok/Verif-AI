import React from 'react';

interface UserReportsCardProps {
  title?: string;
  totalValue?: string;
  percentageChange?: string;
  timeRange?: string;
  metrics?: Array<{
    label: string;
    value: string;
    change: string;
    color: string;
  }>;
}

export const UserReportsCard: React.FC<UserReportsCardProps> = ({
  title = "User Reports",
  totalValue = "6,4K",
  percentageChange = "+3.4%",
  timeRange = "Last 7 Days",
  metrics = [
    { label: "Correct Classification", value: "4,2K", change: "+5.2%", color: "bg-green-500" },
    { label: "Incorrect Classification", value: "1,1K", change: "-2.1%", color: "bg-red-500" },
    { label: "User Refunds", value: "892", change: "+1.8%", color: "bg-orange-500" },
    { label: "New Members", value: "238", change: "+12.4%", color: "bg-blue-500" }
  ]
}) => {
  return (
    <div className="bg-gray-50 rounded-xl shadow-sm p-6 border border-gray-200">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
        
        {/* Dropdown */}
        <div className="relative">
          <button className="flex items-center space-x-2 text-sm text-gray-600 hover:text-gray-900 px-3 py-1.5 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors">
            <span>{timeRange}</span>
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>
        </div>
      </div>
      
      {/* Main value and change */}
      <div className="flex items-baseline mb-6">
        <span className="text-4xl font-bold text-gray-900">{totalValue}</span>
        <span className="ml-3 text-lg text-green-600 font-medium">{percentageChange}</span>
      </div>
      
      {/* Horizontal Bar Chart */}
      <div className="mb-6">
        <div className="flex h-8 rounded-lg overflow-hidden">
          <div className="bg-purple-500 w-3/8"></div>
          <div className="bg-blue-400 w-2/8"></div>
          <div className="bg-green-400 w-2/8"></div>
          <div className="bg-yellow-400 w-1/8"></div>
        </div>
      </div>
      
      {/* Metrics Grid */}
      <div className="grid grid-cols-2 gap-4">
        {metrics.map((metric, index) => (
          <div key={index} className="flex items-start space-x-3">
            <div className={`w-2 h-2 rounded-full ${metric.color} mt-1.5 flex-shrink-0`}></div>
            <div className="flex-1">
              <p className="text-xs text-gray-500 uppercase tracking-wide mb-1">{metric.label}</p>
              <div className="flex items-baseline space-x-2">
                <span className="text-sm font-semibold text-gray-900">{metric.value}</span>
                <span className={`text-xs font-medium ${
                  metric.change.startsWith('+') ? 'text-green-600' : 'text-red-600'
                }`}>
                  {metric.change}
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
