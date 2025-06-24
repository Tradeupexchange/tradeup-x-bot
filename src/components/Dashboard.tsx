import React, { useEffect, useState } from 'react';
import RecentPosts from './RecentPosts';
import BotControl from './BotControl';
import ConnectionTest from './ConnectionTest';
import TestButtons from './TestButtons';
import { useApi } from '../hooks/useApi';

interface DashboardData {
  posts: any[];
  topics: any[];
}

interface RecentPostsResponse {
  success: boolean;
  posts: any[];
  count: number;
  timestamp: string;
}

const Dashboard: React.FC = () => {
  const [dashboardData, setDashboardData] = useState<DashboardData>({
    posts: [],
    topics: []
  });

  // Fetch data from Railway backend
  const { data: initialPosts } = useApi('/api/posts', { autoRefresh: false });
  const { data: initialTopics } = useApi('/api/topics', { autoRefresh: false });
  
  // Add recent posts API integration
  const { 
    data: recentPostsData, 
    loading: postsLoading, 
    error: postsError, 
    refetch: refetchPosts 
  } = useApi<RecentPostsResponse>('/api/recent-posts');

  // Set initial data
  useEffect(() => {
    if (initialPosts) {
      console.log('📝 Dashboard: Setting posts data');
      setDashboardData(prev => ({ ...prev, posts: initialPosts.posts || [] }));
    }
  }, [initialPosts]);

  useEffect(() => {
    if (initialTopics) {
      console.log('🏷️ Dashboard: Setting topics data');
      setDashboardData(prev => ({ ...prev, topics: initialTopics }));
    }
  }, [initialTopics]);

  // Function to refresh posts (only called after posting new content)
  const handleRefreshPosts = () => {
    console.log('🔄 Dashboard: Refreshing recent posts after posting...');
    refetchPosts();
  };

  // Log recent posts data when it changes
  useEffect(() => {
    if (recentPostsData?.posts) {
      console.log('📊 Dashboard: Recent posts updated:', recentPostsData.posts.length, 'posts');
    }
  }, [recentPostsData]);

  return (
    <div className="space-y-8">
      {/* Top row: Connection Test and Test Buttons side by side */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Connection Test */}
        <div className="bg-white border-2 border-gray-400 rounded-xl shadow-lg p-6">
          <ConnectionTest />
        </div>
        
        {/* Test Buttons */}
        <div className="bg-white border-2 border-gray-400 rounded-xl shadow-lg p-6">
          <TestButtons onPostSuccess={handleRefreshPosts} />
        </div>
      </div>
      
      {/* Bot Control Center - full width */}
      <div className="bg-white border-2 border-gray-400 rounded-xl shadow-lg p-6">
        <BotControl onPostSuccess={handleRefreshPosts} />
      </div>
      
      {/* Recent Posts - full width */}
      <div className="bg-white border-2 border-gray-400 rounded-xl shadow-lg p-6">
        <RecentPosts 
          posts={recentPostsData?.posts || []}
          loading={postsLoading}
        />
        
        {/* Show error if there's an issue loading recent posts */}
        {postsError && (
          <div className="mt-4 bg-red-50 border border-red-200 rounded-lg p-4">
            <p className="text-red-700 text-sm">
              ⚠️ Error loading recent posts: {postsError}
            </p>
            <button 
              onClick={handleRefreshPosts}
              className="text-red-600 hover:text-red-800 underline text-sm mt-1"
            >
              Try again
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default Dashboard;