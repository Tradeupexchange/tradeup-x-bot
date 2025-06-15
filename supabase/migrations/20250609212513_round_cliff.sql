/*
  # Pokemon TCG Dashboard Schema

  1. New Tables
    - `posts`
      - `id` (uuid, primary key)
      - `content` (text)
      - `likes` (integer, default 0)
      - `retweets` (integer, default 0)
      - `replies` (integer, default 0)
      - `topics` (text array)
      - `created_at` (timestamp)
      - `user_id` (uuid, foreign key to auth.users)
    
    - `metrics`
      - `id` (uuid, primary key)
      - `total_posts` (integer, default 0)
      - `avg_engagement` (decimal, default 0)
      - `total_likes` (integer, default 0)
      - `followers` (integer, default 0)
      - `date` (date)
      - `user_id` (uuid, foreign key to auth.users)
    
    - `topics`
      - `id` (uuid, primary key)
      - `name` (text)
      - `count` (integer, default 0)
      - `trend` (text, default 'stable')
      - `percentage` (decimal, default 0)
      - `user_id` (uuid, foreign key to auth.users)
    
    - `settings`
      - `id` (uuid, primary key)
      - `posts_per_day` (integer, default 12)
      - `keywords` (text array)
      - `engagement_mode` (text, default 'balanced')
      - `auto_reply` (boolean, default true)
      - `content_types` (jsonb)
      - `user_id` (uuid, foreign key to auth.users)
      - `updated_at` (timestamp)

  2. Security
    - Enable RLS on all tables
    - Add policies for authenticated users to manage their own data
*/

-- Posts table
CREATE TABLE IF NOT EXISTS posts (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  content text NOT NULL,
  likes integer DEFAULT 0,
  retweets integer DEFAULT 0,
  replies integer DEFAULT 0,
  topics text[] DEFAULT '{}',
  created_at timestamptz DEFAULT now(),
  user_id uuid REFERENCES auth.users(id) ON DELETE CASCADE
);

ALTER TABLE posts ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can manage their own posts"
  ON posts
  FOR ALL
  TO authenticated
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

-- Metrics table
CREATE TABLE IF NOT EXISTS metrics (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  total_posts integer DEFAULT 0,
  avg_engagement decimal DEFAULT 0,
  total_likes integer DEFAULT 0,
  followers integer DEFAULT 0,
  date date DEFAULT CURRENT_DATE,
  user_id uuid REFERENCES auth.users(id) ON DELETE CASCADE,
  created_at timestamptz DEFAULT now()
);

ALTER TABLE metrics ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can manage their own metrics"
  ON metrics
  FOR ALL
  TO authenticated
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

-- Topics table
CREATE TABLE IF NOT EXISTS topics (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name text NOT NULL,
  count integer DEFAULT 0,
  trend text DEFAULT 'stable' CHECK (trend IN ('up', 'down', 'stable')),
  percentage decimal DEFAULT 0,
  user_id uuid REFERENCES auth.users(id) ON DELETE CASCADE,
  created_at timestamptz DEFAULT now()
);

ALTER TABLE topics ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can manage their own topics"
  ON topics
  FOR ALL
  TO authenticated
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

-- Settings table
CREATE TABLE IF NOT EXISTS settings (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  posts_per_day integer DEFAULT 12,
  keywords text[] DEFAULT '{"Pokemon", "TCG", "Charizard", "Pikachu", "Tournament"}',
  engagement_mode text DEFAULT 'balanced' CHECK (engagement_mode IN ('conservative', 'balanced', 'aggressive')),
  auto_reply boolean DEFAULT true,
  content_types jsonb DEFAULT '{"cardPulls": true, "deckBuilding": true, "marketAnalysis": true, "tournaments": true}',
  user_id uuid REFERENCES auth.users(id) ON DELETE CASCADE,
  updated_at timestamptz DEFAULT now()
);

ALTER TABLE settings ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can manage their own settings"
  ON settings
  FOR ALL
  TO authenticated
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS posts_user_id_created_at_idx ON posts(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS metrics_user_id_date_idx ON metrics(user_id, date DESC);
CREATE INDEX IF NOT EXISTS topics_user_id_idx ON topics(user_id);
CREATE INDEX IF NOT EXISTS settings_user_id_idx ON settings(user_id);

-- Insert default settings for new users (trigger function)
CREATE OR REPLACE FUNCTION create_default_settings()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO settings (user_id)
  VALUES (NEW.id);
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE OR REPLACE TRIGGER create_default_settings_trigger
  AFTER INSERT ON auth.users
  FOR EACH ROW
  EXECUTE FUNCTION create_default_settings();