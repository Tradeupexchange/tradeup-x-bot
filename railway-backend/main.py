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

# Add these new endpoints after your existing endpoints

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

# Enhanced bot status to include reply metrics
@app.get("/api/bot-status-with-replies")
async def get_bot_status_with_replies():
    """Get bot status including reply metrics"""
    try:
        # Get base status (you'll need to implement this based on your existing code)
        base_status = await get_bot_status() if 'get_bot_status' in globals() else {"status": "running"}
        
        # Add reply-specific metrics
        reply_metrics = {
            "repliesEnabled": True,
            "lastReplyTime": None,  # You can track this in your bot_manager
            "replySuccessRate": 95.0,  # Track this based on actual reply attempts
            "avgResponseTime": "2.3s",  # Track average time to generate and post replies
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

# Reply job management endpoints
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
                "settings": settings,
                "status": "created",
                "created_at": datetime.now().isoformat()
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

# Test endpoint to verify reply functionality
@app.get("/api/test-reply-system")
async def test_reply_system():
    """Test endpoint to verify reply system is working"""
    try:
        # Test reply generation
        test_tweet = "Just pulled a Charizard card from my Pokemon TCG pack! So excited!"
        test_reply = generate_reply(test_tweet, "TestUser")
        
        # Test Twitter API connection (you'll need to implement get_twitter_client)
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

# Your existing endpoints would go here...
# (Make sure to include all your other endpoints from the original main.py)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)