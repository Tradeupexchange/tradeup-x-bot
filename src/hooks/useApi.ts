import { useState, useEffect, useCallback } from 'react';

// Debug environment variables
console.log('🔍 DEBUG - Environment variables:');
console.log('- import.meta.env.VITE_RAILWAY_API_URL:', import.meta.env.VITE_RAILWAY_API_URL);
console.log('- import.meta.env.DEV:', import.meta.env.DEV);
console.log('- import.meta.env.PROD:', import.meta.env.PROD);
console.log('- import.meta.env.MODE:', import.meta.env.MODE);
console.log('- All env vars:', import.meta.env);

// Use Railway backend URL for API calls
const API_BASE_URL = 
  import.meta.env.VITE_RAILWAY_API_URL ||
  (import.meta.env.DEV ? 'http://localhost:8000' : 'https://fallback-url.railway.app');

console.log('🎯 Final API_BASE_URL:', API_BASE_URL);

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
      
      const fullUrl = `${API_BASE_URL}${endpoint}`;
      console.log('🌐 Making request to:', fullUrl);
      
      const response = await fetch(fullUrl, {
        headers: {
          'Content-Type': 'application/json',
        },
        ...options,
      });

      console.log('📡 Response status:', response.status);
      console.log('📡 Response ok:', response.ok);

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      setData(result);
    } catch (err) {
      console.error('❌ API Error:', err);
      setError(err instanceof Error ? err.message : 'An error occurred');
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
  const fullUrl = `${API_BASE_URL}${endpoint}`;
  console.log('🚀 apiCall to:', fullUrl);
  
  const response = await fetch(fullUrl, {
    headers: {
      'Content-Type': 'application/json',
    },
    ...options,
  });

  console.log('📡 apiCall response status:', response.status);
  console.log('📡 apiCall response ok:', response.ok);

  if (!response.ok) {
    const errorText = await response.text();
    console.error('❌ apiCall error response:', errorText);
    throw new Error(`HTTP error! status: ${response.status} - ${errorText}`);
  }

  return response.json();
};