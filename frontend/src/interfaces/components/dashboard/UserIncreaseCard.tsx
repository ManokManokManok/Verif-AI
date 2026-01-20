import React from 'react';

interface UserIncreaseCardProps {
  title?: string;
  totalValue?: string;
  timeRange?: string;
  barData?: Array<{
    label: string;
    value: string;
    change: string;
    color: string;
  }>;
}

export const UserIncreaseCard: React.FC<UserIncreaseCardProps> = ({
  title = "User Increase",
  totalValue = "12,3K",
  timeRange = "Last 7 Days",
  barData = [
    { label: "Members", value: "8,2K", change: "+12.3%", color: "bg-purple-500" },
    { label: "Frequent Visitors", value: "2,8K", change: "+8.1%", color: "bg-blue-400" },
    { label: "New Users", value: "1,3K", change: "+15.7%", color: "bg-green-400" }
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
      
      {/* Main value */}
      <div className="mb-6">
        <span className="text-4xl font-bold text-gray-900">{totalValue}</span>
      </div>
      
      {/* Vertical Bar Chart */}
      <div className="mb-6">
        <div className="flex items-end justify-between h-32 px-2">
          {barData.map((item, index) => (
            <div key={index} className="flex flex-col items-center flex-1">
              {/* Bar */}
              <div className="w-full max-w-16">
                <div className={`h-24 ${item.color} rounded-t-lg`}></div>
              </div>
              
              {/* Label */}
              <p className="text-xs text-gray-600 mt-2 text-center">{item.label}</p>
            </div>
          ))}
        </div>
      </div>
      
      {/* Legend */}
      <div className="space-y-2">
        {barData.map((item, index) => (
          <div key={index} className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className={`w-3 h-3 rounded-full ${item.color}`}></div>
              <span className="text-sm text-gray-700">{item.label}</span>
            </div>
            <div className="flex items-baseline space-x-2">
              <span className="text-sm font-semibold text-gray-900">{item.value}</span>
              <span className={`text-xs font-medium ${
                item.change.startsWith('+') ? 'text-green-600' : 'text-red-600'
              }`}>
                {item.change}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
