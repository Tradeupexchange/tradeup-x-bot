import React, { useMemo } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { useApi, useNextRefreshTime } from '../hooks/useApi';

interface EngagementChartProps {
  data?: any[]; // Keep this for backward compatibility but we'll override with API data
}

interface EngagementData {
  date: string;
  likes: number;
  retweets: number;
  replies: number;
  totalPosts: number;
}

interface ApiPost {
  id: string;
  content: string;
  engagement: {
    likes: number;
    retweets: number;
    replies: number;
  };
  timestamp: string;
  topics: string[];
}

interface ApiResponse {
  posts: ApiPost[];
  total: number;
  hasMore: boolean;
}

const EngagementChart: React.FC<EngagementChartProps> = ({ data }) => {
  // Use the centralized useApi hook - it automatically handles 20-minute intervals!
  const { data: apiData, loading, error, lastFetch } = useApi<ApiResponse>('/api/posts?limit=200&offset=0');
  const nextRefresh = useNextRefreshTime(lastFetch);

  // Fallback data if API fails
  const fallbackData: EngagementData[] = [
    { date: '2024-01-01', likes: 45, retweets: 12, replies: 8, totalPosts: 3 },
    { date: '2024-01-02', likes: 62, retweets: 18, replies: 15, totalPosts: 4 },
    { date: '2024-01-03', likes: 38, retweets: 9, replies: 6, totalPosts: 2 },
    { date: '2024-01-04', likes: 78, retweets: 25, replies: 20, totalPosts: 5 },
    { date: '2024-01-05', likes: 92, retweets: 31, replies: 24, totalPosts: 6 },
    { date: '2024-01-06', likes: 55, retweets: 16, replies: 12, totalPosts: 3 },
    { date: '2024-01-07', likes: 89, retweets: 28, replies: 22, totalPosts: 5 },
  ];

  // Process API data into chart format
  const chartData = useMemo((): EngagementData[] => {
    if (!apiData?.posts || !Array.isArray(apiData.posts)) {
      console.warn('No valid API data, using fallback data');
      return fallbackData;
    }

    console.log('Processing engagement data from API...');

    // Filter to last 7 days
    const oneWeekAgo = new Date();
    oneWeekAgo.setDate(oneWeekAgo.getDate() - 7);

    const recentPosts = apiData.posts.filter(post => {
      try {
        const postDate = new Date(post.timestamp);
        return postDate >= oneWeekAgo;
      } catch {
        return false;
      }
    });

    console.log(`Filtered to ${recentPosts.length} posts from last 7 days for engagement analysis`);

    // Group posts by date
    const dateGroups: { [key: string]: ApiPost[] } = {};
    
    recentPosts.forEach(post => {
      try {
        const postDate = new Date(post.timestamp);
        const dateKey = postDate.toISOString().split('T')[0]; // YYYY-MM-DD format
        
        if (!dateGroups[dateKey]) {
          dateGroups[dateKey] = [];
        }
        dateGroups[dateKey].push(post);
      } catch (err) {
        console.warn('Error processing post timestamp:', post.timestamp, err);
      }
    });

    // Calculate averages per day
    const processedData: EngagementData[] = [];
    
    Object.keys(dateGroups)
      .sort() // Sort dates chronologically
      .slice(-7) // Get last 7 days
      .forEach(date => {
        const dayPosts = dateGroups[date];
        const totalPosts = dayPosts.length;
        
        if (totalPosts > 0) {
          // Calculate averages per post for that day
          const totalLikes = dayPosts.reduce((sum, post) => sum + (post.engagement?.likes || 0), 0);
          const totalRetweets = dayPosts.reduce((sum, post) => sum + (post.engagement?.retweets || 0), 0);
          const totalReplies = dayPosts.reduce((sum, post) => sum + (post.engagement?.replies || 0), 0);
          
          processedData.push({
            date,
            likes: Math.round(totalLikes / totalPosts * 10) / 10, // Average likes per post
            retweets: Math.round(totalRetweets / totalPosts * 10) / 10, // Average retweets per post
            replies: Math.round(totalReplies / totalPosts * 10) / 10, // Average replies per post
            totalPosts
          });
        }
      });

    const result = processedData.length > 0 ? processedData : fallbackData;
    console.log('Processed engagement chart data:', result);
    return result;
  }, [apiData, fallbackData]);

  // Calculate totals for display
  const { totalLikes, totalRetweets, totalReplies, avgLikesPerPost } = useMemo(() => {
    const totals = {
      totalLikes: chartData.reduce((sum, day) => sum + (day.likes * day.totalPosts), 0),
      totalRetweets: chartData.reduce((sum, day) => sum + (day.retweets * day.totalPosts), 0),
      totalReplies: chartData.reduce((sum, day) => sum + (day.replies * day.totalPosts), 0),
      avgLikesPerPost: chartData.length > 0 
        ? Math.round((chartData.reduce((sum, day) => sum + day.likes, 0) / chartData.length) * 10) / 10 
        : 0
    };
    return totals;
  }, [chartData]);

  return (
    <div className="bg-white rounded-xl p-6 shadow-sm">
      <div className="mb-6">
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-xl font-semibold text-gray-900">Engagement per Post</h3>
          <div className="flex items-center space-x-2">
            {loading && (
              <div className="h-2 w-2 bg-blue-500 rounded-full animate-pulse"></div>
            )}
            {lastFetch && (
              <span className="text-xs text-gray-500">
                Updated: {lastFetch.toLocaleTimeString()}
              </span>
            )}
          </div>
        </div>
        
        <p className="text-gray-600 text-sm mb-3">
          Average likes, retweets, and replies per post (last 7 days)
        </p>

        {/* Quick stats */}
        <div className="flex space-x-4 text-sm mb-2">
          <div className="bg-blue-50 px-3 py-1 rounded-lg">
            <span className="text-blue-600 font-medium">❤️ {totalLikes} total likes</span>
          </div>
          <div className="bg-green-50 px-3 py-1 rounded-lg">
            <span className="text-green-600 font-medium">🔄 {totalRetweets} retweets</span>
          </div>
          <div className="bg-purple-50 px-3 py-1 rounded-lg">
            <span className="text-purple-600 font-medium">💬 {totalReplies} replies</span>
          </div>
          <div className="bg-gray-50 px-3 py-1 rounded-lg">
            <span className="text-gray-600 font-medium">📊 {avgLikesPerPost} avg likes/post</span>
          </div>
        </div>

        {error && (
          <div className="mt-2 p-2 bg-red-50 border border-red-200 rounded text-sm text-red-600">
            ⚠️ {error}
          </div>
        )}
      </div>
      
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis 
              dataKey="date" 
              stroke="#6b7280"
              fontSize={12}
              tickFormatter={(value) => {
                try {
                  return new Date(value).toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
                } catch {
                  return value;
                }
              }}
            />
            <YAxis 
              stroke="#6b7280"
              fontSize={12}
              tickFormatter={(value) => `${value}`}
            />
            <Tooltip 
              formatter={(value: number, name: string) => {
                const displayName = name === 'likes' ? 'Likes per Post' : 
                                 name === 'retweets' ? 'Retweets per Post' : 
                                 'Replies per Post';
                return [`${value}`, displayName];
              }}
              labelFormatter={(value) => {
                try {
                  return `Date: ${new Date(value).toLocaleDateString()}`;
                } catch {
                  return `Date: ${value}`;
                }
              }}
              contentStyle={{
                backgroundColor: '#fff',
                border: '1px solid #e5e7eb',
                borderRadius: '8px',
                boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
              }}
            />
            <Legend 
              wrapperStyle={{ paddingTop: '20px' }}
              iconType="line"
            />
            
            {/* Likes line */}
            <Line 
              type="monotone" 
              dataKey="likes" 
              stroke="#3b82f6" 
              strokeWidth={3}
              dot={{ fill: '#3b82f6', strokeWidth: 2, r: 4 }}
              activeDot={{ r: 6, stroke: '#3b82f6', strokeWidth: 2 }}
              name="Likes"
            />
            
            {/* Retweets line */}
            <Line 
              type="monotone" 
              dataKey="retweets" 
              stroke="#10b981" 
              strokeWidth={3}
              dot={{ fill: '#10b981', strokeWidth: 2, r: 4 }}
              activeDot={{ r: 6, stroke: '#10b981', strokeWidth: 2 }}
              name="Retweets"
            />
            
            {/* Replies line */}
            <Line 
              type="monotone" 
              dataKey="replies" 
              stroke="#8b5cf6" 
              strokeWidth={3}
              dot={{ fill: '#8b5cf6', strokeWidth: 2, r: 4 }}
              activeDot={{ r: 6, stroke: '#8b5cf6', strokeWidth: 2 }}
              name="Replies"
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Data refresh info - now uses centralized timing */}
      <div className="mt-4 text-xs text-gray-500 text-center">
        Auto-refreshes every 20 minutes • Next update: {
          nextRefresh 
            ? nextRefresh.toLocaleTimeString()
            : 'Soon'
        }
      </div>
    </div>
  );
};

export default EngagementChart;