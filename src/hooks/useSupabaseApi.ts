import { useState, useEffect, useCallback } from 'react';
import { supabase, Post, Metrics, Topic, Settings } from '../lib/supabase';

interface UseSupabaseApiReturn<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
  refetch: () => void;
}

export const useSupabaseApi = <T>(
  table: string,
  query?: (queryBuilder: any) => any
): UseSupabaseApiReturn<T> => {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      let queryBuilder = supabase.from(table).select('*');
      
      if (query) {
        queryBuilder = query(queryBuilder);
      }

      const { data: result, error: fetchError } = await queryBuilder;

      if (fetchError) throw fetchError;

      setData(result as T);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  }, [table, query]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { data, loading, error, refetch: fetchData };
};

// Specific hooks for each data type
export const usePosts = (limit = 20) => {
  return useSupabaseApi<Post[]>('posts', (query) =>
    query.order('created_at', { ascending: false }).limit(limit)
  );
};

export const useMetrics = () => {
  return useSupabaseApi<Metrics[]>('metrics', (query) =>
    query.order('date', { ascending: false }).limit(1)
  );
};

export const useTopics = () => {
  return useSupabaseApi<Topic[]>('topics', (query) =>
    query.order('count', { ascending: false })
  );
};

export const useSettings = () => {
  return useSupabaseApi<Settings[]>('settings', (query) =>
    query.limit(1)
  );
};

// API functions for mutations
export const createPost = async (content: string, topics: string[] = []) => {
  const { data, error } = await supabase
    .from('posts')
    .insert([{ content, topics }])
    .select()
    .single();

  if (error) throw error;
  return data;
};

export const updateSettings = async (settings: Partial<Settings>) => {
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) throw new Error('User not authenticated');

  const { data, error } = await supabase
    .from('settings')
    .upsert([{ ...settings, user_id: user.id }])
    .select()
    .single();

  if (error) throw error;
  return data;
};

export const updateMetrics = async (metrics: Partial<Metrics>) => {
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) throw new Error('User not authenticated');

  const today = new Date().toISOString().split('T')[0];

  const { data, error } = await supabase
    .from('metrics')
    .upsert([{ ...metrics, user_id: user.id, date: today }])
    .select()
    .single();

  if (error) throw error;
  return data;
};