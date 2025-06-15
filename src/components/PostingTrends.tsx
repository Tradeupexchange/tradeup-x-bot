import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

const data = [
  { day: 'Mon', posts: 18, engagement: 7.2 },
  { day: 'Tue', posts: 22, engagement: 8.1 },
  { day: 'Wed', posts: 15, engagement: 6.8 },
  { day: 'Thu', posts: 25, engagement: 9.3 },
  { day: 'Fri', posts: 20, engagement: 8.7 },
  { day: 'Sat', posts: 12, engagement: 5.9 },
  { day: 'Sun', posts: 14, engagement: 6.4 },
];

const PostingTrends: React.FC = () => {
  return (
    <div className="bg-white rounded-xl p-6 shadow-sm">
      <div className="mb-6">
        <h3 className="text-xl font-semibold text-gray-900 mb-2">Weekly Posting Activity</h3>
        <p className="text-gray-600 text-sm">Posts published by day of the week</p>
      </div>
      
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis 
              dataKey="day" 
              stroke="#6b7280"
              fontSize={12}
            />
            <YAxis 
              stroke="#6b7280"
              fontSize={12}
            />
            <Tooltip 
              formatter={(value: number, name: string) => [
                name === 'posts' ? `${value} posts` : `${value}%`,
                name === 'posts' ? 'Posts' : 'Engagement'
              ]}
              contentStyle={{
                backgroundColor: '#fff',
                border: '1px solid #e5e7eb',
                borderRadius: '8px',
                boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
              }}
            />
            <Bar 
              dataKey="posts" 
              fill="#3b82f6" 
              radius={[4, 4, 0, 0]}
            />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default PostingTrends;