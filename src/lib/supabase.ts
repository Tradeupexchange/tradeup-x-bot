import { createClient } from '@supabase/supabase-js';

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY;

if (!supabaseUrl || !supabaseAnonKey) {
  throw new Error('Missing Supabase environment variables');
}

export const supabase = createClient(supabaseUrl, supabaseAnonKey);

// Database types
export interface Post {
  id: string;
  content: string;
  likes: number;
  retweets: number;
  replies: number;
  topics: string[];
  created_at: string;
  user_id: string;
}

export interface Metrics {
  id: string;
  total_posts: number;
  avg_engagement: number;
  total_likes: number;
  followers: number;
  date: string;
  user_id: string;
  created_at: string;
}

export interface Topic {
  id: string;
  name: string;
  count: number;
  trend: 'up' | 'down' | 'stable';
  percentage: number;
  user_id: string;
  created_at: string;
}

export interface Settings {
  id: string;
  posts_per_day: number;
  keywords: string[];
  engagement_mode: 'conservative' | 'balanced' | 'aggressive';
  auto_reply: boolean;
  content_types: {
    cardPulls: boolean;
    deckBuilding: boolean;
    marketAnalysis: boolean;
    tournaments: boolean;
  };
  user_id: string;
  updated_at: string;
}