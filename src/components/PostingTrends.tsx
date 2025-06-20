import React, { useState } from 'react';
import { TrendingUp, MessageSquare, Heart, Users, BarChart3, X } from 'lucide-react';

interface MetricData {
  id: string;
  title: string;
  value: string;
  change: string;
  changeType: 'positive' | 'negative' | 'neutral';
  icon: React.ComponentType<any>;
  color: string;
  chartData: number[];
}

const PostingTrends: React.FC = () => {
  const [selectedMetric, setSelectedMetric] = useState<string | null>(null);

  // Mock data - replace with real data from your API
  const metrics: MetricData[] = [
    {
      id: 'posts',
      title: 'Posts Today',
      value: '12',
      change: '+3 from yesterday',
      changeType: 'positive',
      icon: MessageSquare,
      color: 'blue',
      chartData: [8, 6, 10, 12, 9, 15, 12] // Last 7 days
    },
    {
      id: 'engagement',
      title: 'Total Likes',
      value: '234',
      change: '+18% this week',
      changeType: 'positive',
      icon: Heart,
      color: 'red',
      chartData: [180, 195, 210, 225, 200, 220, 234]
    },
    {
      id: 'replies',
      title: 'Replies',
      value: '18',
      change: '+2 from yesterday',
      changeType: 'positive',
      icon: Users,
      color: 'green',
      chartData: [12, 14, 16, 15, 20, 16, 18]
    },
    {
      id: 'growth',
      title: 'Growth Rate',
      value: '+15%',
      change: 'vs last week',
      changeType: 'positive',
      icon: TrendingUp,
      color: 'purple',
      chartData: [5, 8, 12, 10, 15, 13, 15]
    }
  ];

  const getColorClasses = (color: string, variant: 'bg' | 'text' | 'border') => {
    const colorMap = {
      blue: { bg: 'bg-blue-50', text: 'text-blue-600', border: 'border-blue-200' },
      red: { bg: 'bg-red-50', text: 'text-red-600', border: 'border-red-200' },
      green: { bg: 'bg-green-50', text: 'text-green-600', border: 'border-green-200' },
      purple: { bg: 'bg-purple-50', text: 'text-purple-600', border: 'border-purple-200' }
    };
    return colorMap[color as keyof typeof colorMap][variant];
  };

  const openChart = (metricId: string) => {
    setSelectedMetric(metricId);
  };

  const closeChart = () => {
    setSelectedMetric(null);
  };

  const selectedMetricData = metrics.find(m => m.id === selectedMetric);

  return (
    <>
      <div className="h-full">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-semibold text-gray-900">Posting Trends</h3>
          <TrendingUp className="h-5 w-5 text-gray-400" />
        </div>

        {/* 2x2 Grid of Metric Squares */}
        <div className="grid grid-cols-2 gap-4 h-[calc(100%-4rem)]">
          {metrics.map((metric) => {
            const Icon = metric.icon;
            return (
              <div
                key={metric.id}
                onClick={() => openChart(metric.id)}
                className={`${getColorClasses(metric.color, 'bg')} ${getColorClasses(metric.color, 'border')} border-2 rounded-lg p-4 cursor-pointer hover:shadow-md transition-all duration-200 hover:scale-105 flex flex-col justify-between`}
              >
                <div className="flex items-center justify-between mb-2">
                  <Icon className={`h-5 w-5 ${getColorClasses(metric.color, 'text')}`} />
                  <BarChart3 className="h-4 w-4 text-gray-400" />
                </div>
                
                <div>
                  <p className="text-2xl font-bold text-gray-900 mb-1">{metric.value}</p>
                  <p className="text-sm font-medium text-gray-700 mb-1">{metric.title}</p>
                  <p className={`text-xs ${
                    metric.changeType === 'positive' ? 'text-green-600' : 
                    metric.changeType === 'negative' ? 'text-red-600' : 
                    'text-gray-600'
                  }`}>
                    {metric.change}
                  </p>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Chart Modal */}
      {selectedMetric && selectedMetricData && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl max-w-2xl w-full max-h-[80vh] overflow-y-auto">
            <div className="p-6 border-b border-gray-200">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <selectedMetricData.icon className={`h-6 w-6 ${getColorClasses(selectedMetricData.color, 'text')}`} />
                  <h3 className="text-xl font-semibold text-gray-900">
                    {selectedMetricData.title} - 7 Day Trend
                  </h3>
                </div>
                <button 
                  onClick={closeChart}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>
            </div>

            <div className="p-6">
              {/* Simple Chart Visualization */}
              <div className="mb-6">
                <div className="flex items-end justify-between h-48 bg-gray-50 rounded-lg p-4">
                  {selectedMetricData.chartData.map((value, index) => {
                    const height = (value / Math.max(...selectedMetricData.chartData)) * 100;
                    return (
                      <div key={index} className="flex flex-col items-center">
                        <div 
                          className={`w-8 ${getColorClasses(selectedMetricData.color, 'text').replace('text-', 'bg-')} rounded-t transition-all duration-500`}
                          style={{ height: `${height}%`, minHeight: '4px' }}
                        ></div>
                        <span className="text-xs text-gray-500 mt-2">
                          {index === 6 ? 'Today' : `${7-index}d ago`}
                        </span>
                        <span className="text-xs font-medium text-gray-700">
                          {value}
                        </span>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Stats Summary */}
              <div className="grid grid-cols-3 gap-4">
                <div className="text-center p-4 bg-gray-50 rounded-lg">
                  <p className="text-2xl font-bold text-gray-900">
                    {selectedMetricData.chartData[selectedMetricData.chartData.length - 1]}
                  </p>
                  <p className="text-sm text-gray-600">Current</p>
                </div>
                <div className="text-center p-4 bg-gray-50 rounded-lg">
                  <p className="text-2xl font-bold text-gray-900">
                    {Math.round(selectedMetricData.chartData.reduce((a, b) => a + b, 0) / selectedMetricData.chartData.length)}
                  </p>
                  <p className="text-sm text-gray-600">7-Day Avg</p>
                </div>
                <div className="text-center p-4 bg-gray-50 rounded-lg">
                  <p className="text-2xl font-bold text-gray-900">
                    {Math.max(...selectedMetricData.chartData)}
                  </p>
                  <p className="text-sm text-gray-600">Peak</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default PostingTrends;