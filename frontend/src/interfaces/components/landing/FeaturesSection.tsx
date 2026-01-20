import React from 'react';

/**
 * Features Section component
 * Displays statistical data about scams and fraud detection
 */
export const FeaturesSection: React.FC = () => {
  const statistics = [
    {
      value: "$8.8B",
      label: "Lost to Scams in 2023",
      description: "Total financial losses reported globally due to fraud and scam activities",
      trend: "+42%",
      trendLabel: "increase from 2022",
      icon: (
        <svg className="w-10 h-10" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      ),
      gradient: "from-red-500 to-orange-500"
    },
    {
      value: "156%",
      label: "Rise in AI-Generated Scams",
      description: "Increase in sophisticated fraud attempts using deepfakes and AI technology",
      trend: "2024",
      trendLabel: "year-over-year",
      icon: (
        <svg className="w-10 h-10" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
        </svg>
      ),
      gradient: "from-yellow-500 to-red-500"
    },
    {
      value: "73%",
      label: "Detection Success Rate",
      description: "Our AI successfully identifies and prevents fraud attempts in real-time",
      trend: "99.2%",
      trendLabel: "accuracy rate",
      icon: (
        <svg className="w-10 h-10" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
        </svg>
      ),
      gradient: "from-green-500 to-emerald-500"
    },
    {
      value: "2.3M",
      label: "Scam Attempts Blocked Daily",
      description: "Number of fraudulent activities prevented across all platforms globally",
      trend: "+89%",
      trendLabel: "vs last quarter",
      icon: (
        <svg className="w-10 h-10" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636" />
        </svg>
      ),
      gradient: "from-blue-500 to-indigo-500"
    },
    {
      value: "34%",
      label: "Increase in Platform Adoption",
      description: "Growth in businesses implementing AI fraud detection systems",
      trend: "Q4 2025",
      trendLabel: "latest quarter",
      icon: (
        <svg className="w-10 h-10" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
        </svg>
      ),
      gradient: "from-purple-500 to-pink-500"
    },
    {
      value: "<2s",
      label: "Average Detection Time",
      description: "Time taken to analyze and flag suspicious activities using AI algorithms",
      trend: "Real-time",
      trendLabel: "processing",
      icon: (
        <svg className="w-10 h-10" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      ),
      gradient: "from-cyan-500 to-blue-500"
    }
  ];

  return (
    <section id="features" className="py-20 bg-slate-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <div className="text-center mb-16">
          <h3 className="text-4xl md:text-5xl font-bold text-white mb-4">
            The Growing Threat of Fraud
          </h3>
          <p className="text-xl text-slate-300 max-w-3xl mx-auto">
            Real-time data showing the rise of scams and the critical need for AI-powered fraud detection
          </p>
        </div>

        {/* Statistics Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {statistics.map((stat, index) => (
            <div
              key={index}
              className="group relative bg-slate-700 p-8 rounded-2xl shadow-lg hover:shadow-2xl transition-all duration-300 border border-slate-600"
            >
              {/* Gradient accent */}
              <div className={`absolute top-0 left-0 right-0 h-1 bg-linear-to-r ${stat.gradient} rounded-t-2xl`}></div>
              
              {/* Icon */}
              <div className={`inline-flex p-3 rounded-xl bg-linear-to-br ${stat.gradient} text-white mb-5 group-hover:scale-110 transition-transform duration-300`}>
                {stat.icon}
              </div>
              
              {/* Main Value */}
              <div className="mb-4">
                <div className="text-5xl font-bold text-white mb-2">
                  {stat.value}
                </div>
                <div className="text-lg font-semibold text-slate-200 mb-3">
                  {stat.label}
                </div>
                <p className="text-sm text-slate-400 leading-relaxed mb-4">
                  {stat.description}
                </p>
              </div>

              {/* Trend Badge */}
              <div className="flex items-center gap-2 text-sm">
                <span className={`inline-flex items-center px-3 py-1 rounded-full bg-linear-to-r ${stat.gradient} text-white font-semibold`}>
                  {stat.trend}
                </span>
                <span className="text-slate-400">
                  {stat.trendLabel}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};
