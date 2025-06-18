import React, { useState } from 'react';
import { Play, MessageSquare, RefreshCw, AlertCircle } from 'lucide-react';
import { apiCall } from '../hooks/useApi';

const TestButtons: React.FC = () => {
  const [loading, setLoading] = useState<string | null>(null);
  const [results, setResults] = useState<any[]>([]);
  const [generatedContent, setGeneratedContent] = useState<string | null>(null);

  const addResult = (test: string, result: any, success: boolean) => {
    setResults(prev => [...prev, {
      test,
      result,
      success,
      timestamp: new Date().toLocaleTimeString()
    }]);
  };

  const testGenerateContent = async () => {
    try {
      setLoading('generate');
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
        console.log('💾 Stored generated content for reuse:', content);
        
        addResult('Generate Content', { 
          content: content,
          stored_for_reuse: true 
        }, true);
      } else {
        addResult('Generate Content', result, false);
      }
    } catch (error) {
      console.error('❌ Content generation failed:', error);
      addResult('Generate Content', error instanceof Error ? error.message : error, false);
    } finally {
      setLoading(null);
    }
  };

  const testPostToInstagram = async () => {
    try {
      setLoading('post');
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
        console.log('🧹 Cleared stored content after successful post');
      }
      
      addResult('Post to Instagram', { 
        content_used: contentToPost,
        was_reused: generatedContent !== null,
        post_result: result 
      }, result.success || false);
      
    } catch (error) {
      console.error('❌ Instagram posting failed:', error);
      addResult('Post to Instagram', error instanceof Error ? error.message : error, false);
    } finally {
      setLoading(null);
    }
  };

  const clearResults = () => {
    setResults([]);
    setGeneratedContent(null);
    console.log('🧹 Cleared all results and stored content');
  };

  return (
    <div className="bg-white rounded-xl p-6 shadow-sm">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">Content Test Buttons</h3>
        {(results.length > 0 || generatedContent) && (
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

      {results.length > 0 && (
        <div className="space-y-2">
          <h4 className="text-sm font-medium text-gray-700">Recent Results:</h4>
          <div className="max-h-32 overflow-y-auto space-y-1">
            {results.slice(-2).reverse().map((result, index) => (
              <div
                key={index}
                className={`p-2 rounded text-xs ${
                  result.success
                    ? 'bg-green-50 border border-green-200'
                    : 'bg-red-50 border border-red-200'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="font-medium">{result.test}</span>
                  <span className="text-xs text-gray-500">{result.timestamp}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default TestButtons;