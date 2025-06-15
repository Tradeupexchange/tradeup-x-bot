"""
Bot Manager for Pokemon TCG Social Media Bot
Handles job creation, management, and execution
"""

import json
import os
import asyncio
import schedule
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import csv
import pandas as pd
from pathlib import Path

from content_generator import generate_viral_content, optimize_content_for_engagement
from twitter_poster import post_original_tweet, get_tweet_url

class BotManager:
    def __init__(self):
        self.data_dir = Path("data")
        self.data_dir.mkdir(exist_ok=True)
        
        self.jobs_file = self.data_dir / "bot_jobs.json"
        self.status_file = self.data_dir / "bot_status.json"
        self.settings_file = self.data_dir / "settings.json"
        
        self.running_jobs = {}  # Track running job threads
        
        # Initialize data files
        self._initialize_files()
    
    def _initialize_files(self):
        """Initialize data files if they don't exist"""
        if not self.jobs_file.exists():
            with open(self.jobs_file, 'w') as f:
                json.dump([], f)
        
        if not self.status_file.exists():
            with open(self.status_file, 'w') as f:
                json.dump({
                    "running": False,
                    "uptime": None,
                    "lastRun": None,
                    "stats": {
                        "postsToday": 0,
                        "repliesToday": 0,
                        "successRate": 100
                    }
                }, f)
        
        if not self.settings_file.exists():
            with open(self.settings_file, 'w') as f:
                json.dump({
                    "postsPerDay": 12,
                    "keywords": ["Pokemon", "TCG", "Charizard", "Pikachu"],
                    "engagementMode": "balanced",
                    "autoReply": True,
                    "contentTypes": {
                        "cardPulls": True,
                        "deckBuilding": True,
                        "marketAnalysis": True,
                        "tournaments": True
                    }
                }, f)
    
    def create_job(self, job_type: str, settings: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new bot job"""
        job_id = f"{job_type}-{int(datetime.now().timestamp())}"
        
        new_job = {
            "id": job_id,
            "type": job_type,
            "status": "stopped",
            "settings": settings,
            "createdAt": datetime.now().isoformat(),
            "lastRun": None,
            "nextRun": None,
            "stats": {
                "postsToday": 0,
                "repliesToday": 0,
                "successRate": 100
            }
        }
        
        # Load existing jobs
        with open(self.jobs_file, 'r') as f:
            jobs = json.load(f)
        
        # Add new job
        jobs.append(new_job)
        
        # Save jobs
        with open(self.jobs_file, 'w') as f:
            json.dump(jobs, f, indent=2)
        
        return new_job
    
    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific job by ID"""
        with open(self.jobs_file, 'r') as f:
            jobs = json.load(f)
        
        for job in jobs:
            if job["id"] == job_id:
                return job
        
        return None
    
    def get_all_jobs(self) -> List[Dict[str, Any]]:
        """Get all jobs"""
        with open(self.jobs_file, 'r') as f:
            return json.load(f)
    
    def update_job(self, job_id: str, updated_job: Dict[str, Any]) -> Dict[str, Any]:
        """Update a job"""
        with open(self.jobs_file, 'r') as f:
            jobs = json.load(f)
        
        for i, job in enumerate(jobs):
            if job["id"] == job_id:
                jobs[i] = updated_job
                break
        
        with open(self.jobs_file, 'w') as f:
            json.dump(jobs, f, indent=2)
        
        return updated_job
    
    async def start_job(self, job_id: str):
        """Start a bot job"""
        job = self.get_job(job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")
        
        if job_id in self.running_jobs:
            print(f"Job {job_id} is already running")
            return
        
        print(f"Starting {job['type']} job: {job_id}")
        
        # Create and start job thread
        if job["type"] == "posting":
            thread = threading.Thread(target=self._run_posting_job, args=(job,))
        else:
            thread = threading.Thread(target=self._run_reply_job, args=(job,))
        
        thread.daemon = True
        thread.start()
        
        self.running_jobs[job_id] = thread
        
        # Update job status
        job["status"] = "running"
        job["lastRun"] = datetime.now().isoformat()
        self.update_job(job_id, job)
    
    def stop_job(self, job_id: str) -> Dict[str, Any]:
        """Stop a bot job"""
        job = self.get_job(job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")
        
        # Remove from running jobs
        if job_id in self.running_jobs:
            del self.running_jobs[job_id]
        
        # Update job status
        job["status"] = "stopped"
        job["nextRun"] = None
        
        return self.update_job(job_id, job)
    
    def pause_job(self, job_id: str) -> Dict[str, Any]:
        """Pause a bot job"""
        job = self.get_job(job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")
        
        # Remove from running jobs
        if job_id in self.running_jobs:
            del self.running_jobs[job_id]
        
        # Update job status
        job["status"] = "paused"
        job["nextRun"] = None
        
        return self.update_job(job_id, job)
    
    def _run_posting_job(self, job: Dict[str, Any]):
        """Run a posting job in a separate thread"""
        job_id = job["id"]
        settings = job["settings"]
        
        posts_per_day = settings.get("postsPerDay", 12)
        posting_hours = settings.get("postingHours", {"start": 9, "end": 21})
        
        # Calculate posting interval
        active_hours = posting_hours["end"] - posting_hours["start"]
        interval_minutes = max(1, (active_hours * 60) // posts_per_day)
        
        print(f"Posting job {job_id} will post every {interval_minutes} minutes")
        
        # Post immediately if in active hours
        current_hour = datetime.now().hour
        if posting_hours["start"] <= current_hour < posting_hours["end"]:
            self._execute_post(job_id, settings)
        
        # Schedule regular posts
        while job_id in self.running_jobs:
            current_hour = datetime.now().hour
            if posting_hours["start"] <= current_hour < posting_hours["end"]:
                self._execute_post(job_id, settings)
            
            # Wait for next interval
            time.sleep(interval_minutes * 60)
    
    def _run_reply_job(self, job: Dict[str, Any]):
        """Run a reply job in a separate thread"""
        job_id = job["id"]
        settings = job["settings"]
        
        max_replies_per_hour = settings.get("maxRepliesPerHour", 10)
        keywords = settings.get("keywords", ["Pokemon", "TCG"])
        
        print(f"Reply job {job_id} monitoring keywords: {keywords}")
        
        while job_id in self.running_jobs:
            # Simulate reply monitoring and execution
            # In a real implementation, this would monitor Twitter for mentions
            print(f"Reply job {job_id} checking for mentions...")
            
            # Update stats
            self._update_job_stats(job_id, "reply_success")
            
            # Wait 5 minutes before next check
            time.sleep(5 * 60)
    
    def _execute_post(self, job_id: str, settings: Dict[str, Any]):
        """Execute a single post"""
        try:
            print(f"Executing post for job {job_id}")
            
            # Generate content
            viral_posts = generate_viral_content(1)
            
            if viral_posts:
                post = viral_posts[0]
                optimized_content = optimize_content_for_engagement(post['content'])
                
                print(f"Generated content: {optimized_content}")
                
                # Post to Twitter
                result = post_original_tweet(optimized_content)
                
                if result.get('success'):
                    print(f"✅ Successfully posted: {optimized_content[:50]}...")
                    
                    # Save to CSV
                    self._save_post_to_csv(optimized_content, result, post.get('topic', 'General'))
                    
                    # Update stats
                    self._update_job_stats(job_id, "post_success")
                    
                    if result.get('tweet_id'):
                        tweet_url = get_tweet_url(result['tweet_id'])
                        print(f"Tweet URL: {tweet_url}")
                else:
                    print(f"❌ Failed to post: {result.get('error', 'Unknown error')}")
                    self._update_job_stats(job_id, "post_failure")
            else:
                print("❌ Failed to generate content")
                self._update_job_stats(job_id, "post_failure")
                
        except Exception as e:
            print(f"❌ Error executing post: {e}")
            self._update_job_stats(job_id, "post_failure")
    
    def _save_post_to_csv(self, content: str, result: Dict[str, Any], topic: str):
        """Save post to CSV file"""
        try:
            csv_path = self.data_dir / "posts.csv"
            
            # Check if file exists and add header if needed
            file_exists = csv_path.exists()
            
            with open(csv_path, 'a', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                
                if not file_exists:
                    writer.writerow(['id', 'content', 'likes', 'retweets', 'replies', 'topics', 'timestamp'])
                
                topics = [topic, 'PokemonTCG', 'TradeUp']
                
                writer.writerow([
                    result.get('tweet_id', int(time.time())),
                    content,
                    0,  # Initial likes
                    0,  # Initial retweets
                    0,  # Initial replies
                    json.dumps(topics),
                    datetime.now().isoformat()
                ])
                
            print(f"✅ Saved post to CSV")
        except Exception as e:
            print(f"❌ Error saving post to CSV: {e}")
    
    def _update_job_stats(self, job_id: str, event_type: str):
        """Update job statistics"""
        try:
            job = self.get_job(job_id)
            if not job:
                return
            
            stats = job.get("stats", {})
            
            if event_type == "post_success":
                stats["postsToday"] = stats.get("postsToday", 0) + 1
            elif event_type == "reply_success":
                stats["repliesToday"] = stats.get("repliesToday", 0) + 1
            
            # Update success rate (simplified)
            stats["successRate"] = min(100, stats.get("successRate", 100))
            
            job["stats"] = stats
            self.update_job(job_id, job)
            
            print(f"✅ Updated job stats: {event_type}")
        except Exception as e:
            print(f"❌ Error updating job stats: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get overall bot status"""
        try:
            with open(self.status_file, 'r') as f:
                return json.load(f)
        except:
            return {
                "running": False,
                "uptime": None,
                "lastRun": None,
                "stats": {
                    "postsToday": 0,
                    "repliesToday": 0,
                    "successRate": 100
                }
            }
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get bot metrics"""
        # This would read from your metrics CSV or database
        return {
            "totalPosts": 1247,
            "avgEngagement": 8.4,
            "totalLikes": 24700,
            "followers": 3421,
            "lastUpdated": datetime.now().isoformat()
        }
    
    def get_posts(self, limit: int = 20, offset: int = 0) -> Dict[str, Any]:
        """Get recent posts"""
        try:
            csv_path = self.data_dir / "posts.csv"
            
            if not csv_path.exists():
                return {"posts": [], "total": 0, "hasMore": False}
            
            df = pd.read_csv(csv_path)
            
            # Sort by timestamp (newest first)
            df = df.sort_values('timestamp', ascending=False)
            
            # Paginate
            total = len(df)
            posts_df = df.iloc[offset:offset + limit]
            
            posts = []
            for _, row in posts_df.iterrows():
                try:
                    topics = json.loads(row['topics']) if row['topics'] else []
                except:
                    topics = []
                
                posts.append({
                    "id": row['id'],
                    "content": row['content'],
                    "engagement": {
                        "likes": int(row['likes']),
                        "retweets": int(row['retweets']),
                        "replies": int(row['replies'])
                    },
                    "timestamp": row['timestamp'],
                    "topics": topics
                })
            
            return {
                "posts": posts,
                "total": total,
                "hasMore": offset + limit < total
            }
        except Exception as e:
            print(f"Error getting posts: {e}")
            return {"posts": [], "total": 0, "hasMore": False}
    
    def get_topics(self) -> List[Dict[str, Any]]:
        """Get trending topics"""
        # Mock data for now
        return [
            {"name": "Charizard", "count": 89, "trend": "up", "percentage": 28},
            {"name": "Pikachu", "count": 76, "trend": "up", "percentage": 24},
            {"name": "Booster Packs", "count": 65, "trend": "stable", "percentage": 20},
            {"name": "Tournament", "count": 45, "trend": "up", "percentage": 14},
            {"name": "Trading", "count": 32, "trend": "down", "percentage": 10},
            {"name": "Collection", "count": 13, "trend": "stable", "percentage": 4}
        ]
    
    def get_engagement_data(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get engagement data for charts"""
        # Mock data for now
        data = []
        for i in range(days):
            date = datetime.now() - timedelta(days=i)
            data.append({
                "date": date.strftime("%Y-%m-%d"),
                "engagement": round(5 + (i * 0.5), 1),
                "posts": 10 + i
            })
        return list(reversed(data))
    
    def get_settings(self) -> Dict[str, Any]:
        """Get bot settings"""
        try:
            with open(self.settings_file, 'r') as f:
                return json.load(f)
        except:
            return {
                "postsPerDay": 12,
                "keywords": ["Pokemon", "TCG", "Charizard", "Pikachu"],
                "engagementMode": "balanced",
                "autoReply": True,
                "contentTypes": {
                    "cardPulls": True,
                    "deckBuilding": True,
                    "marketAnalysis": True,
                    "tournaments": True
                }
            }
    
    def update_settings(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        """Update bot settings"""
        with open(self.settings_file, 'w') as f:
            json.dump(settings, f, indent=2)
        return settings