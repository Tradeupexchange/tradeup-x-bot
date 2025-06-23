import React, { useState, useEffect, useCallback } from 'react';
import { AlertCircle, CheckCircle, RefreshCw, Globe } from 'lucide-react';

const ConnectionTest: React.FC = () => {
  const [status, setStatus] = useState<'testing' | 'connected' | 'error'>('testing');
  const [error, setError] = useState<string | null>(null);
  const [testResults, setTestResults] = useState<any[]>([]);
  const [railwayStatus, setRailwayStatus] = useState<'unknown' | 'healthy' | 'unhealthy'>('unknown');
  const [manualTest, setManualTest] = useState<boolean>(false);
  const [showErrorDetails, setShowErrorDetails] = useState<boolean>(false);

  const normalizeUrl = useCallback((url: string): string => {
    // Remove any trailing slashes
    url = url.replace(/\/+$/, '');
    
    // Add https:// if no protocol specified
    if (!url.startsWith('http://') && !url.startsWith('https://')) {
      url = `https://${url}`;
    }
    
    return url;
  }, []);

  const testRailwayHealth = useCallback(async (baseUrl: string) => {
    try {
      const normalizedUrl = normalizeUrl(baseUrl);
      console.log('Testing normalized URL:', normalizedUrl);
      
      // Test basic connectivity first
      const response = await fetch(normalizedUrl, {
        method: 'GET',
        mode: 'no-cors', // Try without CORS first to see if server is responding
      });
      
      // If no-cors works, server is up but may have CORS issues
      setRailwayStatus('healthy');
      return true;
    } catch (err) {
      console.error('Railway health check failed:', err);
      setRailwayStatus('unhealthy');
      return false;
    }
  }, [normalizeUrl]);

  const testConnection = useCallback(async (isManual: boolean = false) => {
    setStatus('testing');
    setError(null);
    setTestResults([]);
    setShowErrorDetails(false);
    
    if (isManual) {
      setManualTest(true);
    }

    try {
      const railwayUrl = import.meta.env.VITE_RAILWAY_API_URL;
      
      if (!railwayUrl) {
        throw new Error('VITE_RAILWAY_API_URL environment variable not set. Please check your Netlify environment variables.');
      }

      const normalizedUrl = normalizeUrl(railwayUrl);
      console.log('🔧 Testing connection to normalized URL:', normalizedUrl);

      // First, test if Railway server is responding at all
      const isServerHealthy = await testRailwayHealth(normalizedUrl);
      
      if (!isServerHealthy) {
        // If server is not healthy, run detailed endpoint tests for error details
        const tests = [
          { name: 'Health Check', endpoint: '/health', critical: true },
          { name: 'Root Endpoint', endpoint: '/', critical: true },
          { name: 'Bot Status', endpoint: '/api/bot-status', critical: false },
          { name: 'Metrics', endpoint: '/api/metrics', critical: false },
          { name: 'Settings', endpoint: '/api/settings', critical: false }
        ];

        const results = [];
        
        for (const test of tests) {
          try {
            const url = `${normalizedUrl}${test.endpoint}`;
            console.log(`🧪 Testing ${test.name}:`, url);
            
            const response = await fetch(url, {
              method: 'GET',
              headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
              },
              mode: 'cors',
              credentials: 'omit',
            });

            results.push({
              name: test.name,
              endpoint: test.endpoint,
              status: response.ok ? 'success' : 'error',
              statusCode: response.status,
              critical: test.critical
            });

          } catch (err) {
            console.error(`❌ ${test.name} failed:`, err);
            results.push({
              name: test.name,
              endpoint: test.endpoint,
              status: 'error',
              statusCode: 0,
              data: err instanceof Error ? err.message : 'Network error',
              critical: test.critical
            });
          }
        }

        setTestResults(results);
        throw new Error('Railway server appears to be down or unreachable');
      }

      // If server is healthy, we're done
      setStatus('connected');
      console.log('✅ Server is responding - connection successful');

    } catch (err) {
      console.error('❌ Connection test failed:', err);
      setError(err instanceof Error ? err.message : 'Unknown error');
      setStatus('error');
    } finally {
      setManualTest(false);
    }
  }, [normalizeUrl, testRailwayHealth]);

  // Initialize and run initial test
  useEffect(() => {
    console.log('🚀 ConnectionTest: Running initial connection test...');
    testConnection(false);
  }, [testConnection]);

  const handleManualTest = () => {
    console.log('🔄 ConnectionTest: Manual test triggered by user');
    testConnection(true);
  };

  const handleStatusClick = () => {
    if (railwayStatus === 'unhealthy' && testResults.length > 0) {
      setShowErrorDetails(!showErrorDetails);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'success': return 'bg-green-100 text-green-800';
      case 'error': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="bg-white rounded-xl p-6 shadow-sm h-full flex flex-col">
      {/* Header with icon, title, and server status */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-2">
          <Globe className="h-5 w-5 text-blue-600" />
          <h3 className="text-lg font-semibold text-gray-900">Backend Connection</h3>
        </div>
        
        {/* Server Status - pushed to the right */}
        <div 
          className={`flex items-center space-x-2 ${
            railwayStatus === 'unhealthy' ? 'cursor-pointer hover:opacity-80' : ''
          }`}
          onClick={handleStatusClick}
        >
          <span className="text-sm text-gray-600">Server Status:</span>
          {railwayStatus === 'healthy' && (
            <>
              <CheckCircle className="h-4 w-4 text-green-500" />
              <span className="text-sm text-green-600">Responding</span>
            </>
          )}
          {railwayStatus === 'unhealthy' && (
            <>
              <AlertCircle className="h-4 w-4 text-red-500" />
              <span className="text-sm text-red-600">Not Responding</span>
              {testResults.length > 0 && (
                <span className="text-xs text-gray-500">(click for details)</span>
              )}
            </>
          )}
          {railwayStatus === 'unknown' && (
            <span className="text-sm text-gray-600">Unknown</span>
          )}
        </div>
      </div>

      {/* Content area that grows to push button to bottom */}
      <div className="flex-1 space-y-3">
        {/* Status indicators */}
        <div className="flex items-center space-x-2">
          {status === 'testing' && (
            <>
              <RefreshCw className="h-5 w-5 text-blue-500 animate-spin" />
              <span className="text-blue-600">
                {manualTest ? 'Running manual test...' : 'Testing connection...'}
              </span>
            </>
          )}
          {status === 'error' && (
            <>
              <AlertCircle className="h-5 w-5 text-red-500" />
              <span className="text-red-600">Connection issues detected</span>
            </>
          )}
        </div>

        {/* Error details - only shown when server is not responding and user clicks */}
        {showErrorDetails && railwayStatus === 'unhealthy' && testResults.length > 0 && (
          <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg">
            <h4 className="text-sm font-medium text-red-700 mb-2">Failed Endpoints:</h4>
            <div className="space-y-1">
              {testResults.filter(result => result.status === 'error').map((result, index) => (
                <div key={index} className="flex items-center justify-between text-sm">
                  <span className={`text-red-600 ${result.critical ? 'font-medium' : ''}`}>
                    {result.name} {result.critical && '(Critical)'}
                  </span>
                  <div className="flex items-center space-x-2">
                    <span className="font-mono text-xs bg-white px-1 rounded">
                      {result.endpoint}
                    </span>
                    <span className={`px-2 py-1 rounded text-xs ${getStatusColor(result.status)}`}>
                      {result.statusCode || 'Failed'}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {error && (
          <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-sm text-red-700">
              <strong>Error:</strong> {error}
            </p>
          </div>
        )}
      </div>

      {/* Test button centered at bottom - matching Generate Content button size */}
      <div className="flex justify-center mt-6">
        <button
          onClick={handleManualTest}
          disabled={status === 'testing'}
          className="flex items-center justify-center space-x-2 px-8 py-3 bg-blue-600 text-white text-base font-medium rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors duration-200 min-w-[200px]"
        >
          <RefreshCw className={`h-5 w-5 ${status === 'testing' ? 'animate-spin' : ''}`} />
          <span>{manualTest ? 'Testing...' : 'Test Connection'}</span>
        </button>
      </div>
    </div>
  );
};

export default ConnectionTest;