import React, { useState, useEffect, useCallback } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

// Static fallback data in case API fails
const fallbackData = [
  { day: 'Mon', posts: 18, engagement: 7.2 },
  { day: 'Tue', posts: 22, engagement: 8.1 },
  { day: 'Wed', posts: 15, engagement: 6.8 },
  { day: 'Thu', posts: 25, engagement: 9.3 },
  { day: 'Fri', posts: 20, engagement: 8.7 },
  { day: 'Sat', posts: 12, engagement: 5.9 },
  { day: 'Sun', posts: 14, engagement: 6.4 },
];

interface PostingData {
  day: string;
  posts: number;
  engagement: number;
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

const PostingTrends: React.FC = () => {
  const [data, setData] = useState<PostingData[]>(fallbackData);
  const [loading, setLoading] = useState(false);
  const [lastFetch, setLastFetch] = useState<Date | null>(null);
  const [error, setError] = useState<string | null>(null);

  // API base URL - adjust this to match your backend URL
  const API_BASE_URL = process.env.REACT_APP_API_URL || 'https://your-railway-app.railway.app';

  const processApiData = (posts: ApiPost[]): PostingData[] => {
    // Group posts by day of week
    const daysOfWeek = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
    const groupedData: { [key: string]: { posts: number; totalEngagement: number; postsList: ApiPost[] } } = {};

    // Initialize all days
    daysOfWeek.forEach(day => {
      groupedData[day] = { posts: 0, totalEngagement: 0, postsList: [] };
    });

    // Process posts
    posts.forEach(post => {
      try {
        const postDate = new Date(post.timestamp);
        const dayName = daysOfWeek[postDate.getDay()];
        
        if (groupedData[dayName]) {
          groupedData[dayName].posts += 1;
          groupedData[dayName].postsList.push(post);
          
          // Calculate engagement score (likes + retweets + replies)
          const engagementScore = 
            (post.engagement?.likes || 0) + 
            (post.engagement?.retweets || 0) + 
            (post.engagement?.replies || 0);
          
          groupedData[dayName].totalEngagement += engagementScore;
        }
      } catch (err) {
        console.warn('Error processing post timestamp:', post.timestamp, err);
      }
    });

    // Convert to chart format (Monday to Sunday order for business week)
    const orderedDays = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
    
    return orderedDays.map(day => ({
      day,
      posts: groupedData[day].posts,
      engagement: groupedData[day].posts > 0 
        ? Math.round((groupedData[day].totalEngagement / groupedData[day].posts) * 10) / 10
        : 0
    }));
  };

  const fetchPostingData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      console.log('Fetching posting trends data...');

      // Fetch recent posts from your API (last 7 days worth)
      const response = await fetch(`${API_BASE_URL}/api/posts?limit=100&offset=0`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`API request failed: ${response.status} ${response.statusText}`);
      }

      const apiData: ApiResponse = await response.json();
      
      console.log('Received API data:', apiData);

      if (apiData.posts && Array.isArray(apiData.posts)) {
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

        console.log(`Filtered to ${recentPosts.length} posts from last 7 days`);

        const processedData = processApiData(recentPosts);
        setData(processedData);
        setLastFetch(new Date());

        console.log('Updated chart data:', processedData);
      } else {
        console.warn('Invalid API response format, using fallback data');
        setData(fallbackData);
      }

    } catch (err) {
      console.error('Error fetching posting data:', err);
      setError(err instanceof Error ? err.message : 'Failed to fetch data');
      
      // Keep existing data on error, don't revert to fallback
      if (data === fallbackData) {
        setData(fallbackData);
      }
    } finally {
      setLoading(false);
    }
  }, [API_BASE_URL, data]);

  // Initial fetch and setup interval
  useEffect(() => {
    // Fetch immediately on mount
    fetchPostingData();

    // Set up 20-minute interval (20 * 60 * 1000 = 1,200,000 ms)
    const interval = setInterval(() => {
      console.log('20-minute interval: Fetching fresh posting data...');
      fetchPostingData();
    }, 20 * 60 * 1000);

    // Cleanup interval on unmount
    return () => {
      clearInterval(interval);
      console.log('PostingTrends component unmounted, cleared interval');
    };
  }, [fetchPostingData]);

  // Calculate total posts for the week
  const totalPosts = data.reduce((sum, day) => sum + day.posts, 0);
  const avgEngagement = data.length > 0 
    ? Math.round((data.reduce((sum, day) => sum + day.engagement, 0) / data.length) * 10) / 10 
    : 0;

  return (
    <div className="bg-white rounded-xl p-6 shadow-sm">
      <div className="mb-6">
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-xl font-semibold text-gray-900">Weekly Posting Activity</h3>
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
          Posts published by day of the week (last 7 days)
        </p>

        {/* Quick stats */}
        <div className="flex space-x-4 text-sm">
          <div className="bg-blue-50 px-3 py-1 rounded-lg">
            <span className="text-blue-600 font-medium">{totalPosts} total posts</span>
          </div>
          <div className="bg-green-50 px-3 py-1 rounded-lg">
            <span className="text-green-600 font-medium">{avgEngagement} avg engagement</span>
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
          <BarChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
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
                name === 'posts' ? `${value} posts` : `${value} avg engagement`,
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
              name="posts"
            />
            {/* Optionally add engagement as a second bar or line */}
            <Bar 
              dataKey="engagement" 
              fill="#10b981" 
              radius={[4, 4, 0, 0]}
              name="engagement"
            />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Data refresh info */}
      <div className="mt-4 text-xs text-gray-500 text-center">
        Data refreshes every 20 minutes • Next update: {
          lastFetch 
            ? new Date(lastFetch.getTime() + 20 * 60 * 1000).toLocaleTimeString()
            : 'Soon'
        }
      </div>
    </div>
  );
};

export default PostingTrends;