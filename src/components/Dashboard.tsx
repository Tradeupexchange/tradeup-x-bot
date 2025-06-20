import React, { useEffect, useState } from 'react';
import MetricsGrid from './MetricsGrid';
import EngagementChart from './EngagementChart';
import RecentPosts from './RecentPosts';
import PostingTrends from './PostingTrends';
import BotControl from './BotControl';
import ConnectionTest from './ConnectionTest';
import TestButtons from './TestButtons';
import { useApi } from '../hooks/useApi';

interface DashboardData {
  metrics: any;
  posts: any[];
  topics: any[];
  engagementHistory: any[];
}

const Dashboard: React.FC = () => {
  const [dashboardData, setDashboardData] = useState<DashboardData>({
    metrics: null,
    posts: [],
    topics: [],
    engagementHistory: []
  });

  // Fetch data from Railway backend
  const { data: initialMetrics } = useApi('/api/metrics', { autoRefresh: false });
  const { data: initialPosts } = useApi('/api/posts', { autoRefresh: false });
  const { data: initialTopics } = useApi('/api/topics', { autoRefresh: false });
  const { data: initialEngagement } = useApi('/api/engagement', { autoRefresh: false });

  // Set initial data
  useEffect(() => {
    if (initialMetrics) {
      console.log('📊 Dashboard: Setting metrics data');
      setDashboardData(prev => ({ ...prev, metrics: initialMetrics }));
    }
  }, [initialMetrics]);

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

  useEffect(() => {
    if (initialEngagement) {
      console.log('📈 Dashboard: Setting engagement data');
      setDashboardData(prev => ({ ...prev, engagementHistory: initialEngagement }));
    }
  }, [initialEngagement]);

  // Auto-refresh data every 30 seconds
  // Commented out to prevent frequent page refreshes
  // useEffect(() => {
  //   const interval = setInterval(() => {
  //     // Trigger refetch of all data
  //     window.location.reload();
  //   }, 30000);

  //   return () => clearInterval(interval);
  // }, []);

  return (
    <div className="space-y-8">
      {/* Top row: Connection/Content Testing (left) and Posting Trends (right) */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Left side: Connection Test and Content Testing stacked */}
        <div className="space-y-6">
          <div className="bg-white border-2 border-gray-400 rounded-xl shadow-lg p-6">
            <ConnectionTest />
          </div>
          <div className="bg-white border-2 border-gray-400 rounded-xl shadow-lg p-6">
            <TestButtons />
          </div>
        </div>
        
        {/* Right side: Posting Trends with 4 metric squares */}
        <div className="bg-white border-2 border-gray-400 rounded-xl shadow-lg p-6">
          <PostingTrends />
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
      
      {/* Metrics Grid - full width */}
      <div className="bg-white border-2 border-gray-400 rounded-xl shadow-lg p-6">
        <MetricsGrid metrics={dashboardData.metrics} />
      </div>
      
      {/* Engagement Chart - full width */}
      <div className="bg-white border-2 border-gray-400 rounded-xl shadow-lg p-6">
        <EngagementChart data={dashboardData.engagementHistory} />
      </div>
    </div>
  );
};

export default Dashboard;