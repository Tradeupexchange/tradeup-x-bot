import React, { useState, useEffect } from 'react';
import { AlertCircle, CheckCircle, RefreshCw, ExternalLink, Info, Globe, AlertTriangle, Server } from 'lucide-react';

const ConnectionTest: React.FC = () => {
  const [status, setStatus] = useState<'testing' | 'connected' | 'error'>('testing');
  const [error, setError] = useState<string | null>(null);
  const [apiUrl, setApiUrl] = useState<string>('');
  const [testResults, setTestResults] = useState<any[]>([]);
  const [railwayStatus, setRailwayStatus] = useState<'unknown' | 'healthy' | 'unhealthy'>('unknown');
  const [corsIssues, setCorsIssues] = useState<boolean>(false);

  useEffect(() => {
    const railwayUrl = import.meta.env.VITE_RAILWAY_API_URL;
    const normalizedUrl = railwayUrl ? normalizeUrl(railwayUrl) : 'Not set';
    setApiUrl(normalizedUrl);
    testConnection();
  }, []);

  const normalizeUrl = (url: string): string => {
    // Remove any trailing slashes
    url = url.replace(/\/+$/, '');
    
    // Add https:// if no protocol specified
    if (!url.startsWith('http://') && !url.startsWith('https://')) {
      url = `https://${url}`;
    }
    
    return url;
  };

  const testRailwayHealth = async (baseUrl: string) => {
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
  };

  const testConnection = async () => {
    setStatus('testing');
    setError(null);
    setTestResults([]);
    setCorsIssues(false);

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
        throw new Error('Railway server appears to be down or unreachable');
      }

      const tests = [
        { name: 'Health Check', endpoint: '/health', critical: true },
        { name: 'Root Endpoint', endpoint: '/', critical: true },
        { name: 'Bot Status', endpoint: '/api/bot-status', critical: false },
        { name: 'Metrics', endpoint: '/api/metrics', critical: false },
        { name: 'Settings', endpoint: '/api/settings', critical: false }
      ];

      const results = [];
      let corsDetected = false;

      for (const test of tests) {
        try {
          const url = `${normalizedUrl}${test.endpoint}`;
          console.log(`🧪 Testing ${test.name}:`, url);
          
          // Try with CORS first
          let response;
          let corsError = false;
          
          try {
            response = await fetch(url, {
              method: 'GET',
              headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
              },
              mode: 'cors',
              credentials: 'omit',
            });
          } catch (corsErr) {
            console.warn(`CORS error for ${test.name}:`, corsErr);
            corsError = true;
            corsDetected = true;
            
            // Try with no-cors as fallback
            try {
              response = await fetch(url, {
                method: 'GET',
                mode: 'no-cors',
              });
            } catch (noCorsErr) {
              throw noCorsErr;
            }
          }

          console.log(`📡 ${test.name} response:`, {
            status: response.status,
            ok: response.ok,
            type: response.type,
            headers: Object.fromEntries(response.headers.entries())
          });

          let data = 'Response received';
          
          // Only try to parse JSON if we have CORS access
          if (response.type !== 'opaque') {
            try {
              if (response.headers.get('content-type')?.includes('application/json')) {
                data = await response.json();
              } else {
                data = await response.text();
              }
            } catch (parseError) {
              data = 'Could not parse response';
            }
          }
          
          results.push({
            name: test.name,
            endpoint: test.endpoint,
            status: response.ok || response.type === 'opaque' ? 'success' : 'error',
            statusCode: response.status || (response.type === 'opaque' ? 'CORS-blocked' : 0),
            data: response.ok ? 'OK' : (corsError ? 'CORS issue detected' : (typeof data === 'string' ? data : JSON.stringify(data))),
            url: url,
            critical: test.critical,
            corsIssue: corsError
          });

          console.log(`${response.ok || response.type === 'opaque' ? '✅' : '❌'} ${test.name}:`, response.status, corsError ? 'CORS blocked' : 'OK');
        } catch (err) {
          console.error(`❌ ${test.name} failed:`, err);
          results.push({
            name: test.name,
            endpoint: test.endpoint,
            status: 'error',
            statusCode: 0,
            data: err instanceof Error ? err.message : 'Network error',
            url: `${normalizedUrl}${test.endpoint}`,
            critical: test.critical,
            corsIssue: false
          });
        }
      }

      setTestResults(results);
      setCorsIssues(corsDetected);

      // Check if all critical tests passed
      const criticalTests = results.filter(r => r.critical);
      const allCriticalPassed = criticalTests.every(r => r.status === 'success');

      if (allCriticalPassed) {
        setStatus('connected');
        console.log('✅ All critical tests passed - connection successful');
        if (corsDetected) {
          setError('Connection successful but CORS issues detected. Some endpoints may not work properly in production.');
        }
      } else {
        setStatus('error');
        const failedCritical = criticalTests.filter(r => r.status === 'error');
        setError(`Critical endpoints failed: ${failedCritical.map(r => r.name).join(', ')}`);
        console.error('❌ Critical tests failed');
      }

    } catch (err) {
      console.error('❌ Connection test failed:', err);
      setError(err instanceof Error ? err.message : 'Unknown error');
      setStatus('error');
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
    <div className="bg-white rounded-xl p-6 shadow-sm mb-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-2">
          <Globe className="h-5 w-5 text-blue-600" />
          <h3 className="text-lg font-semibold text-gray-900">Railway Backend Connection</h3>
        </div>
        <div className="flex items-center space-x-2">
          {apiUrl && apiUrl !== 'Not set' && (
            <>
              <a
                href={`${apiUrl}/docs`}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center space-x-1 px-3 py-1 bg-gray-100 text-gray-700 rounded hover:bg-gray-200 text-sm"
              >
                <ExternalLink className="h-3 w-3" />
                <span>API Docs</span>
              </a>
              <a
                href={apiUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center space-x-1 px-3 py-1 bg-purple-100 text-purple-700 rounded hover:bg-purple-200 text-sm"
              >
                <Server className="h-3 w-3" />
                <span>Direct Test</span>
              </a>
            </>
          )}
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
          <span className="text-sm font-mono bg-gray-100 px-2 py-1 rounded break-all">
            {apiUrl}
          </span>
        </div>

        <div className="flex items-center justify-between">
          <span className="text-sm text-gray-600">Server Status:</span>
          <div className="flex items-center space-x-2">
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
              </>
            )}
            {railwayStatus === 'unknown' && (
              <span className="text-sm text-gray-600">Unknown</span>
            )}
          </div>
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
              {corsIssues && (
                <div className="flex items-center space-x-1">
                  <AlertTriangle className="h-4 w-4 text-yellow-500" />
                  <span className="text-yellow-600 text-sm">CORS issues detected</span>
                </div>
              )}
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
                <div key={index} className="flex items-center justify-between text-sm p-2 bg-gray-50 rounded">
                  <div className="flex items-center space-x-2">
                    <span className={`text-gray-600 ${result.critical ? 'font-medium' : ''}`}>
                      {result.name} {result.critical && '(Critical)'}
                    </span>
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
                    <span className="font-mono text-xs bg-white px-1 rounded">
                      {result.endpoint}
                    </span>
                    <span className={`px-2 py-1 rounded text-xs ${getStatusColor(result.status)}`}>
                      {result.statusCode} {result.corsIssue && '(CORS)'}
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
              <p><strong>Troubleshooting Steps:</strong></p>
              <ol className="list-decimal list-inside mt-1 space-y-1">
                <li>Click "Direct" button above to test Railway app directly in browser</li>
                <li>Check Railway deployment logs for startup errors</li>
                <li>Verify your backend server is configured to accept CORS requests</li>
                <li>Ensure Railway app has proper PORT environment variable set</li>
                <li>Check if Railway service is sleeping (hobby plan limitation)</li>
                <li>Verify all environment variables are set in Railway dashboard</li>
                <li>Test API endpoints manually using the "API Docs" link</li>
              </ol>
            </div>
          </div>
        )}

        {corsIssues && (
          <div className="mt-3 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
            <div className="flex items-start space-x-2">
              <AlertTriangle className="h-4 w-4 text-yellow-600 mt-0.5" />
              <div className="text-xs text-yellow-700">
                <p><strong>CORS Issues Detected:</strong></p>
                <p>Your backend server needs to be configured to allow cross-origin requests. Add these headers to your Railway backend:</p>
                <div className="mt-2 p-2 bg-yellow-100 rounded font-mono text-xs">
                  Access-Control-Allow-Origin: {window.location.origin}<br/>
                  Access-Control-Allow-Methods: GET, POST, PUT, DELETE<br/>
                  Access-Control-Allow-Headers: Content-Type, Authorization
                </div>
              </div>
            </div>
          </div>
        )}

        <div className="mt-3 p-3 bg-blue-50 border border-blue-200 rounded-lg">
          <div className="flex items-start space-x-2">
            <Info className="h-4 w-4 text-blue-600 mt-0.5" />
            <div className="text-xs text-blue-700">
              <p><strong>Debug Information:</strong></p>
              <div className="grid grid-cols-2 gap-2 mt-1">
                <div>Environment: {import.meta.env.MODE}</div>
                <div>Dev Mode: {import.meta.env.DEV ? 'Yes' : 'No'}</div>
                <div>Raw URL: {import.meta.env.VITE_RAILWAY_API_URL || 'Not set'}</div>
                <div>Normalized URL: {apiUrl}</div>
                <div>Expected Format: https://your-app.up.railway.app</div>
                <div>Railway Status: {railwayStatus}</div>
                <div>CORS Issues: {corsIssues ? 'Yes' : 'No'}</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ConnectionTest;