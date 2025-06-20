import React, { useState } from 'react';
import { Play, MessageSquare, RefreshCw, ExternalLink, X } from 'lucide-react';
import { apiCall } from '../hooks/useApi';

const TestButtons: React.FC = () => {
  const [loading, setLoading] = useState<string | null>(null);
  const [showPopup, setShowPopup] = useState<boolean>(false);
  const [generatedContent, setGeneratedContent] = useState<string | null>(null);
  const [postResult, setPostResult] = useState<{ content: string; link?: string } | null>(null);

  const testGenerateContent = async () => {
    try {
      setLoading('generate');
      setPostResult(null);
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
        setShowPopup(true);
        console.log('💾 Generated content:', content);
      } else {
        setGeneratedContent('Failed to generate content');
        setShowPopup(true);
      }
    } catch (error) {
      console.error('❌ Content generation failed:', error);
      setGeneratedContent(error instanceof Error ? error.message : 'Unknown error');
      setShowPopup(true);
    } finally {
      setLoading(null);
    }
  };

  const postToTwitter = async () => {
    try {
      setLoading('post');
      console.log('📸 Posting to Twitter:', generatedContent);
      
      const result = await apiCall('/api/post-to-twitter', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          content: generatedContent
        })
      });
      
      console.log('✅ Twitter post result:', result);
      
      if (result.success) {
        setPostResult({
          content: generatedContent || '',
          link: result.tweet_url || result.url || result.link
        });
        console.log('🧹 Post successful');
      } else {
        setPostResult({
          content: generatedContent || '',
          link: undefined
        });
      }
      
    } catch (error) {
      console.error('❌ Twitter posting failed:', error);
      setPostResult({
        content: 'Failed to post',
        link: undefined
      });
    } finally {
      setLoading(null);
    }
  };

  const closePopup = () => {
    setShowPopup(false);
    setGeneratedContent(null);
    setPostResult(null);
  };

  return (
    <>
      <div className="bg-white rounded-xl p-6 shadow-sm">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-3">
            <img 
              src="/x-logo.png" 
              alt="X Logo" 
              className="h-6 w-6"
              onError={(e) => {
                // Fallback to a simple X if logo image fails to load
                e.currentTarget.style.display = 'none';
                e.currentTarget.nextElementSibling!.style.display = 'block';
              }}
            />
            <div 
              className="h-6 w-6 bg-black rounded flex items-center justify-center text-white font-bold text-sm hidden"
            >
              X
            </div>
            <h3 className="text-lg font-semibold text-gray-900">Test X Posting</h3>
          </div>
        </div>
        
        <div className="flex justify-center">
          <button
            onClick={testGenerateContent}
            disabled={loading === 'generate'}
            className="flex items-center justify-center space-x-2 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors duration-200"
          >
            {loading === 'generate' ? (
              <RefreshCw className="h-5 w-5 animate-spin" />
            ) : (
              <MessageSquare className="h-5 w-5" />
            )}
            <span className="font-medium">
              {loading === 'generate' ? 'Generating...' : 'Generate Content'}
            </span>
          </button>
        </div>
      </div>

      {/* Content Preview Popup */}
      {showPopup && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl max-w-2xl w-full max-h-[80vh] overflow-y-auto">
            <div className="p-6 border-b border-gray-200">
              <div className="flex items-center justify-between">
                <h3 className="text-xl font-semibold text-gray-900">Generated Content Preview</h3>
                <button 
                  onClick={closePopup}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>
            </div>

            <div className="p-6">
              {/* Generated content display */}
              <div className="mb-6 p-4 bg-gray-50 border border-gray-200 rounded-lg">
                <h4 className="text-sm font-medium text-gray-700 mb-3">Content to Post:</h4>
                <p className="text-gray-800 whitespace-pre-wrap leading-relaxed">
                  {generatedContent}
                </p>
              </div>

              {/* Post result display */}
              {postResult && (
                <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg">
                  <h4 className="text-sm font-medium text-green-700 mb-2">Posted Successfully!</h4>
                  <p className="text-sm text-green-800 mb-3">"{postResult.content}"</p>
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

              {/* Action buttons */}
              <div className="flex gap-4">
                {!postResult && (
                  <button
                    onClick={postToTwitter}
                    disabled={loading === 'post' || !generatedContent || generatedContent.includes('Failed')}
                    className="flex-1 flex items-center justify-center space-x-2 px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200"
                  >
                    {loading === 'post' ? (
                      <RefreshCw className="h-5 w-5 animate-spin" />
                    ) : (
                      <Play className="h-5 w-5" />
                    )}
                    <span className="font-medium">
                      {loading === 'post' ? 'Posting...' : 'Post to Twitter'}
                    </span>
                  </button>
                )}
                
                <button
                  onClick={closePopup}
                  className="px-6 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors duration-200"
                >
                  {postResult ? 'Close' : 'Cancel'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default TestButtons;