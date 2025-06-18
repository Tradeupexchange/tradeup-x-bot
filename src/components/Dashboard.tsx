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
  const { data: initialMetrics } = useApi('/api/metrics');
  const { data: initialPosts } = useApi('/api/posts');
  const { data: initialTopics } = useApi('/api/topics');
  const { data: initialEngagement } = useApi('/api/engagement');

  // Set initial data
  useEffect(() => {
    if (initialMetrics) {
      setDashboardData(prev => ({ ...prev, metrics: initialMetrics }));
    }
  }, [initialMetrics]);

  useEffect(() => {
    if (initialPosts) {
      setDashboardData(prev => ({ ...prev, posts: initialPosts.posts || [] }));
    }
  }, [initialPosts]);

  useEffect(() => {
    if (initialTopics) {
      setDashboardData(prev => ({ ...prev, topics: initialTopics }));
    }
  }, [initialTopics]);

  useEffect(() => {
    if (initialEngagement) {
      setDashboardData(prev => ({ ...prev, engagementHistory: initialEngagement }));
    }
  }, [initialEngagement]);

  // Auto-refresh data every 30 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      // Trigger refetch of all data
      window.location.reload();
    }, 30000);

    return () => clearInterval(interval);
  }, []);

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
      
      <ConnectionTest />
      <TestButtons />
      <BotControl />
      <MetricsGrid metrics={dashboardData.metrics} />
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <EngagementChart data={dashboardData.engagementHistory} />
        <PostingTrends />
      </div>
      
      {/* Modified layout - RecentPosts now takes full width */}
      <div className="grid grid-cols-1 gap-8">
        <RecentPosts posts={dashboardData.posts} />
      </div>
    </div>
  );
};

export default Dashboard;