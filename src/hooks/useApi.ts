import { useState, useEffect, useCallback, useRef } from 'react';

// Debug environment variables
console.log('🔍 DEBUG - Environment variables:');
console.log('- import.meta.env.VITE_RAILWAY_API_URL:', import.meta.env.VITE_RAILWAY_API_URL);
console.log('- import.meta.env.DEV:', import.meta.env.DEV);
console.log('- import.meta.env.PROD:', import.meta.env.PROD);
console.log('- import.meta.env.MODE:', import.meta.env.MODE);

// Use Railway backend URL for API calls
const API_BASE_URL = 
  import.meta.env.VITE_RAILWAY_API_URL ||
  (import.meta.env.DEV ? 'http://localhost:8000' : 'https://fallback-url.railway.app');

console.log('🎯 Final API_BASE_URL:', API_BASE_URL);

// 🎯 CENTRALIZED REFRESH INTERVAL - Change this one value to affect all components!
const REFRESH_INTERVAL_MINUTES = 60;
const REFRESH_INTERVAL_MS = REFRESH_INTERVAL_MINUTES * 60 * 1000; // 60 minutes in milliseconds

// Special longer interval for Twitter API to prevent rate limiting
const TWITTER_REFRESH_INTERVAL_MINUTES = 120; // 2 hours for Twitter
const TWITTER_REFRESH_INTERVAL_MS = TWITTER_REFRESH_INTERVAL_MINUTES * 60 * 1000;

console.log(`⏰ Using ${REFRESH_INTERVAL_MINUTES}-minute refresh interval for all API calls`);
console.log(`🐦 Using ${TWITTER_REFRESH_INTERVAL_MINUTES}-minute refresh interval for Twitter API calls`);

interface ApiResponse<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
  lastFetch: Date | null;
  refetch: () => void;
}

interface UseApiOptions extends RequestInit {
  // Option to disable auto-refresh for one-time calls
  autoRefresh?: boolean;
  // Option to fetch immediately on mount
  fetchOnMount?: boolean;
}

export const useApi = <T>(endpoint: string, options: UseApiOptions = {}): ApiResponse<T> => {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastFetch, setLastFetch] = useState<Date | null>(null);
  
  // Use refs to avoid dependency issues
  const endpointRef = useRef(endpoint);
  const optionsRef = useRef(options);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  // Update refs when props change
  endpointRef.current = endpoint;
  optionsRef.current = options;

  const fetchData = useCallback(async (isManual: boolean = false) => {
    try {
      if (!isManual) {
        setLoading(true);
      }
      setError(null);
      
      const fullUrl = `${API_BASE_URL}${endpointRef.current}`;
      console.log(`🌐 ${isManual ? 'Manual' : 'Auto'} request to:`, fullUrl);
      
      // Destructure options to avoid including our custom properties
      const { autoRefresh, fetchOnMount, ...fetchOptions } = optionsRef.current;
      
      const response = await fetch(fullUrl, {
        headers: {
          'Content-Type': 'application/json',
        },
        ...fetchOptions,
      });

      console.log('📡 Response status:', response.status);
      console.log('📡 Response ok:', response.ok);

      if (!response.ok) {
        // Special handling for rate limiting errors
        if (response.status === 429) {
          throw new Error(`Rate limit exceeded. Please wait before making more requests.`);
        }
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      setData(result);
      setLastFetch(new Date());
      
      console.log(`✅ Successfully fetched data from ${endpointRef.current}`);
    } catch (err) {
      console.error('❌ API Error:', err);
      setError(err instanceof Error ? err.message : 'An error occurred');
      
      // Don't clear existing data on error, just show error message
      setLastFetch(new Date()); // Still update last fetch time to show we tried
    } finally {
      setLoading(false);
    }
  }, []);

  // Manual refetch function
  const refetch = useCallback(() => {
    console.log(`🔄 Manual refetch triggered for ${endpointRef.current}`);
    fetchData(true);
  }, [fetchData]);

  useEffect(() => {
    const { autoRefresh = true, fetchOnMount = true } = options;
    
    // Initial fetch on mount (if enabled)
    if (fetchOnMount) {
      console.log(`🚀 Initial fetch for ${endpoint}`);
      fetchData(false);
    }
    
    // Set up auto-refresh interval (if enabled)
    if (autoRefresh) {
      // Use longer interval for Twitter endpoints to prevent rate limiting
      const isTwitterEndpoint = endpoint.includes('twitter-metrics');
      const intervalMinutes = isTwitterEndpoint ? TWITTER_REFRESH_INTERVAL_MINUTES : REFRESH_INTERVAL_MINUTES;
      const intervalMs = isTwitterEndpoint ? TWITTER_REFRESH_INTERVAL_MS : REFRESH_INTERVAL_MS;
      
      console.log(`⏰ Setting up ${intervalMinutes}-minute auto-refresh for ${endpoint}${isTwitterEndpoint ? ' (Twitter endpoint)' : ''}`);
      
      intervalRef.current = setInterval(() => {
        console.log(`🔄 Auto-refresh triggered for ${endpoint} (${intervalMinutes} minutes elapsed)`);
        fetchData(false);
      }, intervalMs);
    }

    // Cleanup function
    return () => {
      if (intervalRef.current) {
        console.log(`🧹 Cleaning up auto-refresh interval for ${endpoint}`);
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [endpoint, fetchData]); // Only depend on endpoint, not options

  return { data, loading, error, lastFetch, refetch };
};

// Enhanced apiCall function with better error handling
export const apiCall = async <T>(endpoint: string, options?: RequestInit): Promise<T> => {
  const fullUrl = `${API_BASE_URL}${endpoint}`;
  console.log('🚀 apiCall to:', fullUrl);
  
  try {
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
      
      // Special handling for rate limiting
      if (response.status === 429) {
        throw new Error(`Rate limit exceeded. Please try again later.`);
      }
      
      throw new Error(`HTTP error! status: ${response.status} - ${errorText}`);
    }

    const result = await response.json();
    console.log('✅ apiCall successful');
    return result;
  } catch (err) {
    console.error('❌ apiCall failed:', err);
    throw err;
  }
};

// Utility function to get the current refresh interval (for components that want to display it)
export const getRefreshInterval = () => ({
  minutes: REFRESH_INTERVAL_MINUTES,
  milliseconds: REFRESH_INTERVAL_MS,
  displayText: `${REFRESH_INTERVAL_MINUTES} minutes`
});

// Hook for components that want to show next refresh time
export const useNextRefreshTime = (lastFetch: Date | null) => {
  const [nextRefresh, setNextRefresh] = useState<Date | null>(null);

  useEffect(() => {
    if (lastFetch) {
      const next = new Date(lastFetch.getTime() + REFRESH_INTERVAL_MS);
      setNextRefresh(next);
    }
  }, [lastFetch]);

  return nextRefresh;
};