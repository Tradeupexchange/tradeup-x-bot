import React, { useState } from 'react';
import { Heart, MessageCircle, Repeat2, ExternalLink, Calendar, RefreshCw } from 'lucide-react';

interface Post {
  id: number;
  content: string;
  engagement: { likes: number; retweets: number; replies: number };
  timestamp: string;
  topics: string[];
}

interface RecentPostsProps {
  posts: Post[];
}

const RecentPosts: React.FC<RecentPostsProps> = ({ posts }) => {
  const [loading, setLoading] = useState(false);

  const formatEngagement = (num: number) => {
    if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
    return num.toString();
  };

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffInHours = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60));
    
    if (diffInHours < 1) return 'Just now';
    if (diffInHours < 24) return `${diffInHours} hours ago`;
    return date.toLocaleDateString();
  };

  const loadMorePosts = async () => {
    setLoading(true);
    // This would typically make an API call to load more posts
    setTimeout(() => setLoading(false), 1000);
  };

  if (!posts || posts.length === 0) {
    return (
      <div className="bg-white rounded-xl p-6 shadow-sm">
        <div className="mb-6">
          <h3 className="text-xl font-semibold text-gray-900 mb-2">Recent Posts</h3>
          <p className="text-gray-600 text-sm">Latest posts from your Pokemon TCG bot</p>
        </div>
        <div className="text-center py-8">
          <p className="text-gray-500">No posts available yet</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl p-6 shadow-sm">
      <div className="mb-6">
        <h3 className="text-xl font-semibold text-gray-900 mb-2">Recent Posts</h3>
        <p className="text-gray-600 text-sm">Latest posts from your Pokemon TCG bot</p>
      </div>
      
      <div className="space-y-6">
        {posts.map((post) => (
          <div key={post.id} className="border-l-4 border-blue-500 pl-4 pb-6 border-b border-gray-100 last:border-b-0">
            <div className="flex items-start justify-between mb-3">
              <div className="flex items-center space-x-2 text-sm text-gray-500">
                <Calendar className="h-4 w-4" />
                <span>{formatTimestamp(post.timestamp)}</span>
              </div>
              <button className="text-gray-400 hover:text-gray-600 transition-colors duration-150">
                <ExternalLink className="h-4 w-4" />
              </button>
            </div>
            
            <p className="text-gray-900 mb-3 leading-relaxed">{post.content}</p>
            
            <div className="flex flex-wrap gap-2 mb-4">
              {post.topics?.map((topic, index) => (
                <span 
                  key={index} 
                  className="px-2 py-1 bg-blue-50 text-blue-700 text-xs font-medium rounded-full"
                >
                  #{topic}
                </span>
              ))}
            </div>
            
            <div className="flex items-center space-x-6 text-gray-500">
              <div className="flex items-center space-x-1 hover:text-red-500 transition-colors duration-150 cursor-pointer">
                <Heart className="h-4 w-4" />
                <span className="text-sm">{formatEngagement(post.engagement.likes)}</span>
              </div>
              <div className="flex items-center space-x-1 hover:text-green-500 transition-colors duration-150 cursor-pointer">
                <Repeat2 className="h-4 w-4" />
                <span className="text-sm">{formatEngagement(post.engagement.retweets)}</span>
              </div>
              <div className="flex items-center space-x-1 hover:text-blue-500 transition-colors duration-150 cursor-pointer">
                <MessageCircle className="h-4 w-4" />
                <span className="text-sm">{formatEngagement(post.engagement.replies)}</span>
              </div>
            </div>
          </div>
        ))}
      </div>
      
      <div className="mt-6 pt-4 border-t border-gray-200">
        <button 
          onClick={loadMorePosts}
          disabled={loading}
          className="w-full text-center text-blue-600 hover:text-blue-700 font-medium text-sm transition-colors duration-150 flex items-center justify-center space-x-2"
        >
          {loading ? (
            <>
              <RefreshCw className="h-4 w-4 animate-spin" />
              <span>Loading...</span>
            </>
          ) : (
            <span>Load More Posts →</span>
          )}
        </button>
      </div>
    </div>
  );
};

export default RecentPosts;