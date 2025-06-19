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
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold text-gray-900 mb-2">TradeUp X Bot Control Dashboard</h2>
          <p className="text-gray-600">Monitor and control your Pokemon TCG bot's performance</p>
        </div>
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2 px-3 py-1 rounded-full text-sm bg-green-100 text-green-800">
            <div className="w-2 h-2 rounded-full bg-green-500"></div>
            <span>Live Data</span>
          </div>
        </div>
      </div>
      
      {/* Connection Test and Test Buttons side by side at the top */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div className="bg-white border-2 border-gray-400 rounded-xl shadow-lg p-6">
          <ConnectionTest />
        </div>
        <div className="bg-white border-2 border-gray-400 rounded-xl shadow-lg p-6">
          <TestButtons />
        </div>
      </div>
      
      <div className="bg-white border-2 border-gray-400 rounded-xl shadow-lg p-6">
        <BotControl />
      </div>
      
      <div className="bg-white border-2 border-gray-400 rounded-xl shadow-lg p-6">
        <MetricsGrid metrics={dashboardData.metrics} />
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div className="bg-white border-2 border-gray-400 rounded-xl shadow-lg p-6">
          <EngagementChart data={dashboardData.engagementHistory} />
        </div>
        <div className="bg-white border-2 border-gray-400 rounded-xl shadow-lg p-6">
          <PostingTrends />
        </div>
      </div>
      
      {/* Modified layout - RecentPosts now takes full width */}
      <div className="bg-white border-2 border-gray-400 rounded-xl shadow-lg p-6">
        <RecentPosts posts={dashboardData.posts} />
      </div>
    </div>
  );
};

export default Dashboard;