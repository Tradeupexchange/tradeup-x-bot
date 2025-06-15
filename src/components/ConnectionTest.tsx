import React, { useState, useEffect } from 'react';
import { AlertCircle, CheckCircle, RefreshCw, ExternalLink, Info, Globe } from 'lucide-react';

const ConnectionTest: React.FC = () => {
  const [status, setStatus] = useState<'testing' | 'connected' | 'error'>('testing');
  const [error, setError] = useState<string | null>(null);
  const [apiUrl, setApiUrl] = useState<string>('');
  const [testResults, setTestResults] = useState<any[]>([]);

  useEffect(() => {
    const railwayUrl = import.meta.env.VITE_RAILWAY_API_URL;
    setApiUrl(railwayUrl || 'Not set');
    testConnection();
  }, []);

  const testConnection = async () => {
    setStatus('testing');
    setError(null);
    setTestResults([]);

    try {
      const railwayUrl = import.meta.env.VITE_RAILWAY_API_URL;
      
      if (!railwayUrl) {
        throw new Error('VITE_RAILWAY_API_URL environment variable not set');
      }

      console.log('🔧 Testing connection to:', railwayUrl);

      const tests = [
        { name: 'Health Check', endpoint: '/health' },
        { name: 'Root Endpoint', endpoint: '/' },
        { name: 'Bot Status', endpoint: '/api/bot-status' },
        { name: 'Metrics', endpoint: '/api/metrics' },
        { name: 'Settings', endpoint: '/api/settings' }
      ];

      const results = [];

      for (const test of tests) {
        try {
          const url = `${railwayUrl}${test.endpoint}`;
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

          console.log(`📡 ${test.name} response:`, {
            status: response.status,
            ok: response.ok,
            headers: Object.fromEntries(response.headers.entries())
          });

          let data;
          try {
            data = await response.json();
          } catch (jsonError) {
            data = await response.text();
          }
          
          results.push({
            name: test.name,
            endpoint: test.endpoint,
            status: response.ok ? 'success' : 'error',
            statusCode: response.status,
            data: response.ok ? 'OK' : (data?.detail || data || 'Error'),
            url: url
          });

          console.log(`${response.ok ? '✅' : '❌'} ${test.name}:`, response.status, data);
        } catch (err) {
          console.error(`❌ ${test.name} failed:`, err);
          results.push({
            name: test.name,
            endpoint: test.endpoint,
            status: 'error',
            statusCode: 0,
            data: err instanceof Error ? err.message : 'Network error',
            url: `${railwayUrl}${test.endpoint}`
          });
        }
      }

      setTestResults(results);

      // Check if all critical tests passed
      const criticalTests = results.filter(r => ['Health Check', 'Root Endpoint'].includes(r.name));
      const allCriticalPassed = criticalTests.every(r => r.status === 'success');

      if (allCriticalPassed) {
        setStatus('connected');
        console.log('✅ All critical tests passed - connection successful');
      } else {
        setStatus('error');
        setError('Some critical endpoints failed');
        console.error('❌ Critical tests failed');
      }

    } catch (err) {
      console.error('❌ Connection test failed:', err);
      setError(err instanceof Error ? err.message : 'Unknown error');
      setStatus('error');
    }
  };

  return (
    <div className="bg-white rounded-xl p-6 shadow-sm mb-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-2">
          <Globe className="h-5 w-5 text-blue-600" />
          <h3 className="text-lg font-semibold text-gray-900">Backend Connection Status</h3>
        </div>
        <div className="flex items-center space-x-2">
          <a
            href={`${apiUrl}/docs`}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center space-x-1 px-3 py-1 bg-gray-100 text-gray-700 rounded hover:bg-gray-200 text-sm"
          >
            <ExternalLink className="h-3 w-3" />
            <span>API Docs</span>
          </a>
          <button
            onClick={testConnection}
            disabled={status === 'testing'}
            className="flex items-center space-x-2 px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
          >
            <RefreshCw className={`h-4 w-4 ${status === 'testing' ? 'animate-spin' : ''}`} />
            <span>Test</span>
          </button>
        </div>
      </div>

      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <span className="text-sm text-gray-600">Railway URL:</span>
          <span className="text-sm font-mono bg-gray-100 px-2 py-1 rounded">
            {apiUrl}
          </span>
        </div>

        <div className="flex items-center space-x-2">
          {status === 'testing' && (
            <>
              <RefreshCw className="h-5 w-5 text-blue-500 animate-spin" />
              <span className="text-blue-600">Testing connection...</span>
            </>
          )}
          {status === 'connected' && (
            <>
              <CheckCircle className="h-5 w-5 text-green-500" />
              <span className="text-green-600">Connected successfully!</span>
            </>
          )}
          {status === 'error' && (
            <>
              <AlertCircle className="h-5 w-5 text-red-500" />
              <span className="text-red-600">Connection issues detected</span>
            </>
          )}
        </div>

        {testResults.length > 0 && (
          <div className="mt-4">
            <h4 className="text-sm font-medium text-gray-700 mb-2">Endpoint Tests:</h4>
            <div className="space-y-2">
              {testResults.map((result, index) => (
                <div key={index} className="flex items-center justify-between text-sm">
                  <div className="flex items-center space-x-2">
                    <span className="text-gray-600">{result.name}</span>
                    <a
                      href={result.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-blue-500 hover:text-blue-700"
                    >
                      <ExternalLink className="h-3 w-3" />
                    </a>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className="font-mono text-xs bg-gray-100 px-1 rounded">
                      {result.endpoint}
                    </span>
                    <span className={`px-2 py-1 rounded text-xs ${
                      result.status === 'success' 
                        ? 'bg-green-100 text-green-800' 
                        : 'bg-red-100 text-red-800'
                    }`}>
                      {result.statusCode} {result.status}
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
            <div className="mt-2 text-xs text-red-600">
              <p><strong>Troubleshooting:</strong></p>
              <ul className="list-disc list-inside mt-1 space-y-1">
                <li>Check if Railway backend is deployed and running</li>
                <li>Verify VITE_RAILWAY_API_URL is set correctly in Netlify</li>
                <li>Ensure Railway app is publicly accessible</li>
                <li>Check Railway logs for any startup errors</li>
                <li>Visit the API docs link above to test endpoints manually</li>
                <li>Check browser console for CORS errors</li>
                <li>Try accessing the Railway URL directly in a new tab</li>
              </ul>
            </div>
          </div>
        )}

        <div className="mt-3 p-3 bg-blue-50 border border-blue-200 rounded-lg">
          <div className="flex items-start space-x-2">
            <Info className="h-4 w-4 text-blue-600 mt-0.5" />
            <div className="text-xs text-blue-700">
              <p><strong>Debug Info:</strong></p>
              <p>Environment: {import.meta.env.MODE}</p>
              <p>Dev Mode: {import.meta.env.DEV ? 'Yes' : 'No'}</p>
              <p>API URL Set: {import.meta.env.VITE_RAILWAY_API_URL ? 'Yes' : 'No'}</p>
              <p>CORS Mode: cors</p>
              <p>Credentials: omit</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ConnectionTest;