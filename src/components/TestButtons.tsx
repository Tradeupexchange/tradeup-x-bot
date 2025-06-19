import React, { useState } from 'react';
import { Play, MessageSquare, RefreshCw, ExternalLink } from 'lucide-react';
import { apiCall } from '../hooks/useApi';

const TestButtons: React.FC = () => {
  const [loading, setLoading] = useState<string | null>(null);
  const [generatedContent, setGeneratedContent] = useState<string | null>(null);
  const [lastGeneratedContent, setLastGeneratedContent] = useState<string | null>(null);
  const [postResult, setPostResult] = useState<{ content: string; link?: string } | null>(null);

  const testGenerateContent = async () => {
    try {
      setLoading('generate');
      setLastGeneratedContent(null);
      console.log('🧪 Testing content generation...');
      
      const result = await apiCall('/api/generate-content', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          topic: 'Pokemon TCG',
          count: 1
        })
      });
      
      console.log('✅ Content generation result:', result);
      
      if (result.success && result.content) {
        const content = result.content.optimized_content || result.content.content || result.content;
        setGeneratedContent(content);
        setLastGeneratedContent(content);
        console.log('💾 Stored generated content for reuse:', content);
      } else {
        setLastGeneratedContent('Failed to generate content');
      }
    } catch (error) {
      console.error('❌ Content generation failed:', error);
      setLastGeneratedContent(error instanceof Error ? error.message : 'Unknown error');
    } finally {
      setLoading(null);
    }
  };

  const testPostToInstagram = async () => {
    try {
      setLoading('post');
      setPostResult(null);
      let contentToPost = generatedContent;
      
      if (!contentToPost) {
        console.log('📝 No existing content, generating new content...');
        
        const contentResult = await apiCall('/api/generate-content', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            topic: `Pokemon TCG ${Date.now()}`,
            count: 1
          })
        });
        
        console.log('✅ Content generated for posting:', contentResult);
        
        if (contentResult.success && contentResult.content) {
          contentToPost = contentResult.content.optimized_content || contentResult.content.content || contentResult.content;
          setGeneratedContent(contentToPost);
        } else {
          throw new Error('Failed to generate content for posting');
        }
      } else {
        console.log('♻️ Reusing previously generated content:', contentToPost);
      }
      
      console.log('📸 Posting to Instagram:', contentToPost);
      
      const result = await apiCall('/api/post-to-twitter', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          content: contentToPost
        })
      });
      
      console.log('✅ Instagram post result:', result);
      
      if (result.success) {
        setGeneratedContent(null);
        setPostResult({
          content: contentToPost,
          link: result.tweet_url || result.url || result.link
        });
        console.log('🧹 Cleared stored content after successful post');
      } else {
        setPostResult({
          content: contentToPost,
          link: undefined
        });
      }
      
    } catch (error) {
      console.error('❌ Instagram posting failed:', error);
      setPostResult({
        content: 'Failed to post',
        link: undefined
      });
    } finally {
      setLoading(null);
    }
  };

  const clearResults = () => {
    setGeneratedContent(null);
    setLastGeneratedContent(null);
    setPostResult(null);
    console.log('🧹 Cleared all results and stored content');
  };

  return (
    <div className="bg-white rounded-xl p-6 shadow-sm">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">Content Test Buttons</h3>
        {(generatedContent || lastGeneratedContent || postResult) && (
          <button
            onClick={clearResults}
            className="text-sm text-gray-500 hover:text-gray-700"
          >
            Clear All
          </button>
        )}
      </div>
      
      {generatedContent && (
        <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
          <p className="text-sm text-blue-800">
            <strong>Content ready for posting</strong>
          </p>
        </div>
      )}
      
      <div className="grid grid-cols-2 gap-4 mb-4">
        <button
          onClick={testGenerateContent}
          disabled={loading === 'generate'}
          className="flex items-center justify-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors duration-200"
        >
          {loading === 'generate' ? (
            <RefreshCw className="h-4 w-4 animate-spin" />
          ) : (
            <MessageSquare className="h-4 w-4" />
          )}
          <span className="font-medium">Generate</span>
        </button>

        <button
          onClick={testPostToInstagram}
          disabled={loading === 'post'}
          className="flex items-center justify-center space-x-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 transition-colors duration-200"
        >
          {loading === 'post' ? (
            <RefreshCw className="h-4 w-4 animate-spin" />
          ) : (
            <Play className="h-4 w-4" />
          )}
          <span className="font-medium">
            {generatedContent ? 'Post' : 'Gen + Post'}
          </span>
        </button>
      </div>

      {/* Display generated content */}
      {lastGeneratedContent && (
        <div className="mb-4 p-3 bg-gray-50 border border-gray-200 rounded-lg">
          <h4 className="text-sm font-medium text-gray-700 mb-2">Generated Content:</h4>
          <p className="text-sm text-gray-800 whitespace-pre-wrap">
            {lastGeneratedContent}
          </p>
        </div>
      )}

      {/* Display post result */}
      {postResult && (
        <div className="mb-4 p-3 bg-green-50 border border-green-200 rounded-lg">
          <h4 className="text-sm font-medium text-green-700 mb-2">Posted to your account:</h4>
          <p className="text-sm text-green-800 mb-2">"{postResult.content}"</p>
          {postResult.link && (
            <a
              href={postResult.link}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center space-x-1 text-sm text-blue-600 hover:text-blue-800"
            >
              <span>View tweet</span>
              <ExternalLink className="h-3 w-3" />
            </a>
          )}
          {!postResult.link && (
            <p className="text-sm text-yellow-600">Post may have succeeded but no link was returned</p>
          )}
        </div>
      )}
    </div>
  );
};

export default TestButtons;