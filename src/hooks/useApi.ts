import { useState, useEffect, useCallback } from 'react';

// Use Railway backend URL for API calls
const API_BASE_URL = import.meta.env.VITE_RAILWAY_API_URL || 'http://localhost:8000';

console.log('🔧 API Configuration:', {
  VITE_RAILWAY_API_URL: import.meta.env.VITE_RAILWAY_API_URL,
  API_BASE_URL,
  isDev: import.meta.env.DEV,
  mode: import.meta.env.MODE
});

interface ApiResponse<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
  refetch: () => void;
}

export const useApi = <T>(endpoint: string, options?: RequestInit): ApiResponse<T> => {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Ensure endpoint starts with /
      const cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
      const url = `${API_BASE_URL}${cleanEndpoint}`;
      
      console.log(`🔄 Fetching: ${url}`);
      
      const response = await fetch(url, {
        method: 'GET',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
        },
        mode: 'cors',
        credentials: 'omit', // Don't send credentials with CORS
        ...options,
      });

      console.log(`📡 Response for ${url}:`, {
        status: response.status,
        statusText: response.statusText,
        ok: response.ok,
        headers: Object.fromEntries(response.headers.entries())
      });

      if (!response.ok) {
        let errorText;
        try {
          errorText = await response.text();
        } catch {
          errorText = `HTTP ${response.status}: ${response.statusText}`;
        }
        console.error(`❌ Error response body:`, errorText);
        throw new Error(`HTTP ${response.status}: ${response.statusText} - ${errorText}`);
      }

      const result = await response.json();
      console.log(`✅ Data for ${url}:`, result);
      setData(result);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'An error occurred';
      console.error(`❌ Error fetching ${endpoint}:`, errorMessage);
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  }, [endpoint, options]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { data, loading, error, refetch: fetchData };
};

export const apiCall = async <T>(endpoint: string, options?: RequestInit): Promise<T> => {
  // Ensure endpoint starts with /
  const cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
  const url = `${API_BASE_URL}${cleanEndpoint}`;
  
  console.log(`🚀 API Call: ${options?.method || 'GET'} ${url}`);
  
  if (options?.body) {
    console.log(`📤 Request body:`, options.body);
  }
  
  const response = await fetch(url, {
    headers: {
      'Accept': 'application/json',
      'Content-Type': 'application/json',
    },
    mode: 'cors',
    credentials: 'omit', // Don't send credentials with CORS
    ...options,
  });

  console.log(`📡 API Response for ${url}:`, {
    status: response.status,
    statusText: response.statusText,
    ok: response.ok,
    headers: Object.fromEntries(response.headers.entries())
  });

  if (!response.ok) {
    let errorText;
    try {
      errorText = await response.text();
    } catch {
      errorText = `HTTP ${response.status}: ${response.statusText}`;
    }
    console.error(`❌ API Error Response:`, errorText);
    throw new Error(`HTTP ${response.status}: ${response.statusText} - ${errorText}`);
  }

  const result = await response.json();
  console.log(`✅ API Success Response:`, result);
  
  return result;
};