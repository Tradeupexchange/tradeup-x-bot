import React, { useState } from 'react';
import { Heart, MessageCircle, Repeat2, ExternalLink, Calendar, RefreshCw, Reply, MessageSquare } from 'lucide-react';

interface Post {
  id: string;
  content: string;
  type: 'post' | 'reply'; // Add type to distinguish posts from replies
  engagement: { likes: number; retweets: number; replies: number };
  timestamp: string;
  topics?: string[];
  tweet_url?: string; // Direct link to the tweet
  tweet_id?: string;
  // For replies
  replied_to?: {
    tweet_id: string;
    author: string;
    content: string;
    url: string;
  };
}

interface RecentPostsProps {
  posts: Post[];
  loading?: boolean;
}

const RecentPosts: React.FC<RecentPostsProps> = ({ posts, loading = false }) => {
  const [loadingMore, setLoadingMore] = useState(false);

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
    if (diffInHours < 168) return `${Math.floor(diffInHours / 24)} days ago`;
    return date.toLocaleDateString();
  };

  const loadMorePosts = async () => {
    setLoadingMore(true);
    // This would typically make an API call to load more posts
    setTimeout(() => setLoadingMore(false), 1000);
  };

  const handleViewTweet = (post: Post) => {
    if (post.tweet_url) {
      window.open(post.tweet_url, '_blank', 'noopener,noreferrer');
    }
  };

  const handleViewOriginalTweet = (repliedTo: Post['replied_to']) => {
    if (repliedTo?.url) {
      window.open(repliedTo.url, '_blank', 'noopener,noreferrer');
    }
  };

  if (!posts || posts.length === 0) {
    return (
      <div className="bg-white rounded-xl p-6 shadow-sm">
        <div className="mb-6">
          <div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">Recent Posts</h3>
            <p className="text-gray-600 text-sm">Latest posts and replies from your Pokemon TCG bot</p>
          </div>
        </div>
        <div className="text-center py-8">
          <p className="text-gray-500">No posts available yet</p>
          <p className="text-gray-400 text-sm mt-1">Posts and replies will appear here after they're published</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl p-6 shadow-sm">
      <div className="mb-6">
        <div>
          <h3 className="text-xl font-semibold text-gray-900 mb-2">Recent Posts</h3>
          <p className="text-gray-600 text-sm">Latest posts and replies from your Pokemon TCG bot</p>
        </div>
      </div>
      
      <div className="space-y-6">
        {posts.map((post) => (
          <div 
            key={post.id} 
            className={`border-l-4 pl-4 pb-6 border-b border-gray-100 last:border-b-0 ${
              post.type === 'reply' ? 'border-green-500' : 'border-blue-500'
            }`}
          >
            {/* Header with timestamp and type indicator */}
            <div className="flex items-start justify-between mb-3">
              <div className="flex items-center space-x-3">
                <div className="flex items-center space-x-2 text-sm text-gray-500">
                  {post.type === 'reply' ? (
                    <Reply className="h-4 w-4 text-green-600" />
                  ) : (
                    <MessageSquare className="h-4 w-4 text-blue-600" />
                  )}
                  <Calendar className="h-4 w-4" />
                  <span>{formatTimestamp(post.timestamp)}</span>
                </div>
                <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                  post.type === 'reply' 
                    ? 'bg-green-100 text-green-800' 
                    : 'bg-blue-100 text-blue-800'
                }`}>
                  {post.type === 'reply' ? 'Reply' : 'Original Post'}
                </span>
              </div>
              
              {/* View Tweet Button */}
              {post.tweet_url && (
                <button 
                  onClick={() => handleViewTweet(post)}
                  className="text-gray-400 hover:text-blue-600 transition-colors duration-150 flex items-center space-x-1 text-sm"
                  title="View on Twitter"
                >
                  <ExternalLink className="h-4 w-4" />
                  <span className="hidden sm:inline">View Tweet</span>
                </button>
              )}
            </div>

            {/* For replies, show the original tweet context */}
            {post.type === 'reply' && post.replied_to && (
              <div className="mb-3 p-3 bg-gray-50 rounded-lg border-l-2 border-gray-300">
                <div className="flex items-center justify-between mb-2">
                  <p className="text-xs text-gray-500 font-medium">Replying to @{post.replied_to.author}:</p>
                  <button
                    onClick={() => handleViewOriginalTweet(post.replied_to)}
                    className="text-xs text-blue-600 hover:text-blue-800 underline flex items-center space-x-1"
                  >
                    <ExternalLink className="h-3 w-3" />
                    <span>View Original</span>
                  </button>
                </div>
                <p className="text-sm text-gray-700 italic">"{post.replied_to.content}"</p>
              </div>
            )}
            
            {/* Main content */}
            <p className="text-gray-900 mb-3 leading-relaxed font-medium">{post.content}</p>
            
            {/* Topics (mainly for original posts) */}
            {post.topics && post.topics.length > 0 && (
              <div className="flex flex-wrap gap-2 mb-4">
                {post.topics.map((topic, index) => (
                  <span 
                    key={index} 
                    className="px-2 py-1 bg-blue-50 text-blue-700 text-xs font-medium rounded-full"
                  >
                    #{topic}
                  </span>
                ))}
              </div>
            )}
            
            {/* Engagement metrics */}
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

            {/* Status indicator for new posts */}
            {formatTimestamp(post.timestamp) === 'Just now' && (
              <div className="mt-3 pt-3 border-t border-gray-100">
                <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                  <div className="w-2 h-2 bg-green-400 rounded-full mr-2 animate-pulse"></div>
                  Just posted
                </span>
              </div>
            )}
          </div>
        ))}
      </div>
      
      {/* Load more button */}
      <div className="mt-6 pt-4 border-t border-gray-200">
        <button 
          onClick={loadMorePosts}
          disabled={loadingMore}
          className="w-full text-center text-blue-600 hover:text-blue-700 font-medium text-sm transition-colors duration-150 flex items-center justify-center space-x-2"
        >
          {loadingMore ? (
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