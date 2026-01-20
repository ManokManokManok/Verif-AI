import React from 'react';
import { ChevronDown } from 'lucide-react';

interface Metric {
  label: string;
  value: string;
  change: string;
  color: string;
}

interface AnalyticsCardProps {
  title?: string;
  totalValue?: string;
  percentageChange?: string;
  timeRange?: string;
  metrics?: Metric[];
}

export const AnalyticsCard: React.FC<AnalyticsCardProps> = ({
  title = "Todays Analyzed results",
  totalValue = "6,4K",
  percentageChange = "+3.4%",
  timeRange = "Last 7 Days",
  metrics = [
    {
      label: "ASSET RECEIVED",
      value: "1,1K",
      change: "+3.4%",
      color: "bg-purple-500"
    },
    {
      label: "SPENDING",
      value: "2,3K",
      change: "+11.4%",
      color: "bg-blue-400"
    },
    {
      label: "INVESTING",
      value: "1,5K",
      change: "-1.4%",
      color: "bg-orange-500"
    },
    {
      label: "ALLOCATION",
      value: "1,6K",
      change: "+7.0%",
      color: "bg-blue-600"
    }
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
            <ChevronDown size={16} />
          </button>
        </div>
      </div>
      
      {/* Main value and change */}
      <div className="flex items-baseline mb-6">
        <span className="text-4xl font-bold text-gray-900">{totalValue}</span>
        <span className="ml-3 text-lg text-green-600 font-medium">{percentageChange}</span>
      </div>
      
      {/* Bar chart */}
      <div className="mb-6">
        <div className="flex h-8 rounded-lg overflow-hidden">
          <div className="bg-purple-500 w-2/5"></div>
          <div className="bg-blue-400 w-2/5"></div>
          <div className="bg-yellow-400 w-1/5"></div>
        </div>
      </div>
      
      {/* Metrics grid */}
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
