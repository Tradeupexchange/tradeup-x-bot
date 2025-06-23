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

const Dashboard: React.FC = () => {
  const [dashboardData, setDashboardData] = useState<DashboardData>({
    posts: [],
    topics: []
  });

  // Fetch data from Railway backend
  const { data: initialPosts } = useApi('/api/posts', { autoRefresh: false });
  const { data: initialTopics } = useApi('/api/topics', { autoRefresh: false });

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
          <TestButtons />
        </div>
      </div>
      
      {/* Bot Control Center - full width */}
      <div className="bg-white border-2 border-gray-400 rounded-xl shadow-lg p-6">
        <BotControl />
      </div>
      
      {/* Recent Posts - full width */}
      <div className="bg-white border-2 border-gray-400 rounded-xl shadow-lg p-6">
        <RecentPosts posts={dashboardData.posts} />
      </div>
    </div>
  );
};

export default Dashboard;