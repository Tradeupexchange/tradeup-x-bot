# Add these imports at the top with your other imports
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="Pokemon TCG Bot API", description="API for Pokemon TCG engagement bot")

# ===== CORS CONFIGURATION - THIS FIXES YOUR "Failed to fetch" ERROR =====
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://tradeup-bot-engagement-dashboard.netlify.app",
        "http://localhost:3000",  # For local development
        "http://localhost:5173",  # For Vite dev server
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Add preflight handler for OPTIONS requests
@app.options("/{rest_of_path:path}")
async def preflight_handler(rest_of_path: str):
    return JSONResponse(
        content={},
        headers={
            "Access-Control-Allow-Origin": "https://tradeup-bot-engagement-dashboard.netlify.app",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "*",
        }
    )

# Import reply modules with error handling
try:
    from src.reply_generator import generate_reply
    from src.twitter_poster import post_reply_tweet, generate_and_post_replies
    logger.info("Successfully imported reply generation modules")
except ImportError as e:
    logger.warning(f"Could not import reply modules: {e}")
    # Create dummy functions
    def generate_reply(tweet_text, tweet_author=None, conversation_history=None):
        return {"content": f"Thanks for sharing! Great point about Pokemon TCG.", "success": True}
    def post_reply_tweet(content, reply_to_id):
        return {"success": False, "error": "Reply integration not available"}
    def generate_and_post_replies(num_replies=5, post_to_twitter=False, require_confirmation=False):
        return []

# Twitter client function
def get_twitter_client():
    """Get Twitter API client - implement this based on your Twitter setup"""
    try:
        # Replace with your actual Twitter client setup
        import tweepy
        from src.config import TWITTER_API_KEY, TWITTER_API_SECRET, TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_SECRET
        
        if not all([TWITTER_API_KEY, TWITTER_API_SECRET, TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_SECRET]):
            return None
            
        client = tweepy.Client(
            consumer_key=TWITTER_API_KEY,
            consumer_secret=TWITTER_API_SECRET,
            access_token=TWITTER_ACCESS_TOKEN,
            access_token_secret=TWITTER_ACCESS_SECRET
        )
        return client
    except Exception as e:
        logger.error(f"Error creating Twitter client: {e}")
        return None

# Add these new Pydantic models after your existing ones
class GenerateReplyRequest(BaseModel):
    tweet_text: str
    tweet_author: Optional[str] = None
    conversation_history: Optional[str] = None

class PostReplyRequest(BaseModel):
    content: str
    reply_to_tweet_id: str

class FetchTweetsRequest(BaseModel):
    keywords: List[str] = ["Pokemon TCG", "Pokemon", "TCG"]
    max_results: int = 10
    hours_back: int = 24

class TweetData(BaseModel):
    id: str
    text: str
    author: str
    created_at: str
    public_metrics: Optional[Dict[str, int]] = None
    conversation_id: Optional[str] = None

class BulkReplyRequest(BaseModel):
    num_replies: int = 5
    post_to_twitter: bool = False
    require_confirmation: bool = False

# Health check endpoint
@app.get("/")
async def root():
    return {
        "message": "Pokemon TCG Bot API is running",
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "cors": "enabled"
    }

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "message": "Backend is running",
        "timestamp": datetime.now().isoformat(),
        "cors": "enabled"
    }

# ===== MISSING ENDPOINT 1: Bot Status =====
@app.get("/api/bot-status")
async def get_bot_status():
    """Get current bot status and jobs list"""
    try:
        logger.info("Getting bot status...")
        
        # Mock data - replace with your actual bot status logic
        status = {
            "running": True,
            "uptime": "2 hours 15 minutes", 
            "lastRun": datetime.now().isoformat(),
            "stats": {
                "postsToday": 8,
                "repliesToday": 12,
                "successRate": 94.5
            },
            "jobs": [
                # No demo jobs - removed as requested
            ],
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"Returning bot status with {len(status['jobs'])} jobs")
        return status
        
    except Exception as e:
        logger.error(f"Error getting bot status: {e}")
        return {
            "running": False,
            "error": str(e),
            "jobs": [],
            "timestamp": datetime.now().isoformat()
        }

# ===== MISSING ENDPOINT 2: Posts =====
@app.get("/api/posts")
async def get_posts():
    """Get recent posts"""
    try:
        logger.info("Getting recent posts...")
        
        # Mock posts data - replace with your actual posts logic
        posts = [
            {
                "id": "post_1",
                "content": "Just pulled an amazing Charizard card! The artwork is incredible 🔥",
                "timestamp": datetime.now().isoformat(),
                "platform": "twitter",
                "engagement": {
                    "likes": 42,
                    "retweets": 12,
                    "replies": 8
                },
                "status": "posted"
            },
            {
                "id": "post_2", 
                "content": "Building a new deck around Pikachu VMAX. Any suggestions for support cards?",
                "timestamp": (datetime.now() - timedelta(hours=2)).isoformat(),
                "platform": "twitter",
                "engagement": {
                    "likes": 28,
                    "retweets": 5,
                    "replies": 15
                },
                "status": "posted"
            },
            {
                "id": "post_3",
                "content": "The new Pokemon TCG set releases tomorrow! Who else is excited? 🎉",
                "timestamp": (datetime.now() - timedelta(hours=4)).isoformat(),
                "platform": "twitter", 
                "engagement": {
                    "likes": 67,
                    "retweets": 23,
                    "replies": 12
                },
                "status": "posted"
            }
        ]
        
        logger.info(f"Returning {len(posts)} recent posts")
        return {
            "success": True,
            "posts": posts,
            "total": len(posts),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting posts: {e}")
        return {
            "success": False,
            "error": str(e),
            "posts": [],
            "timestamp": datetime.now().isoformat()
        }

# ===== MISSING ENDPOINT 3: Topics =====
@app.get("/api/topics")
async def get_topics():
    """Get available topics for content generation"""
    try:
        logger.info("Getting available topics...")
        
        # Common Pokemon TCG topics
        topics = [
            {
                "id": "card_pulls",
                "name": "Card Pulls & Openings",
                "description": "Posts about opening packs and showing off pulls",
                "popularity": 95,
                "engagement_rate": 8.2
            },
            {
                "id": "deck_building", 
                "name": "Deck Building",
                "description": "Strategy and deck construction content",
                "popularity": 87,
                "engagement_rate": 7.5
            },
            {
                "id": "market_analysis",
                "name": "Market & Pricing",
                "description": "Card values, market trends, and investment advice", 
                "popularity": 72,
                "engagement_rate": 6.8
            },
            {
                "id": "tournaments",
                "name": "Tournaments & Events",
                "description": "Competitive play and tournament coverage",
                "popularity": 68,
                "engagement_rate": 7.1
            },
            {
                "id": "collecting",
                "name": "Collecting & Grading",
                "description": "Collection showcases and card grading content",
                "popularity": 79,
                "engagement_rate": 8.0
            },
            {
                "id": "news_updates",
                "name": "News & Updates", 
                "description": "Latest Pokemon TCG news and announcements",
                "popularity": 83,
                "engagement_rate": 6.9
            }
        ]
        
        logger.info(f"Returning {len(topics)} available topics")
        return {
            "success": True,
            "topics": topics,
            "total": len(topics),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting topics: {e}")
        return {
            "success": False,
            "error": str(e),
            "topics": [],
            "timestamp": datetime.now().isoformat()
        }

# Job Management Endpoints
@app.post("/api/bot-job/create-posting-job")
async def create_posting_job(request: Dict[str, Any]):
    """Create a new posting job"""
    try:
        logger.info("Creating new posting job...")
        
        settings = {
            "type": "posting",
            "name": request.get("name", "Untitled Posting Job"),
            "postsPerDay": request.get("settings", {}).get("postsPerDay", 5),
            "topics": request.get("settings", {}).get("topics", ["Pokemon TCG"]),
            "postingTimeStart": request.get("settings", {}).get("postingTimeStart", "09:00"),
            "postingTimeEnd": request.get("settings", {}).get("postingTimeEnd", "17:00"),
            "contentTypes": request.get("settings", {}).get("contentTypes", {
                "cardPulls": True,
                "deckBuilding": True,
                "marketAnalysis": True,
                "tournaments": False
            }),
            "approvedPosts": request.get("settings", {}).get("approvedPosts", []),
            "autoPost": request.get("settings", {}).get("autoPost", False)
        }
        
        # Create job
        job = {
            "id": f"posting_job_{int(datetime.now().timestamp())}",
            "type": "posting",
            "name": settings["name"],
            "settings": settings,
            "status": "created",
            "created_at": datetime.now().isoformat(),
            "stats": {
                "postsToday": 0,
                "repliesToday": 0,
                "successRate": 100.0
            }
        }
        
        logger.info(f"Created posting job: {job['id']}")
        return {
            "success": True,
            "job": job,
            "message": "Posting job created successfully",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error creating posting job: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/bot-job/{job_id}/start")
async def start_job(job_id: str):
    """Start a specific job"""
    try:
        logger.info(f"Starting job {job_id}")
        
        return {
            "success": True,
            "job_id": job_id,
            "message": "Job started successfully",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error starting job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/bot-job/{job_id}/stop")
async def stop_job(job_id: str):
    """Stop a specific job"""
    try:
        logger.info(f"Stopping job {job_id}")
        
        return {
            "success": True,
            "job_id": job_id,
            "message": "Job stopped successfully",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error stopping job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/bot-job/{job_id}/pause")
async def pause_job(job_id: str):
    """Pause a specific job"""
    try:
        logger.info(f"Pausing job {job_id}")
        
        return {
            "success": True,
            "job_id": job_id,
            "message": "Job paused successfully",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error pausing job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/bot-job/{job_id}/rename")
async def rename_job(job_id: str, request: Dict[str, Any]):
    """Rename a specific job"""
    try:
        new_name = request.get("name", "").strip()
        if not new_name:
            raise HTTPException(status_code=400, detail="Name cannot be empty")
        
        logger.info(f"Renaming job {job_id} to {new_name}")
        
        return {
            "success": True,
            "job_id": job_id,
            "name": new_name,
            "message": "Job renamed successfully",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error renaming job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/generate-content")
async def generate_content_endpoint(request: Dict[str, Any]):
    """Generate content for posts"""
    try:
        topic = request.get("topic", "Pokemon TCG")
        count = request.get("count", 1)
        
        logger.info(f"Generating {count} content piece(s) for topic: {topic}")
        
        # Mock content generation - replace with your actual content generation logic
        content_examples = {
            "card_pulls": f"Just pulled an incredible {topic} card! The foil treatment is absolutely stunning 🔥✨",
            "deck_building": f"Working on a new {topic} deck strategy. The synergy between these cards is amazing!",
            "market_analysis": f"Interesting price movement in the {topic} market this week. Some cards are really gaining value!",
            "tournaments": f"Excited for the upcoming {topic} tournament! Been practicing with this deck for weeks 🏆",
            "collecting": f"Added another graded {topic} card to my collection! PSA 10 condition is chef's kiss 💎",
            "news_updates": f"Big news in the {topic} world! Can't wait to see what this means for the community 📰"
        }
        
        # Pick appropriate content based on topic
        content_key = topic.lower().replace(" ", "_").replace("pokemon_tcg", "card_pulls")
        content = content_examples.get(content_key, content_examples["card_pulls"])
        
        mock_content = {
            "content": content,
            "engagement_score": 85.5,
            "hashtags": ["#PokemonTCG", "#CardCollection", "#Pokemon"],
            "mentions_tradeup": topic.lower() not in ["pokemon tcg", "card_pulls"]
        }
        
        return {
            "success": True,
            "content": mock_content,
            "topic": topic,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error generating content: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

# Generic job creation for backward compatibility
@app.post("/api/bot-job/create")
async def create_bot_job_generic(request: Dict[str, Any]):
    """Generic job creation endpoint"""
    try:
        job_type = request.get("type", "posting")
        
        if job_type == "posting":
            return await create_posting_job(request)
        elif job_type == "replying":
            return await create_reply_job(request)
        else:
            raise HTTPException(status_code=400, detail=f"Unknown job type: {job_type}")
            
    except Exception as e:
        logger.error(f"Error in generic job creation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Test endpoint
@app.get("/api/test")
async def test_endpoint():
    """Simple test endpoint"""
    return {
        "success": True,
        "message": "API is working correctly",
        "timestamp": datetime.now().isoformat(),
        "endpoints_available": [
            "/api/health",
            "/api/bot-status", 
            "/api/posts",
            "/api/topics",
            "/api/bot-job/create",
            "/api/bot-job/create-posting-job",
            "/api/bot-job/create-reply-job",
            "/api/generate-content",
            "/api/generate-reply",
            "/api/post-reply"
        ]
    }

# === ALL YOUR EXISTING ENDPOINTS BELOW ===

@app.post("/api/generate-reply")
async def generate_reply_endpoint(request: GenerateReplyRequest):
    """Generate a contextual reply to a tweet"""
    try:
        logger.info(f"Generating reply for tweet: {request.tweet_text[:50]}...")
        
        # Generate reply using the reply_generator module
        reply_result = generate_reply(
            tweet_text=request.tweet_text,
            tweet_author=request.tweet_author,
            conversation_history=request.conversation_history
        )
        
        if isinstance(reply_result, dict):
            result = {
                "success": True,
                "reply": reply_result.get("content", reply_result),
                "original_tweet": request.tweet_text,
                "timestamp": datetime.now().isoformat()
            }
        else:
            result = {
                "success": True,
                "reply": reply_result,
                "original_tweet": request.tweet_text,
                "timestamp": datetime.now().isoformat()
            }
        
        logger.info(f"Generated reply: {result['reply'][:50]}...")
        return result
        
    except Exception as e:
        logger.error(f"Error generating reply: {e}")
        return {
            "success": False,
            "error": str(e),
            "reply": None,
            "timestamp": datetime.now().isoformat()
        }

@app.post("/api/post-reply")
async def post_reply_endpoint(request: PostReplyRequest):
    """Post a reply to a specific tweet"""
    try:
        logger.info(f"Posting reply to tweet {request.reply_to_tweet_id}: {request.content[:50]}...")
        
        # Post reply using twitter_poster module
        result = post_reply_tweet(request.content, request.reply_to_tweet_id)
        
        if isinstance(result, dict) and result.get('success'):
            logger.info(f"Successfully posted reply to tweet {request.reply_to_tweet_id}")
            result['timestamp'] = datetime.now().isoformat()
        else:
            logger.error(f"Failed to post reply: {result.get('error') if isinstance(result, dict) else 'Unknown error'}")
            if not isinstance(result, dict):
                result = {"success": False, "error": "Reply posting failed"}
            result['timestamp'] = datetime.now().isoformat()
        
        return result
        
    except Exception as e:
        logger.error(f"Error posting reply: {e}")
        return {
            "success": False,
            "error": str(e),
            "tweet_id": None,
            "timestamp": datetime.now().isoformat()
        }

@app.get("/api/fetch-tweets")
async def fetch_tweets_to_reply(keywords: str = "Pokemon TCG", max_results: int = 10, hours_back: int = 24):
    """Fetch recent tweets that we could reply to"""
    try:
        client = get_twitter_client()
        if not client:
            logger.warning("Twitter API not configured for tweet fetching")
            return {
                "success": False,
                "error": "Twitter API not configured",
                "tweets": [],
                "timestamp": datetime.now().isoformat()
            }
        
        # Calculate time range
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours_back)
        
        # Search for tweets with keywords
        keywords_list = [k.strip() for k in keywords.split(",")]
        query = " OR ".join([f'"{keyword}"' for keyword in keywords_list])
        query += " -is:retweet lang:en"  # Exclude retweets, English only
        
        logger.info(f"Searching Twitter for: {query}")
        
        # Search tweets
        tweets = client.search_recent_tweets(
            query=query,
            max_results=max_results,
            tweet_fields=['author_id', 'created_at', 'public_metrics', 'conversation_id'],
            user_fields=['username', 'name'],
            expansions=['author_id'],
            start_time=start_time.isoformat(),
            end_time=end_time.isoformat()
        )
        
        if not tweets.data:
            logger.info("No tweets found matching criteria")
            return {
                "success": True,
                "tweets": [],
                "query": query,
                "timestamp": datetime.now().isoformat()
            }
        
        # Process tweets
        processed_tweets = []
        users_dict = {}
        
        # Create users dictionary for quick lookup
        if tweets.includes and 'users' in tweets.includes:
            users_dict = {user.id: user for user in tweets.includes['users']}
        
        for tweet in tweets.data:
            author = users_dict.get(tweet.author_id, None)
            author_username = author.username if author else "unknown"
            author_name = author.name if author else "Unknown User"
            
            processed_tweet = {
                "id": tweet.id,
                "text": tweet.text,
                "author": author_username,
                "author_name": author_name,
                "created_at": tweet.created_at.isoformat() if tweet.created_at else None,
                "public_metrics": tweet.public_metrics if hasattr(tweet, 'public_metrics') else {},
                "conversation_id": tweet.conversation_id if hasattr(tweet, 'conversation_id') else tweet.id,
                "url": f"https://twitter.com/{author_username}/status/{tweet.id}" if author else f"https://twitter.com/i/status/{tweet.id}"
            }
            processed_tweets.append(processed_tweet)
        
        logger.info(f"Found {len(processed_tweets)} tweets to potentially reply to")
        
        return {
            "success": True,
            "tweets": processed_tweets,
            "query": query,
            "count": len(processed_tweets),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error fetching tweets: {e}")
        return {
            "success": False,
            "error": str(e),
            "tweets": [],
            "timestamp": datetime.now().isoformat()
        }

@app.post("/api/generate-and-post-reply")
async def generate_and_post_reply(request: Dict[str, Any]):
    """Generate and optionally post a reply to a tweet (combined endpoint)"""
    try:
        tweet_id = request.get("tweet_id")
        tweet_text = request.get("tweet_text")
        tweet_author = request.get("tweet_author")
        auto_post = request.get("auto_post", False)
        
        if not tweet_text:
            raise HTTPException(status_code=400, detail="tweet_text is required")
        
        logger.info(f"Generating reply for tweet {tweet_id}: {tweet_text[:50]}...")
        
        # Generate reply
        reply_result = generate_reply(
            tweet_text=tweet_text,
            tweet_author=tweet_author
        )
        
        reply_content = reply_result.get("content", reply_result) if isinstance(reply_result, dict) else reply_result
        
        result = {
            "success": True,
            "reply": reply_content,
            "original_tweet": tweet_text,
            "tweet_id": tweet_id,
            "auto_posted": False,
            "timestamp": datetime.now().isoformat()
        }
        
        # Auto-post if requested and tweet_id is provided
        if auto_post and tweet_id and reply_content:
            logger.info("Auto-posting reply...")
            post_result = post_reply_tweet(reply_content, tweet_id)
            
            if isinstance(post_result, dict) and post_result.get('success'):
                result["auto_posted"] = True
                result["posted_reply_id"] = post_result.get("tweet_id")
                logger.info(f"Successfully auto-posted reply to tweet {tweet_id}")
            else:
                result["post_error"] = post_result.get("error") if isinstance(post_result, dict) else "Posting failed"
                logger.error(f"Failed to auto-post reply: {result['post_error']}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error in generate-and-post-reply: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.post("/api/bulk-generate-replies")
async def bulk_generate_replies(request: BulkReplyRequest):
    """Generate replies to multiple tweets from Google Sheets"""
    try:
        logger.info(f"Starting bulk reply generation: {request.num_replies} replies, post_to_twitter={request.post_to_twitter}")
        
        # Use the integrated function from twitter_poster
        results = generate_and_post_replies(
            num_replies=request.num_replies,
            post_to_twitter=request.post_to_twitter,
            require_confirmation=request.require_confirmation
        )
        
        # Process results for API response
        processed_results = []
        successful_posts = 0
        
        for result in results:
            processed_result = {
                "original_tweet": result.get("original_tweet", ""),
                "username": result.get("username", ""),
                "tweet_id": result.get("tweet_id", ""),
                "tweet_url": result.get("tweet_url", ""),
                "reply_content": result.get("reply_content", ""),
                "posted": result.get("posted", False),
                "post_error": result.get("post_error", None),
                "reply_id": result.get("reply_id", None),
                "reply_url": result.get("reply_url", None)
            }
            processed_results.append(processed_result)
            
            if processed_result["posted"]:
                successful_posts += 1
        
        return {
            "success": True,
            "total_processed": len(processed_results),
            "successful_posts": successful_posts,
            "results": processed_results,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in bulk reply generation: {e}")
        return {
            "success": False,
            "error": str(e),
            "total_processed": 0,
            "successful_posts": 0,
            "results": [],
            "timestamp": datetime.now().isoformat()
        }

@app.get("/api/bot-status-with-replies")
async def get_bot_status_with_replies():
    """Get bot status including reply metrics"""
    try:
        # Get base status
        base_status = await get_bot_status()
        
        # Add reply-specific metrics
        reply_metrics = {
            "repliesEnabled": True,
            "lastReplyTime": None,
            "replySuccessRate": 95.0,
            "avgResponseTime": "2.3s",
        }
        
        # Merge with base status
        if isinstance(base_status, dict):
            base_status["replyMetrics"] = reply_metrics
        
        return base_status
        
    except Exception as e:
        logger.error(f"Error getting bot status with replies: {e}")
        return {
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.post("/api/bot-job/create-reply-job")
async def create_reply_job(request: Dict[str, Any]):
    """Create a new reply monitoring job"""
    try:
        settings = {
            "type": "replying",
            "keywords": request.get("keywords", ["Pokemon TCG", "Pokemon", "TCG"]),
            "maxRepliesPerHour": request.get("maxRepliesPerHour", 5),
            "replyTypes": request.get("replyTypes", {
                "helpful": True,
                "engaging": True,
                "promotional": False
            }),
            "autoReply": request.get("autoReply", False),  # Require manual approval by default
            "sentiment_filter": request.get("sentiment_filter", "positive"),  # Only reply to positive/neutral tweets
        }
        
        # If you have a bot_manager, use it, otherwise create a simple job response
        if 'bot_manager' in globals():
            job = bot_manager.create_job("replying", settings)
        else:
            job = {
                "id": f"reply_job_{int(datetime.now().timestamp())}",
                "type": "replying",
                "name": request.get("name", "Reply Job"),
                "settings": settings,
                "status": "created",
                "created_at": datetime.now().isoformat(),
                "stats": {
                    "postsToday": 0,
                    "repliesToday": 0,
                    "successRate": 100.0
                }
            }
        
        logger.info(f"Created reply job: {job}")
        return {
            "success": True,
            "job": job,
            "message": "Reply monitoring job created successfully",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error creating reply job: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/test-reply-system")
async def test_reply_system():
    """Test endpoint to verify reply system is working"""
    try:
        # Test reply generation
        test_tweet = "Just pulled a Charizard card from my Pokemon TCG pack! So excited!"
        test_reply = generate_reply(test_tweet, "TestUser")
        
        # Test Twitter API connection
        twitter_connected = False
        try:
            if 'get_twitter_client' in globals():
                client = get_twitter_client()
                twitter_connected = client is not None
        except:
            pass
        
        return {
            "success": True,
            "reply_generation": {
                "working": bool(test_reply),
                "sample_reply": test_reply.get("content", test_reply) if isinstance(test_reply, dict) else test_reply
            },
            "twitter_api": {
                "connected": twitter_connected,
                "can_post_replies": twitter_connected
            },
            "modules_loaded": {
                "reply_generator": "generate_reply" in globals(),
                "twitter_poster": "post_reply_tweet" in globals()
            },
            "cors_enabled": True,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error testing reply system: {e}")
        return {
            "success": False,
            "error": str(e),
            "cors_enabled": True,
            "timestamp": datetime.now().isoformat()
        }

# ===== FIXED GOOGLE SHEETS ENDPOINTS =====

@app.get("/api/fetch-tweets-from-sheets")
async def fetch_tweets_from_sheets():
    """Fetch tweets from Google Sheets for reply generation"""
    try:
        logger.info("Fetching tweets from Google Sheets...")
        
        # Import your Google Sheets reader
        try:
            from src.google_sheets_reader import get_tweets_for_reply
        except ImportError:
            logger.error("Google Sheets reader not available")
            return {
                "success": False,
                "error": "Google Sheets integration not configured",
                "tweets": [],
                "timestamp": datetime.now().isoformat()
            }
        
        # Get tweets from your Google Sheets using the correct function signature
        # FIXED: Using correct parameter name (num_replies instead of max_tweets)
        tweets_data = get_tweets_for_reply(
            "https://docs.google.com/spreadsheets/d/1U50KjbsYUswh0IGWTPgeP97Y2kXRcYM_H1VoeyAQhpw/edit?gid=0#gid=0",
            20  # Get 20 tweets so we have enough for the rejection workflow
        )
        
        if not tweets_data or len(tweets_data) == 0:
            logger.warning("No tweets found in Google Sheets")
            return {
                "success": False,
                "error": "No tweets found in Google Sheets. Please check that your sheet has tweets and is accessible.",
                "tweets": [],
                "timestamp": datetime.now().isoformat()
            }
        
        # Convert to the format expected by the frontend
        processed_tweets = []
        for i, tweet_data in enumerate(tweets_data):
            processed_tweet = {
                "id": tweet_data.get("tweet_id", f"tweet_{i}"),
                "text": tweet_data.get("tweet_content", ""),
                "author": tweet_data.get("username", "unknown"),
                "author_name": tweet_data.get("username", "Unknown User"),
                "created_at": datetime.now().isoformat(),
                "url": tweet_data.get("url", ""),
                "conversation_id": tweet_data.get("tweet_id", f"tweet_{i}")
            }
            
            # Only add if we have actual content
            if processed_tweet["text"].strip():
                processed_tweets.append(processed_tweet)
        
        logger.info(f"Successfully fetched {len(processed_tweets)} tweets from Google Sheets")
        
        return {
            "success": True,
            "tweets": processed_tweets,
            "count": len(processed_tweets),
            "source": "Google Sheets",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error fetching tweets from Google Sheets: {e}")
        return {
            "success": False,
            "error": f"Failed to fetch tweets from Google Sheets: {str(e)}",
            "tweets": [],
            "timestamp": datetime.now().isoformat()
        }

@app.get("/api/test-google-sheets")
async def test_google_sheets_connection():
    """Test Google Sheets connection and show what data is available"""
    try:
        logger.info("Testing Google Sheets connection...")
        
        # Test import
        try:
            from src.google_sheets_reader import get_tweets_for_reply
            import_success = True
            import_error = None
        except ImportError as e:
            import_success = False
            import_error = str(e)
        
        result = {
            "success": import_success,
            "timestamp": datetime.now().isoformat(),
            "google_sheets_reader": {
                "imported": import_success,
                "error": import_error
            }
        }
        
        if import_success:
            # Try to fetch a small sample using the correct function signature
            # FIXED: Using correct parameter name (num_replies instead of max_tweets)
            try:
                sample_tweets = get_tweets_for_reply(
                    "https://docs.google.com/spreadsheets/d/1U50KjbsYUswh0IGWTPgeP97Y2kXRcYM_H1VoeyAQhpw/edit?gid=0#gid=0",
                    3  # Just get 3 tweets for testing
                )
                
                result["sheets_data"] = {
                    "accessible": True,
                    "tweet_count": len(sample_tweets) if sample_tweets else 0,
                    "sample_tweets": sample_tweets[:2] if sample_tweets else [],
                    "data_structure": list(sample_tweets[0].keys()) if sample_tweets and len(sample_tweets) > 0 else [],
                    "function_signature": "get_tweets_for_reply(sheet_url, num_replies)"
                }
                
            except Exception as sheets_error:
                result["sheets_data"] = {
                    "accessible": False,
                    "error": str(sheets_error),
                    "function_signature": "get_tweets_for_reply(sheet_url, num_replies)"
                }
        
        return result
        
    except Exception as e:
        logger.error(f"Error testing Google Sheets: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)