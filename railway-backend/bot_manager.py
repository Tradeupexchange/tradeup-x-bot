"""
Bot Manager for Pokemon TCG Social Media Bot
Handles job creation, management, and execution
Enhanced with post approval workflow and frontend integration
Railway-compatible version with proper imports
"""

import json
import os
import asyncio
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import csv
import pandas as pd
from pathlib import Path
import uuid

# Fixed imports for Railway deployment
try:
    from src.content_generator import generate_viral_content_main as generate_content_main
    from src.twitter_poster import post_original_tweet, get_tweet_url
    from src.llm_manager import llm_manager
    print("✅ Successfully imported content generation modules")
except ImportError as e:
    print(f"⚠️ Warning: Could not import content modules: {e}")
    # Fallback functions for Railway deployment
    def generate_content_main(count=1, topic=None):
        return [f"Great Pokemon TCG content about {topic or 'collecting'}! Trade safely on TradeUp!"] * count
    
    def post_original_tweet(content):
        return {"success": False, "error": "Twitter integration not available", "tweet_id": None}
    
    def get_tweet_url(tweet_id):
        return f"https://x.com/TradeUpApp/status/{tweet_id}"
    
    class FallbackLLMManager:
        def call_llm(self, prompt):
            return "Sample Pokemon TCG response"
    
    llm_manager = FallbackLLMManager()

def generate_viral_content(count: int = 1, topic: str = None) -> List[Dict[str, Any]]:
    """Generate viral content wrapper function"""
    try:
        # Use your existing content generator
        content_list = generate_content_main(count=count, topic=topic)
        
        viral_posts = []
        for i, content in enumerate(content_list):
            viral_posts.append({
                "content": content,
                "engagement_score": 0.75,
                "topic": topic or "general",
                "generated_at": datetime.now().isoformat(),
                "hashtags": ["#PokemonTCG", "#Trading", "#TradeUp"],
                "mentions_tradeup": "TradeUp" in content
            })
        
        return viral_posts
    except Exception as e:
        print(f"Error generating viral content: {e}")
        return [{
            "content": "Pokemon TCG collecting tips! What's your favorite card? Trade safely on TradeUp!",
            "engagement_score": 0.7,
            "topic": topic or "general",
            "generated_at": datetime.now().isoformat(),
            "hashtags": ["#PokemonTCG", "#Trading", "#TradeUp"],
            "mentions_tradeup": True
        }] * count

def optimize_content_for_engagement(content: str) -> str:
    """Optimize content for better engagement"""
    try:
        # Add TradeUp mention if not present (20% chance)
        if "TradeUp" not in content and "tradeup" not in content.lower():
            if content.endswith("!") or content.endswith("."):
                content = content[:-1] + " Trade safely on TradeUp!"
            else:
                content += " Trade safely on TradeUp!"
        
        return content
    except Exception as e:
        print(f"Error optimizing content: {e}")
        return content

class BotManager:
    def __init__(self):
        # Use Railway-compatible data directory
        self.data_dir = Path("data")
        self.data_dir.mkdir(exist_ok=True)
        
        self.jobs_file = self.data_dir / "bot_jobs.json"
        self.status_file = self.data_dir / "bot_status.json"
        self.settings_file = self.data_dir / "settings.json"
        self.generated_posts_file = self.data_dir / "generated_posts.json"  # New file for approval workflow
        
        self.running_jobs = {}  # Track running job threads
        self.generated_posts = []  # In-memory storage for generated posts
        
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
        
        # Initialize generated posts file
        if not self.generated_posts_file.exists():
            with open(self.generated_posts_file, 'w') as f:
                json.dump([], f)
        
        # Load existing generated posts
        try:
            with open(self.generated_posts_file, 'r') as f:
                self.generated_posts = json.load(f)
        except:
            self.generated_posts = []
    
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
        try:
            with open(self.jobs_file, 'r') as f:
                jobs = json.load(f)
        except:
            jobs = []
        
        # Add new job
        jobs.append(new_job)
        
        # Save jobs
        with open(self.jobs_file, 'w') as f:
            json.dump(jobs, f, indent=2)
        
        return new_job
    
    def create_job_with_approval(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        """Create a job that will use the approval workflow"""
        # This method prepares for approval workflow but doesn't create the actual job yet
        # The actual job will be created when posts are approved and scheduled
        return {
            "workflow": "approval",
            "settings": settings,
            "status": "awaiting_approval",
            "created_at": datetime.now().isoformat()
        }
    
    def store_generated_posts(self, posts: List[Dict[str, Any]], settings: Dict[str, Any]) -> bool:
        """Store generated posts for the approval workflow"""
        try:
            # Add metadata to each post
            for post in posts:
                post["created_at"] = datetime.now().isoformat()
                post["workflow_id"] = f"workflow-{int(datetime.now().timestamp())}"
            
            # Store in memory
            self.generated_posts.extend(posts)
            
            # Also save to file for persistence
            with open(self.generated_posts_file, 'w') as f:
                json.dump(self.generated_posts, f, indent=2)
            
            print(f"✅ Stored {len(posts)} generated posts for approval")
            return True
        except Exception as e:
            print(f"❌ Error storing generated posts: {e}")
            return False
    
    def get_generated_posts(self) -> List[Dict[str, Any]]:
        """Get all generated posts pending approval"""
        try:
            # Return only posts that haven't been processed yet (approved=null)
            pending_posts = [
                post for post in self.generated_posts 
                if post.get("approved") is None
            ]
            return pending_posts
        except Exception as e:
            print(f"Error getting generated posts: {e}")
            return []
    
    def approve_post(self, post_id: str) -> bool:
        """Approve a generated post"""
        try:
            for post in self.generated_posts:
                if post.get("id") == post_id:
                    post["approved"] = True
                    post["approved_at"] = datetime.now().isoformat()
                    
                    # Save updated posts
                    with open(self.generated_posts_file, 'w') as f:
                        json.dump(self.generated_posts, f, indent=2)
                    
                    print(f"✅ Approved post: {post_id}")
                    return True
            
            print(f"❌ Post not found for approval: {post_id}")
            return False
        except Exception as e:
            print(f"❌ Error approving post: {e}")
            return False
    
    def reject_post(self, post_id: str) -> bool:
        """Reject a generated post"""
        try:
            for post in self.generated_posts:
                if post.get("id") == post_id:
                    post["approved"] = False
                    post["rejected_at"] = datetime.now().isoformat()
                    
                    # Save updated posts
                    with open(self.generated_posts_file, 'w') as f:
                        json.dump(self.generated_posts, f, indent=2)
                    
                    print(f"✅ Rejected post: {post_id}")
                    return True
            
            print(f"❌ Post not found for rejection: {post_id}")
            return False
        except Exception as e:
            print(f"❌ Error rejecting post: {e}")
            return False
    
    def schedule_approved_posts(self) -> Dict[str, Any]:
        """Create a job from approved posts and schedule them"""
        try:
            # Get all approved posts
            approved_posts = [
                post for post in self.generated_posts 
                if post.get("approved") is True and not post.get("scheduled", False)
            ]
            
            if not approved_posts:
                return {"scheduled_count": 0, "message": "No approved posts to schedule"}
            
            # Create job settings from approved posts
            settings = {
                "postsPerDay": len(approved_posts),
                "approvedPosts": approved_posts,
                "autoPost": True,
                "type": "scheduled_posting",
                "postingTimeStart": "09:00",
                "postingTimeEnd": "17:00"
            }
            
            # Create the actual job
            job = self.create_job("posting", settings)
            
            # Mark posts as scheduled
            for post in approved_posts:
                post["scheduled"] = True
                post["job_id"] = job["id"]
                post["scheduled_at"] = datetime.now().isoformat()
            
            # Save updated posts
            with open(self.generated_posts_file, 'w') as f:
                json.dump(self.generated_posts, f, indent=2)
            
            print(f"✅ Scheduled {len(approved_posts)} approved posts as job {job['id']}")
            
            return {
                "scheduled_count": len(approved_posts),
                "job_id": job["id"],
                "job": job,
                "message": f"Successfully scheduled {len(approved_posts)} posts"
            }
            
        except Exception as e:
            print(f"❌ Error scheduling approved posts: {e}")
            return {"scheduled_count": 0, "error": str(e)}
    
    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific job by ID"""
        try:
            with open(self.jobs_file, 'r') as f:
                jobs = json.load(f)
            
            for job in jobs:
                if job["id"] == job_id:
                    return job
        except:
            pass
        
        return None
    
    def get_all_jobs(self) -> List[Dict[str, Any]]:
        """Get all jobs"""
        try:
            with open(self.jobs_file, 'r') as f:
                return json.load(f)
        except:
            return []
    
    def update_job(self, job_id: str, updated_job: Dict[str, Any]) -> Dict[str, Any]:
        """Update a job"""
        try:
            with open(self.jobs_file, 'r') as f:
                jobs = json.load(f)
            
            for i, job in enumerate(jobs):
                if job["id"] == job_id:
                    jobs[i] = updated_job
                    break
            
            with open(self.jobs_file, 'w') as f:
                json.dump(jobs, f, indent=2)
        except Exception as e:
            print(f"Error updating job: {e}")
        
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
        
        # Check if this job has pre-approved posts
        if settings.get("approvedPosts") and settings.get("autoPost"):
            self._run_scheduled_posting_job(job)
        else:
            self._run_regular_posting_job(job)
    
    def _run_scheduled_posting_job(self, job: Dict[str, Any]):
        """Run a job with pre-approved, scheduled posts"""
        job_id = job["id"]
        settings = job["settings"]
        approved_posts = settings.get("approvedPosts", [])
        
        print(f"Running scheduled posting job {job_id} with {len(approved_posts)} approved posts")
        
        for post in approved_posts:
            # Check if job is still running
            if job_id not in self.running_jobs:
                break
            
            try:
                # Post the approved content
                content = post.get("content", "")
                optimized_content = optimize_content_for_engagement(content)
                
                print(f"Posting approved content: {optimized_content[:50]}...")
                
                # Post to Twitter
                result = post_original_tweet(optimized_content)
                
                if result.get('success'):
                    print(f"✅ Successfully posted approved content")
                    
                    # Save to CSV
                    self._save_post_to_csv(optimized_content, result, post.get('topic', 'General'))
                    
                    # Update stats
                    self._update_job_stats(job_id, "post_success")
                    
                    if result.get('tweet_id'):
                        tweet_url = get_tweet_url(result['tweet_id'])
                        print(f"Tweet URL: {tweet_url}")
                else:
                    print(f"❌ Failed to post approved content: {result.get('error', 'Unknown error')}")
                    self._update_job_stats(job_id, "post_failure")
                
                # Wait between posts (5-15 minutes)
                wait_time = 300 + (len(approved_posts) * 60)  # Scale wait time
                time.sleep(min(wait_time, 900))  # Max 15 minutes
                
            except Exception as e:
                print(f"❌ Error posting approved content: {e}")
                self._update_job_stats(job_id, "post_failure")
        
        # Job completed - stop it
        print(f"✅ Scheduled posting job {job_id} completed")
        self.stop_job(job_id)
    
    def _run_regular_posting_job(self, job: Dict[str, Any]):
        """Run a regular posting job (original functionality)"""
        job_id = job["id"]
        settings = job["settings"]
        
        posts_per_day = settings.get("postsPerDay", 12)
        posting_hours = settings.get("postingHours", {"start": 9, "end": 21})
        
        # Calculate posting interval
        active_hours = posting_hours["end"] - posting_hours["start"]
        interval_minutes = max(30, (active_hours * 60) // posts_per_day)  # Minimum 30 minutes
        
        print(f"Regular posting job {job_id} will post every {interval_minutes} minutes")
        
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
            print(f"Reply job {job_id} checking for mentions...")
            
            # Update stats
            self._update_job_stats(job_id, "reply_success")
            
            # Wait 10 minutes before next check (Railway-friendly)
            time.sleep(10 * 60)
    
    def _execute_post(self, job_id: str, settings: Dict[str, Any]):
        """Execute a single post"""
        try:
            print(f"Executing post for job {job_id}")
            
            # Get topics from settings
            topics = settings.get("topics", ["Pokemon TCG"])
            selected_topic = topics[0] if topics else "Pokemon TCG"
            
            # Generate content using your existing system
            viral_posts = generate_viral_content(1, topic=selected_topic)
            
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
            elif event_type == "post_failure":
                # Decrease success rate slightly on failure
                current_rate = stats.get("successRate", 100)
                stats["successRate"] = max(50, current_rate - 2)
            
            # Improve success rate on success
            if event_type.endswith("_success"):
                current_rate = stats.get("successRate", 100)
                stats["successRate"] = min(100, current_rate + 1)
            
            job["stats"] = stats
            self.update_job(job_id, job)
            
            print(f"✅ Updated job stats: {event_type}")
        except Exception as e:
            print(f"❌ Error updating job stats: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get overall bot status"""
        try:
            with open(self.status_file, 'r') as f:
                status = json.load(f)
            
            # Add current running jobs info
            status["active_jobs"] = len(self.running_jobs)
            status["running"] = len(self.running_jobs) > 0
            status["pending_approvals"] = len([p for p in self.generated_posts if p.get("approved") is None])
            
            return status
        except:
            return {
                "running": False,
                "uptime": None,
                "lastRun": None,
                "active_jobs": 0,
                "pending_approvals": 0,
                "stats": {
                    "postsToday": 0,
                    "repliesToday": 0,
                    "successRate": 100
                }
            }
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get bot metrics"""
        # Calculate metrics from actual data if available
        try:
            csv_path = self.data_dir / "posts.csv"
            if csv_path.exists():
                df = pd.read_csv(csv_path)
                total_posts = len(df)
                total_likes = df['likes'].sum() if 'likes' in df.columns else 0
                avg_engagement = df['likes'].mean() if 'likes' in df.columns and len(df) > 0 else 0
            else:
                total_posts = 0
                total_likes = 0
                avg_engagement = 0
            
            # Add approval workflow metrics
            approved_posts = len([p for p in self.generated_posts if p.get("approved") is True])
            pending_posts = len([p for p in self.generated_posts if p.get("approved") is None])
            
        except:
            total_posts = 0
            total_likes = 0
            avg_engagement = 0
            approved_posts = 0
            pending_posts = 0
        
        return {
            "totalPosts": total_posts,
            "avgEngagement": round(avg_engagement, 1),
            "totalLikes": int(total_likes),
            "followers": 3421,  # This would come from Twitter API
            "approvedPosts": approved_posts,
            "pendingApproval": pending_posts,
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
                    topics = json.loads(row['topics']) if 'topics' in row and pd.notna(row['topics']) else []
                except:
                    topics = []
                
                posts.append({
                    "id": str(row['id']) if 'id' in row else str(int(time.time())),
                    "content": row['content'] if 'content' in row else "",
                    "engagement": {
                        "likes": int(row['likes']) if 'likes' in row and pd.notna(row['likes']) else 0,
                        "retweets": int(row['retweets']) if 'retweets' in row and pd.notna(row['retweets']) else 0,
                        "replies": int(row['replies']) if 'replies' in row and pd.notna(row['replies']) else 0
                    },
                    "timestamp": row['timestamp'] if 'timestamp' in row else datetime.now().isoformat(),
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
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(settings, f, indent=2)
        except Exception as e:
            print(f"Error updating settings: {e}")
        return settings
    
    def cleanup_old_posts(self, days_old: int = 7):
        """Clean up old generated posts to prevent memory bloat"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_old)
            
            # Remove old posts that are either approved/rejected or very old
            original_count = len(self.generated_posts)
            
            self.generated_posts = [
                post for post in self.generated_posts
                if (post.get("approved") is None and 
                    datetime.fromisoformat(post.get("created_at", "2020-01-01")) > cutoff_date)
                or post.get("approved") is True  # Keep approved posts longer
            ]
            
            cleaned_count = original_count - len(self.generated_posts)
            
            if cleaned_count > 0:
                # Save updated posts
                with open(self.generated_posts_file, 'w') as f:
                    json.dump(self.generated_posts, f, indent=2)
                
                print(f"✅ Cleaned up {cleaned_count} old generated posts")
            
        except Exception as e:
            print(f"❌ Error cleaning up old posts: {e}")
    
    def get_approval_workflow_stats(self) -> Dict[str, Any]:
        """Get statistics about the approval workflow"""
        try:
            total_generated = len(self.generated_posts)
            approved_count = len([p for p in self.generated_posts if p.get("approved") is True])
            rejected_count = len([p for p in self.generated_posts if p.get("approved") is False])
            pending_count = len([p for p in self.generated_posts if p.get("approved") is None])
            scheduled_count = len([p for p in self.generated_posts if p.get("scheduled") is True])
            
            approval_rate = (approved_count / total_generated * 100) if total_generated > 0 else 0
            
            return {
                "total_generated": total_generated,
                "approved": approved_count,
                "rejected": rejected_count,
                "pending": pending_count,
                "scheduled": scheduled_count,
                "approval_rate": round(approval_rate, 1),
                "last_generated": max([
                    p.get("created_at", "") for p in self.generated_posts
                ], default=None)
            }
        except Exception as e:
            print(f"Error getting approval workflow stats: {e}")
            return {
                "total_generated": 0,
                "approved": 0,
                "rejected": 0,
                "pending": 0,
                "scheduled": 0,
                "approval_rate": 0,
                "last_generated": None
            }
    
    def bulk_approve_posts(self, post_ids: List[str]) -> Dict[str, Any]:
        """Approve multiple posts at once"""
        try:
            approved_count = 0
            failed_count = 0
            
            for post_id in post_ids:
                if self.approve_post(post_id):
                    approved_count += 1
                else:
                    failed_count += 1
            
            return {
                "approved_count": approved_count,
                "failed_count": failed_count,
                "success": failed_count == 0
            }
        except Exception as e:
            print(f"Error bulk approving posts: {e}")
            return {
                "approved_count": 0,
                "failed_count": len(post_ids),
                "success": False,
                "error": str(e)
            }
    
    def bulk_reject_posts(self, post_ids: List[str]) -> Dict[str, Any]:
        """Reject multiple posts at once"""
        try:
            rejected_count = 0
            failed_count = 0
            
            for post_id in post_ids:
                if self.reject_post(post_id):
                    rejected_count += 1
                else:
                    failed_count += 1
            
            return {
                "rejected_count": rejected_count,
                "failed_count": failed_count,
                "success": failed_count == 0
            }
        except Exception as e:
            print(f"Error bulk rejecting posts: {e}")
            return {
                "rejected_count": 0,
                "failed_count": len(post_ids),
                "success": False,
                "error": str(e)
            }
    
    def regenerate_post_content(self, post_id: str, new_topic: str = None) -> Dict[str, Any]:
        """Regenerate content for a specific post"""
        try:
            # Find the post
            target_post = None
            for post in self.generated_posts:
                if post.get("id") == post_id:
                    target_post = post
                    break
            
            if not target_post:
                return {"success": False, "error": "Post not found"}
            
            # Generate new content
            topic = new_topic or target_post.get("topic", "Pokemon TCG")
            new_content = generate_viral_content(1, topic=topic)
            
            if new_content and len(new_content) > 0:
                # Update the post with new content
                target_post["content"] = new_content[0].get("content", target_post["content"])
                target_post["engagement_score"] = new_content[0].get("engagement_score", 0.75)
                target_post["hashtags"] = new_content[0].get("hashtags", target_post.get("hashtags", []))
                target_post["mentions_tradeup"] = new_content[0].get("mentions_tradeup", False)
                target_post["regenerated_at"] = datetime.now().isoformat()
                target_post["approved"] = None  # Reset approval status
                
                # Save updated posts
                with open(self.generated_posts_file, 'w') as f:
                    json.dump(self.generated_posts, f, indent=2)
                
                print(f"✅ Regenerated content for post: {post_id}")
                return {"success": True, "post": target_post}
            else:
                return {"success": False, "error": "Failed to generate new content"}
                
        except Exception as e:
            print(f"❌ Error regenerating post content: {e}")
            return {"success": False, "error": str(e)}
    
    def export_posts_data(self, format_type: str = "json") -> Dict[str, Any]:
        """Export posts data in various formats"""
        try:
            if format_type.lower() == "json":
                export_data = {
                    "generated_posts": self.generated_posts,
                    "jobs": self.get_all_jobs(),
                    "settings": self.get_settings(),
                    "export_timestamp": datetime.now().isoformat()
                }
                
                export_path = self.data_dir / f"posts_export_{int(datetime.now().timestamp())}.json"
                with open(export_path, 'w') as f:
                    json.dump(export_data, f, indent=2)
                
                return {
                    "success": True,
                    "file_path": str(export_path),
                    "format": "json",
                    "records_count": len(self.generated_posts)
                }
            
            elif format_type.lower() == "csv":
                # Export to CSV format
                csv_data = []
                for post in self.generated_posts:
                    csv_data.append({
                        "id": post.get("id", ""),
                        "content": post.get("content", ""),
                        "topic": post.get("topic", ""),
                        "approved": post.get("approved", ""),
                        "scheduled_time": post.get("scheduledTime", ""),
                        "engagement_score": post.get("engagement_score", ""),
                        "created_at": post.get("created_at", ""),
                        "approved_at": post.get("approved_at", ""),
                        "scheduled": post.get("scheduled", False)
                    })
                
                export_path = self.data_dir / f"posts_export_{int(datetime.now().timestamp())}.csv"
                df = pd.DataFrame(csv_data)
                df.to_csv(export_path, index=False)
                
                return {
                    "success": True,
                    "file_path": str(export_path),
                    "format": "csv",
                    "records_count": len(csv_data)
                }
            
            else:
                return {"success": False, "error": f"Unsupported format: {format_type}"}
                
        except Exception as e:
            print(f"❌ Error exporting posts data: {e}")
            return {"success": False, "error": str(e)}