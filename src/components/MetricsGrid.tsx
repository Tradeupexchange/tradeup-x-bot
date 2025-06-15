import React from 'react';
import { TrendingUp, MessageCircle, Heart, Users } from 'lucide-react';

interface MetricsGridProps {
  metrics: any;
}

const MetricsGrid: React.FC<MetricsGridProps> = ({ metrics }) => {
  if (!metrics) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {[...Array(4)].map((_, index) => (
          <div key={index} className="bg-white rounded-xl p-6 shadow-sm animate-pulse">
            <div className="flex items-center justify-between mb-4">
              <div className="w-10 h-10 bg-gray-200 rounded-lg"></div>
              <div className="w-16 h-4 bg-gray-200 rounded"></div>
            </div>
            <div className="w-20 h-8 bg-gray-200 rounded mb-2"></div>
            <div className="w-24 h-4 bg-gray-200 rounded"></div>
          </div>
        ))}
      </div>
    );
  }

  const metricsData = [
    {
      title: 'Total Posts',
      value: metrics.totalPosts?.toLocaleString() || '0',
      change: '+12%',
      trend: 'up',
      icon: MessageCircle,
      color: 'blue'
    },
    {
      title: 'Avg Engagement',
      value: `${metrics.avgEngagement || 0}%`,
      change: '+2.1%',
      trend: 'up',
      icon: TrendingUp,
      color: 'green'
    },
    {
      title: 'Total Likes',
      value: metrics.totalLikes >= 1000 ? `${(metrics.totalLikes / 1000).toFixed(1)}K` : metrics.totalLikes?.toString() || '0',
      change: '+18%',
      trend: 'up',
      icon: Heart,
      color: 'red'
    },
    {
      title: 'Followers',
      value: metrics.followers?.toLocaleString() || '0',
      change: '+5.2%',
      trend: 'up',
      icon: Users,
      color: 'purple'
    }
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      {metricsData.map((metric, index) => {
        const Icon = metric.icon;
        const colorClasses = {
          blue: 'bg-blue-500 text-blue-600 bg-blue-50',
          green: 'bg-green-500 text-green-600 bg-green-50',
          red: 'bg-red-500 text-red-600 bg-red-50',
          purple: 'bg-purple-500 text-purple-600 bg-purple-50'
        };
        
        return (
          <div key={index} className="bg-white rounded-xl p-6 shadow-sm hover:shadow-md transition-shadow duration-200">
            <div className="flex items-center justify-between mb-4">
              <div className={`p-2 rounded-lg ${colorClasses[metric.color as keyof typeof colorClasses].split(' ')[2]}`}>
                <Icon className={`h-5 w-5 ${colorClasses[metric.color as keyof typeof colorClasses].split(' ')[1]}`} />
              </div>
              <span className="text-green-600 text-sm font-medium flex items-center">
                <TrendingUp className="h-3 w-3 mr-1" />
                {metric.change}
              </span>
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-900 mb-1">{metric.value}</p>
              <p className="text-gray-600 text-sm">{metric.title}</p>
            </div>
          </div>
        );
      })}
    </div>
  );
};

export default MetricsGrid;