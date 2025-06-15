import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

interface EngagementChartProps {
  data: any[];
}

const EngagementChart: React.FC<EngagementChartProps> = ({ data }) => {
  // Fallback data if no data is provided
  const chartData = data && data.length > 0 ? data : [
    { date: '2024-01-01', engagement: 6.2, posts: 12 },
    { date: '2024-01-02', engagement: 7.1, posts: 15 },
    { date: '2024-01-03', engagement: 5.8, posts: 10 },
    { date: '2024-01-04', engagement: 8.3, posts: 18 },
    { date: '2024-01-05', engagement: 9.1, posts: 20 },
    { date: '2024-01-06', engagement: 7.6, posts: 14 },
    { date: '2024-01-07', engagement: 8.9, posts: 22 },
  ];

  return (
    <div className="bg-white rounded-xl p-6 shadow-sm">
      <div className="mb-6">
        <h3 className="text-xl font-semibold text-gray-900 mb-2">Engagement Trends</h3>
        <p className="text-gray-600 text-sm">Daily engagement rate over time</p>
      </div>
      
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis 
              dataKey="date" 
              stroke="#6b7280"
              fontSize={12}
              tickFormatter={(value) => new Date(value).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
            />
            <YAxis 
              stroke="#6b7280"
              fontSize={12}
              tickFormatter={(value) => `${value}%`}
            />
            <Tooltip 
              formatter={(value: number) => [`${value}%`, 'Engagement Rate']}
              labelFormatter={(value) => new Date(value).toLocaleDateString()}
              contentStyle={{
                backgroundColor: '#fff',
                border: '1px solid #e5e7eb',
                borderRadius: '8px',
                boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
              }}
            />
            <Line 
              type="monotone" 
              dataKey="engagement" 
              stroke="#3b82f6" 
              strokeWidth={3}
              dot={{ fill: '#3b82f6', strokeWidth: 2, r: 4 }}
              activeDot={{ r: 6, stroke: '#3b82f6', strokeWidth: 2 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default EngagementChart;