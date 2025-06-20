import React, { useState, useEffect } from 'react';
import { TrendingUp, MessageSquare, Heart, Users, BarChart3, X, Rocket } from 'lucide-react';
import { useApi } from '../hooks/useApi';

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

interface TwitterMetricsResponse {
  posts: {
    today: number;
    change: string;
    chartData: number[];
  };
  likes: {
    total: number;
    change: string;
    chartData: number[];
  };
  replies: {
    total: number;
    change: string;
    chartData: number[];
  };
  growth: {
    rate: number;
    change: string;
    chartData: number[];
  };
  success: boolean;
  mock?: boolean;
}

const PostingTrends: React.FC = () => {
  const [selectedMetric, setSelectedMetric] = useState<string | null>(null);
  const [metrics, setMetrics] = useState<MetricData[]>([]);

  // Fetch live Twitter data
  const { data: twitterData, loading, error } = useApi<TwitterMetricsResponse>('/api/twitter-metrics', { 
    autoRefresh: true 
  });

  // Update metrics when Twitter data changes
  useEffect(() => {
    if (twitterData && twitterData.success) {
      const newMetrics: MetricData[] = [
        {
          id: 'posts',
          title: 'Posts Today',
          value: twitterData.posts.today.toString(),
          change: twitterData.posts.change,
          changeType: twitterData.posts.change.includes('+') ? 'positive' : 
                     twitterData.posts.change.includes('-') ? 'negative' : 'neutral',
          icon: MessageSquare,
          color: 'blue',
          chartData: twitterData.posts.chartData
        },
        {
          id: 'engagement',
          title: 'Total Likes',
          value: twitterData.likes.total.toString(),
          change: twitterData.likes.change,
          changeType: twitterData.likes.change.includes('+') ? 'positive' : 
                     twitterData.likes.change.includes('-') ? 'negative' : 'neutral',
          icon: Heart,
          color: 'red',
          chartData: twitterData.likes.chartData
        },
        {
          id: 'replies',
          title: 'Replies',
          value: twitterData.replies.total.toString(),
          change: twitterData.replies.change,
          changeType: twitterData.replies.change.includes('+') ? 'positive' : 
                     twitterData.replies.change.includes('-') ? 'negative' : 'neutral',
          icon: Users,
          color: 'green',
          chartData: twitterData.replies.chartData
        },
        {
          id: 'growth',
          title: 'Growth Rate',
          value: `${twitterData.growth.rate > 0 ? '+' : ''}${twitterData.growth.rate}%`,
          change: twitterData.growth.change,
          changeType: twitterData.growth.rate > 0 ? 'positive' : 
                     twitterData.growth.rate < 0 ? 'negative' : 'neutral',
          icon: TrendingUp,
          color: 'purple',
          chartData: twitterData.growth.chartData
        }
      ];
      
      setMetrics(newMetrics);
      
      // Log whether we're using real or mock data
      if (twitterData.mock) {
        console.log('📊 PostingTrends: Using mock Twitter data');
      } else {
        console.log('🐦 PostingTrends: Using live Twitter data');
      }
    }
  }, [twitterData]);

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

  // Loading state
  if (loading && metrics.length === 0) {
    return (
      <div className="h-full">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center space-x-3">
            <Rocket className="h-5 w-5 text-gray-600" />
            <h3 className="text-lg font-semibold text-gray-900">Posting Trends</h3>
          </div>
        </div>
        <div className="grid grid-cols-2 gap-4 h-[calc(100%-4rem)]">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="bg-gray-100 border-2 border-gray-200 rounded-lg p-4 animate-pulse">
              <div className="flex items-center justify-between mb-2">
                <div className="w-5 h-5 bg-gray-300 rounded"></div>
                <div className="w-4 h-4 bg-gray-300 rounded"></div>
              </div>
              <div className="space-y-2">
                <div className="w-12 h-8 bg-gray-300 rounded"></div>
                <div className="w-20 h-4 bg-gray-300 rounded"></div>
                <div className="w-16 h-3 bg-gray-300 rounded"></div>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  // Error state
  if (error && metrics.length === 0) {
    return (
      <div className="h-full">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center space-x-3">
            <Rocket className="h-5 w-5 text-gray-600" />
            <h3 className="text-lg font-semibold text-gray-900">Posting Trends</h3>
          </div>
        </div>
        <div className="flex items-center justify-center h-[calc(100%-4rem)]">
          <div className="text-center">
            <div className="text-red-500 mb-2">⚠️</div>
            <p className="text-sm text-gray-600">Unable to load Twitter metrics</p>
            <p className="text-xs text-gray-500">Check your API configuration</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <>
      <div className="h-full">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center space-x-3">
            <Rocket className="h-5 w-5 text-gray-600" />
            <h3 className="text-lg font-semibold text-gray-900">Posting Trends</h3>
            {twitterData?.mock && (
              <span className="text-xs bg-yellow-100 text-yellow-800 px-2 py-1 rounded-full">
                Demo Data
              </span>
            )}
          </div>
          {loading && (
            <div className="flex items-center space-x-2 text-sm text-gray-500">
              <div className="w-3 h-3 bg-blue-500 rounded-full animate-pulse"></div>
              <span>Updating...</span>
            </div>
          )}
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