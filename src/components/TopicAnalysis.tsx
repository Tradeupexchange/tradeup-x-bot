import React from 'react';
import { Hash, TrendingUp } from 'lucide-react';

interface Topic {
  name: string;
  count: number;
  trend: 'up' | 'down' | 'stable';
  percentage: number;
}

interface TopicAnalysisProps {
  topics: Topic[];
}

const TopicAnalysis: React.FC<TopicAnalysisProps> = ({ topics }) => {
  if (!topics || topics.length === 0) {
    return (
      <div className="bg-white rounded-xl p-6 shadow-sm">
        <div className="mb-6">
          <h3 className="text-xl font-semibold text-gray-900 mb-2">Topic Analysis</h3>
          <p className="text-gray-600 text-sm">Most discussed Pokemon TCG topics</p>
        </div>
        <div className="text-center py-8">
          <p className="text-gray-500">No topic data available</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl p-6 shadow-sm">
      <div className="mb-6">
        <h3 className="text-xl font-semibold text-gray-900 mb-2">Topic Analysis</h3>
        <p className="text-gray-600 text-sm">Most discussed Pokemon TCG topics</p>
      </div>
      
      <div className="space-y-4">
        {topics.map((topic, index) => (
          <div key={index} className="flex items-center justify-between p-3 rounded-lg hover:bg-gray-50 transition-colors duration-150">
            <div className="flex items-center space-x-3">
              <div className="flex items-center justify-center w-8 h-8 bg-blue-50 rounded-lg">
                <Hash className="h-4 w-4 text-blue-600" />
              </div>
              <div>
                <p className="font-medium text-gray-900">{topic.name}</p>
                <p className="text-sm text-gray-600">{topic.count} mentions</p>
              </div>
            </div>
            
            <div className="flex items-center space-x-2">
              <div className="w-16 bg-gray-200 rounded-full h-2">
                <div 
                  className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${topic.percentage}%` }}
                ></div>
              </div>
              {topic.trend === 'up' && (
                <TrendingUp className="h-4 w-4 text-green-500" />
              )}
            </div>
          </div>
        ))}
      </div>
      
      <div className="mt-6 pt-4 border-t border-gray-200">
        <button className="w-full text-center text-blue-600 hover:text-blue-700 font-medium text-sm transition-colors duration-150">
          View All Topics →
        </button>
      </div>
    </div>
  );
};

export default TopicAnalysis;