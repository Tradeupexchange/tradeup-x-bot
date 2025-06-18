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
        // Store the generated content for potential reuse
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
      
      // If no generated content exists, generate new content first
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
          setGeneratedContent(contentToPost); // Store for future use
        } else {
          throw new Error('Failed to generate content for posting');
        }
      } else {
        console.log('♻️ Reusing previously generated content:', contentToPost);
      }
      
      console.log('📸 Posting to Instagram:', contentToPost);
      
      // Note: Replace this with actual Instagram API endpoint when available
      // For now, using the Twitter endpoint as placeholder
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
      
      // Clear the stored content after successful posting
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
    <div className="bg-white rounded-xl p-6 shadow-sm mb-6">
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
      
      {/* Status indicator for stored content */}
      {generatedContent && (
        <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
          <p className="text-sm text-blue-800">
            <strong>Content ready:</strong> Generated content is stored and ready for posting
          </p>
          <p className="text-xs text-blue-600 mt-1 truncate">
            Preview: "{generatedContent.substring(0, 80)}..."
          </p>
        </div>
      )}
      
      <div className="grid grid-cols-2 gap-4 mb-6">
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
          <span className="font-medium">Generate</span>
        </button>

        <button
          onClick={testPostToInstagram}
          disabled={loading === 'post'}
          className="flex items-center justify-center space-x-2 px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 transition-colors duration-200"
        >
          {loading === 'post' ? (
            <RefreshCw className="h-5 w-5 animate-spin" />
          ) : (
            <Play className="h-5 w-5" />
          )}
          <span className="font-medium">
            {generatedContent ? 'Post (Stored)' : 'Post (Generate + Post)'}
          </span>
        </button>
      </div>

      {results.length > 0 && (
        <div className="space-y-2">
          <h4 className="text-sm font-medium text-gray-700">Test Results:</h4>
          <div className="max-h-64 overflow-y-auto space-y-2">
            {results.slice().reverse().map((result, index) => (
              <div
                key={index}
                className={`p-3 rounded-lg text-sm ${
                  result.success
                    ? 'bg-green-50 border border-green-200'
                    : 'bg-red-50 border border-red-200'
                }`}
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="font-medium">{result.test}</span>
                  <span className="text-xs text-gray-500">{result.timestamp}</span>
                </div>
                <pre className="text-xs overflow-x-auto whitespace-pre-wrap max-h-32">
                  {typeof result.result === 'string' 
                    ? result.result 
                    : JSON.stringify(result.result, null, 2)
                  }
                </pre>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
        <div className="flex items-start space-x-2">
          <AlertCircle className="h-4 w-4 text-yellow-600 mt-0.5" />
          <div className="text-sm text-yellow-800">
            <p><strong>How it works:</strong></p>
            <ul className="list-disc list-inside mt-1 space-y-1">
              <li><strong>Generate:</strong> Creates content and stores it for reuse</li>
              <li><strong>Post (when content stored):</strong> Uses the stored content to post</li>
              <li><strong>Post (when no content):</strong> Generates new content then posts immediately</li>
              <li>Content is cleared after successful posting or when clicking "Clear All"</li>
              <li>Check browser console for detailed logs</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TestButtons;