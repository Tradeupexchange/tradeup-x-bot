import React, { useState } from 'react';
import { Play, MessageSquare, Settings, RefreshCw, AlertCircle } from 'lucide-react';
import { apiCall } from '../hooks/useApi';

const TestButtons: React.FC = () => {
  const [loading, setLoading] = useState<string | null>(null);
  const [results, setResults] = useState<any[]>([]);

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
      addResult('Generate Content', result, true);
    } catch (error) {
      console.error('❌ Content generation failed:', error);
      addResult('Generate Content', error instanceof Error ? error.message : error, false);
    } finally {
      setLoading(null);
    }
  };

  const testPostToTwitter = async () => {
    try {
      setLoading('post');
      console.log('🧪 Testing Twitter posting...');
      
      // First generate unique content
      console.log('📝 Generating unique content...');
      const contentResult = await apiCall('/api/generate-content', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          topic: `Pokemon TCG Test ${Date.now()}`,
          count: 1
        })
      });
      
      console.log('✅ Content generated:', contentResult);
      
      if (contentResult.success && contentResult.content) {
        // Use the generated content for posting
        const postContent = contentResult.content.optimized_content || contentResult.content.content || contentResult.content;
        
        console.log('🐦 Posting to Twitter:', postContent);
        
        const result = await apiCall('/api/post-to-twitter', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            content: postContent
          })
        });
        
        console.log('✅ Twitter post result:', result);
        
        addResult('Post to Twitter', { 
          generated_content: postContent,
          post_result: result 
        }, result.success || false);
      } else {
        throw new Error('Failed to generate content for posting');
      }
    } catch (error) {
      console.error('❌ Twitter posting failed:', error);
      addResult('Post to Twitter', error instanceof Error ? error.message : error, false);
    } finally {
      setLoading(null);
    }
  };

  const testCreateJob = async () => {
    try {
      setLoading('job');
      console.log('🧪 Testing job creation...');
      
      const result = await apiCall('/api/bot-job/create', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          type: 'posting',
          settings: {
            postsPerDay: 5,
            postingHours: { start: 9, end: 17 },
            contentTypes: {
              cardPulls: true,
              deckBuilding: false,
              marketAnalysis: true,
              tournaments: false
            }
          }
        })
      });
      
      console.log('✅ Job creation result:', result);
      addResult('Create Job', result, result.success || false);
    } catch (error) {
      console.error('❌ Job creation failed:', error);
      addResult('Create Job', error instanceof Error ? error.message : error, false);
    } finally {
      setLoading(null);
    }
  };

  const testUpdateSettings = async () => {
    try {
      setLoading('settings');
      console.log('🧪 Testing settings update...');
      
      const result = await apiCall('/api/settings', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          postsPerDay: 15,
          keywords: ['Pokemon', 'TCG', 'Test'],
          engagementMode: 'balanced',
          autoReply: true,
          contentTypes: {
            cardPulls: true,
            deckBuilding: true,
            marketAnalysis: false,
            tournaments: true
          }
        })
      });
      
      console.log('✅ Settings update result:', result);
      addResult('Update Settings', result, result.success || false);
    } catch (error) {
      console.error('❌ Settings update failed:', error);
      addResult('Update Settings', error instanceof Error ? error.message : error, false);
    } finally {
      setLoading(null);
    }
  };

  const clearResults = () => {
    setResults([]);
  };

  return (
    <div className="bg-white rounded-xl p-6 shadow-sm mb-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">API Test Buttons</h3>
        {results.length > 0 && (
          <button
            onClick={clearResults}
            className="text-sm text-gray-500 hover:text-gray-700"
          >
            Clear Results
          </button>
        )}
      </div>
      
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <button
          onClick={testGenerateContent}
          disabled={loading === 'generate'}
          className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
        >
          {loading === 'generate' ? (
            <RefreshCw className="h-4 w-4 animate-spin" />
          ) : (
            <MessageSquare className="h-4 w-4" />
          )}
          <span>Generate</span>
        </button>

        <button
          onClick={testPostToTwitter}
          disabled={loading === 'post'}
          className="flex items-center space-x-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
        >
          {loading === 'post' ? (
            <RefreshCw className="h-4 w-4 animate-spin" />
          ) : (
            <Play className="h-4 w-4" />
          )}
          <span>Post (Unique)</span>
        </button>

        <button
          onClick={testCreateJob}
          disabled={loading === 'job'}
          className="flex items-center space-x-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50"
        >
          {loading === 'job' ? (
            <RefreshCw className="h-4 w-4 animate-spin" />
          ) : (
            <Play className="h-4 w-4" />
          )}
          <span>Create Job</span>
        </button>

        <button
          onClick={testUpdateSettings}
          disabled={loading === 'settings'}
          className="flex items-center space-x-2 px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700 disabled:opacity-50"
        >
          {loading === 'settings' ? (
            <RefreshCw className="h-4 w-4 animate-spin" />
          ) : (
            <Settings className="h-4 w-4" />
          )}
          <span>Settings</span>
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
            <p><strong>Testing Notes:</strong></p>
            <ul className="list-disc list-inside mt-1 space-y-1">
              <li>The "Generate" button tests content generation</li>
              <li>The "Post (Unique)" button generates fresh content then posts to Twitter</li>
              <li>Check browser console for detailed logs</li>
              <li>All requests include proper CORS headers</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TestButtons;